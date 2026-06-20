"""Runtime Manager API client for sizing and deployment generation."""

from __future__ import annotations

from typing import Any

import httpx

from ai_delivery_validator.config import settings


async def post_sizing(payload: dict[str, Any], *, base_url: str | None = None) -> dict[str, Any]:
    url = (base_url or settings.runtime_manager_base_url).rstrip("/")
    async with httpx.AsyncClient(base_url=url, timeout=60.0) as client:
        response = await client.post("/api/v1/sizing", json=payload)
        response.raise_for_status()
        body = response.json()
    return body.get("data", body)


async def post_generate_deployment(
    payload: dict[str, Any],
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    url = (base_url or settings.runtime_manager_base_url).rstrip("/")
    async with httpx.AsyncClient(base_url=url, timeout=120.0) as client:
        response = await client.post("/api/v1/deployments/generate", json=payload)
        response.raise_for_status()
        body = response.json()
    return body.get("data", body)
