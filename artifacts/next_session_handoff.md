# Next-session handoff

**Recorded:** 2026-08-09

## Durable checkpoint

- Repository: `birdybro/adsp-2100_sv`
- Branch: `agent/adsp2100-owner-differential`
- Pushed engineering commit:
  `2970496c6878d352e90f9a048ab69c5f2ce7fb6b`
  (`rtl: integrate shared PM/DM ownership and tracing`)
- Remote tracking branch:
  `origin/agent/adsp2100-owner-differential`
- The engineering worktree was clean and the local/remote hashes matched at
  that checkpoint. This handoff and its `TASKS.md`/`CHANGELOG.md` links are
  later local documentation changes until the user explicitly requests
  another commit and push.

The pushed increment integrates the bounded shared architectural-state,
cache, native-PM, and native-DM ownership seams for the currently attached
fetched and PM-data classes; adds source-bounded Type 1 logical dual-read
execution without claiming native timing; and establishes the common
implementation-neutral differential trace, canonical legal-program corpus,
model adapter, comparator, reducer, and CLI.

## Verification at the checkpoint

- `make test`: passed the complete implemented-foundation regression,
  including 839 Python checks and all generated model/RTL comparisons.
- `make lint`: passed Python compilation, text hygiene over 819 files, and
  strict Verilator lint/elaboration.
- `make fuzz`: passed 11 deterministic generator/reducer tests. RTL and MAME
  program fuzz remained explicit skips because those adapters do not exist.
- `make formal`: passed all 78 Verilator assertion syntax/elaboration recipes.
  Proof execution skipped because SymbiYosys is not installed.
- `make synth-yosys`: exited successfully with an explicit skip because Yosys
  is not installed.
- The current tracked synthesis report records the fresh, fully constrained
  20 ns Cyclone V combined-owner fit and its positive multicorner timing.

## Resume procedure

Start by confirming that the checkout still points at the checkpoint and by
reviewing any local handoff diff:

```text
git status -sb
git log -1 --oneline
git diff -- TASKS.md CHANGELOG.md artifacts/progress.md \
  artifacts/next_session_handoff.md
```

Then reread `AGENTS.md`, `TASKS.md`, `CHANGELOG.md`, this file, the applicable
architecture/timing/ADR material, both research issue files, and the current
artifacts as required by repository policy. Do not discard the local handoff
changes. Commit them with the next coherent documentation or engineering
increment, or commit and push them separately only when the user asks.

## Recommended next bounded increment

Continue `VERIF-DIFF-001` with the first unified RTL legal-program trace
adapter. The smallest defensible step is to run the existing canonical
source-closed straight-line corpus through the bounded fetched RTL owner,
observe actual retirement boundaries, convert those observations to the
version-1 common trace, and compare them exactly with the independent-model
trace.

Use the current thirteen-class corpus only: NOP; Types 6, 7, 9, 15, 16, 18,
21, 23, 24, and 25; DREG-only Type 17; and the no-effect Type 26 alias. Begin
with `adsp2100_linear_core_slice` and a deterministic PM response because this
keeps the first adapter independent of unresolved PM-data, DM-wait, and event
priority. Extend the adapter to the combined owner only after the bounded
straight-line comparison is stable.

Relevant seams:

- `sim/differential/legal_programs.py`: canonical corpus and seeded generator
- `sim/differential/model_trace_adapter.py`: independent-model trace producer
- `tools/trace/adsp2100_trace.py`: strict version-1 trace schema
- `tools/trace/compare_traces.py`: exact/projected comparison and mismatch path
- `tools/trace/reducer.py`: deterministic one-minimal reduction
- `tools/trace/run_legal_program.py`: existing model-side CLI boundary
- `rtl/core/adsp2100_linear_core_slice.sv`: first bounded RTL execution owner
- `sim/unit/tb_adsp2100_linear_core_slice.sv`: existing retirement-driving
  testbench conventions
- `rtl/core/adsp2100_program_clients_owner_control_slice.sv`: later combined-
  owner adapter target, not the first step
- `tests/test_differential_trace.py` and `tests/test_legal_programs.py`: current
  contract fixtures

A practical implementation shape is a deterministic RTL runner that writes a
simple strict interchange record at each qualified retirement, followed by a
Python adapter that creates canonical NDJSON. Keep schema ownership in Python;
do not duplicate a handwritten JSON implementation in SystemVerilog.

The increment is done when at least one fixed corpus and multiple deterministic
seeds produce byte-stable or exactly comparator-equal post-retirement model and
RTL traces; initial/final PC, opcode, instruction-cycle count, all requested
known masks, and ordinary PM fetch transactions are checked; a deliberate
mismatch reports a stable path; the reducer preserves that mismatch signature;
and `TASKS.md`, `CHANGELOG.md`, verification/progress artifacts, focused tests,
`make test`, `make lint`, applicable formal, and synthesis status are updated.
Do not call this whole-core differential execution.

## Evidence gates and invariants to preserve

- OQ-016 is still open. Generated Type 17 programs must remain DREG-only; do
  not depend on the provisional narrow status/control source extension.
- OQ-023 is still open. Type 1 may be tested only at its existing logical
  atomic-completion boundary; do not attach native simultaneous PM/DM phases.
- OQ-024 is still open. Do not invent reset-time PMS/PMRD sequencing or replace
  deterministic preload with an authentic-first-fetch claim.
- Do not use the installed unpinned MAME executable as an oracle. A MAME path
  requires an isolated, commit-pinned, license-compatible adapter.
- Preserve one architectural-state owner, one shared cache, and one native
  controller per bus in the combined composition. Collisions without sourced
  priority remain fail-closed and observable.
- HALT during BG, interrupt/TRAP/HALT/BR simultaneous priority, capture without
  a state-7 sample, additional architectural DM requesters, and self-modifying
  PM/cache behavior remain open. Do not silently assign behavior.
- Maintain original ADSP-2100 scope. Do not import later-family features or
  timing as original-device behavior.

If the RTL trace adapter exposes an architectural ambiguity, stop that path,
record it in `docs/research/open_questions.md` or
`docs/research/source_conflicts.md`, and continue with an independent bounded
portion rather than inventing an expectation.
