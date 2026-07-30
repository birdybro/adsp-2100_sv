#!/usr/bin/env python3
"""Create an isolated sparse MAME source checkout at the manifest-pinned commit."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESTINATION = ROOT / "reference_cache/mame-tree"
REPOSITORY = "https://github.com/mamedev/mame.git"
PINNED_COMMIT = "030fefcbd14e47c01ec9d67655be90f64a1dc8ab"
SPARSE_PATHS = (
    "COPYING",
    "src/devices/cpu/adsp2100",
    "src/mame/atari/harddriv.cpp",
    "src/mame/atari/harddriv.h",
    "src/mame/atari/harddriv_m.cpp",
)


class CheckoutError(RuntimeError):
    pass


def run(arguments: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        arguments,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise CheckoutError(
            f"{' '.join(arguments)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def verify_existing(destination: Path) -> None:
    if not (destination / ".git").is_dir():
        raise CheckoutError(f"refusing non-Git destination: {destination}")
    remote = run(["git", "remote", "get-url", "origin"], cwd=destination)
    if remote.rstrip("/") not in {REPOSITORY.rstrip("/"), "git@github.com:mamedev/mame.git"}:
        raise CheckoutError(f"unexpected existing origin: {remote}")
    commit = run(["git", "rev-parse", "HEAD"], cwd=destination)
    if commit != PINNED_COMMIT:
        raise CheckoutError(
            f"existing checkout is {commit}; expected pinned {PINNED_COMMIT}"
        )


def create_checkout(destination: Path) -> None:
    if shutil.which("git") is None:
        raise CheckoutError("git is not installed")
    if destination.exists():
        verify_existing(destination)
        print(f"PRESENT {destination}: {PINNED_COMMIT}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            "--no-tags",
            REPOSITORY,
            str(destination),
        ]
    )
    try:
        run(["git", "sparse-checkout", "init", "--no-cone"], cwd=destination)
        sparse_patterns = "\n".join(f"/{path}" for path in SPARSE_PATHS) + "\n"
        sparse_file = destination / ".git/info/sparse-checkout"
        sparse_file.write_text(sparse_patterns, encoding="utf-8")
        run(["git", "fetch", "--depth=1", "origin", PINNED_COMMIT], cwd=destination)
        run(["git", "checkout", "--detach", PINNED_COMMIT], cwd=destination)
        verify_existing(destination)
    except Exception:
        # The incomplete directory is intentionally retained for inspection.
        # Nothing downloaded is executed.
        raise
    print(f"FETCHED {destination}: {PINNED_COMMIT}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    destination = args.destination.resolve()
    allowed_root = (ROOT / "reference_cache").resolve()
    if allowed_root not in destination.parents:
        print(f"FAIL destination must be below {allowed_root}", file=sys.stderr)
        return 2
    try:
        create_checkout(destination)
    except CheckoutError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
