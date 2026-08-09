#!/usr/bin/env python3
"""Generate or replay a bounded legal program into a common trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sim.differential.legal_programs import (
    LegalProgram,
    generate_legal_program,
    run_model_program,
)
from tools.trace.adsp2100_trace import trace_stream_to_ndjson


def _integer(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not an integer"
        ) from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate or replay a bounded original ADSP-2100 legal program"
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--program-in",
        type=Path,
        metavar="PATH",
        help="strict canonical corpus to replay",
    )
    source.add_argument(
        "--seed",
        type=_integer,
        help="unsigned 64-bit generator seed (decimal or 0x-prefixed)",
    )
    parser.add_argument(
        "--length",
        type=_integer,
        help="generated instruction count; required with --seed",
    )
    parser.add_argument(
        "--origin",
        type=_integer,
        help="generated 14-bit PM origin (default: 4)",
    )
    parser.add_argument(
        "--program-out",
        type=Path,
        metavar="PATH",
        help="write the canonical replay corpus",
    )
    parser.add_argument(
        "--trace-out",
        type=Path,
        metavar="PATH",
        help="write common NDJSON instead of printing it",
    )
    return parser


def _reject_path_collisions(paths: Sequence[tuple[str, Path | None]]) -> None:
    seen: dict[Path, str] = {}
    for name, path in paths:
        if path is None:
            continue
        resolved = path.resolve()
        if resolved in seen:
            raise ValueError(f"{name} aliases {seen[resolved]}")
        seen[resolved] = name


def main(arguments: Sequence[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    try:
        if options.program_in is not None:
            if options.length is not None or options.origin is not None:
                raise ValueError(
                    "--length and --origin are valid only with --seed"
                )
            program = LegalProgram.from_json(
                options.program_in.read_text(encoding="utf-8")
            )
        else:
            if options.length is None:
                raise ValueError("--length is required with --seed")
            program = generate_legal_program(
                options.seed,
                options.length,
                origin=4 if options.origin is None else options.origin,
            )

        _reject_path_collisions(
            (
                ("--program-in", options.program_in),
                ("--program-out", options.program_out),
                ("--trace-out", options.trace_out),
            )
        )
        program_text = program.to_json() + "\n"
        trace_text = trace_stream_to_ndjson(run_model_program(program))
        if options.program_out is not None:
            options.program_out.write_text(program_text, encoding="utf-8")
        if options.trace_out is not None:
            options.trace_out.write_text(trace_text, encoding="utf-8")
        else:
            sys.stdout.write(trace_text)
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"error": str(exc)}, sort_keys=True, separators=(",", ":")
            ),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
