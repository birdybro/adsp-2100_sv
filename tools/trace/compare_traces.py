#!/usr/bin/env python3
"""Compare two common-schema NDJSON retirement traces."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import sys
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.trace.adsp2100_trace import (
    TraceWord,
    compare_trace_streams,
    trace_stream_from_ndjson,
)


def _json_value(value: object) -> object:
    if isinstance(value, TraceWord):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare original ADSP-2100 differential retirement traces"
    )
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument(
        "--state",
        action="append",
        default=None,
        metavar="PATH",
        help="compare only this state path; repeat for a projection",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    try:
        left = trace_stream_from_ndjson(options.left.read_text(encoding="utf-8"))
        right = trace_stream_from_ndjson(options.right.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True))
        return 2
    mismatches = compare_trace_streams(
        left, right, requested_state=options.state
    )
    for mismatch in mismatches:
        print(
            json.dumps(
                {
                    "path": mismatch.path,
                    "left": _json_value(mismatch.left),
                    "right": _json_value(mismatch.right),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
