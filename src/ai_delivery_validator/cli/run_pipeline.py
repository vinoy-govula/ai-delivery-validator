#!/usr/bin/env python3
"""End-to-end delivery pipeline: generate kit, deploy lab, validate."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from ai_runtime_manager.assessment.checkpoints import approve_checkpoint

from ai_delivery_validator.services.deploy_lab import deploy_lab
from ai_delivery_validator.services.kit_workflow import (
    approve_cp3,
    generate_kit_and_deployment,
)
from ai_delivery_validator.services.validate import validate_manifest


async def run_pipeline(
    assessment_path: Path,
    branding_path: Path,
    staging_dir: Path,
    *,
    api_key: str,
    skip_deploy: bool = False,
    skip_validate: bool = False,
    approve_cp3_actor: str = "delivery@example.com",
    runtime_manager_url: str | None = None,
    gateway_base_url: str | None = None,
) -> dict[str, object]:
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    branding = json.loads(branding_path.read_text(encoding="utf-8"))

    manifest, deployment = await generate_kit_and_deployment(
        assessment,
        branding,
        staging_dir,
        runtime_manager_base_url=runtime_manager_url,
    )
    manifest = approve_cp3(manifest, approve_cp3_actor)
    manifest_path = staging_dir / "playground-kit.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    deploy_result: dict[str, object] | None = None
    if not skip_deploy:
        deploy_result = await deploy_lab(manifest, staging_dir, skip_compose=True)

    validation_result: dict[str, object] | None = None
    if not skip_validate:
        validation_result = await validate_manifest(
            manifest_path,
            staging_dir / "validation-output",
            api_key=api_key,
            gateway_base_url=gateway_base_url,
            runtime_manager_base_url=runtime_manager_url,
        )
        if validation_result["report"]["status"] == "passed":
            assessment = approve_checkpoint(
                assessment,
                "cp4_ship_approved",
                actor=approve_cp3_actor,
            )
            assessment["status"] = "ready_for_client_delivery"
            (staging_dir / "assessment-report.json").write_text(
                json.dumps(assessment, indent=2),
                encoding="utf-8",
            )

    return {
        "manifest_id": manifest["manifest_id"],
        "deployment_id": deployment.get("deployment_id"),
        "deploy_result": deploy_result,
        "validation_result": validation_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run delivery pipeline.")
    parser.add_argument("--assessment", required=True, type=Path)
    parser.add_argument("--branding", required=True, type=Path)
    parser.add_argument("--staging-dir", required=True, type=Path)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--skip-deploy", action="store_true")
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--runtime-manager-url", default=None)
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()

    try:
        result = asyncio.run(
            run_pipeline(
                args.assessment,
                args.branding,
                args.staging_dir,
                api_key=args.api_key,
                skip_deploy=args.skip_deploy,
                skip_validate=args.skip_validate,
                runtime_manager_url=args.runtime_manager_url,
                gateway_base_url=args.base_url,
            )
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
