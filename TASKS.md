# Engineering backlog

Task completion means that cited documentation and named objective tests pass;
the existence of RTL alone is never sufficient. Status values are `NOT
STARTED`, `RESEARCHING`, `BLOCKED`, `IMPLEMENTING`, `VERIFYING`, and
`COMPLETE`. Confidence values are `VERIFIED_PRIMARY`, `VERIFIED_HARDWARE`,
`CORROBORATED`, `INFERRED`, `PROVISIONAL`, and `UNKNOWN`.

Priorities are P0 (blocks trustworthy implementation), P1 (core architecture),
P2 (qualification), and P3 (release/integration follow-on). Reference IDs refer
to `docs/references/manifest.yaml`; `TBD-PRIMARY` means that a task cannot
advance beyond research until a page-level primary citation is added.

## M1 — Repository and automation foundation

### FND-001 — Repository and automation foundation

- **Status:** VERIFYING
- **Priority:** P0
- **Dependencies:** none
- **Acceptance criteria:** required layout and governance files exist; manifest,
  policy, model, lint, formal, and synthesis entry points return meaningful
  status; CI runs all license-compatible foundation checks.
- **Source references:** project requirements; ADR-0001, ADR-0002, ADR-0003
- **Relevant tests:** `tests/test_repository.py`,
  `tests/test_reference_manifest.py`, `make test`, `make lint`
- **Implementation notes:** required layout, governance, CI, `make test`,
  strict Verilator package lint, and explicit optional-tool skips exist;
  preserve existing `main` history and MIT license.
- **Unresolved questions:** CI tool-version pins and the minimum supported
  Quartus release need target qualification.
- **Confidence:** PROVISIONAL

## M2 — Documentation acquisition and provenance

### REF-001 — Documentation acquisition and provenance

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** FND-001
- **Acceptance criteria:** initial target list has complete provenance records;
  lawful configured downloads are idempotent, content-validated, hashed, and
  gitignored; missing and mismatched references are reported independently.
- **Source references:** ADI-MANUAL-INDEX, ADI-ASM-1994,
  ADI-2101-CROSS-1990, ATARI-ADSP-SCHEM, MAME-ADSP2100-CORE,
  MAME-HARDDRIV, MAME-HARDDRIV-MACHINE
- **Relevant tests:** `tests/test_reference_manifest.py`,
  `tests/test_reference_scripts.py`
- **Implementation notes:** redistribution-unclear files remain only under
  `reference_cache/`; downloaded binaries are never executed. The acquired
  1989 First Edition ADSP-2101 Cross-Software manual is later-device
  comparative evidence only; its §2.5.3 confirms that contemporary System
  Builder defaulted to ADSP-2100 unless `.ADSP2101` was present.
- **Unresolved questions:** locate the exact original ADSP-2100 Cross-Software
  manual, an ADI-hosted original ADSP-2100/2100A data sheet, and the earliest
  user-manual revision with stable URLs.
- **Confidence:** CORROBORATED

## M3 — Original ADSP-2100 device identification

### DEV-001 — Identify the original ADSP-2100/ADSP-2100A boundary

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** REF-001
- **Acceptance criteria:** package, address/data widths, pins, clocks, memory
  interfaces, revision naming, and documented 2100-versus-2100A differences are
  cited to original-device pages; Hard Drivin' fitted part evidence is cited.
- **Source references:** ADI-DATABOOK-1987 printed pp. 2-15 onward,
  ADI-UM-1989, ATARI-ADSP-SCHEM
- **Relevant tests:** `tests/test_architecture_claims.py::test_device_scope`
- **Implementation notes:** do not treat assembler convention that “ADSP-2100”
  includes 2100A as proof of electrical identity.
- **Unresolved questions:** exact mask/revision differences and authentic
  power-up state.
- **Confidence:** PROVISIONAL

## M4 — ADSP-2100 versus ADSP-21xx feature matrix

### DEV-002 — Source-backed family feature matrix

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** DEV-001
- **Acceptance criteria:** ADSP-2100, 2101, 2103, 2104, 2105, 2111/2115, and
  evolution-relevant 217x/218x rows cover all requested features with per-cell
  citations or `UNKNOWN`; default configuration excludes all later features.
- **Source references:** ADI-UM-FAMILY-1995, ADI-21XX-DS-REVC,
  ADI-DATABOOK-1987, ADI-2104-DS-REV0
- **Relevant tests:** `tests/test_architecture_claims.py::test_feature_matrix`
- **Implementation notes:** unknown cells are intentional research targets, not
  evidence of absence.
- **Unresolved questions:** 2104 primary documentation and original core
  arithmetic/revision differences.
- **Confidence:** PROVISIONAL

## M5 — Programmer's model

### ARCH-001 — Original-device programmer's model

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** DEV-001, DEV-002
- **Acceptance criteria:** every architectural register has width, signedness,
  read/write paths, reset/power-up state, bank behavior, visibility timing, and
  page-level original-device applicability evidence.
- **Source references:** ADI-UM-1989, ADI-DATABOOK-1987,
  ADI-UM-FAMILY-1995 for explicitly applicable comparisons only
- **Relevant tests:** `tests/test_model_state.py`,
  `tests/test_register_metadata.py`, `tests/test_counter.py`,
  `tests/test_internal_move.py`, `tests/test_internal_move_slice.py`,
  `tests/test_load_dreg_immediate.py`,
  `tests/test_load_non_dreg_immediate.py`, `tests/test_immediate_shift.py`,
  `tests/test_conditional_shift.py`, `tests/test_shift_move.py`,
  `tests/test_shifter_dm.py`,
  `tests/test_compute_move.py`, `tests/test_conditional_compute.py`
- **Implementation notes:** initial register map and reset-state
  classifications exist; the original 2-bit RGP/4-bit REG table accounts for
  48 codes and every blank code. CNTR now has machine-readable 14-bit,
  reset-validity, test/decrement, and count-stack transition metadata, while
  Type 17 now closes the 48 readable and 47 writable general-MOVE selectors.
  A bounded Type 17 path now composes both computational banks, both DAGs,
  status/control, PX, CNTR/count-stack, and SSTAT. OQ-016 narrow status reads
  remain visibly provisional. Exact Type 6 execution now covers all sixteen
  DREG destinations in both computational banks, including narrow storage and
  MR1 sign-fill side effects. Exact Type 7 execution now covers all 31 writable
  original non-data destinations, including exact-width narrowing,
  selected-bank SB, and CNTR/count-stack side effects. Bounded Type 15
  execution now covers
  selected-bank X-operand reads and SR writeback for all source-closed
  immediate LSHIFT/ASHIFT forms, while hidden state and whole-core
  fetch/interrupt access still require complete extraction. Bounded Type 16
  execution now connects all source-backed conditional shifter functions to
  cycle-start selected-bank and ASTAT inputs plus cycle-end SR/SE/SB/SS
  writeback. Bounded Type 14 execution now samples two parallel selected-bank
  sources and commits noncolliding DREG plus SR/SE/SB/SS results at cycle end.
  Bounded Type 8 execution samples ALU/MAC operands, feedback, ASTAT, and the
  simultaneous DREG source from cycle-start selected-bank state and atomically
  commits noncolliding computational, status, and DREG writes at cycle end.
  Type 9 now applies the same banked ALU/MAC operand/feedback paths behind a
  cycle-start condition and commits true-only result/status writes; false and
  AMF-zero actions preserve both banks.
  Emulator variable
  names are discovery aids only.
- **Unresolved questions:** hidden sequencer state, undefined reset fields, and
  exact alternate-bank coverage.
- **Confidence:** UNKNOWN

## M6 — Instruction encoding database

### ISA-001 — Complete machine-readable 24-bit ISA database

- **Status:** IMPLEMENTING
- **Priority:** P0
- **Dependencies:** ARCH-001, REF-001
- **Acceptance criteria:** every legal and reserved 24-bit encoding class is
  represented with all required semantic/timing fields, citations, confidence,
  schema validation, uniqueness checks, and hand-reviewed opcode fixtures.
- **Source references:** ADI-ASM-1994 Appendix A,
  ADI-UM-1989 instruction chapters and Appendix A
- **Relevant tests:** `tests/test_isa_database.py`,
  `tests/test_instruction_formats.py`, `tests/test_stack_control.py`,
  `tests/test_mr_saturation.py`, `tests/test_mode_control.py`,
  `tests/test_dm_write_immediate.py`,
  `tests/test_direct_dm.py`,
  `tests/test_dm_write_immediate_slice.py`,
  `tests/test_assembler_disassembler.py`,
  `tests/test_modify_address.py`, `tests/test_internal_move.py`,
  `tests/test_load_dreg_immediate.py`,
  `tests/test_load_non_dreg_immediate.py`, `tests/test_immediate_shift.py`,
  `tests/test_conditional_shift.py`, `tests/test_shift_move.py`,
  `tests/test_shifter_pm.py`,
  `tests/test_compute_move.py`, `tests/test_compute_dm.py`,
  `tests/test_compute_pm.py`, `tests/test_compute_pm_cache.py`,
  `tests/test_compute_pm_native.py`,
  `tests/test_direct_jump.py`,
  `sim/unit/tb_adsp2100_decode.sv`,
  `sim/unit/tb_adsp2100_stack_control_decode.sv`,
  `sim/unit/tb_adsp2100_mr_saturation_decode.sv`,
  `sim/unit/tb_adsp2100_mode_control_decode.sv`,
  `sim/unit/tb_adsp2100_modify_address_decode.sv`,
  `sim/unit/tb_adsp2100_dm_write_immediate_decode.sv`,
  `sim/unit/tb_adsp2100_direct_dm_decode.sv`,
  `sim/unit/tb_adsp2100_dm_write_immediate_slice.sv`,
  `sim/unit/tb_adsp2100_internal_move_decode.sv`,
  `sim/unit/tb_adsp2100_load_dreg_immediate_decode.sv`,
  `sim/unit/tb_adsp2100_load_non_dreg_immediate_decode.sv`,
  `sim/unit/tb_adsp2100_immediate_shift_decode.sv`,
  `sim/unit/tb_adsp2100_conditional_shift_decode.sv`,
  `sim/unit/tb_adsp2100_shift_move_decode.sv`,
  `sim/unit/tb_adsp2100_shifter_dm_decode.sv`,
  `sim/unit/tb_adsp2100_shifter_pm_decode.sv`,
  `sim/unit/tb_adsp2100_compute_move_decode.sv`,
  `sim/unit/tb_adsp2100_compute_dm_decode.sv`,
  `sim/unit/tb_adsp2100_compute_pm_decode.sv`,
  `sim/unit/tb_adsp2100_direct_jump_decode.sv`,
  `formal/class_decode.sby`, `formal/stack_control_decode.sby`,
  `formal/mr_saturation_decode.sby`, `formal/mode_control_decode.sby`,
  `formal/dm_write_immediate_decode.sby`,
  `formal/direct_dm_decode.sby`,
  `formal/dm_write_immediate_slice.sby`,
  `formal/modify_address_decode.sby`, `formal/internal_move_decode.sby`,
  `formal/load_dreg_immediate.sby`,
  `formal/load_non_dreg_immediate.sby`, `formal/immediate_shift.sby`,
  `formal/conditional_shift.sby`,
  `formal/shift_move.sby`, `formal/shifter_dm.sby`, `formal/shifter_pm.sby`,
  `formal/compute_move.sby`, `formal/compute_dm_decode.sby`,
  `formal/compute_pm_decode.sby`, `formal/compute_pm.sby`,
  `formal/compute_pm_cache.sby`, `formal/compute_pm_native.sby`,
  `formal/direct_jump.sby`,
  `make decode-tests`
- **Implementation notes:** the database enumerates all 30 original top-level
  classes with primary-transcribed, non-overlapping masks, explicitly covers
  1,304,038 unshown words as reserved, and generates synthesizable class
  decode. All 106 fields and 393 variable bit positions across the 30 diagrams
  are machine-readable, independently fixture-checked, and required to
  partition the masks exactly. The complete original 16-code IF and
  inverse-sense DO UNTIL condition fields and all 19 finite Appendix A
  abbreviation tables are separately machine-readable and exhaustively
  checked. The generated RTL class decoder agrees with an independent
  classifier for all 16,777,216 program words. A bounded Type 26 semantic
  database now covers all 32 stack-control action encodings, 24 distinct
  behaviors after collapsing the two no-change aliases, combined one-cycle
  action selection, and fail-closed non-Type-26 decode. It has an independent
  model, fixtures, exhaustive RTL test, formal harness, and constrained
  Cyclone V fit. A separate machine-readable execution boundary connects
  those actions to all four stack classes, CNTR, ASTAT/MSTAT/IMASK, and SSTAT
  with nine model checks and 50,015 stateful RTL comparison cycles. The
  all-zero NOP, parameterized Type 6 immediate DREG load, parameterized Type
  18 MODE CONTROL, parameterized Type 21 MODIFY, and exact Type 25
  `IF MV SAT MR;` words are hand-verified class-complete semantic instruction
  entries. Type 2 now has a primary-backed class-complete action record,
  independent decoder, three hand fixtures, exhaustive 24-bit RTL traversal,
  and six model/metadata tests for all 2,097,152 field-defined words. Its
  160 boundary/selector algebraic forms round trip. A separate execution
  model/RTL slice captures old-I address, raw immediate, and next I once;
  retains them through arbitrary DMACK-low extensions; and commits selected-I
  post-modification only at acknowledgment. Eleven directed tests and 50,035
  deterministic model/RTL clocks cover every I/M selection, both DAGs, DAG1
  bit reversal, reset, conflicts, unknown/invalid DAG state, and waits.
  Its native-DM wrapper adds five directed checks and 50,027 clocks covering
  state-8 issue, complete-cycle wait extension, late-ACK rejection, state-7
  completion-only I writeback, off-boundary rejection, and relinquishment.
  Type 3 now has a primary-backed class-complete action record, independent
  model/database decoders, two legal plus two invalid hand fixtures,
  exhaustive 24-bit RTL traversal, assembler/disassembler support, a formal
  harness, and a constrained decoder fit. All 2,097,152 words partition into
  770,048 legal reads, 786,432 legal writes, and 540,672 reserved-selector or
  read-only-SSTAT-destination words. Its bounded state/native-DM composition
  shares the complete general-register state, preserves reset unknowns and
  selected-bank validity, holds absolute-address transactions over full-cycle
  waits, and commits reads only at state 7-to-8. Fourteen directed tests and
  50,151 logical plus 50,077 native clocks pass; narrow status/control write
  sources retain an observable OQ-016 flag.
  Type 16 has a bounded semantic entry for 1,792 documented words;
  its 256 unassigned-XOP subencodings fail closed. Type 14 has a bounded
  semantic entry for 25,648 canonical words; 39,888 unresolved or unsupported
  words fail closed. Type 15 has a bounded
  semantic entry for the 14,336 source-closed immediate LSHIFT/ASHIFT words;
  its other 18,432 subencodings fail closed.
  Type 25 has primary-
  backed cycle-start MV/bank/MR semantics, an independent state model, exact
  decoder, bounded execution RTL, exhaustive 24-bit decode, nine model tests,
  and 50,112 stateful differential cycles. Generated assembler/
  disassembler artifacts must derive from these databases as instruction
  entries are independently verified. Type 18 covers all 256 field-defined
  words, 81 distinct action bundles, both no-change aliases, exact algebraic
  assembly, exhaustive decode, every opcode/initial-MSTAT transform, and
  58,248 stateful model/RTL cycles. Later timer, GO, and
  multiplier-placement controls remain excluded. Type 21 covers all 32
  same-DAG I/M selections, corresponding-L use, exact assembly syntax,
  exhaustive decode, authentic reset-invalid I/M/L storage, and 50,124
  stateful model/RTL cycles; PM/DM transfer attachment remains outside this
  bounded no-memory-access instruction. Type 17 action decode now accounts for
  all 4,096 field-defined words: 2,256 legal moves and 1,840 reserved or
  read-only-SSTAT-destination subencodings. Independent model/RTL selection,
  exhaustive fail-closed decode, and all legal assembler/disassembler pairs
  pass. Its bounded state model/RTL executes all legal pairs in both banks and
  passes 59,430 cycles across computational, DAG, status, PX, CNTR/count-stack,
  and SSTAT state. OQ-016 extension remains provisional and whole-core
  fetch/interrupt/bus integration remains incomplete. Type 6 covers all
  1,048,576 field-defined immediate/DREG words, has two independent opcode
  fixtures, assembler/disassembler round trips, exact SE/MR2 storage and MR1
  sign-fill behavior, and 50,204 stateful model/RTL cycles across both banks.
  Type 7 partitions all 1,048,576 words into 507,904 supported loads to 31
  writable non-data registers and 540,672 group-zero, reserved-selector, or
  read-only-SSTAT words. Its semantic database, two legal and three invalid
  hand-derived fixtures, exhaustive Python and RTL decode, algebraic/raw tools,
  formal harness, eight directed model tests, and 50,299 stateful model/RTL
  clocks cover exact-width I/M/L/status/PX/CNTR/SB writes, selected-bank SB,
  reset unknowns, conflicts, and CNTR/count-stack push. Fetch, interrupt,
  active-loop, and physical instruction-fetch phases remain outside the
  bounded state slice.
  Type 15 exhaustively partitions all 32,768 class words into 14,336 supported
  actions and 18,432 unsupported subencodings. Two manual fixtures, 280 syntax
  forms, all supported words in both banks, and 58,709 stateful model/RTL
  cycles pass; fetch/interrupt/bus timing and SF 8–15 behavior remain open.
  Type 16 exhaustively partitions all 2,048 class words into 1,792 supported
  actions and 256 unavailable-XOP subencodings. Two hand fixtures, every
  supported assembler/disassembler form, all supported words in both banks,
  and 54,403 stateful model/RTL cycles pass; OQ-020 and whole-core timing
  remain open.
  Type 14 exhaustively partitions all 65,536 class words into 25,648 supported
  canonical actions, 32,768 OQ-021 bit-15 forms, 4,096 unavailable-XOP forms,
  and 3,024 same-destination forms. Two hand fixtures, every supported syntax
  form, every supported word in both banks, and 82,597 stateful model/RTL
  cycles pass; whole-core timing remains open.
  Type 12 exhaustively partitions all 131,072 class words into 108,640
  source-closed actions, 16,384 unavailable-XOP words, and 6,048 illegal
  DM-read destination collisions. Two hand-derived fixtures, all supported
  assembler/disassembler forms, exhaustive 24-bit RTL decode, and 50,069
  state/bus differential clocks pass. A separate native-DM composition adds
  six directed tests and 50,064 connected phase clocks; whole-core PM/event
  integration remains open.
  Type 13 exhaustively partitions all 65,536 class words into 54,320
  source-closed actions, 8,192 unavailable-XOP words, and 3,024 illegal
  PM-read destination collisions. Two hand-derived fixtures, every supported
  assembler/disassembler form, exhaustive 24-bit RTL decode, and 50,070
  state/cache/bus differential clocks pass. The bounded slice covers PX
  packing, old-value PM stores, DAG2 post-modification, same-cycle cache hits,
  and one pure recovery fetch after a miss. A composed cache boundary now
  derives hits from the standalone monitor, supplies the actual cached word,
  fills recovery and ordinary external fetches, and passes ten integration
  tests plus 50,086 model/RTL clocks; attachment to the separately verified
  native PM pin phases and whole-core event integration remain open.
  Type 4 action selection exhaustively partitions all 2,097,152 class words
  into 2,034,688 source-closed compute/memory or memory-only actions and
  62,464 prohibited DM-read destination collisions. Two independent
  manual-derived fixtures, six model checks, exhaustive 24-bit RTL decode,
  canonical/raw assembler-disassembler preservation, a formal harness, and a
  constrained decoder fit pass. The bounded state model and RTL capture
  selected-bank compute/DREG/DAG state, hold logical bus and state across
  arbitrary DMACK waits, and atomically commit compute/status, optional read,
  and I postmodify. Twelve model/schema/directed checks and 50,072 deterministic clocks
  pass. A separate six-test, 50,082-clock native attachment comparison now
  closes state-8 issue, full-cycle waits, state-7 atomic completion, reset,
  late ACK, off-boundary controls, and relinquishment for this bounded client.
  Type 5 action selection now exhaustively partitions all 1,048,576 class
  words into 1,017,344 source-closed ALU/MAC-plus-PM or PM-only actions and
  31,232 prohibited read-destination collisions. Two independent
  manual-derived fixtures, seven model/schema checks, canonical/raw
  assembler-disassembler paths, exhaustive 24-bit RTL traversal, a formal
  harness, and a fully constrained 51-ALM Cyclone V decoder fit pass. State,
  cache-recovery, native-PM, and whole-core execution remain open.
  Type 8 exhaustively partitions all 524,288 class words into 476,672
  source-closed actions, 16,384 AMF-zero words held under OQ-022, and 31,232
  same-destination collision words held under OQ-014. Two hand-derived
  fixtures, 20,513 representative canonical syntax packets, every supported
  word in both banks, and 983,386 stateful model/RTL cycles pass; fetch,
  interrupt, and bus timing remain open.
  Type 9 is class-complete: all 32,768 words partition into 31,744 conditional
  computations and 1,024 documented AMF-zero no-operation aliases. Two
  hand-derived fixtures, all 21,920 uniquely spellable forms plus raw aliases,
  every word in both banks, and 283,996 stateful model/RTL cycles pass; fetch,
  counter/loop, interrupt, and bus timing remain open.
  Type 10 exhaustively partitions all 524,288 direct-transfer words into
  507,904 source-closed JUMP/CALL actions and 16,384 CALL NOT CE words held
  under OQ-012. Two hand-derived fixtures, every supported numeric-target
  assembler/disassembler form, every supported word in stateful execution,
  and 554,412 model/RTL cycles pass. Active-loop, fetch/cache, interrupt,
  wait-state, bus, and phase integration remain open.
  Type 11 is class-complete for setup: all 262,144 ADDR/TERM words decode and
  execute with simultaneous PC+1/descriptor pushes. Two hand-derived
  fixtures, every assembler/disassembler form, exhaustive RTL decode, and
  554,309 stateful cycles pass. Same-terminal nesting is rejected per the
  original restriction; DO on an active terminal remains OQ-018.
  Type 19 partitions all 128 original fixed-bit words into 124 source-closed
  DAG2-indirect JUMP/CALL actions and four CALL NOT CE words held under
  OQ-012. Two hand-derived fixtures, every supported syntax form, exhaustive
  24-bit RTL decode, and 50,259 stateful cycles pass. Bit-5-one words remain
  reserved under SC-007; active-loop/fetch/interrupt/bus phases remain open.
  Type 20 is class-complete: all 32 conditional RTS/RTI words decode and
  execute. Two hand-derived fixtures, every syntax form, exhaustive 24-bit
  RTL decode, twelve model tests, and 50,254 stateful cycles cover false/taken
  flow, valid PC/status pops, atomic RTI status restore, and non-mutating
  return NOT CE. Missing taken-return context remains an explicit OQ-013
  fail-closed boundary; active-loop/fetch/interrupt-entry/bus phases remain
  open.
  Type 22 is class-complete and phase-aware: all sixteen conditional TRAP
  words decode and execute. Two hand-derived fixtures, every syntax form,
  exhaustive 24-bit RTL decode, twelve model tests, and 50,168 model/RTL
  clocks cover condition outcomes, a held state 7, the state-7/state-8 TRAP
  assertion, state-8 halt, observable PC+1, HALT acknowledgment, and restart.
  General HALT synchronization, BR/BG, interrupt and loop arbitration, and PM
  strobes remain outside the bounded slice; SC-013 records MAME's conflicting
  reserved classification.
  Type 23 is class-complete: all eight ALU-X divisor selections decode and
  execute one old-AQ-selected non-restoring quotient iteration. Two
  hand-derived fixtures, all eight assembler/disassembler forms, exhaustive
  24-bit RTL decode, ten directed tests, and 50,081 unknown-aware model/RTL
  cycles pass. A composed model test executes DIVS plus fifteen DIVQ steps for
  signed positive and negative examples. Appendix B correction exceptions and
  integrated fetch/PC/loop/interrupt/wait timing remain explicitly outside the
  primitive slice.
  Type 24 now partitions all 32 field words into sixteen source-closed DIVS
  actions (AY1/AF times eight ALU-X divisors) and sixteen unsupported AY0/zero
  YOP words. Two hand-derived fixtures, all sixteen assembler/disassembler
  forms, exhaustive 24-bit RTL decode, eleven directed tests, and 50,109
  unknown-aware model/RTL cycles pass. SC-014 records and resolves the
  later-device flag-description conflict in favor of the original-device
  ASTAT table. Fetch/PC/interrupt/loop/wait integration remains.
- **Unresolved questions:** earliest-tool opcode differences and undocumented
  encoding behavior.
- **Confidence:** UNKNOWN

## M7 — Multifunction-instruction semantics

### ISA-002 — Formalize parallel action and collision semantics

- **Status:** IMPLEMENTING
- **Priority:** P0
- **Dependencies:** ISA-001, ARCH-001
- **Acceptance criteria:** legal combinations, pre/new-value rules, DAG update,
  condition/status timing, move/compute collisions, PM/DM concurrency, and
  wait-state effects have source-backed action graphs and directed tests.
- **Source references:** ADI-UM-1989, ADI-UM-FAMILY-1995,
  ADI-ASM-1994
- **Relevant tests:** `make compute-tests`, `tests/test_shift_move.py`,
  `tests/test_compute_dual.py`,
  `tests/test_shifter_dm.py`, `tests/test_compute_move.py`,
  `tests/test_compute_dm.py`, `tests/test_shifter_pm.py`,
  `tests/test_compute_pm.py`, `tests/test_compute_pm_cache.py`,
  `tests/test_compute_pm_native.py`,
  `sim/unit/tb_adsp2100_shift_move_slice.sv`,
  `sim/unit/tb_adsp2100_shifter_dm_slice.sv`,
  `sim/unit/tb_adsp2100_shifter_pm_slice.sv`,
  `sim/unit/tb_adsp2100_compute_move_slice.sv`,
  `sim/unit/tb_adsp2100_compute_dm_slice.sv`, `formal/shift_move.sby`,
  `formal/shifter_dm.sby`, `formal/shifter_pm.sby`,
  `formal/compute_move.sby`, `formal/compute_dm_decode.sby`,
  `formal/compute_dual_decode.sby`,
  `formal/compute_pm_decode.sby`, `formal/compute_pm.sby`,
  `formal/compute_pm_cache.sby`, `formal/compute_pm_native.sby`,
  `formal/compute_dm.sby`
- **Implementation notes:** the bounded Type 14 action graph implements the
  first complete source-backed parallel execution boundary. Shifter X and
  DREG-move source read cycle-start selected-bank state; noncolliding DREG,
  SR/SE/SB, and SS writes commit together at cycle end. Source overlap is
  legal. The decoder fails closed for all same-destination requests and for
  source-unclosed bit-15/XOP forms. Ten directed checks and 82,597 stateful
  RTL/model cycles cover every supported canonical word in both banks. The
  bounded Type 8 action graph independently extends that rule to every
  source-closed ALU/MAC computation and DREG move: all operands and status are
  sampled at cycle start and noncolliding result, feedback, ASTAT, and move
  writes commit together at cycle end. Its exhaustive partition and 983,386
  stateful cycles cover both banks. The bounded Type 12 graph adds old-value
  shifter/store/DAG sampling, read-collision rejection, stable logical DM bus
  extension, and atomic acknowledged shifter/read/I commit for 108,640 words;
  50,069 state/bus clocks pass. The Type 13 graph adds the corresponding
  original PM data action for 54,320 words: old-value `{DREG,PX}` writes,
  24-bit reads split into DREG/PX, DAG2 update, cache-hit completion, and a
  single pure recovery fetch after a miss. Its 50,070 differential clocks
  pass. The integrated monitor boundary adds real pre-cycle hit/data selection,
  recovery fills, ordinary external fills, explicit ownership conflicts, ten
  directed tests, and 50,086 model/RTL clocks. Type 4 now has a source-closed
  action graph: all computation/memory operands are cycle-start selections,
  writes use the old DREG, AMF zero is memory-only, and colliding reads fail
  closed. Its 2,097,152 words partition exhaustively in Python and RTL. The
  bounded state implementation captures all old values once, holds the
  logical transaction and state over DMACK-low clocks, and commits ALU/MAC,
  ASTAT, optional read DREG, and selected I atomically on acknowledgment.
  Twelve model/schema/directed checks and 50,072 differential clocks cover both banks and
  DAGs, memory-only aliases, old-value overlap, reset, conflicts, and unknowns.
  The separate Type 4/native-DM composition adds six directed checks and
  50,082 clocks for state-8 issue, documented pin phases, complete-cycle waits,
  and state-7-only compute/read/I commit. Type 5 now has a source-closed
  action graph for all computation/PM/DAG2 fields, AMF-zero PM-only moves,
  old `{DREG,PX}` stores, PM-read packing, and same-destination rejection;
  all 1,048,576 words partition in Python and RTL. Its bounded state/cache/
  native composition adds old-value selected-bank and DAG2 capture, atomic
  compute/status/read/PX/I completion, issue-time cache-hit selection, one
  pure miss-recovery fetch, 25 directed tests, 50,071 logical clocks, and
  50,083 native phase clocks. Type 1 now has a source-closed action graph for
  all 4,194,304 words: fixed DAG1 DM plus DAG2 PM reads, restricted DD/PD
  destinations, implicit AR/MR compute results, AMF-zero dual fetch, and
  cycle-start/cycle-end ordering. Independent exhaustive Python and RTL,
  primary-derived fixtures, assembler/disassembler, formal assertions, and a
  constrained Cyclone V decoder project verify selection. Type 1 state/cache/
  native execution, shared-owner arbitration, and whole-core events remain.
  Type 3 now has a source-closed direct-DM action graph for all general-register
  directions and absolute addresses. Independent model/database decode,
  hand-derived fixtures, exhaustive RTL, formal assertions, algebraic/raw
  tools, and a constrained Cyclone V decoder fit verify the 1,556,480
  supported and 540,672 unsupported words. Separate structurally independent
  model/RTL compositions connect all general-register state and the native DM
  controller with 50,151 logical and 50,077 native differential clocks. OQ-016
  narrow write sources and whole-core ownership remain open.
- **Unresolved questions:** OQ-014 same-destination behavior, OQ-022 AMF-zero
  Type 8 legality, OQ-023 native PM behavior during Type 1 DMACK extension,
  and result forwarding outside the bounded old-value rule remain high-risk.
- **Confidence:** UNKNOWN

## M8 — Executable architectural model

### MODEL-001 — Independent cycle/transaction reference model

- **Status:** IMPLEMENTING
- **Priority:** P0
- **Dependencies:** ARCH-001; incremental groups depend on ISA-001/ISA-002
- **Acceptance criteria:** model covers all original instructions, exact-width
  state, simultaneous actions, sequencing, interrupts, reset/halt/BR, PM/DM
  transactions, waits, deterministic traces/replay, random initialization, and
  passes directed plus independent differential tests.
- **Source references:** source set required by each implemented group
- **Relevant tests:** `make model-tests`, `make differential`
- **Implementation notes:** the partial model has exact-width primitives,
  fail-closed unsupported opcodes, and a source-derived IF/DO condition
  evaluator. It also has independent pure Type 26 action and composed state
  models that retain both SPP no-change encodings, sample cycle-start
  status/stack values, and atomically update all four stack classes, CNTR, and
  live status at cycle end. Interrupt/RTI arbitration and fetch/bus timing
  remain outside this bounded execution slice. A separate Type 25 model reads
  cycle-start MV, MSTAT bank selection, and MR, conservatively retains unknown
  reset state, and commits conditional MR saturation at cycle end. A separate
  Type 18 model retains all raw MCC aliases, atomically transforms cycle-start
  MSTAT, and fails closed on invalid opcodes or setup collisions. A separate
  Type 21 state model stores all 24 exact-width DAG registers with independent
  validity, applies original linear/circular post-modification to the selected
  I, and invalidates rather than inventing results for unknown or unsupported
  configurations. A separate Type 17 state model independently decodes every
  source/destination selector, rejects reserved or read-only destinations,
  composes all original movable state, preserves authentic unknown reset
  values, and exposes OQ-016 provisional reads. Seven directed checks and all
  4,512 legal pair/bank executions pass; fetch/interrupt/bus cycles remain
  outside the bounded model. A separate Type 6 model decodes the complete
  immediate/DREG class and executes selected-bank cycle-end writes while
  preserving authentic reset unknowns and exact narrow-register side effects.
  A separate Type 7 model independently partitions the complete class,
  right-justifies its fourteen-bit immediate, reuses the complete non-data
  register state, preserves reset unknowns, performs selected-bank SB and
  CNTR/count-stack writes, and fails closed for computational-group, reserved,
  and read-only-SSTAT destinations.
  The integrated model now retires NOP, legal Type 6/7, and all Type 18 MODE
  CONTROL words in a bounded linear-flow context. It applies their state
  actions, advances the PC, records the overlapped fetch at PC+1 rather than
  at the retiring address, and rejects the former synthetic PM-fetch wait
  extension. Seventeen foundation tests cover this boundary, including atomic
  Type 18 MSTAT changes, selected-bank loads, narrow registers, DAG/status,
  count-stack saturation/SSTAT, and reserved Type 7 selectors. Reset-first-
  fetch and multi-owner RTL attachment, active loops, control transfers,
  interrupts, PM-data/cache, HALT, and BR/BG remain outside this model
  increment.
  A structurally separate phase model now composes that architectural state
  with the native PM transaction model. Ten directed tests and 53,427
  deterministic model/RTL clocks cover enabled state-8 issue, state-7 retire,
  phase holds, bus-output relinquishment, PC wrap, invalid fetched data,
  selected-bank Type 6/7/18 ordering, every Type 18 encoding, CNTR stack
  saturation, and fail-closed unsupported/reserved words. Its instruction
  preload is explicitly a deterministic test hook rather than an
  architectural loading mechanism.
  A separate Type 15 model samples a supported shifter X operand and optional
  old SR from the selected bank, applies the signed immediate exponent through
  an independently structured compute model, commits SR at cycle end, and
  preserves authentic unknown state and SE. A separate Type 16 model evaluates
  every IF condition from cycle-start state, preserves all destinations when
  false, executes all sixteen shifter functions when true, and conservatively
  propagates unknown predicate or operand state. A separate Type 14 model
  independently reads both parallel sources from cycle-start state, commits
  the legal write set atomically, propagates unknown operands only to affected
  destinations, and rejects source-unclosed or colliding encodings.
  A separate Type 8 model independently selects ALU/MAC operands and feedback,
  evaluates compute and move sources from one cycle-start bank snapshot,
  atomically commits result/feedback/status/move writes, preserves unknowns,
  and rejects AMF-zero or same-destination encodings.
  A separate Type 9 model evaluates every condition from cycle-start status,
  independently selects ALU/MAC operands and feedback, preserves state for
  false and AMF-zero actions, and atomically commits true result/status writes.
  A separate Type 10 model stores exact-width PC/CNTR/PC-stack/count-stack
  state, applies the sourced direct JUMP/CALL target and return-address rules,
  and executes JUMP NOT CE post-decrement/restore. It fails closed for CALL
  NOT CE and for missing condition/counter context rather than inventing state.
  A separate Type 11 model stores exact-width PC/CNTR/PC-stack/loop-stack
  state, executes all loop-setup words, and makes same-terminal and OQ-018
  rejection explicit.
  A separate Type 19 model adds exact I4-I7 reset-validity state, reads a
  selected target only for taken flow, preserves I without modification,
  exposes PMA drive intent, and composes PC/CNTR/PC-stack/count-stack updates.
  A separate Type 20 model composes exact PC, status, CNTR, PC/count/status
  stack state; implements false PC+1, taken RTS PC pop, and taken RTI atomic
  PC/status pop plus ASTAT/MSTAT/IMASK restore; and samples return NOT CE
  without any counter transition. Missing taken-return context fails closed
  under OQ-013.
  A separate Type 22 model stores exact PC/ASTAT/CNTR validity plus pending,
  TRAP, halt, and HALT-handoff state. It accepts a condition in logical state
  1, preserves it across disabled phase transitions, commits PC+1 and taken
  TRAP at the state-7/state-8 boundary, and resumes only after the documented
  external HALT acknowledgment/release handshake. Twelve directed tests and
  50,168 model/RTL clocks pass.
  A separate Type 23 model reads old selected-bank divisor, AF, AY0, and AQ;
  performs the sourced 16-bit add/subtract; and atomically writes shifted
  AF/AY0 plus new AQ while preserving every other ASTAT bit and the inactive
  bank. Ten directed tests and 50,081 model/RTL cycles pass, including a
  composed signed DIVS-plus-fifteen-DIVQ sequence.
  A separate Type 24 model reads old selected-bank upper-dividend, divisor,
  and AY0 values; atomically writes shifted AF/AY0 plus sign-XOR AQ; preserves
  every other ASTAT bit and the inactive bank; and propagates unknown reset
  sources only to those three destinations. Eleven directed tests and 50,109
  model/RTL cycles pass for all source-closed operands and fail-closed edges.
  A separate Type 12 transaction model captures old selected-bank shifter and
  store operands plus selected I/M/L, holds one logical DM transaction through
  arbitrary DMACK-low clocks, and atomically commits shifter/status, optional
  read DREG, and I post-modification on acknowledgment. Nine directed tests
  and 50,069 state/bus differential clocks pass across both banks and DAGs.
  A separate Type 4 transaction model captures old selected-bank ALU/MAC,
  DREG, and DAG state; holds one logical DM transaction over arbitrary waits;
  and commits computation/status, optional read, and I postmodify atomically.
  Twelve model/schema/directed checks and 50,072 model/RTL clocks pass for both banks and
  DAGs, memory-only aliases, reset, conflicts, and unknown-state propagation.
  A structurally separate Type 4/native-DM model composes that transaction
  with the eight-state bus controller; six directed tests and 50,082 clocks
  cover issue/commit phase alignment, native strobes, waits, reset, late ACK,
  off-boundary rejection, and relinquishment without transliterating RTL.
  A separate Type 5 model closes all ALU/MAC/PM/DAG2 fields and the
  read-destination collision partition, then composes selected-bank state,
  PX packing, fixed PM completion, the instruction-cache monitor, and native
  state-8/state-7 phases. Fourteen logical, six cache, and five native directed
  tests plus 50,071 logical and 50,083 native comparison clocks pass.
  A structurally separate Type 13 transaction model captures old shifter,
  DREG, PX, and DAG2 state; performs the fixed logical PM data action; and
  distinguishes same-cycle next-fetch cache hits from exactly one external
  recovery-fetch cycle. Nine directed tests and 50,070 state/cache/bus clocks
  pass, including read packing, old-value writes, forced fetches, misses,
  reset aborts, conflicts, and authentic invalid-state propagation.
  The standalone instruction-cache model represents the documented 16-word
  low-four-bit-indexed array as one contiguous valid PM region, including
  sequential fill, inside-region refresh, discontinuity restart, circular
  oldest replacement, reset invalidation, and unknown-data preservation. Ten
  directed tests and 50,028 deterministic model/RTL clocks pass.
- **Unresolved questions:** model cycle granularity awaits ADR-0003 evidence.
- **Confidence:** PROVISIONAL

## M9 — Assembler and disassembler workflow

### TOOL-001 — Original-syntax assembler/disassembler workflow

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ISA-001
- **Acceptance criteria:** all documented syntax and directives required by the
  project assemble deterministically; round trips preserve encodings; every
  class has hand-verified fixtures independent of the assembler.
- **Source references:** ADI-ASM-1994; ADI-2101-CROSS-1990 §2.5.3 for
  contemporary original-versus-2101 tool selection only
- **Relevant tests:** `make assembler-tests`, `make decode-tests`
- **Implementation notes:** a fail-closed database-driven seed round-trips the
  independent NOP, exact Type 25 `IF MV SAT MR;`, and original Type 18
  algebraic fixtures and distinguishes legal-unimplemented, original
  reserved, and unshown-reserved words. Type 18 accepts unique comma-separated
  ENA/DIS clauses and emits raw `.WORD` syntax when an MCC=01 alias must be
  preserved exactly. All 32 original `MODIFY (Ix, My);` same-DAG combinations
  also round trip; cross-DAG selections fail closed. All 2,256 legal Type 17
  register pairs round trip while SSTAT destinations and reserved selectors
  fail closed and report bounded execution. Type 3 accepts every supported
  `reg = DM(address);` and `DM(address) = reg;` form at representative address
  boundaries; reserved selectors and reads to SSTAT remain raw unsupported
  words. Type 6 accepts hexadecimal and
  signed/unsigned decimal 16-bit immediates for every DREG destination and
  round trips through canonical hexadecimal disassembly. Type 7 accepts
  hexadecimal and decimal values from -8192 through 16383 for every writable
  non-data destination and round trips through canonical right-justified
  hexadecimal disassembly; SSTAT, computational DREGs, reserved selectors,
  and wider immediates fail closed. Type 15 accepts all
  280 algebraic LSHIFT/ASHIFT PASS/OR HI/LO and source combinations with
  signed-decimal or raw hexadecimal exponents. Unsupported SF/XOP
  subencodings disassemble as unverified and never assemble silently. Type 16
  round trips all 1,792 conditional/unconditional LSHIFT, ASHIFT, NORM, EXP,
  and EXPADJ forms; XOP `001` remains unassembled and visibly unverified. Type
  14 round trips all 25,648 canonical noncolliding shifter-plus-DREG forms;
  bit-15-one, unavailable-XOP, and same-destination words remain visibly
  fail-closed. Type 12 round trips all 108,640 source-closed shifter-plus-DM
  read/write forms with same-DAG address syntax; unavailable-XOP, cross-DAG
  syntax, and read destination collisions fail closed. Type 13 round trips all
  54,320 source-closed shifter-plus-PM read/write forms with DAG2 address
  syntax; unavailable-XOP, DAG1 syntax, and PM-read destination collisions
  fail closed. Type 8 accepts
  canonical source-closed ALU/MAC-plus-DREG
  packets, preserves non-unique supported aliases as raw `.WORD` encodings,
  and visibly rejects AMF-zero and same-destination words. Two hand-derived
  Type 8 fixtures and 20,513 representative canonical packets round trip.
  Type 4 accepts memory-only and computation-plus-DM forms in documented
  clause order, round trips 1,024 canonical memory-only forms plus 2,649
  representative canonical compute forms and two hand-derived fixtures,
  preserves field-valid aliases as raw `.WORD`, rejects cross-DAG syntax,
  and rejects compute/read destination collisions while allowing the
  documented same-register write overlap.
  Type 5 accepts PM-only and computation-plus-PM forms using DAG2 syntax,
  round trips 512 canonical memory-only forms plus 2,649 representative
  canonical compute forms and two hand-derived fixtures, preserves
  field-valid aliases as raw `.WORD`, rejects DAG1 syntax, and rejects
  compute/read destination collisions while allowing old-value write overlap.
  Type 9 round trips all 21,920 uniquely spellable conditional/unconditional
  computations, preserves every field-valid alias with raw `.WORD` syntax,
  and includes two hand-derived primary examples. Type 10 accepts all 507,904
  supported direct numeric-target JUMP/CALL forms, includes two independent
  fixtures, and rejects CALL NOT CE with an OQ-012 diagnostic.
  Type 11 round trips all 262,144 address/termination forms and includes two
  independent hand-derived fixtures. Research surviving lawful assemblers
  first; do not execute legacy tools on the host.
  Type 19 round trips all 124 supported I4-I7 indirect JUMP/CALL forms and
  includes two independent hand-derived fixtures; bit-5-one and four CALL NOT
  CE words remain visibly fail-closed.
  Type 20 round trips all 32 `[IF condition] RTS/RTI;` forms and includes two
  independent hand-derived fixtures.
  Type 22 round trips all sixteen `[IF condition] TRAP;` forms and includes
  two independent hand-derived fixtures. Pinned MAME is not used as its oracle
  because SC-013 records that MAME labels this exact original class reserved.
  Type 23 round trips all eight `DIVQ XOP;` forms and two independent
  hand-derived fixtures.
  Type 24 round trips all sixteen `DIVS AY1/AF, XOP;` forms and two independent
  hand-derived fixtures. The other sixteen field words disassemble as explicit
  unsupported YOP encodings and cannot be silently assembled.
- **Unresolved questions:** scope of macros/object/linker compatibility needed
  for ROM qualification.
- **Confidence:** UNKNOWN

## M10 — Arithmetic logic unit

### RTL-ALU-001 — ALU model and synthesizable RTL

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-001
- **Acceptance criteria:** all ALU operations, feedback paths, flags, saturation,
  condition-false, and bank interactions match cited behavior in model and RTL;
  directed boundary/differential/formal tests pass; synthesis is warning-clean.
- **Source references:** ADI-UM-1989 computational-unit and instruction chapters
- **Relevant tests:** `make compute-tests`, `tests/test_compute_move.py`,
  `tests/test_conditional_compute.py`, `formal/alu.sby`,
  `formal/compute_move.sby`, `formal/conditional_compute.sby`,
  `tests/test_divide_quotient.py`, `formal/divide_quotient.sby`,
  `tests/test_divide_sign.py`, `formal/divide_sign.sby`
- **Implementation notes:** the source-backed standard AMF `0x10`–`0x1f`
  compute block, flags, sticky AV, and AR saturation exist in independent
  model and RTL. Type 8 now connects every source-closed standard ALU field to
  selected-bank operand/feedback selection, atomic AR/AF/ASTAT and parallel
  DREG writeback, and 983,386 ALU/MAC model/RTL packet cycles. Type 9 connects
  all standard conditional ALU fields with true-only AR/AF/ASTAT writeback and
  passes 283,996 cycles over every class word. The bounded Type 23 slice
  executes all eight source-closed DIVQ divisor selections with the old-AQ
  add/subtract decision and atomic AF/AY0/AQ write across 50,081 cycles. The
  bounded Type 24 slice
  executes all sixteen source-closed DIVS operand combinations with atomic
  old-value AF/AY0/AQ semantics and authentic unknown tracking across 50,109
  cycles. Memory multifunction classes remain.
- **Unresolved questions:** Appendix B quotient correction belongs to software;
  whole-core instruction/fetch timing remains open.
- **Confidence:** CORROBORATED

## M11 — Multiplier/accumulator

### RTL-MAC-001 — MAC model and synthesizable RTL

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-001
- **Acceptance criteria:** sign modes, fractional/integer alignment, guard bits,
  rounding, accumulation, saturation, overflow, segmentation, and feedback are
  source-backed and pass boundary, randomized, differential, and formal tests.
- **Source references:** ADI-UM-1989 MAC and instruction chapters
- **Relevant tests:** `make compute-tests`, `tests/test_compute_move.py`,
  `tests/test_conditional_compute.py`, `formal/mac.sby`,
  `formal/compute_move.sby`, `formal/conditional_compute.sby`
- **Implementation notes:** the source-backed fixed-fractional AMF `0x01`–`0x0f`
  compute block, four signedness modes, unbiased rounding, MF extraction, MV,
  and SAT MR transform exist in independent model and RTL. The exact Type 25
  saturation instruction now has a machine-readable semantic entry,
  assembler/disassembler fixture, exact decoder, independent state model,
  selected-bank execution RTL, formal recipes, exhaustive decode, nine model
  tests, and 50,112 model/RTL cycles. Type 8 now connects every source-closed
  fractional MAC field to selected-bank operand/feedback selection and atomic
  MR/MF/MV plus parallel DREG writeback; all supported Type 8 words execute in
  both banks within the 983,386-cycle differential run. Type 9 connects all
  standard conditional MAC fields with true-only MR/MF/MV writeback and passes
  283,996 cycles over every class word. Memory-access multifunction timing
  remains.
- **Unresolved questions:** original-device multiplier visibility within
  multifunction instructions and the recorded MAME rounding conflict SC-008.
- **Confidence:** CORROBORATED

## M12 — Barrel shifter

### RTL-SHIFT-001 — Shifter model and synthesizable RTL

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-001
- **Acceptance criteria:** immediate/register shifts, logical/arithmetic modes,
  normalization, exponent/block exponent, off-scale fill, feedback, and status
  pass edge, differential, and formal tests.
- **Source references:** ADI-UM-1989 shifter and instruction chapters
- **Relevant tests:** `make compute-tests`, `tests/test_immediate_shift.py`,
  `tests/test_conditional_shift.py`, `formal/shifter.sby`,
  `tests/test_shift_move.py`, `formal/immediate_shift.sby`,
  `formal/conditional_shift.sby`, `formal/shift_move.sby`,
  `tests/test_shifter_dm.py`, `formal/shifter_dm.sby`,
  `tests/test_shifter_pm.py`, `formal/shifter_pm.sby`
- **Implementation notes:** all sixteen source-backed SF functions now exist
  in the independent model and portable combinational RTL. Exact signed counts,
  HI/LO placement, PASS/OR, ASHIFT/LSHIFT, NORM AC extension, EXP HI/HIX/LO,
  EXPADJ, and explicit write enables pass directed and 644,368-vector
  model-versus-RTL tests. The bounded Type 15 slice adds exact decode,
  selected-bank reads, old-SR OR feedback, cycle-end SR writeback, and 58,709
  stateful cycles over all 14,336 supported words in both banks. SF 8–15 and
  unavailable XOP `001` fail closed. The bounded Type 16 slice adds all 1,792
  source-backed conditional register-exponent functions, true/false gating,
  SR/SE/SB/SS writeback, exhaustive class partitioning, and 54,403 stateful
  model/RTL cycles. Its 256 unavailable-XOP words fail closed under OQ-020.
  The bounded Type 14 slice adds old-value shifter-plus-DREG parallel reads,
  atomic noncolliding writeback, 25,648 supported canonical words, and 82,597
  stateful model/RTL cycles. The bounded Type 12 slice adds all 108,640
  source-closed shifter-plus-DM actions, stable acknowledged/waited logical
  bus transactions, atomic shifter/read/DAG completion, and 50,069 stateful
  differential clocks. The bounded Type 13 slice adds all 54,320 source-closed
  shifter-plus-PM actions, exact PX packing, old-value stores, atomic PM-read/
  shifter/DAG2 completion, same-cycle next-fetch cache hits, and one pure
  recovery fetch after a miss across 50,070 differential clocks. Standalone-
  cache wiring, whole-core fetch integration, and physical eight-state
  bus phases remain.
- **Unresolved questions:** reset values, same-cycle visibility during
  multifunction writeback, and OQ-011's manually loaded `SE=0x80` NORM
  negation; no undocumented shifter saturation operation is assumed.
- **Confidence:** CORROBORATED

## M13 — Data-address generator 1

### RTL-DAG1-001 — DAG1 addressing

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-002
- **Acceptance criteria:** all legal I/M/L combinations, linear/circular and
  applicable bit-reversed behavior, signed modifies, zero/non-power-of-two
  lengths, update order, waits, loops, and interrupts pass model/RTL tests.
- **Source references:** ADI-UM-1989 DAG and data-move chapters
- **Relevant tests:** `make dag-tests`, `formal/dag.sby`,
  `formal/modify_address_slice.sby`, `tests/test_indirect_jump.py`,
  `formal/indirect_jump.sby`
- **Implementation notes:** an independent function model and portable
  combinational RTL implement old-I output, signed post-modify, L=0 linear
  wrap, circular wrap, original power-of-two alignment, and all-14-bit DAG1
  reversal. Ten directed/random model tests and 204,864 model-versus-RTL
  vectors pass, including all reversed addresses. Invalid circular
  configurations are exposed diagnostically, not assigned invented semantics.
  A bounded Type 21 slice adds exact I/M/L storage, all DAG1 selections,
  selected-I cycle-end writeback, and 50,124 stateful model/RTL cycles. Type
  12 now attaches every DAG1 I/M selection to a DM transaction, including bit
  reversal and completion-only post-modification through arbitrary waits;
  50,064 connected clocks verify its native-phase attachment. Type
  2 adds the same sourced waited/post-modified path for immediate DM writes
  across 50,035 logical differential clocks and 50,027 native-attached clocks.
- **Unresolved questions:** remaining direct-transfer writeback and stall enables,
  same-cycle external register writes, alternate banking, multifunction
  ordering, loops, interrupts, and externally visible timing.
- **Confidence:** CORROBORATED

## M14 — Data-address generator 2

### RTL-DAG2-001 — DAG2 addressing

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-002
- **Acceptance criteria:** DAG2's documented PM/DM roles and every legal
  I/M/L/update case pass independently and concurrently with DAG1.
- **Source references:** ADI-UM-1989 DAG and data-move chapters
- **Relevant tests:** `make dag-tests`, `formal/dag.sby`,
  `formal/modify_address_slice.sby`, `tests/test_shifter_pm.py`,
  `formal/shifter_pm.sby`
- **Implementation notes:** the common source-backed post-modify/modulus block
  has a DAG2 configuration in which bit-reverse is structurally ineffective;
  all vectors compare DAG1/DAG2 arithmetic. The bounded Type 21 slice adds all
  DAG2 register selections, exact I/M/L storage, selected-I writeback, and
  stateful comparison. Type 2, Type 4, and Type 12 attach every DAG2 I/M
  selection to immediate, ALU/MAC-plus-DM, and shifter-plus-DM transactions,
  respectively, with
  completion-only post-modification. The bounded Type 19
  slice now reads exact I4-I7 storage
  without modification, drives a testable PMA-target observation when taken,
  and passes 50,259 model/RTL cycles. The bounded Type 13 path attaches every
  DAG2 I/M selection to a PM data transaction and post-modifies only when its
  fixed data cycle commits. Other PM and non-Type-2/4/12 DM data-bus attachment
  does not exist.
- **Unresolved questions:** differing register group restrictions and
  simultaneous PM/DM semantics.
- **Confidence:** CORROBORATED

## M15 — Program sequencer

### RTL-SEQ-001 — Program sequencer

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-001, TIME-001
- **Acceptance criteria:** sequential PC, every condition, branch/call/return,
  loops, stacks, flushes, and control interactions match model, cycle, and
  formal properties.
- **Source references:** ADI-UM-1989 sequencer and instruction chapters
- **Relevant tests:** `make sequencer-tests`, `tests/test_counter.py`,
  `tests/test_sequencer_stacks.py`, `tests/test_sequencer_slice.py`,
  `tests/test_stack_control.py`, `tests/test_stack_control_slice.py`,
  `tests/test_direct_jump.py`, `tests/test_do_until.py`,
  `tests/test_indirect_jump.py`, `tests/test_conditional_return.py`,
  `tests/test_conditional_trap.py`,
  `formal/sequencer_flow.sby`, `formal/counter.sby`,
  `formal/sequencer_stacks.sby`, `formal/sequencer_slice.sby`,
  `formal/stack_control_decode.sby`, `formal/stack_control_slice.sby`,
  `formal/direct_jump.sby`, `formal/do_until.sby`, `formal/indirect_jump.sby`,
  `formal/conditional_return.sby`, `formal/conditional_trap.sby`
- **Implementation notes:** an independent instruction-boundary model and
  portable combinational RTL select sequential, jump, call, return, loop-back,
  and loop-exit flow. All 636,512 model-versus-RTL vectors pass, including
  every 14-bit PC for return-address wrap and explicit-transfer precedence at
  loop end. A separate model/RTL boundary implements exact 16-entry PC,
  four-entry count, and four-entry loop stack storage, saturating pointers,
  newest-push loss, sticky overflow, and their six SSTAT sources. Ten
  directed/model tests and 50,062 model-versus-RTL stack cycles pass. The flow
  and storage blocks also remain independently testable. A third model/RTL
  boundary implements CNTR validity, cycle-start CE/NOT CE, cycle-end
  post-decrement, valid-load stack push, true-CE pop/restore or empty
  invalidation, and valid manual restore. Twelve directed/model tests and
  50,022 model-versus-RTL counter cycles pass. A bounded integration model/RTL
  now connects conditions, DO setup, explicit flow, CNTR, and all three
  sequencer stacks. Fifteen directed/random tests and 50,014 stateful
  model-versus-RTL cycles cover exact-N/nested CE loops, JUMP/RETURN CE
  distinctions, loop-stack descriptors, and atomic rejection of unresolved
  collisions. A separate source-backed Type 26 model/RTL boundary now
  executes all 32 manual stack-control words against all four stack classes,
  live CNTR/status, and composed SSTAT. Nine directed/schema/random checks and
  50,015 stateful comparison cycles pass; automatic sequencer and interrupt
  arbitration remain deliberately unconnected.
  A bounded Type 10 instruction slice now connects exact decode to an authentic
  reset-valued 14-bit PC, conditional direct targets, CALL return stacking,
  and JUMP NOT CE CNTR/count-stack transitions. Twelve model tests, exhaustive
  RTL decode, and 554,412 stateful cycles cover all 507,904 supported words;
  the 16,384 CALL NOT CE words fail closed under OQ-012.
  A bounded Type 11 instruction slice connects exact DO decode to PC and
  PC/loop stacks. Twelve model tests, exhaustive 24-bit RTL decode, and
  554,309 stateful cycles cover every word, sourced nesting legality, CE
  context, OQ-018, reset, overflow, invalid opcodes, and conflicts.
  A bounded Type 19 instruction slice connects exact fixed-bit decode to I4-I7
  target storage, conditional PC selection, PMA-drive intent, taken CALL
  stacking, and JUMP NOT CE transitions. Twelve model tests, exhaustive
  24-bit RTL decode, and 50,259 stateful cycles cover all 124 supported words;
  four CALL NOT CE words fail closed under OQ-012 and bit-5-one remains
  reserved under SC-007.
  A bounded Type 20 instruction slice connects exact decode to conditional
  PC-stack returns and RTI's simultaneous PC/status pops plus live status
  restore. Twelve model tests, exhaustive 24-bit RTL decode, and 50,254
  stateful cycles cover all 32 words, including return NOT CE without counter
  mutation and OQ-013 missing-context rejection.
  A phase-aware Type 22 instruction slice connects exact decode to PC+1,
  condition sampling, state-7/state-8 TRAP assertion, state-8 hold, and the
  external HALT handoff. Twelve model tests, exhaustive 24-bit RTL decode,
  and 50,168 deterministic model/RTL clocks cover every word and the complete
  documented handshake.
- **Unresolved questions:** whole-core PC/fetch integration,
  conditional-CALL CE semantics (OQ-012), competing automatic/manual actions
  (OQ-018), interrupt recognition/entry, delayed transfers, cache interaction,
  physical empty-pop effects (OQ-013), pipeline visibility, and logical bus
  phases.
- **Confidence:** CORROBORATED

## M16 — Register files and alternate register bank

### RTL-REG-001 — Computational register files and banking

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-002
- **Acceptance criteria:** all primary/alternate registers, switching timing,
  interrupt/context interactions, simultaneous reads/writes, and reset
  classifications pass directed and formal tests.
- **Source references:** ADI-UM-1989 printed pp. 2-5–2-7, 2-13–2-18,
  2-21–2-23, 4-8, 4-22, 5-13, 6-4–6-6, A-9
- **Relevant tests:** `make register-tests`, `tests/test_register_banks.py`,
  `make mode-tests`, `tests/test_mode_integration.py`,
  `tests/test_internal_move.py`, `formal/registers.sby`,
  `tests/test_load_dreg_immediate.py`,
  `tests/test_load_non_dreg_immediate.py`, `tests/test_immediate_shift.py`,
  `tests/test_conditional_shift.py`,
  `tests/test_shift_move.py`,
  `tests/test_compute_move.py`,
  `formal/mode_slice.sby`, `formal/internal_move_decode.sby`,
  `formal/load_dreg_immediate.sby`,
  `formal/load_non_dreg_immediate.sby`, `formal/immediate_shift.sby`,
  `formal/conditional_shift.sby`, `formal/shift_move.sby`,
  `formal/compute_move.sby`
- **Implementation notes:** the exact banked set is primary-verified. The
  independent model and portable RTL implement both banks for all 16 DREG
  codes plus AF, MF, and SB; exact SE/MR2/SB widths; three cycle-start reads;
  cycle-end DREG and unit-specific ALU/MAC/shifter writeback; atomic 40-bit MR
  writes; MF bits 31–16 extraction; MR1-to-MR2 sign extension; and
  fail-closed collision suppression. The RTL has exactly 554 architectural
  storage bits and deliberately no reset assignment. An integrated
  model/RTL slice connects MSTAT bit 0 using old-mode/current-cycle and
  new-mode/following-cycle visibility. The regression passes
  58,307 DREG cycles plus 50,120 full-bank/writeback cycles against the
  independent model, plus 50,112 mixed MSTAT-consumer cycles. Exact Type 17
  action decode now identifies every legal computational/DAG/status/PX/CNTR
  source and destination. The bounded Type 17 slice now connects them with
  old-bank/current-cycle ordering and 59,430 passing model/RTL cycles. The
  exact Type 6 slice connects full-width immediate decode to the same banked
  DREG write path and passes exhaustive class decode plus 50,204 stateful
  model/RTL cycles across all destinations and both banks. The exact Type 7
  slice reuses the shared complete register state; selected-bank SB writes and
  all other exact-width non-data writes pass exhaustive decode plus 50,299
  stateful model/RTL clocks. The bounded Type 15
  slice uses the same selected-bank SR writeback and passes 58,709 cycles over
  every supported word in both banks. The bounded Type 16 slice uses the same
  bank boundary for all SR/SE/SB shifter writebacks, commits EXP SS to ASTAT,
  and passes 54,403 cycles over every supported word in both banks.
  The bounded Type 14 slice exercises simultaneous DREG and shifter writeback,
  preserves old-value reads in both clauses, and passes 82,597 cycles over all
  25,648 supported canonical words in both banks.
  The bounded Type 8 slice adds simultaneous selected-bank ALU/MAC result,
  feedback/status, and DREG writeback with cycle-start old-value reads. Its
  exhaustive both-bank differential run passes 983,386 cycles over all
  476,672 source-closed words plus deterministic setup/error cases.
  The Type 9 slice uses the same selected-bank computational destinations,
  suppresses every false/AMF-zero write, and passes 283,996 cycles over all
  32,768 words in both banks.
- **Unresolved questions:** full instruction/multifunction legality, operand
  and result decode connectivity, interrupt/context interactions, OQ-014
  real-device behavior for illegal collisions, and OQ-015
  interrupt-adjacent bank-switch visibility.
- **Confidence:** CORROBORATED

## M17 — Status and mode registers

### RTL-STATUS-001 — Status, mode, interrupt, and system registers

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, RTL-REG-001
- **Acceptance criteria:** all fields, reserved bits, reset values, read/write
  effects, flag latency, masks, and context stacking pass tests tied to cited
  original applicability.
- **Source references:** ADI-UM-1989 printed pp. 4-20–4-24, 5-13, A-8
- **Relevant tests:** `make status-tests`, `make mode-tests`,
  `make sequencer-tests`,
  `tests/test_status_registers.py`, `tests/test_mode_integration.py`,
  `tests/test_mode_control.py`,
  `tests/test_internal_move_slice.py`,
  `tests/test_load_non_dreg_immediate.py`,
  `tests/test_sequencer_stacks.py`, `formal/status_registers.sby`,
  `formal/mode_slice.sby`, `formal/mode_control_slice.sby`,
  `formal/sequencer_stacks.sby`, `formal/internal_move_slice.sby`
- **Implementation notes:** the machine-readable register map, independent
  model, and portable RTL now implement exact eight-bit ASTAT, four-bit MSTAT,
  five-bit ICNTL, and four-bit IMASK storage; authentic ASTAT/ICNTL reset
  unknowns; MSTAT/IMASK reset clear; all four direct mode outputs; both MODE
  CONTROL no-change codes plus independent clear/set; cycle-end
  ALU/divide/MAC/shifter status writes; interrupt-entry snapshot and nested
  mask transformation; RTI-style status restore; aborted-instruction status
  suppression; and fail-closed collision handling. Seventeen directed tests
  and 50,287 model-versus-RTL cycles pass. The SSTAT field map is extracted,
  and separate status and sequencer-stack storage blocks now provide all eight
  SSTAT empty/sticky-overflow sources. The bounded Type 26 execution slice
  composes those sources and connects manual status push/restore to live
  ASTAT/MSTAT/IMASK. Later
  memory-mapped peripheral control registers are excluded from the ADSP-2100
  default. A bounded integration slice now wires all four MSTAT bits to the
  computational bank, DAG1 bit reverse, sticky AV, and AR saturation using
  the documented start-read/end-write cycle boundary. Five directed tests and
  50,112 model-versus-RTL integration cycles pass. The exact Type 18 decoder
  and bounded state slice connect every original MCC combination to live
  MSTAT. Eight directed/schema/random tests, exhaustive 24-bit decode, all
  4,096 opcode/initial-state transforms, and 58,248 model/RTL cycles pass.
  The bounded Type 17 slice now connects direct ASTAT/MSTAT/IMASK/ICNTL moves,
  composed SSTAT reads, and CNTR/count-stack effects; its narrow read extension
  remains explicitly provisional under OQ-016.
  The exact Type 7 slice connects immediate ASTAT/MSTAT/IMASK/ICNTL/CNTR loads
  to the same live state, rejects read-only SSTAT, and passes exact-width and
  CNTR/count-stack tests without depending on OQ-016 read extension.
- **Unresolved questions:** architectural SSTAT instruction reads, interrupt
  recognition/RTI/status-stack arbitration, empty-pop effects (OQ-013), narrow
  DMD read extension (OQ-016), competing-write behavior (OQ-017), and
  interrupt-adjacent bank-switch visibility (OQ-015).
- **Confidence:** CORROBORATED

## M18 — Program-memory interface

### RTL-PMBUS-001 — Native program-memory interface

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** DEV-001, TIME-001
- **Acceptance criteria:** sourced pins/polarities, logical phases, fetch
  transactions, wait extension, bus relinquishment, and data stability pass
  trace assertions and formal properties.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989 system-interface chapter
- **Relevant tests:** `make bus-tests`, `tests/test_shifter_pm_cache.py`,
  `sim/unit/tb_adsp2100_shifter_pm_cache_slice.sv`,
  `formal/shifter_pm_cache.sby`, `tests/test_program_bus.py`,
  `sim/unit/tb_adsp2100_program_bus.sv`, `formal/pm_bus.sby`,
  `tests/test_shifter_pm_native.py`,
  `sim/unit/tb_adsp2100_shifter_pm_native_slice.sv`,
  `formal/shifter_pm_native.sby`, `tests/test_compute_pm_cache.py`,
  `tests/test_compute_pm_native.py`,
  `sim/unit/tb_adsp2100_compute_pm_native_slice.sv`,
  `formal/compute_pm_cache.sby`, `formal/compute_pm_native.sby`,
  `tests/test_linear_core.py`,
  `sim/unit/tb_adsp2100_linear_core_slice.sv`, `formal/linear_core.sby`
- **Implementation notes:** keep PM physically/logically distinct from DM.
  The Type 13 slice now exposes a bounded logical PM data/fetch boundary with
  separate 14-bit address, 24-bit read/write data, direction, data-cycle, and
  recovery-fetch observations. It verifies that a cache hit completes the
  next fetch in the data cycle and that a miss/forced fetch emits exactly one
  pure recovery cycle. A composed boundary now connects the functional
  16-word monitor: pre-cycle hits supply the actual next instruction, recovery
  fetches fill it, and ordinary external fetches share it under explicit
  ownership rules. Ten directed tests and 50,086 integration clocks pass.
  Simultaneous external-fill/Type-13 requests are integration errors; their
  fail-closed priority is not claimed as original-device arbitration.
  A separate native PM phase controller uses an implementation request
  boundary aligned to the state-8-to-1 edge, implements active-low
  PMS/PMRD/PMWR, PMA/PMDA, state-7 read sampling,
  states-5-through-8 write-data drive, back-to-back PMS continuity, and
  externally directed bus-output masking. Ten directed tests and 50,032
  model/RTL clocks pass; its formal recipe is assertion-linted and its
  constrained Cyclone V fit passes. A bounded native wrapper now attaches the
  cache-integrated Type 13 owner: issue/setup controls are accepted only on an
  enabled state-8-to-state-1 boundary; captured old-value PM data descriptors
  remain stable; architectural effects commit only at state 7-to-8; and a
  miss recovery is accepted back-to-back on the following state 8-to-1 edge.
  Five directed tests and 50,081 model/RTL clocks pass, its formal recipe
  syntax-checks, and a fully constrained 50 MHz Cyclone V fit uses
  2,055 ALMs and 1,648 registers. A second bounded client now attaches Type 5
  ALU/MAC-plus-PM through the same cache/native boundary. Six cache and five
  native directed tests plus 50,083 native clocks verify old-value compute/PX/
  DAG2 capture, state-7 atomic completion, hit/miss recovery, and
  relinquishment; its fully constrained 25 ns native fit uses 1,894 ALMs,
  1,746 registers, one DSP, and no RAM. Whole-core fetch/control arbitration
  remains open. A bounded ordinary linear-fetch owner now shares the native PM
  controller with NOP, legal Type 6/7, and every Type 18 MODE CONTROL word. It
  admits PC+1 fetch only at enabled state 8-to-1, commits the current action
  and loaded next word at state 7-to-8, preserves pending state through phase
  holds/relinquishment, and fails closed for unsupported or reserved current
  words. Ten directed tests and 53,427 phase clocks pass, with each Type 18
  encoding exercised in the integrated flow. Reset's special first-fetch
  waveform, PM-data/cache ownership, transfers, loops, interrupts, HALT, and
  BR/BG arbitration remain separate work.
- **Unresolved questions:** whole-core PM ownership, BR/BG recognition timing,
  and electrical wrapper constraints.
- **Confidence:** CORROBORATED

## M19 — Data-memory interface

### RTL-DMBUS-001 — Native data-memory interface

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** DEV-001, TIME-001
- **Acceptance criteria:** sourced pins/polarities, read/write phases, waits,
  bus arbitration, concurrent PM operation, and stall stability pass traces and
  formal properties.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989 system-interface chapter
- **Relevant tests:** `tests/test_dm_write_immediate_slice.py`,
  `sim/unit/tb_adsp2100_dm_write_immediate_slice.sv`,
  `formal/dm_write_immediate_slice.sby`, `tests/test_shifter_dm.py`,
  `sim/unit/tb_adsp2100_shifter_dm_slice.sv`, `formal/shifter_dm.sby`,
  `tests/test_data_bus.py`, `sim/unit/tb_adsp2100_data_bus.sv`,
  `formal/dm_bus.sby`, `tests/test_dm_write_immediate_native.py`,
  `sim/unit/tb_adsp2100_dm_write_immediate_native_slice.sv`,
  `formal/dm_write_immediate_native.sby`, `tests/test_shifter_dm_native.py`,
  `sim/unit/tb_adsp2100_shifter_dm_native_slice.sv`,
  `formal/shifter_dm_native.sby`, `tests/test_compute_dm_native.py`,
  `sim/unit/tb_adsp2100_compute_dm_native_slice.sv`,
  `formal/compute_dm_native.sby`, `make dm-bus-tests`,
  `make dm-write-native-tests`, `make dm-shifter-native-tests`,
  `make dm-compute-native-tests`, `make compute-tests`
- **Implementation notes:** the Type 2 immediate-write, Type 4 ALU/MAC, and Type 12
  multifunction boundaries expose a distinct logical
  14-bit DM address, select, read/write direction, 16-bit write data, DMACK,
  completion, and validity signals. It holds the transaction stable over waits
  and sample read data only at completion. Type 2 adds captured raw immediate
  data and passes 50,035 state/bus clocks. A separate native controller now
  captures descriptors at state 8-to-1, drives DMA/DMS states 1–8,
  DMRD/DMWR states 4–7, samples DMACK at state 6-to-7, samples read data at
  state 7-to-8, and drives write data states 5–8. A low DMACK retains
  processor state seven while all eight physical substates repeat; nine
  directed tests and 50,039 model/RTL clocks cover repeated low samples,
  late ACK rejection, back-to-back DMS continuity, holds, reset, unknowns,
  and relinquishment masking. A bounded Type 2 wrapper now accepts the
  old-I/raw-immediate write descriptor only at state 8-to-1 and commits the
  selected-I postmodify only when the native controller completes at state
  7-to-8 after a qualified DMACK. Five directed tests and 50,027 connected
  model/RTL clocks cover issue/commit ordering, complete-cycle waits, late-ACK
  rejection, stable old values, off-boundary rejection, and relinquishment.
  A second bounded wrapper attaches Type 12 reads and writes: it samples DMD
  at native completion and atomically commits the shifter, optional DREG load,
  and selected-I postmodify. Six directed tests and 50,064 connected clocks
  cover old-DREG stores, state-7 reads, full-cycle waits, invalid read data,
  reset, conflicts, and relinquishment. Its forty-eighth formal recipe
  syntax-checks;
  a fully constrained 50 MHz Cyclone V fit uses 100 ALMs and 57 registers.
  The attached Type 2 fit uses 608 ALMs and 466 registers, meets 50 MHz with
  +2.590 ns worst setup and +0.159 ns worst hold slack, and has no
  unconstrained paths. The attached Type 12 fit uses 1,739 ALMs and 1,139
  registers, meets 50 MHz with +1.262 ns worst setup and +0.167 ns worst hold
  slack, and has no unconstrained paths. A third bounded wrapper attaches
  Type 4 memory-only and ALU/MAC reads/writes. Six directed tests and 50,082
  clocks cover state-8 issue, native phases, complete-cycle waits, state-7
  atomic compute/status/read/I commit, reset, late ACK, off-boundary rejection,
  and relinquishment. Its fully constrained 25 ns Cyclone V fit uses 1,693
  ALMs, 1,226 registers, one DSP, no RAM, and has positive multicorner
  setup/hold slack. Whole-core arbitration does not yet exist.
- **Unresolved questions:** shared data-bus turnaround, Type 1 dual-memory
  concurrency, event latching during waits, and BR/BG recognition.
- **Confidence:** CORROBORATED

## M20 — Program-memory data transfers

### RTL-PMDATA-001 — PM data read/write semantics

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ISA-002, RTL-PMBUS-001, RTL-DAG2-001
- **Acceptance criteria:** all PM data-move widths, packing, addressing,
  concurrency, waits, destination timing, and write data pass model/RTL bus
  traces and collision tests.
- **Source references:** ADI-UM-1989 PM transfer and data-move sections
- **Relevant tests:** `make instruction-tests`, `make bus-tests`,
  `tests/test_shifter_pm.py`, `sim/unit/tb_adsp2100_shifter_pm_slice.sv`,
  `formal/shifter_pm.sby`, `tests/test_shifter_pm_cache.py`,
  `sim/unit/tb_adsp2100_shifter_pm_cache_slice.sv`,
  `formal/shifter_pm_cache.sby`
- **Implementation notes:** Type 13 closes the original shifter-plus-PM form
  for 54,320 source-backed words: reads place PMD bits 23:8 in the selected
  DREG and bits 7:0 in PX; writes use old `{DREG,PX}`; all actions use DAG2
  and commit in the fixed PM data cycle. A cache miss or forced fetch adds one
  external recovery-fetch cycle without repeating the data/shifter/DAG action.
  The composed monitor boundary supplies actual hit data, fills that recovery
  word, accepts ordinary external instruction fills, and passes 50,086
  model/RTL clocks.
- **Unresolved questions:** exact hidden cache-monitor/event interactions,
  ordinary fetch and other original PM-transfer owners, whole-core fetch/event
  arbitration, and BR/BG/HALT/interrupt ownership.
- **Confidence:** CORROBORATED

## M21 — Loop and stack behavior

### RTL-STACK-001 — Hardware loops and architectural stacks

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** RTL-SEQ-001, ARCH-001
- **Acceptance criteria:** loop/PC/status stack depths, push/pop timing, nesting,
  terminal instruction behavior, interrupts, and documented overflow/underflow
  pass boundary and formal tests.
- **Source references:** ADI-DATABOOK-1987 printed pp. 2-21–2-22;
  ADI-UM-1989 printed pp. 4-3–4-10, 4-22, 5-13, A-10
- **Relevant tests:** `make sequencer-tests`, `make status-tests`,
  `make decode-tests`,
  `tests/test_counter.py`, `tests/test_status_stack.py`,
  `tests/test_sequencer_stacks.py`, `tests/test_sequencer_slice.py`,
  `tests/test_stack_control.py`, `tests/test_stack_control_slice.py`,
  `formal/counter.sby`, `formal/status_stack.sby`,
  `formal/sequencer_stacks.sby`, `formal/sequencer_slice.sby`,
  `formal/stack_control_decode.sby`, `formal/stack_control_slice.sby`
- **Implementation notes:** all original depths are now source-backed. The
  four-by-sixteen status stack has an independent state model, portable RTL,
  eight directed/model tests, 50,037 model-versus-RTL cycles, a formal
  harness, and a constrained Cyclone V fit. The exact 16-by-14 PC, four-by-14
  count, and four-by-18 loop stacks have a separate independent model,
  portable RTL, ten directed/model tests, 50,062 model-versus-RTL cycles,
  a formal harness, and a constrained Cyclone V fit. Every stack drops the
  newest push when full, saturates its depth, and retains sticky overflow
  until reset; all SSTAT source bits now exist at storage boundaries. The
  separate CNTR boundary generates the documented load/true-CE/manual-pop
  count-stack requests and passes 50,022 model/RTL cycles. A bounded
  integration slice physically connects those requests to count storage and
  couples DO setup/termination with PC and loop storage across 50,014
  additional model/RTL cycles. The Type 26 action decoder now maps every
  original manual encoding to status/count/PC/loop requests, retains both
  status no-change aliases, and is exhaustive over the 24-bit input space. A
  composed Type 26 model/RTL slice now applies all field-selected actions
  atomically to PC/count/loop/status storage, restores CNTR and live status
  from cycle-start tops, composes SSTAT, and passes nine directed/schema/random
  model checks plus 50,015 model-versus-RTL cycles.
- **Unresolved questions:** integration with automatic instruction flow and
  interrupt/RTI actions, conditional-CALL CE behavior (OQ-012), competing
  automatic/manual priorities (OQ-018), the architectural SSTAT read path,
  and empty-pop architectural behavior (OQ-013).
- **Confidence:** CORROBORATED

## M22 — Interrupt behavior

### RTL-IRQ-001 — Interrupt recognition, priority, entry, and return

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** RTL-SEQ-001, RTL-STATUS-001, TIME-001
- **Acceptance criteria:** original pins/vectors, recognition boundary,
  priority, mask/latch behavior, nesting, context/bank effects, latency, and
  return timing pass directed, randomized, bus, and formal tests.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989 interrupt sections
- **Relevant tests:** `make interrupt-tests`, `tests/test_conditional_return.py`,
  `formal/conditional_return.sby`, `formal/interrupt.sby`
- **Implementation notes:** exclude later-device interrupt sources and vectors.
  Status entry snapshot/mask transformation exists. The bounded Type 20 slice
  now implements the valid-context RTI half: simultaneous PC/status pops and
  ASTAT/MSTAT/IMASK restoration pass 50,254 model/RTL cycles. Recognition,
  priority, vectoring, abort, entry-stack connectivity, and full latency do
  not yet exist.
- **Unresolved questions:** edge/level sensitivity and reset-release boundary.
- **Confidence:** UNKNOWN

## M23 — Reset, halt, and bus arbitration

### RTL-SYS-001 — Reset, HALT, BR/BG, and restart

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** DEV-001, TIME-001, RTL-PMBUS-001, RTL-DMBUS-001
- **Acceptance criteria:** assertion/release, minimum reset, initial fetch,
  documented/unknown state, bus pins during reset, halt/restart, BR recognition,
  BG/reacquire, and interrupt interactions pass cycle and formal tests.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ATARI-ADSP-SCHEM
- **Relevant tests:** `make bus-tests`, `make interrupt-tests`,
  `tests/test_conditional_trap.py`, `formal/conditional_trap.sby`,
  `formal/system_control.sby`
- **Implementation notes:** use clock enables and phase state, never gated
  clocks. The Type 22 boundary now implements the source-backed TRAP half of
  system control, including state-8 hold and an input explicitly representing
  HALT after recognition. The raw asynchronous HALT synchronizer, general
  pin-driven halt, BR/BG, and bus tristate control remain unimplemented.
- **Unresolved questions:** exact composition priority among general HALT,
  TRAP, BR/BG, DMACK waits, reset, and interrupts.
- **Confidence:** UNKNOWN

## M24 — Pipeline and instruction timing

### TIME-001 — Source-backed pipeline and cycle model

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** DEV-001, REF-001
- **Acceptance criteria:** all documented instruction cases, overlap, false
  conditions, transfers, loops, stacks, interrupts, waits, halt, and BR have
  cycle definitions and automated assertions; unresolved timing is disclosed.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989, ADR-0003
- **Relevant tests:** `tests/test_cycle_tables.py`, all timing/bus regressions
- **Implementation notes:** the eight-state baseline, ordinary/PM-miss/wait/
  interrupt/HALT cases, and phase sampling points are documented. Type 22 now
  has an automated phase-level state-7/state-8 assertion and HALT handshake,
  including phase-hold testing. Types 5 and 13 now automate the documented
  fixed PM data cycle and distinguish same-cycle cached-next-fetch completion from
  exactly one recovery-fetch cycle on a miss or forced fetch; the full opcode
  timing table is not. Logical
  phase fidelity is separate from analog delay modeling.
  The connected cache monitor verifies low-four-bit fills, contiguous-region
  hits, discontinuity invalidation, oldest replacement, hit-word selection,
  and recovery fills; this does not yet close branch/loop/interrupt/HALT/BR
  arbitration under OQ-008.
  The independent top-level model and a bounded native RTL owner now enforce
  the sourced ordinary-flow overlap for NOP, legal Type 6/7, and all Type 18
  MODE CONTROL words: the current-PC instruction executes while PC+1 is
  fetched, then action/PC/next-word state retires at state 7-to-8. The phase
  model and RTL agree for 53,427 clocks, including every Type 18 encoding, and
  no longer permit an invented ordinary-PM wait extension. Reset first-fetch,
  all other instruction owners, control events, and arbitration are pending.
- **Unresolved questions:** fetch/decode/execute visibility and PM-data conflict
  penalties.
- **Confidence:** UNKNOWN

## M25 — External wait-state behavior

### TIME-002 — PM/DM wait states and transaction extension

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** TIME-001, RTL-PMBUS-001, RTL-DMBUS-001
- **Acceptance criteria:** wait sampling, per-space configuration/input,
  address/control/data stability, phase extension, simultaneous transactions,
  interrupts, and BR during waits pass trace and liveness tests.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989 system-interface chapter
- **Relevant tests:** `tests/test_dm_write_immediate_slice.py`,
  `formal/dm_write_immediate_slice.sby`, `tests/test_shifter_dm.py`,
  `sim/unit/tb_adsp2100_shifter_dm_slice.sv`, `formal/shifter_dm.sby`,
  `tests/test_data_bus.py`, `formal/dm_bus.sby`,
  `tests/test_dm_write_immediate_native.py`,
  `formal/dm_write_immediate_native.sby`,
  `tests/test_shifter_dm_native.py`, `formal/shifter_dm_native.sby`,
  `tests/test_compute_dm_native.py`, `formal/compute_dm_native.sby`
- **Implementation notes:** Type 2, Type 3, Type 4, and Type 12 implement the
  sourced logical DMACK rule:
  each low sample extends the transaction by a processor clock, bus outputs
  remain stable, state does not commit, and the first high sample commits all
  parallel actions. The Type 2 differential adds 50,035 clocks of raw
  immediate writes, both DAGs, and completion-only I updates. The native DM
  controller and attached Type 2 wrapper add 50,039 standalone and 50,027
  connected clocks proving the state-6 DMACK sample, complete-cycle extension,
  and state-7 completion. The Type 12 attachment adds 50,064 connected clocks
  proving read/write phase alignment and atomic parallel completion. The
  Type 4 attachment adds 50,082 clocks proving the same phase contract for
  memory-only and ALU/MAC actions without any wait-time architectural write.
  The Type 3 attachment adds 50,077 clocks proving absolute-address transfers,
  old general-register write data, and completion-only read destinations. PM
  concurrency,
  interrupt/BR/HALT latching, and electrical constraints remain.
- **Unresolved questions:** original ADSP-2100 wait pins versus programmed wait
  behavior.
- **Confidence:** CORROBORATED

## M26 — Differential testing

### VERIF-DIFF-001 — Model/RTL/MAME differential framework

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** MODEL-001, ISA-001; MAME path depends on REF-001
- **Acceptance criteria:** deterministic trace schema compares all requested
  state and transactions; seeded legal programs run model/RTL; isolated
  commit-pinned MAME adapter runs where practical; reducer preserves failures.
- **Source references:** MAME-ADSP2100-CORE, MAME-ADSP2100-OPS,
  MAME-ADSP2100-DASM, and per-instruction primary sources
- **Relevant tests:** `make differential`, `make fuzz`
- **Implementation notes:** deterministic independent-model/RTL vector
  comparison exists for the implemented compute, DAG, sequencer, register,
  status, and bounded instruction slices. Type 12 adds the first memory-bus
  transaction comparison, covering 50,069 seeded clocks with waits. Type 13
  adds 50,070 deterministic state/cache/bus clocks over fixed PM data cycles,
  hit completion, miss/forced-fetch recovery, PX packing, and DAG2 updates.
  Type 4 adds 50,072 deterministic logical-DM clocks over selected-bank
  ALU/MAC, old-value reads/writes, DAG postmodify, waits, and invalid state.
  Its independent native composition adds 50,082 clocks spanning state-8
  acceptance, native strobes, full-cycle waits, state-7 atomic completion,
  reset, and relinquishment.
  These are
  bounded state/action traces, not legal-program execution; the MAME adapter,
  unified architectural trace schema, and reducer remain absent. MAME is an
  implementation under test and cannot override primary evidence by itself.
- **Unresolved questions:** minimal licensed MAME build and cycle limitations.
- **Confidence:** UNKNOWN

## M27 — Formal verification

### FORMAL-001 — Bounded and invariant proof suite

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** applicable RTL blocks
- **Acceptance criteria:** requested control/bus/DAG/stack/interrupt/arithmetic
  properties run in CI with documented assumptions, engines, bounds, covers,
  and uncovered state.
- **Source references:** architecture specifications for each property
- **Relevant tests:** `make formal`
- **Implementation notes:** depth-one condition, ALU, MAC, shifter, DAG, and
  sequencer-flow combinational harnesses now exist; never call a bounded
  result a complete proof. Sixty harnesses now pass strict assertion
  syntax lint, including Type 2 action decode and waited logical execution,
  exact Type 6 and Type 7 immediate loads, bounded Type 15 immediate-shift,
  bounded Type 16 conditional-shift, bounded Type 14 shifter-plus-DREG move,
  bounded Type 12 shifter-plus-DM decode, wait stability, and atomic completion,
  bounded Type 13 shifter-plus-PM decode, fixed-cycle commit, and one-cycle
  cache-miss recovery plus connected cache selection/fill ownership,
  source-bounded instruction-cache count, reset, hold, restart, and oldest-
  replacement invariants,
  bounded Type 4 ALU/MAC-plus-DM wait stability and atomic completion plus
  native issue/completion attachment and stalled-descriptor stability,
  exhaustive Type 5 ALU/MAC-plus-PM action selection and collision exclusion,
  logical fixed-cycle execution/cache recovery/native state-8 issue and
  state-7 completion,
  bounded Type 8 ALU/MAC-plus-DREG execution,
  class-complete bounded Type 9 conditional ALU/MAC execution,
  bounded Type 10 direct JUMP/CALL decode and state execution,
  bounded Type 11 DO UNTIL decode and state execution,
  bounded Type 19 indirect JUMP/CALL decode and state execution,
  class-complete bounded Type 20 conditional RTS/RTI state execution,
  phase-aware Type 22 conditional TRAP and HALT-handoff execution,
  class-complete Type 23 DIVQ decode and atomic AF/AY0/AQ state execution,
  bounded Type 24 DIVS decode and atomic AF/AY0/AQ state execution,
  Type 17 action decode/state execution, Type 21 decode, and bounded Type 21
  state execution.
  Proof execution awaits an installed
  SymbiYosys/Yosys/SMT toolchain.
- **Unresolved questions:** solver/tool version and tractable whole-core bounds.
- **Confidence:** UNKNOWN

## M28 — FPGA synthesis and timing

### SYNTH-001 — Portable and Cyclone V synthesis qualification

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** first synthesizable RTL block
- **Acceptance criteria:** Yosys and Quartus builds have zero latches/accidental
  clocks, constrained interfaces, recorded warnings/utilization/Fmax/critical
  paths, optional no-DSP comparison, and passing behavioral equivalence tests.
- **Source references:** Intel Cyclone V/TimeQuest documentation; RTL specs
- **Relevant tests:** `make synth-yosys`, `make synth-quartus`
- **Implementation notes:** constrained Quartus Cyclone V smoke projects cover
  the condition, ALU, MAC, shifter, DAG, sequencer-flow, and bounded Type
  2/10/11/19/20, Type 18, Type 21, Type 25, and Type 26 execution blocks. The Type 18 slice fits in
  46 ALMs and four registers with positive multicorner setup/hold slack and
  zero unconstrained paths. The Type 21 slice fits in 526 ALMs with exactly
  360 architectural DAG data/valid registers, no RAM/DSPs, positive
  multicorner setup/hold slack, and zero unconstrained paths. The Type 17
  decoder fits in 42 ALMs and 24 combinational ALUTs with no
  registers/RAM/DSPs, positive multicorner setup/hold slack, and zero
  unconstrained paths. The bounded Type 17 state slice fits in 816 ALMs and
  906 registers with no RAM/DSPs, +6.401 ns worst setup, +0.151 ns worst hold,
  and zero unconstrained clocks, ports, or paths. The bounded Type 6 slice
  fits in 302 ALMs and 484 registers with no RAM/DSPs, +8.167 ns worst setup,
  +0.133 ns worst hold, and zero unconstrained clocks, ports, or paths.
  The bounded Type 7 slice fits in 572 ALMs and 886 fitted registers with no
  RAM/DSPs against 25 ns. Worst multicorner setup is +13.448 ns, worst hold is
  +0.185 ns, worst slow-100C Fmax is 86.57 MHz, and no clocks, ports, or paths
  are unconstrained. This is a bounded register-state fit, not whole-core or
  MiSTer timing closure.
  The bounded Type 15 slice fits in 774 ALMs and 501 fitted registers with no
  RAM/DSPs, +3.728 ns worst setup, +0.057 ns worst hold, and zero unconstrained
  clocks, ports, or paths.
  The bounded Type 16 slice fits in 840 ALMs and 520 fitted registers with no
  RAM/DSPs, +2.304 ns worst setup, +0.173 ns worst hold, and zero unconstrained
  clocks, ports, or paths.
  The bounded Type 14 slice fits in 1,032 ALMs and 565 fitted registers with no
  RAM/DSPs, +3.041 ns worst setup, +0.171 ns worst hold, and zero unconstrained
  clocks, ports, or paths.
  The bounded Type 4 logical-DM slice fits in 1,677 ALMs and 1,258 fitted
  registers with one DSP and no RAM at 25 ns. Standard Fit closes the initial
  Auto Fit hold failure with +3.644 ns worst setup, +0.104 ns worst
  multicorner hold, 46.83 MHz worst slow-corner Fmax, and zero unconstrained
  clocks, ports, or paths. The bounded Type 4/native-DM attachment fits in
  1,693 ALMs and 1,226 registers with one DSP and no RAM at 25 ns; worst setup
  is +1.121 ns, worst hold is +0.167 ns, worst slow-corner Fmax is 41.88 MHz,
  and no clock, port, or path is unconstrained. Whole-core timing remains open.
  The combinational Type 5 action decoder fits in 51 ALMs with no registers,
  RAM, or DSP blocks at 20 ns. Worst multicorner setup is +12.323 ns, worst
  hold is +4.281 ns, worst slow-corner Fmax is 130.26 MHz, and no path is
  unconstrained. The bounded Type 5 logical execution, cache composition, and
  native-PM attachment also pass fully constrained 25 ns Standard Fits. They
  use respectively 1,681/1,912/1,894 ALMs, 1,262/1,672/1,746 registers, one
  DSP and no RAM; their worst multicorner setup slacks are +0.811/+4.571/
  +4.233 ns, worst hold slacks +0.166/+0.164/+0.164 ns, and worst slow-corner
  Fmax values 41.34/48.95/48.15 MHz. These are bounded-client, not whole-core,
  results.
  The bounded Type 2 DM-write slice fits in 581 ALMs and 430 fitted registers
  with no RAM/DSP blocks against a 20 ns standalone constraint. Worst setup is
  +3.590 ns, worst multicorner hold is +0.165 ns, worst slow-corner Fmax is
  60.94 MHz, and no clocks, ports, or paths are unconstrained. Constant
  read/PM outputs and asynchronous-read DAG arrays are expected for this
  write-only bounded smoke project.
  The bounded Type 12 DM transaction slice fits in 1,704 ALMs and 1,091 fitted
  registers with no RAM/DSPs, +1.377 ns worst setup, +0.166 ns worst
  multicorner hold slack at 21 ns, 50.96 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths. The unassigned standalone clock pin
  warning is expected for this virtual-pin smoke project.
  The bounded Type 12/native-DM attachment fits in 1,739 ALMs and 1,139 fitted
  registers with no RAM/DSPs at 20 ns. Worst multicorner setup is +1.262 ns,
  worst hold is +0.167 ns, worst slow-corner Fmax is 53.37 MHz, and no clocks,
  ports, or paths are unconstrained.
  The bounded Type 13 PM transaction/cache-recovery slice fits in 1,640 ALMs
  and 1,002 fitted registers with no RAM/DSP blocks, +1.172 ns worst setup,
  +0.168 ns worst multicorner hold slack at 21 ns, 50.43 MHz worst slow-corner
  Fmax, and zero unconstrained clocks, ports, or paths. The standalone virtual
  clock-pin warning and constant DM-access output are expected.
  The cache-integrated Type 13 boundary fits in 1,937 ALMs and 1,446 fitted
  registers with no RAM/DSP blocks at 20 ns. Worst multicorner setup is
  +2.615 ns, worst hold is +0.166 ns, worst slow-corner Fmax is 57.52 MHz,
  and no clocks, ports, or paths are unconstrained. Quartus retains the
  asynchronous-read cache and DAG arrays in logic/registers.
  The standalone instruction cache fits in 310 ALMs and 429 fitted registers
  with no RAM/DSP blocks, +7.071 ns worst setup, +0.163 ns worst multicorner
  hold slack at 20 ns, 77.35 MHz worst slow-corner Fmax, and zero unconstrained
  clocks, ports, or paths. Quartus reports the asynchronous-read 16-by-24 array
  as uninferred RAM; its 384 data bits plus monitor/valid state are registers.
  The bounded Type 8 slice fits in 983 ALMs and 693 fitted registers with one
  DSP and no RAM against a 22 ns standalone-slice constraint. Worst setup is
  +1.131 ns, worst hold is +0.177 ns, worst slow-corner Fmax is 47.92 MHz, and
  all clocks, ports, and paths are constrained. The same monolithic slice
  missed a 20 ns constraint by 1.721 ns; this is not whole-core or MiSTer
  timing closure and phase scheduling remains an integration task.
  The bounded Type 9 slice fits in 970 ALMs and 697 fitted registers with one
  DSP and no RAM against a 22 ns standalone constraint. Worst setup is +1.140
  ns, worst hold is +0.165 ns, worst slow-corner Fmax is 47.94 MHz, and no
  clocks, ports, or paths are unconstrained. Its initial 20 ns fit missed
  setup by 1.735 ns; this likewise is not whole-core or MiSTer closure.
  The bounded Type 10 direct-transfer slice fits in 284 ALMs and 334 fitted
  registers with no RAM or DSP blocks against a 20 ns standalone constraint.
  Worst setup is +8.138 ns, worst multicorner hold is +0.167 ns, worst
  slow-corner Fmax is 84.3 MHz, and no clocks, ports, or paths are
  unconstrained. This is not whole-core or MiSTer timing closure.
  The bounded Type 11 setup slice fits in 308 ALMs and 402 fitted registers
  with no RAM or DSP blocks against a 20 ns standalone constraint. Worst
  setup is +7.263 ns, worst multicorner hold is +0.074 ns, worst slow-corner
  Fmax is 78.51 MHz, and no clocks, ports, or paths are unconstrained.
  The bounded Type 19 indirect-transfer slice fits in 353 ALMs and 400 fitted
  registers with no RAM or DSP blocks against a 20 ns standalone constraint.
  Worst setup is +7.520 ns, worst multicorner hold is +0.045 ns, worst
  slow-corner Fmax is 80.93 MHz, and no clocks, ports, or paths are
  unconstrained.
  The bounded Type 20 return slice fits in 318 ALMs and 417 fitted registers
  with no RAM or DSP blocks against a 20 ns standalone constraint. Worst
  setup is +7.725 ns, worst multicorner hold is +0.136 ns, worst slow-corner
  Fmax is 81.47 MHz, and no clocks, ports, or paths are unconstrained.
  The bounded phase-aware Type 22 TRAP slice fits in 116 ALMs and 67 fitted
  registers (53 design registers plus fourteen routing duplicates), with no
  RAM or DSP blocks against a 20 ns standalone constraint. Worst setup is
  +7.592 ns, worst multicorner hold is +0.069 ns, worst slow-corner Fmax is
  80.59 MHz, and no clocks, ports, or paths are unconstrained.
  The bounded Type 23 DIVQ slice fits in 316 ALMs and 341 fitted registers
  (338 design registers plus three routing duplicates), with no RAM or DSP
  blocks against a 20 ns standalone constraint. Worst setup is +7.009 ns,
  worst multicorner hold is +0.164 ns, worst slow-100C Fmax is 77.71 MHz,
  and no clocks, ports, or paths are unconstrained.
  The bounded Type 24 DIVS slice fits in 351 ALMs and 381 fitted registers
  (372 design registers plus nine routing duplicates), with no RAM or DSP
  blocks against a 20 ns standalone constraint. Worst setup is +8.448 ns,
  worst multicorner hold is +0.168 ns, worst slow-corner Fmax is 86.81 MHz,
  and no clocks, ports, or paths are unconstrained.
  Whole-core clocks,
  utilization, and timing remain
  unavailable; Yosys is not installed.
- **Unresolved questions:** exact DE10-Nano device support in installed edition.
- **Confidence:** UNKNOWN

## M29 — MiSTer-compatible wrapper

### INTEG-MISTER-001 — MiSTer clock-enable/memory wrapper

- **Status:** NOT STARTED
- **Priority:** P2
- **Dependencies:** generic core timing and interfaces, SYNTH-001
- **Acceptance criteria:** single system clock, sourced cycle enables, separate
  synchronous PM/DM, reset/halt/BR/BG/IRQs, trace/debug hooks, and SDRAM
  adaptation as needed pass wrapper tests and Quartus timing.
- **Source references:** MiSTer framework documentation; generic interface spec
- **Relevant tests:** `make synth-quartus`, wrapper regressions
- **Implementation notes:** keep Atari memory map outside the generic core.
- **Unresolved questions:** host-core clock and SDRAM schedule.
- **Confidence:** UNKNOWN

## M30 — Hard Drivin' ADSP-board research

### HD-RESEARCH-001 — Reconstruct ADSP and ADSP II boards

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** REF-001, DEV-001
- **Acceptance criteria:** requested board variants, fitted part/package/clock,
  memory organization, host arbitration, reset/halt/IRQs, SIM/SOM, banking,
  PAL logic, and discrepancies are cited per schematic sheet/source line.
- **Source references:** ATARI-ADSP-SCHEM, ATARI-MARGOLIN,
  ATARI-HD-SERVICE, MAME-HARDDRIV, MAME-HARDDRIV-MACHINE
- **Relevant tests:** `tests/test_harddriv_metadata.py`
- **Implementation notes:** board schematics take precedence over MAME handler
  abstractions; engineer commentary establishes provenance/context.
- **Unresolved questions:** missing PAL/GAL equations and physical captures.
- **Confidence:** INFERRED

## M31 — Hard Drivin' synthetic integration tests

### HD-SYNTH-001 — Noncopyrighted board-level programs

- **Status:** NOT STARTED
- **Priority:** P2
- **Dependencies:** HD-RESEARCH-001, TOOL-001, generic core and board wrapper
- **Acceptance criteria:** synthetic tests cover host PM/DM loading, reset/halt,
  BR/BG, execution, SIM/SOM, banking, both signaling directions, X flag, and
  geometry command/result behavior with bus traces.
- **Source references:** HD-RESEARCH-001 outputs
- **Relevant tests:** `make harddriv-tests`
- **Implementation notes:** programs and fixtures must be project-authored and
  redistributable.
- **Unresolved questions:** authoritative X flag and bank-switch timing.
- **Confidence:** UNKNOWN

## M32 — Hard Drivin' ROM-based qualification

### HD-ROM-001 — Authorized local-ROM qualification

- **Status:** BLOCKED
- **Priority:** P2
- **Dependencies:** HD-SYNTH-001, VERIF-DIFF-001, local authorized ROMs
- **Acceptance criteria:** hash-verified user-supplied ROMs load; reset/initial
  trace, self-test, command wait loop, trigger, known geometry result, IRQ, and
  frame-level processing compare against MAME and available hardware captures.
- **Source references:** MAME-HARDDRIV, MAME-HARDDRIV-MACHINE,
  ATARI-ADSP-SCHEM, ATARI-HD-SERVICE, user-local ROM hash metadata
- **Relevant tests:** `make harddriv-tests` with local ROM configuration
- **Implementation notes:** never distribute ROM contents or derived large
  extracts.
- **Unresolved questions:** authorized ROM availability and physical golden
  captures.
- **Confidence:** UNKNOWN

## M33 — Release qualification

### RELEASE-001 — Architecture, verification, synthesis, and license audit

- **Status:** NOT STARTED
- **Priority:** P3
- **Dependencies:** FND-001 through HD-SYNTH-001; HD-ROM-001 where lawful
  inputs are available
- **Acceptance criteria:** every instruction-complete, cycle-accurate,
  Hard-Drivin'-ready, and release-ready criterion in the project requirements
  has linked objective evidence; all regressions/proofs/syntheses pass; no
  hidden discrepancies, license issues, or unconstrained paths remain.
- **Source references:** complete manifest and architecture corpus
- **Relevant tests:** `make test`, `make formal`, `make synth-yosys`,
  `make synth-quartus`, `make harddriv-tests`
- **Implementation notes:** release audit is independent of implementation
  existence and includes provenance plus copyright checks.
- **Unresolved questions:** remain explicit until all preceding task questions
  are resolved or bounded by documented hardware evidence.
- **Confidence:** UNKNOWN

## Next task selection

The highest-priority unblocked implementation work is extending the bounded
steady-state NOP/Type 6/Type 7/Type 18 owner with additional source-closed,
non-memory linear instruction classes, followed by replacing its deterministic
preload with the sourced reset-release/first-fetch sequence and a documented
next-PC/PM-owner arbiter. Type 7 immediate non-data-register execution and
Type 3 state/native-DM execution are bounded and verified. The Type 1
dual-memory action graph is complete,
but its state/native attachment remains withheld under OQ-023 until the PM
pin behavior during a DMACK extension can be sourced rather than invented.
`REF-001` retains acquisition of the exact original Cross-Software/opcode
reference. Field placement and bounded Type 4/Type 5 execution/native
attachments are closed, while whole-core integration and the remaining
multifunction classes are not.
`TIME-001` must be completed before architectural execution RTL is permitted
to claim cycle accuracy.
