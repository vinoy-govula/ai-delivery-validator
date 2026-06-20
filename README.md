# AI Delivery Validator

Lab deploy orchestration and full-stack validation for Adoption Studio playground kits.

## Prerequisites

Platform services must be running with a valid Gateway bootstrap key — see [deployment-catalog/README.md](../deployment-catalog/README.md) and [ai-gateway/README.md](../ai-gateway/README.md).

```powershell
$env:RUNTIME_MANAGER_BASE_URL = "http://localhost:8001"
$env:AI_PLATFORM_BASE_URL = "http://localhost:8000"
$env:AI_PLATFORM_API_KEY = "sk-your-bootstrap-key"
```

## Commands

```powershell
pip install -e ../ai-runtime-manager
pip install -e ".[dev]"

delivery-generate-kit --assessment assessment-report.json --branding branding.json --output-dir ./lab/acme-health
delivery-deploy-lab --manifest ./lab/acme-health/playground-kit.manifest.json --staging-dir ./lab/acme-health
delivery-validate --manifest ./lab/acme-health/playground-kit.manifest.json --output-dir ./validation-output
delivery-pipeline --assessment assessment-report.json --branding branding.json --staging-dir ./lab/acme-health --api-key sk-your-bootstrap-key
```

## Environment

| Variable | Purpose |
|----------|---------|
| `RUNTIME_MANAGER_BASE_URL` | Runtime Manager API |
| `AI_PLATFORM_BASE_URL` | Gateway base URL for validation |
| `AI_PLATFORM_API_KEY` | Gateway API key for validation |
