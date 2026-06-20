#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from ai_delivery_validator.services.kit_workflow import generate_kit_and_deployment


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate playground kit and RM deployment.")
    parser.add_argument("--assessment", required=True, type=Path)
    parser.add_argument("--branding", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--public-url", default=None)
    parser.add_argument("--runtime-manager-url", default=None)
    args = parser.parse_args()

    assessment = json.loads(args.assessment.read_text(encoding="utf-8"))
    branding = json.loads(args.branding.read_text(encoding="utf-8"))

    try:
        manifest, _ = asyncio.run(
            generate_kit_and_deployment(
                assessment,
                branding,
                args.output_dir,
                runtime_manager_base_url=args.runtime_manager_url,
                public_url=args.public_url,
            )
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"Manifest: {args.output_dir / 'playground-kit.manifest.json'}")
    print(f"Manifest ID: {manifest['manifest_id']}")


if __name__ == "__main__":
    main()
