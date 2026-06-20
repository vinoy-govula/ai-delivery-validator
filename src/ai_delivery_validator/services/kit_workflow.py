"""Generate playground kit manifest and Runtime Manager deployment artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_runtime_manager.assessment.checkpoints import approve_checkpoint
from ai_runtime_manager.delivery.playground_kit import build_playground_manifest

from ai_delivery_validator.services.runtime_client import post_generate_deployment, post_sizing


def sizing_payload_from_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
    sizing = assessment.get("sizing", {})
    recommendation = assessment.get("recommendation", {})
    return {
        "users": sizing.get("users", 20),
        "concurrent_users": sizing.get("concurrent_users", 5),
        "daily_requests": sizing.get("daily_requests", 1000),
        "target_latency_ms": sizing.get("target_latency_ms", 3000),
        "model_size_b": sizing.get("model_size_b", 7.0),
        "model": recommendation.get("production_model"),
    }


def deployment_payload_from_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
    sizing = assessment.get("sizing", {})
    recommendation = assessment.get("recommendation", {})
    profile = sizing.get("recommended_profile", "business")
    runtime_map = {"starter": "llama.cpp", "business": "vllm", "enterprise": "vllm"}
    return {
        "profile": profile,
        "model": recommendation.get("production_model", "qwen3-7b"),
        "runtime": runtime_map.get(profile, "vllm"),
    }


async def generate_kit_and_deployment(
    assessment: dict[str, Any],
    branding: dict[str, Any],
    output_dir: Path,
    *,
    runtime_manager_base_url: str | None = None,
    public_url: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Write manifest, sizing result, and deployment artifacts to output_dir."""
    manifest = build_playground_manifest(assessment, branding, public_url=public_url)
    output_dir.mkdir(parents=True, exist_ok=True)

    sizing_result = await post_sizing(
        sizing_payload_from_assessment(assessment),
        base_url=runtime_manager_base_url,
    )
    deployment_result = await post_generate_deployment(
        deployment_payload_from_assessment(assessment),
        base_url=runtime_manager_base_url,
    )

    manifest["deployment"]["runtime_manager"]["deployment_id"] = deployment_result.get(
        "deployment_id"
    )
    manifest_path = output_dir / "playground-kit.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    (output_dir / "sizing-result.json").write_text(
        json.dumps(sizing_result, indent=2),
        encoding="utf-8",
    )

    artifacts_dir = output_dir / "deployment-artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for artifact in deployment_result.get("artifacts", []):
        filename = artifact.get("filename", "artifact.txt")
        content = artifact.get("content", "")
        (artifacts_dir / filename).write_text(content, encoding="utf-8")

    branding_env = {
        "CC_BRANDING_ORG_NAME": branding.get(
            "organisation_name",
            assessment.get("client", {}).get("display_name", ""),
        ),
        "CC_BRANDING_LOGO_URL": branding.get("logo_url", ""),
        "CC_BRANDING_PRIMARY_COLOUR": branding.get("primary_colour", "#0B5FFF"),
        "CC_BRANDING_WELCOME_MESSAGE": branding.get("welcome_message", ""),
    }
    (output_dir / "control-centre-branding.env").write_text(
        "\n".join(f"{key}={value}" for key, value in branding_env.items()),
        encoding="utf-8",
    )

    return manifest, deployment_result


def approve_cp3(manifest: dict[str, Any], actor: str) -> dict[str, Any]:
    updated = approve_checkpoint(manifest, "cp3_deploy_test_approved", actor=actor)
    updated["status"] = "active"
    return updated
