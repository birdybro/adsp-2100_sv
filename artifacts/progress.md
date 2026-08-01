# Project progress

**Updated:** 2026-07-31

**Latest verified engineering commit:** `98561ea`

**Current milestone:** architecture extraction, executable model, and
source-backed compute/address-generation/register/status-storage blocks plus
bounded semantic instruction decode and logical DM/PM transaction slices

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
- class-complete original Type 2 immediate-DM-write action semantics,
  independent model, three hand-derived fixtures, all 160 boundary/selector
  assembler-disassembler forms, exhaustive 24-bit fail-closed RTL decode, and
  formal field/same-DAG invariants; plus a waited logical DM execution model
  and RTL slice with captured address/immediate, completion-only I
  post-modification, deterministic differential vectors, stall-stability
  invariants, and a constrained Cyclone V project;
- exact Type 6 immediate-to-DREG semantics, assembler/disassembler support,
  exhaustive Python/RTL field decode, both-bank independent state execution,
  and exact SE/MR2/MR1 storage side effects;
- bounded Type 8 ALU/MAC-plus-internal-MOVE semantics, two hand-derived
  fixtures, representative canonical assembler/disassembler coverage,
  exhaustive three-way class partitioning, cycle-start selected-bank operand,
  feedback, status, and move-source reads, atomic cycle-end noncolliding
  writeback, and explicit fail-closed handling for AMF zero and destination
  collisions under OQ-022/OQ-014;
- class-complete Type 9 conditional ALU/MAC semantics, two hand-derived
  fixtures, all 21,920 uniquely spellable algebraic forms plus lossless raw
  aliases, exhaustive 24-bit decode, cycle-start condition/bank/operand reads,
  true-only atomic result/status writeback, and documented AMF-zero
  no-operation behavior for all 32,768 class words;
- bounded Type 10 direct JUMP/CALL semantics, two hand-derived fixtures, every
  supported numeric-target assembler/disassembler form, exhaustive class
  partitioning, a decoder-connected 14-bit PC, CALL return stacking, JUMP NOT
  CE counter transitions, and explicit fail-closed OQ-012 handling for all
  16,384 CALL NOT CE words;
- class-complete Type 11 DO UNTIL setup semantics, two hand-derived fixtures,
  all 262,144 assembler/disassembler forms, exhaustive decode, simultaneous
  PC+1/loop-descriptor stack updates, distinct-end nesting, and fail-closed
  same-end/OQ-018 handling;
- bounded Type 19 indirect JUMP/CALL semantics, two hand-derived fixtures, all
  124 source-closed assembler/disassembler forms, exhaustive decode separating
  four OQ-012 CALL NOT CE words, exact I4-I7 target selection without DAG
  modification, conditional PMA drive intent, CALL return stacking, and JUMP
  NOT CE counter transitions;
- class-complete Type 20 conditional RTS/RTI semantics, two hand-derived
  fixtures, all 32 assembler/disassembler forms, exhaustive decode, false
  PC+1 behavior, taken PC/status stack actions, atomic RTI status restore,
  non-mutating return NOT CE, and explicit OQ-013 missing-context rejection;
- class-complete phase-aware Type 22 conditional TRAP semantics, two
  hand-derived fixtures, all 16 assembler/disassembler forms, exhaustive
  decode, state-7/state-8 TRAP assertion, PC+1 observation, state-8 hold, and
  the recognized-HALT clear/release handshake;
- class-complete Type 23 DIVQ semantics, two hand-derived fixtures, all eight
  ALU-X divisor assembler/disassembler forms, exhaustive 24-bit decode,
  old-AQ-selected add/subtract iteration, atomic selected-bank AF/AY0/AQ
  writeback, and a composed signed DIVS-plus-fifteen-DIVQ model sequence;
- source-closed Type 24 DIVS initialization semantics, two hand-derived
  fixtures, all 16 AY1/AF-by-ALU-X assembler/disassembler forms, exhaustive
  32-word class partitioning, cycle-start selected-bank operand reads, and
  atomic cycle-end AF/AY0/AQ writeback with non-AQ ASTAT preservation;
- bounded canonical Type 14 shifter-plus-internal-MOVE semantics, two manual
  fixtures, all 25,648 algebraic forms, exhaustive four-way class
  partitioning, cycle-start selected-bank operand reads, atomic cycle-end
  noncolliding writeback, and explicit fail-closed handling for bit 15,
  unavailable XOP 001, and same-destination packets under OQ-021;
- bounded Type 12 shifter-plus-DM semantics, two hand-derived fixtures, all
  108,640 source-closed algebraic forms, exhaustive three-way class
  partitioning, stable logical DM transactions over arbitrary DMACK waits,
  old-value stores, completion-only DAG post-modification, and atomic
  shifter/read/I writeback with unknown-state preservation;
- bounded Type 13 shifter-plus-PM semantics, two hand-derived fixtures, all
  54,320 source-closed algebraic forms, exhaustive three-way partitioning,
  exact 24-bit DREG/PX packing, old-value stores, fixed-cycle shifter/read/DAG2
  commits, same-cycle next-fetch cache hits, and exactly one pure recovery
  fetch after a miss or forced fetch;
- source-bounded 16-by-24 instruction cache and contiguous-region monitor,
  including low-four-bit indexing, sequential fills, inside-region refresh,
  discontinuity restart, 14-bit wrap, circular oldest replacement, and reset/
  unknown validity handling in independent model and portable RTL;
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
- partial NOP, Type 2, Type 6, Type 8, Type 9, Type 10, Type 11, Type 14, Type 15,
  Type 16, Type 17, Type 18, Type 19, Type 20, Type 21, Type 22, Type 23,
  Type 24, and
  Type 25 assembler/disassembler round trip;
- dependency-free regression, Verilator package lint, and CI workflow.

No TASKS.md milestone is marked complete yet. The foundation is under
verification because installed-tool coverage and CI execution evidence remain
outstanding.

## Current evidence

- 19 provenance records; 14 locally acquired and hash-verified;
- 455 implemented Python unit checks plus manifest/hash verification;
- all 16,777,216 program words pass independent class-decode comparison:
  15,473,178 shown-class and 1,304,038 reserved-unshown words;
- all 2,097,152 Type 2 words decode to exact immediate/G/I/M fields in Python
  and exhaustive RTL traversal; every other 24-bit word is action-free;
- 50,035 Type 2 model/RTL clocks cover both DAGs, every I/M selection, DAG1
  bit reversal, immediate and multi-clock DMACK completion, stable captured
  address/data, completion-only I updates, reset, conflicts, and invalid state;
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
- all 524,288 Type 8 words partition into exactly 476,672 supported actions,
  16,384 unresolved AMF-zero words, and 31,232 same-destination conflicts in
  Python and exhaustive RTL; 983,386 model/RTL cycles execute every supported
  word in both banks plus deterministic setup, unknown, invalid, and conflict
  cases;
- all 32,768 Type 9 words decode as actions in Python and exhaustive RTL:
  31,744 conditional computations and 1,024 documented no-operation aliases;
  283,996 model/RTL cycles execute every word in both banks and both outcomes
  for every nonconstant condition;
- all 524,288 Type 10 words partition into exactly 507,904 supported direct
  JUMP/CALL actions and 16,384 OQ-012 CALL NOT CE words in Python and
  exhaustive RTL; 554,412 model/RTL cycles execute every supported word plus
  deterministic reset, predicate, counter restore, stack overflow, invalid,
  and conflict cases;
- all 262,144 Type 11 words decode to exact ADDR/TERM fields in Python and
  exhaustive RTL; 554,309 model/RTL cycles execute every word plus nesting,
  CE-context, overflow, reset, invalid, and integration-conflict cases;
- all 128 original fixed-bit Type 19 words partition into exactly 124
  source-closed indirect JUMP/CALL actions and four OQ-012 CALL NOT CE words
  in Python and exhaustive RTL; 50,259 model/RTL cycles cover I4-I7 targets,
  target validity, both predicate outcomes, PMA drive intent, CALL stacking,
  JUMP NOT CE transitions, overflow, reset, invalid state, and conflicts;
- all 32 original Type 20 words decode in Python and exhaustive RTL; 50,254
  model/RTL cycles cover every condition and return kind, false/taken flow,
  PC/status stack actions, atomic RTI status restore, return NOT CE
  preservation, reset, invalid state, and conflicts;
- all 16 original Type 22 words decode in Python and exhaustive RTL; 50,168
  model/RTL clocks cover every condition, false/taken flow, held state 7,
  state-8 halt, PC+1 observation, recognized-HALT acknowledgment/release,
  reset, invalid phase/state, and conflicts;
- all eight field-defined Type 23 words decode as source-closed DIVQ actions
  in Python and exhaustive RTL; 50,081 model/RTL cycles cover both banks,
  every divisor, both old-AQ paths, atomic AF/AY0/AQ writeback, non-AQ ASTAT
  preservation, reset unknowns, invalid state, and conflicts;
- all 32 field-defined Type 24 words partition in Python and exhaustive RTL
  into 16 source-closed AY1/AF actions and 16 unsupported AY0/zero YOP words;
  50,109 model/RTL cycles cover both banks, every legal operand combination,
  atomic AF/AY0/AQ writeback, non-AQ ASTAT preservation, reset unknowns,
  unsupported words, invalid state, and conflicts;
- all 65,536 Type 14 class words partition into exactly 25,648 canonical
  supported actions, 32,768 unverified bit-15 words, 4,096 unavailable-XOP
  words, and 3,024 same-destination conflicts in Python and exhaustive RTL;
  82,597 model/RTL cycles cover every supported packet in both banks plus
  deterministic reset, invalid, conflict, and unknown-state cases;
- all 65,536 Type 13 class words partition into exactly 54,320 source-closed
  actions, 8,192 unavailable-XOP words, and 3,024 PM-read destination
  conflicts in Python and exhaustive RTL; 50,070 model/RTL clocks cover both
  banks, all DAG2 selections, read packing, old writes, cache-hit completion,
  miss/forced-fetch recovery, reset, invalid, and unknown-state cases;
- the instruction cache passes ten directed tests and 50,028 deterministic
  model/RTL clocks across all 16 slots, contiguous-region fill/lookup,
  seventeenth-word replacement, discontinuities, PM-address wrap, and unknown
  address/data handling;
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
  sequencer-flow vectors, 50,022 CNTR cycles, 50,014 sequencer-integration
  cycles, 58,307 DREG cycles, and 50,120 full-bank/writeback cycles plus
  50,287 status/control, 50,037 status-stack, 50,062 PC/count/loop stack, and
  50,112 MSTAT-consumer integration cycles plus 50,015 stateful Type 26
  execution cycles and 50,112 stateful Type 25 cycles pass simulation;
  the Type 18 state slice adds 58,248 passing cycles and the Type 21 slice adds
  50,124, while the Type 17 state slice adds 59,430 and the Type 6 slice adds
  50,204; the Type 8 state slice adds 983,386, the Type 9 state slice adds
  283,996, the Type 10 state slice adds 554,412, the Type 11 state slice adds
  554,309, the Type 19 state slice adds 50,259, the Type 20 slice adds 50,254,
  the phase-aware Type 22 slice adds 50,168 clocks, the Type 23 slice adds
  50,081 cycles, the Type 24 slice adds 50,109 cycles, the Type 2 slice adds
  50,035 state/bus clocks, the Type 12 slice adds
  50,069 state/bus clocks, the Type 13 slice adds 50,070 state/cache/bus
  clocks, and the standalone cache adds 50,028 clocks,
  and the Type 14 state slice adds
  82,597, the Type 15 state slice adds
  58,709, and the Type 16 state slice adds 54,403;
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
  the Type 14 slice fits in 1,032 ALMs and 565 fitted registers (502 design
  plus 63 routing duplicates) with +3.041 ns setup, +0.171 ns hold, and no
  unconstrained paths;
  the Type 16 slice fits in 840 ALMs and 520 fitted registers with +2.304 ns
  setup, +0.173 ns hold, and no unconstrained paths;
  the Type 12 slice fits in 1,704 ALMs and 1,091 fitted registers with no RAM
  or DSP blocks, +1.377 ns setup, +0.166 ns worst multicorner hold, 50.96 MHz
  worst slow-corner Fmax, and no unconstrained paths against its 21 ns
  standalone constraint;
  the Type 13 slice fits in 1,640 ALMs and 1,002 fitted registers with no RAM
  or DSP blocks, +1.172 ns setup, +0.168 ns worst multicorner hold, 50.43 MHz
  worst slow-corner Fmax, and no unconstrained paths against its 21 ns
  standalone constraint;
  the standalone instruction cache fits in 310 ALMs and 429 fitted registers
  with no RAM or DSP blocks, +7.071 ns setup, +0.163 ns worst multicorner
  hold, 77.35 MHz worst slow-corner Fmax, and no unconstrained paths against
  its 20 ns constraint;
  the Type 8 slice fits in 983 ALMs and 693 fitted registers with one DSP and
  no RAM, +1.131 ns setup, +0.177 ns hold, 47.92 MHz worst slow-corner Fmax,
  and no unconstrained paths against its 22 ns standalone constraint; it
  missed a 20 ns constraint by 1.721 ns and is not a whole-core timing claim;
- the Type 9 slice fits in 970 ALMs and 697 fitted registers with one DSP and
  no RAM, +1.140 ns setup, +0.165 ns hold, 47.94 MHz worst slow-corner Fmax,
  and no unconstrained paths against its 22 ns standalone constraint; its
  initial 20 ns fit missed setup by 1.735 ns;
- the Type 10 slice fits in 284 ALMs and 334 fitted registers with no RAM or
  DSP blocks, +8.138 ns setup, +0.167 ns worst multicorner hold, 84.3 MHz
  worst slow-corner Fmax, and no unconstrained paths against its 20 ns
  standalone constraint;
- the Type 11 slice fits in 308 ALMs and 402 fitted registers with no RAM or
  DSP blocks, +7.263 ns setup, +0.074 ns worst multicorner hold, 78.51 MHz
  worst slow-corner Fmax, and no unconstrained paths against its 20 ns
  standalone constraint;
- the Type 19 slice fits in 353 ALMs and 400 fitted registers with no RAM or
  DSP blocks, +7.520 ns setup, +0.045 ns worst multicorner hold, 80.93 MHz
  worst slow-corner Fmax, and no unconstrained clocks, ports, or paths against
  its 20 ns standalone constraint;
- the Type 20 slice fits in 318 ALMs and 417 fitted registers with no RAM or
  DSP blocks, +7.725 ns setup, +0.136 ns worst multicorner hold, 81.47 MHz
  worst slow-corner Fmax, and no unconstrained clocks, ports, or paths against
  its 20 ns standalone constraint;
- the Type 22 slice fits in 116 ALMs and 67 fitted registers (53 design plus
  14 routing duplicates) with no RAM or DSP blocks, +7.592 ns setup,
  +0.069 ns worst multicorner hold, 80.59 MHz worst slow-corner Fmax, and no
  unconstrained clocks, ports, or paths against its 20 ns standalone
  constraint;
- the Type 23 slice fits in 316 ALMs and 341 fitted registers (338 design plus
  three routing duplicates) with no RAM or DSP blocks, +7.009 ns setup,
  +0.164 ns worst multicorner hold, 77.71 MHz worst slow-100C Fmax, and no
  unconstrained clocks, ports, or paths against its 20 ns standalone
  constraint;
- the Type 24 slice fits in 351 ALMs and 381 fitted registers (372 design plus
  nine routing duplicates) with no RAM or DSP blocks, +8.448 ns setup,
  +0.168 ns worst multicorner hold, 86.81 MHz worst slow-corner Fmax, and no
  unconstrained clocks, ports, or paths against its 20 ns standalone
  constraint;
- the Type 2 DM-write slice fits in 581 ALMs and 430 fitted registers with no
  RAM/DSP blocks, +3.590 ns setup, +0.165 ns worst multicorner hold, 60.94 MHz
  worst slow-corner Fmax, and no unconstrained clocks, ports, or paths against
  its 20 ns standalone constraint;
- class-decode, stack-control decode/integration, condition, ALU, MAC, shifter, DAG,
  register-file, CNTR, sequencer-stack, sequencer-integration, status-register,
  status-stack,
  MSTAT-integration, Type 18 decode/execution, Type 21 decode/execution, and
  Type 25 decode/execution plus Type 17 action/state execution
  formal harnesses plus Type 6, Type 8, Type 9, Type 10, Type 11, Type 14,
  Type 12, Type 13, Type 15, Type 16, Type 19, Type 20, phase-aware Type 22,
  Type 2 action/execution, Type 23, Type 24, and instruction-cache invariants
  (42 total) pass
  assertion syntax lint, but no
  formal proof ran because SymbiYosys/Yosys are unavailable;
- no integrated architectural core, complete assembler, or whole-core
  synthesis top exists.

## Next highest-priority work

1. Locate the exact original Cross-Software/instruction reference and a
   separately identifiable original data sheet.
2. Locate primary or physical evidence for OQ-016 to replace or reject the
   bounded Type 17 slice's explicitly provisional zero-extension hypothesis.
3. Connect the source-bounded 16-entry instruction-cache monitor to Type 13
   and a unified fetch owner, replacing the bounded caller oracle while
   retaining OQ-008 event-interaction limits.
4. Extend the bounded logical DM and PM paths into sourced native pin phases and
   whole-core transaction arbitration.
5. Trace Atari schematic nets and PAL behavior before writing the board wrapper.
6. Research and connect interrupt-entry sequencing to the now-composed SSTAT
   and status-stack boundary without inventing arbitration priorities.
