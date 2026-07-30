# Contributing

This is a clean-room hardware reimplementation. Architectural correctness and
provenance take precedence over feature velocity.

## Before changing behavior

Read `AGENTS.md`, `TASKS.md`, `CHANGELOG.md`, the relevant architecture and
timing documents, and applicable ADRs. Pick a stable task ID and ensure its
acceptance criteria and source requirements are explicit before implementation.

## Development flow

1. Add or improve the source record.
2. Record ambiguity instead of guessing.
3. Add independently reviewed fixtures or tests.
4. Implement the smallest coherent model or RTL behavior.
5. Run focused tests, then `make test` and `make lint`.
6. For RTL, run available synthesis and formal checks.
7. Update the task, changelog, citations, and status artifacts.
8. Review the complete diff and staged files before committing.

Tests must fail loudly on defects. Missing optional tools may report a clear
skip, but required foundation checks may not be skipped. Do not modify expected
results merely to match an implementation; explain and cite why a prior
expectation was wrong.

## Style

Python uses type hints, deterministic I/O, the standard library where
practical, and no network access during tests. SystemVerilog follows the
portable subset and width/signedness rules in `AGENTS.md`.

## References and third-party material

Do not submit copyrighted manuals, ROMs, PAL dumps, or legacy executables.
Update `docs/references/manifest.yaml` with provenance and keep local copies in
`reference_cache/`. Do not paste emulator implementation code into issues,
tests, the model, or RTL.

## Pull requests

Describe:

- task IDs and exact device behavior affected;
- evidence and confidence level;
- tests and synthesis/formal commands run;
- any unavailable tools or unresolved questions;
- whether generated artifacts were refreshed.

Architectural changes without citations and objective tests are not ready to
merge.
