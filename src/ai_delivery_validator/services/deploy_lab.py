"""Lab deployment orchestration via docker compose."""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from ai_runtime_manager.assessment.checkpoints import can_deploy_lab
from ai_delivery_validator.config import settings


async def _wait_for_health(url: str, *, timeout_seconds: float = 180.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    async with httpx.AsyncClient(timeout=5.0) as client:
        while time.monotonic() < deadline:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return True
            except httpx.HTTPError:
                pass
            await asyncio.sleep(3)
    return False


def _compose_file(staging_dir: Path) -> Path | None:
    artifacts = staging_dir / "deployment-artifacts"
    for name in ("docker-compose.yml", "docker-compose.yaml"):
        candidate = artifacts / name
        if candidate.exists():
            return candidate
    candidate = staging_dir / name
    if candidate.exists():
        return candidate
    return None


async def deploy_lab(
    manifest: dict[str, Any],
    staging_dir: Path,
    *,
    compose_command: str | None = None,
    skip_compose: bool = False,
) -> dict[str, Any]:
    """Run docker compose up and wait for platform health endpoints."""
    if not can_deploy_lab(manifest):
        raise ValueError("cp2 and cp3 must be approved before lab deploy")

    staging_dir.mkdir(parents=True, exist_ok=True)
    compose_path = _compose_file(staging_dir)
    result: dict[str, Any] = {
        "compose_file": str(compose_path) if compose_path else None,
        "compose_started": False,
        "health_checks": {},
    }

    if not skip_compose:
        if compose_path is None:
            raise FileNotFoundError("docker-compose.yml not found in staging directory")
        cmd = (compose_command or settings.docker_compose_command).split() + [
            "-f",
            str(compose_path),
            "up",
            "-d",
        ]
        subprocess.run(cmd, check=True, cwd=compose_path.parent)
        result["compose_started"] = True

    access = manifest.get("access", {})
    public_url = access.get("public_url", settings.gateway_base_url).rstrip("/")
    gateway_health = f"{public_url}/healthz"
    cc_path = access.get("control_centre_path", "/control-centre")
    cc_health = f"{public_url}{cc_path}/healthz".replace("//", "/").replace(":/", "://")

    result["health_checks"]["gateway"] = await _wait_for_health(gateway_health)
    result["health_checks"]["control_centre"] = await _wait_for_health(
        cc_health,
        timeout_seconds=60.0,
    )

    manifest_copy = dict(manifest)
    manifest_copy["status"] = "active"
    (staging_dir / "playground-kit.manifest.json").write_text(
        json.dumps(manifest_copy, indent=2),
        encoding="utf-8",
    )
    return result
