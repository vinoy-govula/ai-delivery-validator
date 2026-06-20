"""Wrap playground validation harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_runtime_manager.validation.playground import (
    load_manifest,
    run_playground_validation,
    write_deployment_report,
)

from ai_delivery_validator.config import settings


async def validate_manifest(
    manifest_path: Path,
    output_dir: Path,
    *,
    api_key: str | None = None,
    gateway_base_url: str | None = None,
    runtime_manager_base_url: str | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    result = await run_playground_validation(
        manifest,
        api_key=api_key or settings.gateway_api_key,
        gateway_base_url=gateway_base_url or settings.gateway_base_url,
        runtime_manager_base_url=runtime_manager_base_url or settings.runtime_manager_base_url,
    )
    json_path, md_path = write_deployment_report(result, output_dir)

    manifest["validation"]["last_run_at"] = result.report.get("completed_at")
    manifest["validation"]["last_run_status"] = result.report.get("status")
    manifest["validation"]["validation_report_id"] = result.report.get("report_id")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "report": result.report,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }
