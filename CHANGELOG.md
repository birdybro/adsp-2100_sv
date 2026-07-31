# Changelog

All notable engineering changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
semantic versioning after its first release.

## [Unreleased]

### Added

- Repository governance, contribution policy, required directory layout, and
  explicit evidence-based completion rules.
- Initial reference provenance schema and safe local-cache workflow.
- Initial architecture, timing, integration, decision, and research framework.
- Foundation automation for manifest validation, repository checks, model
  tests, lint entry points, and optional-tool reporting.
- Nineteen-record reference manifest with fourteen hash-verified local sources,
  including original ADI manuals/data book, Atari schematics, and a pinned
  MAME ADSP/Hard Drivin' source set.
- A cache-only copy and applicability record for the 1989 First Edition
  ADSP-2101 Cross-Software programming reference. It is retained as
  contemporary later-device/toolchain comparison, not original ISA proof.
- Isolated sparse MAME checkout workflow pinned to commit
  `030fefcbd14e47c01ec9d67655be90f64a1dc8ab`.
- Machine-readable 30-class original opcode inventory with a complete-field,
  hand-verified all-zero NOP fixture and fail-closed schema validator.
- Primary-transcribed masks for all 30 original encoding classes, explicit
  accounting for 1,304,038 unshown-reserved words, generated synthesizable
  class decode, and a generated opcode table.
- A complete Appendix A bit-placement database for all 30 formats: 106 named
  fields exactly cover 393 variable positions. Generated documentation and
  SystemVerilog masks derive from it, while independent fixtures retain review
  separation.
- A portable instruction-class decoder RTL boundary, an independent bounded
  formal harness, exhaustive 24-bit Verilator comparison, and a constrained
  Cyclone V synthesis project.
- A primary-backed Type 26 stack-control semantics database, independent
  executable action decoder, hand-reviewed fixtures, portable RTL decoder,
  bounded formal harness, exhaustive 24-bit fail-closed simulation, and
  constrained Cyclone V synthesis project. All 32 encodings and both SPP
  no-change aliases are retained without inventing OQ-013 underflow effects.
- Original RGP/REG general-MOVE table accounting for 48 register encodings,
  reserved holes, storage widths, and verified narrow-register extension
  behavior.
- Independent Python exact-width state, authentic reset-unknown
  classification, deterministic random-state/replay foundation, PM fetch
  transactions, program/data image loading, reserved-code rejection, and the
  verified NOP execution slice.
- Partial database-driven assembler/disassembler that round-trips the
  independent NOP fixture and fails closed for unimplemented/reserved words.
- Shared SystemVerilog width/phase/type package and GitHub Actions foundation
  regression.
- Complete primary-backed 4-bit IF and inverse-sense DO UNTIL condition
  databases, an independent model evaluator, synthesizable combinational
  condition logic, and exhaustive 2,048-vector RTL comparison.
- A constrained Quartus Cyclone V smoke project for the first architectural
  condition-logic block.
- Primary-transcribed exhaustive tables for all 19 remaining finite Appendix A
  abbreviations, including AMF, DREG, DAG selectors, stack controls, SF, and
  X/Y/Z operands.
- Independent model and portable RTL for all 16 standard ALU AMF functions,
  including carry/borrow, overflow, sticky AV, ABS sign, and AR saturation.
- Independent model and portable RTL for all 15 original fractional MAC AMF
  functions, including mixed signedness, 40-bit accumulation, unbiased
  rounding, MF extraction, MV, and one-shot MR saturation.
- Independent model and portable RTL for all 16 original shifter SF functions,
  including full-range HI/LO placement, PASS/OR, logical/arithmetic shifts,
  normalization, HI/HIX/LO exponent detection, EXPADJ, and explicit write
  enables.
- Independent DAG arithmetic model and portable RTL for old-I addressing,
  signed post-modification, linear and circular wrap, original-device base
  alignment, DAG1 bit reversal, and DAG2's non-reversed output.
- Independent model and portable RTL for instruction-boundary sequential,
  jump, call, return, loop-back, and loop-exit arbitration, including explicit
  control-transfer precedence at a loop end.
- Generated SystemVerilog constants for all 16 original computational DREG
  codes plus independent model and portable stateful RTL for both complete
  computational banks. The storage preserves exact SE/MR2/SB widths,
  cycle-start reads, cycle-end DREG and ALU/MAC/shifter writeback, atomic MR,
  MF middle-word extraction, MR1-to-MR2 sign extension, and fail-closed
  write-collision suppression.
- Bounded combinational formal harnesses and SymbiYosys recipes for condition,
  ALU, MAC, shifter, DAG, and sequencer-flow invariants, with assertion lint
  available without SymbiYosys.
- A stateful register-bank formal harness, 58,307-cycle DREG regression,
  50,120-cycle full-bank/writeback regression, and a constrained Cyclone V
  synthesis project.
- Machine-readable original ASTAT/MSTAT/ICNTL/IMASK fields, SSTAT field map,
  reset metadata, and interrupt-entry masks; an independent status/control
  model; and portable stateful RTL for direct writes, all four MODE CONTROL
  fields, ALU/divide/MAC/shifter status updates, exact cycle-end visibility,
  authentic ASTAT/ICNTL reset unknowns, interrupt snapshots, nested masking,
  RTI-style restoration, aborted-instruction suppression, and fail-closed
  collision handling.
- A status/control formal harness, 50,287-cycle model-versus-RTL regression,
  and a constrained Cyclone V synthesis project.
- Primary-backed four-by-sixteen status-stack metadata, an independent
  saturating LIFO model, and portable RTL with both Spp no-change codes,
  accepted push/pop state, newest-item overflow loss, sticky overflow,
  empty/overflow SSTAT sources, explicit empty-pop invalidation, and reset
  behavior.
- Eight directed/model status-stack tests, a 50,037-cycle model-versus-RTL
  regression, a bounded formal harness, and a constrained Cyclone V synthesis
  project.
- An independent cycle-boundary integration model and portable
  `adsp2100_mode_slice` RTL connecting the original four MSTAT bits to
  computational-bank selection, DAG1 bit reversal, sticky ALU overflow, and
  AR saturation without adding instruction-decode claims.
- Five directed MSTAT-consumer tests, a deterministic 50,112-cycle
  model-versus-RTL regression, a bounded composition formal harness, and a
  constrained Cyclone V integration synthesis project.
- Primary-backed exact 16-by-14 PC, four-by-14 count, and four-by-18 loop
  stack metadata, an independent saturating LIFO model, and portable stateful
  RTL with newest-item overflow loss, sticky overflow, explicit empty-pop
  invalidation, and SSTAT sources in bits 0–3 and 6–7.
- Ten directed/model sequencer-stack tests, a deterministic 50,062-cycle
  model-versus-RTL regression, a bounded state-transition formal harness, and
  a constrained Cyclone V synthesis project.
- Machine-readable original CNTR transition metadata, an independent
  reset-valid counter model, and portable stateful RTL for pre-decrement
  CE/NOT CE, cycle-end post-decrement, valid-load count-stack pushes, true-CE
  pop/restore or empty invalidation, valid manual-pop restore, and fail-closed
  unresolved action collisions.
- Twelve directed/model CNTR tests, a deterministic 50,022-cycle
  model-versus-RTL regression, a bounded formal harness, and a constrained
  Cyclone V synthesis project.
- Machine-readable sequencer-integration boundaries, an independent composed
  integration model, and portable RTL connecting IF/DO conditions, explicit
  flow, DO setup, CNTR, and PC/count/loop stack storage without adding opcode
  decode or PC-register claims.
- Fourteen directed/random sequencer-integration tests, a deterministic
  50,011-cycle model-versus-RTL regression, a bounded formal harness, and a
  constrained Cyclone V synthesis project.
- Machine-readable Type 26 execution-boundary metadata, an independent
  composed state model, and portable RTL connecting all 32 stack-control words
  to PC/count/loop/status storage, CNTR restore, live status restore, and all
  eight SSTAT stack fields without inventing interrupt arbitration.
- Nine directed/schema/random Type 26 execution tests, a deterministic
  50,015-cycle model-versus-RTL regression, a bounded formal harness, and a
  constrained Cyclone V synthesis project.

### Changed

- Expanded the initial README to state the exact ADSP-2100 scope and current
  non-complete status.
- Identified the contemporary original ADSP-2100 data sheet within the 1987
  ADI data book at printed pages 2-15 onward.

### Fixed

- Made clean-checkout CI independent of the intentionally untracked reference
  cache while retaining strict local hash checks whenever the cache is present.
- Excluded ignored Quartus database products from source-text hygiene checks so
  synthesis followed by regression is deterministic.
- Renamed the condition boundary's counter input from the misleading
  `counter_nonzero` to `not_counter_expired`: original CE asserts at a valid
  count of one, not at zero. The exhaustive Boolean truth table is unchanged.
- Corrected the stack-control Type 26 mask from `0xfffff0` to `0xffffe0`.
  The original diagram identifies bit 4 as PC-stack pop (`PP`); the prior local
  transcription accidentally excluded sixteen documented class words.

### Verified

- Existing repository state and installed-tool baseline recorded on
  2026-07-30: Git/Python/Make/Verilator/Quartus available; pytest, Icarus,
  Yosys, SymbiYosys, and svlint unavailable.
- `make test` passes 139 Python checks, ISA/register/condition/field validators,
  thirteen cached reference hash checks, generated-file checks, strict
  Verilator 5.048 lint, 2,048 exhaustive condition-logic vectors, and 51,472
  ALU, 21,760 MAC, 644,368 shifter, 204,864 DAG, 636,512 sequencer-flow,
  58,307 stateful DREG model-versus-RTL cycles, 50,120 complete-bank
  writeback cycles, 50,287 status/control state-transition cycles, and 50,037
  status-stack state-transition cycles.
- The expanded `make test` passes 166 Python checks and adds 50,112 stateful
  MSTAT-consumer cycles. Both banks are initialized distinctly, all 16 MSTAT
  values are observed, and ordinary-cycle old-mode/new-mode ordering is
  checked across register, DAG1, and ALU consumers. It also adds 50,062
  PC/count/loop stack-storage cycles covering exact LIFO depths, saturation,
  independent simultaneous actions, reset, and empty-pop invalidation, plus
  50,022 CNTR cycles covering validity, N-pass CE behavior, decrement, nested
  restore, and empty invalidation.
- The further expanded `make test` passes 180 Python checks and adds 50,011
  bounded sequencer-integration cycles covering DO setup, stored inverse-sense
  termination, exact-N and nested CE loops, JUMP CE decrement/pop, RETURN CE
  non-decrement, explicit-transfer precedence, and atomic fail-closed
  collision handling.
- The instruction-format regression independently checks all 30 layouts,
  validates all 106 fields and 393 variable positions, and exhaustively
  compares the synthesizable class decoder across all 16,777,216 opcodes:
  15,473,178 shown-class words and 1,304,038 reserved-unshown words.
- The latest `make test` passes 187 Python checks, 14 cached-reference hashes,
  all generated-file checks, strict RTL lint, the exhaustive class decoder,
  and every existing compute, DAG, sequencer, register, and status regression.
- The Type 26 focused regression adds six schema/model tests, checks all 32
  stack-control words, exhaustively proves that every other 24-bit word emits
  no stack action in RTL, and passes strict lint plus formal-harness lint.
- The expanded `make test` now passes 193 Python checks, 14 cached-reference
  hashes, all generated-file checks, both exhaustive 24-bit decoders, and
  every existing compute, DAG, sequencer, register, and status regression.
- Quartus full compilation passes for the Type 26 action decoder: 25 ALMs,
  12 combinational ALUTs, no registers/RAM/DSPs, +17.244 ns worst setup,
  +0.287 ns worst hold slack, and zero unconstrained paths against the 20 ns
  virtual I/O constraint.
- The stateful Type 26 regression verifies pre-instruction status capture,
  simultaneous status/count/loop/PC pops from cycle-start tops, valid/empty/
  full-stack behavior, both no-effect aliases, authentic CNTR reset
  invalidation, invalid-opcode suppression, SSTAT composition, and atomic
  OQ-018 conflict rejection across 50,015 cycles.
- Quartus full compilation passes for the stateful Type 26 integration slice:
  351 ALMs, 260 combinational logic ALUTs, 465 design registers plus 12 fitter
  duplicates, no RAM/DSPs, +10.550 ns worst setup, +0.165 ns worst hold slack,
  and zero unconstrained paths against the 20 ns constraint.
- Quartus full compilation passes for the constrained class-decoder block: 55
  ALMs, 63 combinational ALUTs, no registers/RAM/DSPs, +14.723 ns worst setup,
  +0.407 ns worst hold slack, and zero unconstrained clocks, ports, or paths.
- Quartus 17.0.2 full compilation for Cyclone V `5CSEBA6U23I7` passes for the
  constrained condition block: 10 ALMs, no registers/RAM/DSPs, positive
  setup/hold slack, and zero unconstrained ports or paths.
- Quartus full compilation also passes for the constrained ALU block: 161
  ALMs, 196 combinational ALUTs, no registers/RAM/DSPs, positive setup/hold
  slack, and zero unconstrained ports or paths.
- Quartus full compilation passes for the constrained MAC block: 229 ALMs, 229
  combinational ALUTs, one inferred DSP block, no registers/RAM, positive
  setup/hold slack, and zero unconstrained ports or paths.
- Quartus full compilation passes for the constrained shifter block: 374 ALMs,
  580 combinational ALUTs, no registers/RAM/DSPs, positive setup/hold slack,
  and zero unconstrained ports or paths.
- Quartus full compilation passes for the constrained DAG block: 172 ALMs, 305
  combinational ALUTs, no registers/RAM/DSPs, positive setup/hold slack, and
  zero unconstrained ports or paths.
- Quartus full compilation passes for the constrained sequencer-flow block: 74
  ALMs, 44 combinational ALUTs, no registers/RAM/DSPs, positive setup/hold
  slack, and zero unconstrained ports or paths.
- Quartus full compilation passes for the constrained register-file block:
  1,084 ALMs, exactly 554 architectural implementation registers plus 55
  fitter-created routing duplicates, no RAM/DSPs, +9.985 ns worst setup,
  +0.109 ns worst hold slack, and zero unconstrained ports or paths.
- Quartus full compilation passes for the constrained status/control block: 84
  ALMs, 41 combinational ALUTs, exactly 21 architectural registers, no
  RAM/DSPs, +11.811 ns worst setup, +0.169 ns worst hold slack, and zero
  unconstrained ports or paths. The
  isolated virtual inputs model same-clock register-launched controls with a
  documented 5 ns arrival assumption.
- Quartus full compilation passes for the constrained status-stack block: 53
  ALMs, 30 combinational logic ALUTs, exactly 68 design registers plus one
  fitter-created routing duplicate, no RAM/DSPs, +13.077 ns worst setup,
  +0.172 ns worst hold slack, and zero unconstrained ports or paths.
- Quartus full compilation passes for the constrained MSTAT integration slice:
  543 ALMs, 578 combinational ALUTs, 492 design implementation registers plus
  two fitter-created routing duplicates, no RAM/DSPs, +5.529 ns worst setup,
  +0.168 ns worst hold slack, and zero unconstrained ports or paths. The fit
  retains the 480 DREG storage bits and the observable ASTAT/MSTAT state; the
  bounded top intentionally does not expose all feedback/control registers.
- Quartus full compilation passes for the constrained PC/count/loop
  stack-storage block: 245 ALMs, 177 combinational logic ALUTs, exactly 366
  design implementation registers plus six fitter-created routing duplicates,
  no RAM/DSPs, +10.383 ns worst setup, +0.162 ns worst hold slack, and zero
  unconstrained ports or paths.
- Quartus full compilation passes for the constrained CNTR block: 72 ALMs, 49
  design combinational ALUTs, exactly 15 design registers plus seven
  fitter-created routing duplicates, no RAM/DSPs, +11.818 ns worst setup,
  +0.171 ns worst hold slack, and zero unconstrained ports or paths.
- Quartus full compilation passes for the bounded sequencer integration slice:
  388 ALMs, 383 fitted combinational ALUTs, exactly 381 design registers plus
  fourteen fitter-created routing duplicates, no RAM/DSPs, +6.776 ns worst
  setup, +0.166 ns worst hold slack, and zero unconstrained ports or paths.
- `make formal` passes strict assertion syntax lint for class decode,
  condition, ALU,
  MAC, shifter, DAG, sequencer-flow, register-file, status-register, and
  status-stack, sequencer-stack, CNTR, sequencer-integration, and
  MSTAT-integration harnesses; proof execution remains explicitly skipped
  without SymbiYosys.

### Documentation

- Established primary-source precedence, clean-room rules, clock/reset policy,
  signedness policy, verification expectations, and provenance requirements.
- Added first-pass original-device programmer, compute, DAG, sequencer,
  bus/timing, scope/matrix, and Hard Drivin' host/SIM/SOM/interrupt/PAL notes
  with explicit confidence boundaries.
- Closed the condition-field encoding and predicate table while leaving
  counter update, loop-stack, and instruction timing explicitly open.
- Recorded original-reserved versus later-family reuse and the Type 19 bit-5
  disagreement with MAME as explicit source conflicts.
- Recorded MAME's rounded accumulate/subtract midpoint-test divergence and
  retained the primary manual's complete-result rounding rule.
- Recorded MAME's MF-destination MV omission and retained the original
  manual's rule that every non-saturation MAC operation updates MV.
- Closed original shifter array fill, NORM AC extension, exponent range, and
  SE/SB/SS update semantics from the original compute chapter and SF table.
- Recorded the unresolved NORM `SE=0x80` negation-width edge as OQ-011; the
  provisional behavior agrees with pinned MAME and is outside generated
  exponent values.
- Recorded and implemented the original ADSP-2100 power-of-two circular-buffer
  alignment rule, explicitly distinguishing it from all later ADSP-21xx parts
  and pinned MAME (SC-010).
- Recorded the original manual's modify-equals-length allowance against the
  later family's strict inequality (SC-011).
- Recorded MAME's loop-before-instruction ordering against the original
  explicit-control-transfer precedence rule (SC-012).
- Closed the computational-bank membership and DREG access/storage slice,
  preserving undocumented reset state and recording illegal write collisions
  and interrupt-adjacent bank-switch visibility as OQ-014/OQ-015.
- Extended that slice through AF/MF/SB and unit-specific ALU/MAC/shifter
  writeback, while keeping full instruction legality, MSTAT timing, status
  writeback, and interrupt interaction explicitly incomplete.
- Closed the original ASTAT and MSTAT field maps, automatic flag-update
  sources, MODE CONTROL code effects, cycle-end flag latency, MSTAT reset
  clear, and ASTAT reset-unknown classification from the 1989 manual. Narrow
  DMD read extension and competing-write behavior are recorded as OQ-016 and
  OQ-017 rather than inferred.
- Closed the original SSTAT field map and ICNTL/IMASK storage, reset, and
  interrupt-entry mask rules. Implemented pre-entry ASTAT/MSTAT/IMASK
  snapshots and restore at a sequencer-facing boundary while leaving physical
  status-stack/SSTAT behavior and interrupt recognition explicitly incomplete.
- Resolved OQ-004 from the original 1987 ADSP-2100 data-book diagram: the
  status stack has four 16-bit entries. Combined with the original 1989
  pointer/overflow rules, this closes accepted LIFO, saturation, oldest-data
  retention, sticky overflow, and SSTAT bits 4/5 while retaining empty-pop
  effects as OQ-013.
- Connected all four original MSTAT consumers at an ordinary
  cycle-start/cycle-end boundary. Direct MOVE and MODE CONTROL changes are
  visible to bank selection, DAG1, sticky AV, and saturation on the following
  cycle; interrupt-adjacent visibility remains explicitly open as OQ-015.
- Closed PC/count/loop stack storage dimensions and normal accepted-operation
  behavior from the original program-sequencer chapter, and applied the
  original global saturation/newest-loss/sticky-overflow rule to all three.
  All SSTAT storage sources now exist, while SSTAT composition, decode,
  interrupt/status-stack connectivity, and empty-pop effects remain explicit
  gaps.
- Closed CNTR's separate validity state, cycle-start CE-at-one predicate,
  cycle-end post-decrement, valid-load push rule, and true-CE
  restore-or-invalidate behavior from the original program-control chapter.
  Conditional CALL remains OQ-012, empty manual pop remains OQ-013, and the
  standalone controller remains independently testable.
- Connected condition evaluation, DO setup/termination, explicit
  jump/call/return flow, CNTR, and PC/count/loop storage at a bounded
  instruction boundary. Conditional CALL CE remains rejected as OQ-012;
  empty-pop effects remain OQ-013; and newly recorded OQ-018 covers competing
  automatic/manual sequencer actions and DO setup at an outer loop end.
- Closed original Type 26 action selection from the original combined syntax
  and Appendix A field tables: status push/pop and count/PC/loop pops are
  independently selectable in one cycle. A bounded execution slice now applies
  these actions to all four architectural stack classes, CNTR, live status,
  and SSTAT with cycle-start reads and cycle-end commits. Automatic/interrupt
  arbitration and empty-stack effects remain explicitly outside this boundary.

### Known Issues

- The exact original ADSP-2100 Cross-Software manual, evaluation-board manual,
  independent data-sheet revisions, and errata remain unavailable. Appendix A
  bit placement is complete, but semantic extraction remains incomplete.
- No instruction-completeness, external-cycle, bus, interrupt, or Hard Drivin'
  compatibility claim is complete. Type 26 action decode and bounded stateful
  execution are verified, but fetch/PC, automatic-flow, interrupt/RTI, and bus
  integration are not connected.
- Register/status instruction-decode connectivity, ICNTL consumer wiring,
  PC-register/decode-level sequencer connectivity, status-stack interrupt/RTI
  arbitration, architectural SSTAT reads, narrow status reads, and
  interrupt recognition/cycle integration are not implemented. Sequencer and
  MSTAT consumer wiring exists only in bounded integration slices, not a
  whole instruction execution core.
- Open-source synthesis and formal tools are not installed in this environment.

[Unreleased]: https://github.com/birdybro/adsp-2100_sv/compare/HEAD...HEAD
