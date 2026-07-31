# Project progress

**Updated:** 2026-07-31

**Latest verified engineering commit:** `6305d6f`

**Current milestone:** architecture extraction, executable model, and
source-backed compute/address-generation/register/status-storage blocks plus
bounded semantic instruction decode

**Release status:** research/implementation in progress; not instruction-,
cycle-, or Hard Drivin'-complete

## Completed increments

- required repository layout and autonomous-agent governance;
- lawful cache-only reference workflow with content and SHA-256 validation;
- initial source-precedence, exact-device, and cycle-model ADRs;
- original-versus-later-device feature-matrix first pass;
- original architecture/timing documentation framework;
- Hard Drivin' board-interface first-pass notes;
- complete 30-class mask inventory, all 106 diagrammed fields across 393
  variable bit positions, explicit unshown-reserved fallback, and one
  hand-verified NOP semantic fixture;
- exact Type 6 immediate-to-DREG semantics, assembler/disassembler support,
  exhaustive Python/RTL field decode, both-bank independent state execution,
  and exact SE/MR2/MR1 storage side effects;
- bounded Type 15 immediate LSHIFT/ASHIFT semantics, two manual fixtures,
  original-syntax assembler/disassembler support, exhaustive class
  partitioning, selected-bank SR execution, and explicit fail-closed handling
  for every source-unclosed subencoding;
- complete source-backed Type 16 conditional-shifter semantics, two hand
  fixtures, all 1,792 algebraic forms, exhaustive class partitioning,
  cycle-start condition/bank/operand reads, cycle-end SR/SE/SB/SS execution,
  and explicit fail-closed handling for the 256 unavailable-XOP words;
- exact Type 17 internal-MOVE action decode covering all register selectors,
  reserved holes, SSTAT read-only direction, and all 2,256 legal assembler/
  disassembler pairs;
- bounded Type 17 state execution connecting both computational banks, both
  DAG register files, status/control, PX, CNTR/count-stack, and SSTAT, with
  OQ-016 narrow status extension exposed as a provisional output;
- bounded Type 26 stack-control semantic database, independent executable
  action model, portable decoder RTL, and exhaustive fail-closed decode;
- exact Type 25 MR-saturation semantic entry, hand-reviewed assembler fixture,
  independent action/state model, shared saturation primitive, portable
  selected-bank execution RTL, and exhaustive fail-closed decode;
- parameterized original Type 18 MODE CONTROL semantics, algebraic
  assembler/disassembler support, independent state model, portable execution
  RTL, and exhaustive fail-closed decode for all 256 field-defined words;
- all 32 original Type 21 MODIFY selections with primary-backed semantics,
  assembler/disassembler support, exact decode, independent state model,
  exact-width reset-valid I/M/L storage, and bounded stateful RTL execution;
- bounded stateful Type 26 model/RTL execution connecting all four stack
  classes, CNTR, ASTAT/MSTAT/IMASK, and composed SSTAT with cycle-start reads
  and atomic cycle-end commits;
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
- source-backed stateful model/RTL for both complete computational banks,
  authentic reset unknowns, exact SE/MR2/SB widths, cycle-boundary DREG
  accesses, and unit-specific ALU/MAC/shifter writeback;
- source-backed stateful model/RTL for exact-width ASTAT/MSTAT/ICNTL/IMASK,
  authentic ASTAT/ICNTL reset unknowns, MSTAT/IMASK reset clear, all MODE
  CONTROL effects, cycle-boundary computational status writes, interrupt-entry
  status snapshots and nested masks, and RTI-style restore;
- source-backed four-by-sixteen status-stack model/RTL with exact context
  packing, saturating depth, oldest-data retention, sticky overflow, and
  status-stack SSTAT sources;
- source-backed exact 16-by-14 PC, four-by-14 count, and four-by-18 loop
  stack-storage model/RTL with saturating depth, newest-push loss, sticky
  overflow, and the remaining six SSTAT sources;
- source-backed stateful 14-bit CNTR model/RTL with explicit validity, load
  push requests, cycle-start CE/NOT CE evaluation, false-CE post-decrement,
  true-CE count-stack restore or invalidation, and fail-closed unresolved
  empty-pop behavior;
- bounded sequencer integration connecting IF/DO condition evaluation,
  explicit flow, DO setup, CNTR, and PC/count/loop stack storage, with
  unresolved CALL-CE and competing-action cases held and flagged;
- bounded cycle-ordered MSTAT integration connecting alternate computational
  bank selection, DAG1 bit reversal, sticky AV, and AR saturation in both the
  independent model and portable RTL;
- 48-code general-MOVE register table with reserved-code accounting;
- independent exact-width/reset/image-loading/reserved-rejection/NOP model
  foundation;
- partial NOP, Type 6, Type 15, Type 16, Type 17, Type 18, Type 21, and Type 25
  assembler/disassembler round trip;
- dependency-free regression, Verilator package lint, and CI workflow.

No TASKS.md milestone is marked complete yet. The foundation is under
verification because installed-tool coverage and CI execution evidence remain
outstanding.

## Current evidence

- 19 provenance records; 14 locally acquired and hash-verified;
- 277 implemented Python unit checks plus manifest/hash verification;
- all 16,777,216 program words pass independent class-decode comparison:
  15,473,178 shown-class and 1,304,038 reserved-unshown words;
- all 32 Type 26 words produce their exact SPP/CP/LP/PP actions and every
  other 24-bit word produces no stack-control action in exhaustive RTL
  simulation;
- all 4,096 Type 17 class words partition into exactly 2,256 legal moves and
  1,840 reserved/read-only-destination subencodings; all other program words
  are action-free in exhaustive RTL simulation; all 4,512 legal pair/bank
  executions and 59,430 stateful model/RTL cycles pass;
- all 1,048,576 Type 6 words decode to exact immediate/DREG fields in both
  Python and exhaustive RTL traversal; 50,204 selected-bank model/RTL cycles
  pass with no PM-data or DM activity;
- all 32,768 Type 15 class words partition into 14,336 source-closed actions
  and 18,432 unsupported subencodings in Python and exhaustive RTL traversal;
  58,709 model/RTL cycles cover every supported word in both banks;
- all 2,048 Type 16 class words partition into 1,792 source-backed actions and
  256 unavailable-XOP subencodings in Python and exhaustive RTL traversal;
  54,403 model/RTL cycles cover every supported word in both banks and all
  condition/writeback forms;
- exact Type 25 word `0x050000` is the sole MR-saturation action across an
  exhaustive 16,777,216-word RTL traversal;
- exactly 256 Type 18 words decode as original MODE CONTROL across an
  exhaustive 16,777,216-word traversal; all 4,096 opcode/initial-MSTAT
  transforms and 58,248 stateful model/RTL cycles pass;
- exactly 32 Type 21 words decode as original MODIFY across an exhaustive
  16,777,216-word traversal; every same-DAG selection and 50,124 stateful
  model/RTL cycles pass;
- Verilator strict lint passes for shared types, generated class decode,
  condition RTL, ALU, MAC, shifter, DAG,
  sequencer-flow/CNTR/sequencer-stack/integration, register-file,
  status-register/status-stack, and MSTAT-consumer integration RTL;
  all 2,048 condition/flag combinations, 51,472 ALU vectors, 21,760 MAC
  vectors, 644,368 shifter vectors, 204,864 DAG vectors, 636,512
  sequencer-flow vectors, 50,022 CNTR cycles, 50,011 sequencer-integration
  cycles, 58,307 DREG cycles, and 50,120 full-bank/writeback cycles plus
  50,287 status/control, 50,037 status-stack, 50,062 PC/count/loop stack, and
  50,112 MSTAT-consumer integration cycles plus 50,015 stateful Type 26
  execution cycles and 50,112 stateful Type 25 cycles pass simulation;
  the Type 18 state slice adds 58,248 passing cycles and the Type 21 slice adds
  50,124, while the Type 17 state slice adds 59,430 and the Type 6 slice adds
  50,204; the Type 15 state slice adds 58,709 and the Type 16 state slice adds
  54,403;
- constrained Quartus Cyclone V class-decode, stack-control decode, condition,
  ALU, MAC, shifter, DAG,
  sequencer-flow, CNTR, sequencer-stack, sequencer-integration, register-file,
  status-register, and status-stack block compilations plus the MSTAT and
  stateful Type 26 integration-slice compilations pass with no unconstrained
  paths; the Type 25 slice separately fits in 144 ALMs and 92 registers with
  positive setup/hold slack and no unconstrained paths; the Type 18 slice fits
  in 46 ALMs and four registers with positive setup/hold slack and no
  unconstrained paths; the Type 21 slice fits in 526 ALMs with exactly 360
  architectural DAG data/valid registers, positive setup/hold slack, and no
  unconstrained paths; the Type 17 decoder fits in 42 ALMs and 24
  combinational ALUTs with positive multicorner slack and no unconstrained
  paths, while the Type 17 state slice fits in 816 ALMs and 906 registers with
  +6.401 ns setup, +0.151 ns hold, and no unconstrained paths; the Type 6 slice
  fits in 302 ALMs and 484 registers with +8.167 ns setup, +0.133 ns hold, and
  no unconstrained paths; the Type 15 slice fits in 774 ALMs and 501 fitted
  registers with +3.728 ns setup, +0.057 ns hold, and no unconstrained paths;
  the Type 16 slice fits in 840 ALMs and 520 fitted registers with +2.304 ns
  setup, +0.173 ns hold, and no unconstrained paths;
- class-decode, stack-control decode/integration, condition, ALU, MAC, shifter, DAG,
  register-file, CNTR, sequencer-stack, sequencer-integration, status-register,
  status-stack,
  MSTAT-integration, Type 18 decode/execution, Type 21 decode/execution, and
  Type 25 decode/execution plus Type 17 action/state execution
  formal harnesses plus Type 6, Type 15, and Type 16 decode/execution (27 total) pass
  assertion syntax lint, but no
  formal proof ran because SymbiYosys/Yosys are unavailable;
- no integrated architectural core, complete assembler, or whole-core
  synthesis top exists.

## Next highest-priority work

1. Locate the exact original Cross-Software/instruction reference and a
   separately identifiable original data sheet.
2. Locate primary or physical evidence for OQ-016 to replace or reject the
   bounded Type 17 slice's explicitly provisional zero-extension hypothesis.
3. Add stateful PC/reset/enable integration only after the next-PC update and
   stall boundaries are source-closed.
4. Trace Atari schematic nets and PAL behavior before writing the board wrapper.
5. Research and connect interrupt/RTI sequencing to the now-composed SSTAT and
   status-stack boundary without inventing arbitration priorities.
