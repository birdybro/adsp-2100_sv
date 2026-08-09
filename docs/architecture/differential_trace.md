# Differential retirement trace

**Status: implementation-neutral schema, independent-model adapter, comparator,
deterministic reducer, and bounded model-side legal-program generator
implemented; RTL program adapter, complete legal-program generation, and
pinned-MAME adapter pending**

The common trace is an implementation convenience for comparing independently
produced results. It does not define ADSP-2100 behavior and cannot promote an
emulator observation over the source order in ADR-0001. The target remains the
original external-memory ADSP-2100 from ADR-0002.

Schema version 1 records one post-retirement observation as canonical NDJSON:

- producer provenance, retirement index, opcode, PC before/after, and logical
  instruction-cycle count;
- a dotted-path map of requested architectural state;
- ordered PM/DM transactions with address, width, optional data, and logical
  wait count; and
- a sorted set of named retirement events.

Every word carries an exact width, a value, and a bitwise known mask. Unknown
bits have canonical value zero. This preserves documented reset-unknown and
partially known classifications without treating their hidden binary contents
as architectural evidence. The common comparator ignores producer identity,
strictly compares every state path by default, accepts an explicit state
projection when an adapter exposes only a sourced subset, and compares
transactions in order. The machine-readable definition is
`docs/generated/adsp2100_differential_trace.yaml`.

The independent-model adapter currently flattens both computational banks,
all I/M/L registers, PX, PC, status/control/CNTR, and every represented
PC/count/loop/status stack entry after retirement. That inventory follows the
original widths and reset classifications summarized in `programmers_model.md`
[ADI-UM-1989, printed pp. 2-5–2-30, 3-1–3-8, 4-3–4-24, and 5-13]. It adapts
the model's ordered PM/DM transaction records without changing their meaning.

`tools/trace/compare_traces.py LEFT RIGHT` compares two schema-valid NDJSON
streams and reports stable field paths for each mismatch. Repeated `--state`
arguments select an explicit state projection. The reducer accepts a caller-
supplied predicate defining the exact failure signature, removes only complete
ordered items, and returns a deterministic one-minimal subsequence. The
predicate—not the reducer—must distinguish the requested mismatch from an
unrelated crash.

`sim/differential/legal_programs.py` adds a canonical replay corpus and a
deterministic generator for NOP, Types 6, 7, 9, 15, 16, 18, 21, and 23, the
sixteen source-closed Type 24 forms, exact Type 25, the Type 26 no-effect
alias, and Type 17 moves restricted to DREG sources and destinations. The
Type 17 subset therefore does not depend on OQ-016 narrow-register extension.
Those thirteen classes are strictly sequential and require no unresolved
stack, control-event, PM-data, or DM-data context. Each seed reconstructs a fully
known architectural state with empty sequencer stacks, then the independent
model emits one common post-retirement frame per opcode. The machine-readable
scope is `docs/generated/adsp2100_legal_programs.yaml`. Thirty-two seeds of 128
instructions cover 4,096 model retirements in `tests/test_legal_programs.py`.
This is generator qualification and model execution, not differential evidence
against a second implementation.

`tools/trace/run_legal_program.py` exposes the bounded generator and replay
path without adding an architectural claim. `--seed` plus `--length` creates a
program, while `--program-in` strictly parses an existing canonical corpus.
`--program-out` preserves the corpus and `--trace-out` writes byte-stable
NDJSON; without `--trace-out`, the trace is written to standard output. Input
and output aliases fail closed so a replay cannot overwrite its source.

This boundary does not claim a unified RTL program trace, all legal opcode
classes or control/bus contexts in the generator, a MAME timing model, or a
MAME architectural oracle.
An installed but unpinned MAME executable is not used for qualification. A
future MAME adapter must remain isolated, commit-pinned, license-audited, and
classified as reference-software observation under ADR-0001.
