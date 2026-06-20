from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ai_runtime_manager.assessment.checkpoints import approve_checkpoint
from ai_runtime_manager.assessment.report_builder import build_assessment_report
from ai_delivery_validator.services.kit_workflow import (
    deployment_payload_from_assessment,
    sizing_payload_from_assessment,
)

EOI = (
    Path(__file__).resolve().parents[1].parent
    / "ai-runtime-manager/docs/schemas/examples/eoi-intent.example.json"
)
INTERNAL = {
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


@pytest.fixture
def approved_assessment() -> dict:
    eoi = json.loads(EOI.read_text(encoding="utf-8"))
    report = build_assessment_report(eoi, INTERNAL)
    return approve_checkpoint(report, "cp2_assessment_approved", actor="client@example.com")


def test_sizing_payload_from_assessment(approved_assessment: dict) -> None:
    payload = sizing_payload_from_assessment(approved_assessment)
    assert payload["users"] == approved_assessment["sizing"]["users"]
    assert payload["model"] == approved_assessment["recommendation"]["production_model"]


def test_deployment_payload_from_assessment(approved_assessment: dict) -> None:
    payload = deployment_payload_from_assessment(approved_assessment)
    assert payload["profile"] in {"starter", "business", "enterprise"}
    assert payload["model"]


@pytest.mark.asyncio
async def test_generate_kit_and_deployment(tmp_path: Path, approved_assessment: dict) -> None:
    from ai_delivery_validator.services.kit_workflow import generate_kit_and_deployment

    branding = {"organisation_name": "Acme", "primary_colour": "#000000"}
    with (
        patch(
            "ai_delivery_validator.services.kit_workflow.post_sizing",
            new=AsyncMock(return_value={"recommended_profile": "business"}),
        ),
        patch(
            "ai_delivery_validator.services.kit_workflow.post_generate_deployment",
            new=AsyncMock(
                return_value={
                    "deployment_id": "dep-1",
                    "artifacts": [{"filename": "docker-compose.yml", "content": "services: {}"}],
                }
            ),
        ),
    ):
        manifest, deployment = await generate_kit_and_deployment(
            approved_assessment,
            branding,
            tmp_path,
        )
    assert manifest["manifest_id"]
    assert (tmp_path / "playground-kit.manifest.json").exists()
    assert (tmp_path / "control-centre-branding.env").exists()
    assert deployment["deployment_id"] == "dep-1"
