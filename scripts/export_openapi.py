from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "docs" / "api" / "openapi.json"


def render_contract() -> bytes:
    """Build the schema against isolated data so exporting never writes user data."""

    with TemporaryDirectory(prefix="exchange-openapi-") as temporary_directory:
        previous_data_dir = os.environ.get("EXCHANGE_INFO_DATA_DIR")
        os.environ["EXCHANGE_INFO_DATA_DIR"] = temporary_directory
        try:
            from exchange_info.api import create_app
            from exchange_info.openapi_contract import serialize_openapi_contract

            schema = create_app(Path(temporary_directory)).openapi()
            return serialize_openapi_contract(schema)
        finally:
            if previous_data_dir is None:
                os.environ.pop("EXCHANGE_INFO_DATA_DIR", None)
            else:
                os.environ["EXCHANGE_INFO_DATA_DIR"] = previous_data_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export or verify the frozen Web/Flutter OpenAPI contract."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Snapshot path (default: docs/api/openapi.json).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the existing snapshot differs from the generated contract.",
    )
    args = parser.parse_args(argv)
    output = args.output.resolve()
    rendered = render_contract()

    if args.check:
        if not output.exists():
            print(f"OpenAPI snapshot is missing: {output}", file=sys.stderr)
            return 1
        if output.read_bytes() != rendered:
            print(
                "OpenAPI contract drift detected. "
                "Review the API change, then run python scripts/export_openapi.py.",
                file=sys.stderr,
            )
            return 1
        print(f"OpenAPI contract is current: {output}")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(rendered)
    print(f"Wrote OpenAPI contract: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
