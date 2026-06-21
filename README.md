# AI Delivery Validator

Lab deploy orchestration and full-stack validation for Adoption Studio playground kits.

## Prerequisites

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13. Sibling checkout of [ai-runtime-manager](../ai-runtime-manager) is required (path dependency).

Platform services must be running with a valid Gateway bootstrap key — see [deployment-catalog/README.md](../deployment-catalog/README.md) and [ai-gateway/README.md](../ai-gateway/README.md).

```powershell
$env:RUNTIME_MANAGER_BASE_URL = "http://localhost:8001"
$env:AI_PLATFORM_BASE_URL = "http://localhost:8000"
$env:AI_PLATFORM_API_KEY = "sk-your-bootstrap-key"
```

## Setup

```powershell
cd ai-delivery-validator
uv venv --python 3.13
uv sync --extra dev
```

## Commands

```powershell
uv run delivery-generate-kit --assessment assessment-report.json --branding branding.json --output-dir ./lab/acme-health
uv run delivery-deploy-lab --manifest ./lab/acme-health/playground-kit.manifest.json --staging-dir ./lab/acme-health
uv run delivery-validate --manifest ./lab/acme-health/playground-kit.manifest.json --output-dir ./validation-output
uv run delivery-pipeline --assessment assessment-report.json --branding branding.json --staging-dir ./lab/acme-health --api-key sk-your-bootstrap-key
```

## Run Tests

```powershell
uv run pytest -v
```

## Environment

| Variable | Purpose |
|----------|---------|
| `RUNTIME_MANAGER_BASE_URL` | Runtime Manager API |
| `AI_PLATFORM_BASE_URL` | Gateway base URL for validation |
| `AI_PLATFORM_API_KEY` | Gateway API key for validation |
