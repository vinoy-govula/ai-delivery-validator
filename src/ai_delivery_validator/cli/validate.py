#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from ai_delivery_validator.services.validate import validate_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate playground deployment.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("validation-output"))
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--runtime-manager-url", default=None)
    args = parser.parse_args()

    try:
        result = asyncio.run(
            validate_manifest(
                args.manifest,
                args.output_dir,
                api_key=args.api_key,
                gateway_base_url=args.base_url,
                runtime_manager_base_url=args.runtime_manager_url,
            )
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    status = result["report"]["status"]
    print(f"Validation status: {status}")
    print(f"Report JSON: {result['json_path']}")
    print(f"Report Markdown: {result['markdown_path']}")
    raise SystemExit(0 if status == "passed" else 1)


if __name__ == "__main__":
    main()
