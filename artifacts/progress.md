# Project progress

**Updated:** 2026-07-30

**Latest verified engineering commit:** `955fa3a`

**Current milestone:** architecture extraction, executable model, and
source-backed compute/address-generation blocks

**Release status:** research/implementation in progress; not instruction-,
cycle-, or Hard Drivin'-complete

## Completed increments

- required repository layout and autonomous-agent governance;
- lawful cache-only reference workflow with content and SHA-256 validation;
- initial source-precedence, exact-device, and cycle-model ADRs;
- original-versus-later-device feature-matrix first pass;
- original architecture/timing documentation framework;
- Hard Drivin' board-interface first-pass notes;
- complete 30-class mask inventory, explicit unshown-reserved fallback, and one
  hand-verified NOP semantic fixture;
- complete source-backed IF/DO condition field with independent model and
  exhaustive combinational RTL verification;
- complete source-backed inventory of the 19 remaining finite Appendix A
  abbreviation tables;
- source-backed standard ALU model/RTL with flags, sticky overflow, and AR
  saturation;
- source-backed standard fractional MAC model/RTL with mixed signedness,
  unbiased rounding, MV, and MR saturation;
- source-backed all-function shifter model/RTL with full signed count range,
  normalization, exponent detection, and block exponent adjustment;
- source-backed DAG arithmetic model/RTL with original circular-base
  alignment, signed post-modification, and DAG1 bit reversal;
- source-backed sequencer-flow model/RTL for explicit transfer and loop-end
  arbitration;
- 48-code general-MOVE register table with reserved-code accounting;
- independent exact-width/reset/image-loading/reserved-rejection/NOP model
  foundation;
- partial NOP-only assembler/disassembler round trip;
- dependency-free regression, Verilator package lint, and CI workflow.

No TASKS.md milestone is marked complete yet. The foundation is under
verification because installed-tool coverage and CI execution evidence remain
outstanding.

## Current evidence

- 18 provenance records; 13 locally acquired and hash-verified;
- 100 implemented Python unit checks plus manifest/hash verification;
- Verilator strict lint passes for shared types, generated class decode,
  condition RTL, ALU, MAC, shifter, DAG, and sequencer-flow RTL; all 2,048
  condition/flag combinations, 51,472 ALU vectors, 21,760 MAC vectors, 644,368
  shifter vectors, 204,864 DAG vectors, and 636,512 sequencer-flow vectors pass
  simulation;
- constrained Quartus Cyclone V condition, ALU, MAC, shifter, DAG, and
  sequencer-flow block compilations pass with no unconstrained paths;
- condition, ALU, MAC, shifter, DAG, and sequencer-flow formal harnesses pass
  assertion syntax lint, but no formal proof ran because SymbiYosys/Yosys are
  unavailable;
- no architectural execution RTL, complete assembler, or whole-core synthesis
  top exists.

## Next highest-priority work

1. Locate the original Cross-Software/instruction reference and a separately
   identifiable original data sheet.
2. Extend the independently cross-checked class masks into field-level and
   semantic instruction records.
3. Close programmer-model reset widths and stack semantics.
4. Extend the independent model only for source-verified instruction groups.
5. Trace Atari schematic nets and PAL behavior before writing the board wrapper.
