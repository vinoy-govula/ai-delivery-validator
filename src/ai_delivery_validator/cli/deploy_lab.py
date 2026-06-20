#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from ai_delivery_validator.services.deploy_lab import deploy_lab


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy lab stack from staging directory.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--staging-dir", required=True, type=Path)
    parser.add_argument("--skip-compose", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    try:
        result = asyncio.run(
            deploy_lab(
                manifest,
                args.staging_dir,
                skip_compose=args.skip_compose,
            )
        )
    except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
