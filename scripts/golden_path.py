#!/usr/bin/env python3
"""Golden-path walkthrough for Adoption Studio → Delivery Validator lifecycle."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

from ai_runtime_manager.assessment.checkpoints import approve_checkpoint
from ai_runtime_manager.assessment.report_builder import build_assessment_report
from ai_runtime_manager.assessment.narrative import write_narrative_file
from ai_runtime_manager.export.pipeline_csv import export_pipeline_csv

from ai_delivery_validator.cli.run_pipeline import run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Golden-path E2E demo (offline-friendly).")
    parser.add_argument(
        "--eoi",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "../ai-runtime-manager/docs/schemas/examples/eoi-intent.example.json",
    )
    parser.add_argument("--output-root", type=Path, default=Path("./golden-path-output"))
    parser.add_argument("--api-key", default="sk-test")
    parser.add_argument("--skip-validate", action="store_true", default=True)
    return parser


async def _async_main(args: argparse.Namespace) -> int:
    output_root = args.output_root
    lead_dir = output_root / "data" / "lead-golden"
    lead_dir.mkdir(parents=True, exist_ok=True)

    eoi = json.loads(args.eoi.read_text(encoding="utf-8"))
    (lead_dir / "eoi-intent.json").write_text(json.dumps(eoi, indent=2), encoding="utf-8")

    internal = {
        "executive_sponsor_identified": True,
        "ai_strategy_documented": "draft",
        "document_corpus_ready": "partially_curated",
        "data_classification_in_place": True,
        "compliance_frameworks": ["privacy_act"],
        "it_ops_capacity": "moderate",
        "deployment_target": "private_cloud",
        "concurrent_users": 25,
        "daily_requests": 8000,
        "change_champion_identified": True,
        "staff_ai_literacy": "moderate",
    }

    report = build_assessment_report(eoi, internal, cp1_approved=True)
    report = approve_checkpoint(report, "cp1_lead_qualified", actor="sales@example.com")
    report = approve_checkpoint(report, "cp2_assessment_approved", actor="client@example.com")
    assessment_path = lead_dir / "assessment-report.json"
    assessment_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    await write_narrative_file(report, lead_dir, use_llm=False)

    branding = {
        "organisation_name": report["client"]["display_name"],
        "primary_colour": "#0B5FFF",
        "welcome_message": "Welcome to your private AI playground.",
    }
    branding_path = lead_dir / "branding.json"
    branding_path.write_text(json.dumps(branding, indent=2), encoding="utf-8")

    staging_dir = output_root / "lab" / report["client"]["slug"]
    staging_dir.mkdir(parents=True, exist_ok=True)

    mock_sizing = AsyncMock(return_value={"recommended_profile": report["sizing"]["recommended_profile"]})
    mock_generate = AsyncMock(
        return_value={
            "deployment_id": "golden-dep-1",
            "artifacts": [{"filename": "docker-compose.yml", "content": "services: {}"}],
        }
    )

    with (
        patch("ai_delivery_validator.services.kit_workflow.post_sizing", mock_sizing),
        patch("ai_delivery_validator.services.kit_workflow.post_generate_deployment", mock_generate),
    ):
        pipeline_result = await run_pipeline(
            assessment_path,
            branding_path,
            staging_dir,
            api_key=args.api_key,
            skip_deploy=True,
            skip_validate=args.skip_validate,
        )

    export_pipeline_csv(output_root / "data", output_root / "exports", as_zip=True)

    summary = {
        "lead_dir": str(lead_dir),
        "staging_dir": str(staging_dir),
        "pipeline": pipeline_result,
        "exports": str(output_root / "exports"),
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_async_main(_build_parser().parse_args())))


if __name__ == "__main__":
    main()
