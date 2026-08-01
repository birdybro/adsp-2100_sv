# Changelog

All notable engineering changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
semantic versioning after its first release.

## [Unreleased]

### Added

- A bounded Type 5/cache architectural client attached to the single shared
  PM owner and normal BR/BG composition. Captured PM-data and recovery-fetch
  descriptors survive fail-closed collision or issue inhibition and retry at
  a later enabled state-8 boundary; only routed Type 5 completion advances
  ALU/MAC/PM/PX/DAG2 state, and completed ordinary fetches fill the same
  instruction cache. Six directed tests and 50,063 deterministic model/RTL
  clocks cover 2,742 accepted Type 5 descriptors, 713 retained retries,
  1,371 one-time data completions, 17,072 recovery observations, 290 ordinary-
  fetch fills, 322 raw Type 13 completions, 78 BR recognitions/resumes, and
  2,727 masked grant clocks. A machine-readable boundary, formal harness,
  Yosys recipe, and fully constrained Cyclone V project bind the result.
  Quartus uses 1,923 ALMs, 1,756 fitted registers, one DSP and no RAM,
  +3.950 ns worst setup, +0.161 ns worst hold, 47.51 MHz worst slow-corner
  Fmax, and no unconstrained paths at 25 ns. Ordinary fetch and Type 13 remain
  raw descriptor inputs; unified Type 5/Type 13/fetch ownership and complete
  HALT/TRAP/interrupt/loop/DM priority remain open.

- A bounded Type 13/cache architectural client attached to the single shared
  PM owner and normal BR/BG composition. The client presents captured PM-data
  or recovery-fetch descriptors only at enabled state-8 boundaries, retains
  rejected descriptors for retry without replaying the architectural data
  action, consumes only Type 13 completion events, and receives completed
  ordinary fetches as cache fills. Six directed tests and 50,061 deterministic
  model/RTL clocks cover 2,783 accepted Type 13 descriptors, 752 retained
  retries/collisions, 1,391 data completions, 17,757 recovery observations,
  286 ordinary-fetch fills, 286 independently completed raw Type 5
  transactions, 88 BR recognitions/resumes, and 3,126 masked grant clocks. A
  machine-readable boundary, formal harness, Yosys recipe, and fully
  constrained Cyclone V project bind the result. Quartus uses 2,089 ALMs and
  1,646 fitted registers, no RAM/DSP blocks, +8.194 ns worst setup,
  +0.166 ns worst hold, 59.5 MHz worst slow-corner Fmax, and no unconstrained
  paths at 25 ns. Ordinary fetch and Type 5 remain raw descriptor inputs;
  HALT/TRAP/interrupt/loop/DM priority and whole-core execution remain open.

- A source-backed composition of the fail-closed shared PM owner and the
  original normal BR/BG sequencer. A state-3 bus request lets the active
  fetch/Type 5/Type 13 transaction complete, blocks later descriptor capture,
  masks every PM driver during grant, and accepts exactly one held descriptor
  at the state-8 resume boundary. Six directed tests and 50,002 deterministic
  model/RTL clocks cover all owners, 111 complete handshakes, 80 completions
  after request recognition, 1,417 blocked requests, 3,536 masked grant
  clocks, 79 resume-edge accepts, 530 fail-closed collisions, and 1,264
  accepted Type 5/13 instruction-access descriptors. A
  machine-readable contract, formal harness, Yosys recipe, and fully
  constrained Cyclone V project bind the result. Quartus uses 190 ALMs and 84
  fitted registers, no RAM/DSP blocks, +11.053 ns worst setup, +0.167 ns worst
  hold, 111.77 MHz worst slow-corner Fmax, and no unconstrained paths at
  20 ns. The Type 13 client is now attached in a separate bounded composition;
  ordinary-fetch/Type 5 requester storage, DM-bus composition, and
  HALT/TRAP/interrupt/loop priority remain open.

- A bounded fail-closed shared program-memory owner selector in an independent
  Python model and portable SystemVerilog. Ordinary fetch, Type 5 PM data, and
  Type 13 PM data descriptors now converge on exactly one native PM phase
  controller; exactly-one requests are accepted at state 8-to-1, owners and
  descriptors are retained through completion/relinquishment, and one-hot
  acceptance/read/completion events return to the accepted requester.
  PMDA is captured per descriptor rather than inferred from requester identity.
  Simultaneous and out-of-phase requests are rejected and observed rather than
  assigned an undocumented priority. Eight directed tests and 50,007
  deterministic model/RTL clocks cover 3,248 completions, 1,097 collisions,
  1,346 out-of-phase attempts, 2,576 owner switches, 611 active
  relinquishment holds, and 1,113 accepted Type 5/13 instruction-access
  descriptors. A machine-readable contract, formal harness, Yosys
  recipe, and fully constrained Cyclone V project bind the result. Quartus uses
  160 ALMs and 77 registers, no RAM/DSP blocks, +12.059 ns worst setup,
  +0.168 ns worst hold, 125.93 MHz worst slow-corner Fmax, and no unconstrained
  paths at 20 ns. A Type 13 client is attached in a separate bounded
  composition; complete client wiring and event priority remain open.

- A primary-backed bounded Type 5/native-PM/HALT composition in an independent
  Python model and portable SystemVerilog. HALT recognized during the PM-data
  cycle now converts an issue-time hit into a recovery, suppresses the cached
  word, commits the ALU/MAC/PM/PX/DAG2 action exactly once, performs one native
  external fetch, fills the cache, and stops after that fetch completes. Five
  directed tests and 50,126 deterministic model/RTL clocks cover 197 PM-data
  recognitions, late hit overrides, and forced fetches, 1,996 data
  completions, 387 stops/resumes, 196 DMACK-blocked releases, and 577 held
  clocks. A formal harness, Yosys recipe, and fully constrained Cyclone V
  project bind the claim. Quartus fit uses 1,946 ALMs and 1,768 registers,
  no RAM, one DSP, +3.651 ns worst setup, +0.166 ns worst hold, 46.84 MHz
  worst slow-corner Fmax, and no unconstrained paths at 25 ns. Shared
  PM/BR/BG/interrupt/TRAP/reset priority remains outside this bounded result.

- A primary-backed bounded Type 13/native-PM/HALT composition in an
  independent Python model and portable SystemVerilog. HALT recognized during
  the PM-data cycle now latches a late recovery request, discards an
  issue-time cache hit, commits the shifter/PM/PX/DAG action exactly once,
  accepts one external fetch at the next state-8 boundary, fills the cache,
  and stops after that fetch completes at state 7. Five directed tests and
  50,124 deterministic model/RTL clocks cover 210 PM-data recognitions, 210
  hit overrides and forced fetches, 397 stops/resumes, 209 DMACK-blocked
  releases, and 580 held clocks. A formal harness, Yosys recipe, and fully
  constrained Cyclone V project bind the claim. Quartus fit uses 2,094 ALMs
  and 1,655 registers, no RAM/DSP blocks, +7.946 ns worst setup, +0.168 ns
  worst hold, 58.64 MHz worst slow-corner Fmax, and no unconstrained paths at
  25 ns. Type 5 is independently attached; shared
  PM/BR/BG/interrupt/TRAP/reset priority remains outside both bounded
  compositions.

- A primary-backed standalone HALT sequencer for both ordinary instruction-
  fetch and PM-data recognition. A PM-data recognition completes its current
  cycle, admits exactly one forced external fetch at the following state-8
  issue boundary, and stops only after that fetch reaches state 7; issue is
  inhibited on every intervening boundary. Eight directed tests and 50,033
  deterministic model/RTL clocks cover 332 ordinary and 335 PM-data
  recognitions, 335 forced issues, 667 stops, 665 releases, 291 DMACK-blocked
  releases, and 2,269 held clocks. A machine-readable contract, formal recipe,
  Yosys flow, and fully constrained Cyclone V project bind the claim. The fit
  uses 26 ALMs and 6 registers, no RAM/DSP blocks, +12.584 ns worst setup,
  +0.172 ns worst hold, 134.84 MHz worst slow-corner Fmax, and no unconstrained
  paths at 20 ns. Type 5 and Type 13 now consume the forced-fetch pulse in
  separate bounded compositions; Type 13 is also attached separately to
  shared PM plus normal BR/BG, while combined HALT/shared-PM priority remains
  open.

- A primary-backed bounded ordinary-fetch HALT controller and structural
  attachment in independent Python and portable SystemVerilog. It recognizes
  the active-low input at enabled state 3, latches a short assertion, lets the
  current PM read retire at state 7-to-8, holds driven PM outputs stable in
  state 8, and resumes at state 8-to-1 only after HALT is inactive with DMACK
  high. Seven directed tests and 50,003 deterministic differential clocks
  cover 790 complete recognize/stop/resume sequences, 161 DMACK-low blocked
  releases, and 742 held clocks. A machine-readable contract, formal harness,
  Yosys flow, and fully constrained Cyclone V project bound the attachment.
  The requalified fit uses 916 ALMs and 1,026 registers, no RAM/DSP blocks,
  +12.809 ns worst setup, +0.164 ns worst hold, 82.03 MHz worst slow-corner
  Fmax, and no unconstrained paths at 25 ns. PM-data forced-fetch scheduling is
  verified separately, but its PM-owner attachment, HALT during BG or DMACK
  waits, TRAP handoff, BR while halted, interrupt/reset priority, and analog
  synchronization remain explicitly outside this composition.

- A bounded structural composition of the ordinary linear PM owner and the
  source-backed BR/BG controller in independent Python and portable
  SystemVerilog. It lets an in-flight fetch remain driven and retire after
  state-3 request recognition, inhibits the following state-8 issue, masks
  every PM output enable only while native BG is asserted, preserves state
  throughout grant, and accepts the restart fetch at state 8-to-1 after the
  full release interval. Five directed tests and 50,003 deterministic
  differential clocks cover 93 complete request/grant/release/resume
  handshakes, 5,375 retirements, and 5,376 issues. A machine-readable contract,
  formal harness, Yosys flow, and fully constrained Cyclone V project bound
  the attachment. The integrated fit uses 898 ALMs and 1,041 registers, no
  RAM/DSP blocks, +12.845 ns worst setup, +0.166 ns worst hold, 82.27 MHz worst
  slow-corner Fmax, and no unconstrained paths at 25 ns. PM-data/cache, DM,
  control-transfer, interrupt, HALT, and reset-first-fetch ownership remain
  outside this result.

- A primary-backed original normal-operation BR/BG controller in structurally
  independent Python and portable SystemVerilog. It recognizes active-low BR
  at enabled state 3, inhibits new issue while allowing the current instruction
  to finish, asserts BG one complete eight-state cycle later, masks all PM/DM
  drivers during grant, delays release by the same interval, and resumes issue
  on the following state-8-to-state-1 edge. A separate native-pin wrapper
  confines the documented asynchronous RESET-time BR/BG relationship outside
  architectural state. Seven directed tests and 50,084 deterministic
  differential clocks, a machine-readable timing contract, formal harness,
  Yosys flow, and fully constrained Cyclone V project bound the claim. The fit
  uses 27 ALMs and 7 registers with no RAM/DSP blocks, +12.350 ns worst setup,
  +0.172 ns worst hold, 131.58 MHz worst slow-corner Fmax, and no unconstrained
  paths at 20 ns. Invalid early request changes fail closed with observable
  protocol events and are not presented as device behavior.

- A primary-backed original RESET/logical-phase owner in structurally
  independent Python and portable SystemVerilog. It recognizes RESET only on
  represented rising CLKIN edges, qualifies four asserted samples, holds
  state 4 and CLKOUT low, releases into state 5 on exactly the second rising
  edge after deassertion, and traverses all eight logical states using clock
  enables rather than gated clocks. Six directed tests and 50,034
  deterministic differential clocks cover disabled edges, mid-run assertion,
  too-short fail-closed behavior, and restart; a formal harness and Yosys flow
  are wired into automation. A fully constrained Cyclone V fit uses 26 ALMs
  and 15 registers with +12.432 ns worst setup and +0.144 ns worst hold slack
  at 20 ns. Reset-time PMA `0x0004` is source-backed, while
  the undocumented reset-specific PM strobe onset is recorded as OQ-024 and
  intentionally not attached. Integrators are required to assert RESET before
  consuming phase outputs because synthesis cannot portably retain an
  architectural unknown power-up validity flag.

- A bounded steady-state linear instruction owner in structurally independent
  Python and portable SystemVerilog. It executes NOP, legal Type 6/7, all
  2,256 legal Type 17 internal MOVE words, and all Type 18 MODE CONTROL words
  at the current PC while the native PM controller
  fetches PC+1, admits the fetch at state 8-to-1, atomically retires state/PC/
  next word at state 7-to-8, and fails closed for unsupported or reserved
  words. Thirteen directed tests and 53,985 deterministic differential clocks,
  including every Type 17 source/destination pair and Type 18 encoding, a
  formal recipe, a machine-readable boundary contract, Yosys flow, and a fully
  constrained Cyclone V project bound the claim. Type 17 status/control-source
  extension is exposed on a dedicated retirement pulse under OQ-016; reset
  first-fetch and all multi-owner/event/cache arbitration remain explicitly
  excluded. The standalone fit now uses 885 ALMs and 1,020 registers, no
  RAM/DSP blocks, +13.145 ns worst setup, +0.166 ns worst hold, and 84.35 MHz
  worst slow-corner Fmax with no unconstrained paths at 25 ns.

- A primary-backed original Type 7 immediate-to-non-data-register database,
  independent decoder and state model, exact assembler/disassembler support,
  portable RTL decoder/state composition, hand-derived fixtures, exhaustive
  1,048,576-word Python and RTL partitions, eight directed model tests, and
  50,299 deterministic model/RTL clocks. The implementation accepts 507,904
  words selecting 31 writable original non-data registers, rejects 540,672
  group-zero, reserved-selector, or read-only-SSTAT words, preserves exact
  destination widths and reset unknowns, applies selected-bank SB writes and
  the documented CNTR/count-stack side effect, and emits no PM-data or DM
  transaction. A formal harness and fully constrained Cyclone V fit provide
  additional bounded evidence.

- A bounded original Type 3 state/native-DM composition in structurally
  independent Python and portable SystemVerilog. It shares the complete Type
  17 general-register state, captures absolute address and cycle-start write
  sources, commits read destinations only at completion, retains unknown
  values and OQ-016 visibility, and attaches issue/completion to native state
  8-to-1/state 7-to-8 boundaries. Fourteen directed tests, 50,151 logical and
  50,077 native differential clocks, two formal harnesses, and two constrained
  Cyclone V projects cover the bounded implementation.

- A primary-backed original Type 3 direct-DM action database, independent
  decoder, two legal and two unsupported hand-derived fixtures, original
  algebraic/raw assembler-disassembler paths, exact portable RTL decoder,
  formal assertions, exhaustive 24-bit traversal, and a constrained Cyclone V
  decoder project. The class partitions into 770,048 reads, 786,432 writes,
  and 540,672 reserved/read-only-destination words without assigning behavior
  to unsupported selectors.

- A primary-backed original Type 1 ALU/MAC-plus-dual-read action database,
  independent exhaustive decoder, two hand-derived fixtures, original
  algebraic/raw assembler-disassembler paths, portable exact RTL decoder,
  formal assertions, exhaustive class traversal, and a constrained Cyclone V
  decoder project.

- A bounded original Type 5 state/cache/native-PM composition in structurally
  independent Python and portable SystemVerilog. It captures selected-bank
  ALU/MAC, old `{DREG,PX}`, and DAG2 state once; commits compute/status,
  optional PM-read DREG/PX, and selected-I effects atomically; selects an
  issue-time cache hit or one pure recovery fetch; and attaches issue/commit
  to state 8-to-1/state 7-to-8, with directed/random differential tests,
  formal assertions, and three constrained Cyclone V projects.

- A primary-backed original Type 5 ALU/MAC-plus-PM action database,
  independent exhaustive decoder, two hand-derived field fixtures,
  algebraic/raw assembler-disassembler paths, portable exact RTL decoder,
  formal assertions, exhaustive 24-bit traversal, and a constrained Cyclone V
  decoder project.

- A bounded original Type 4/native-DM composition in structurally independent
  Python and portable SystemVerilog. It accepts only at state 8-to-1, reuses
  the sourced state-6 DMACK/full-cycle wait controller, and commits
  compute/status, optional read, and selected-I state only at state 7-to-8;
  with directed/random differential tests, formal assertions, and a
  constrained Cyclone V project.

- A bounded original Type 4 state/transaction model and portable RTL slice
  connecting the exact action decoder to selected-bank ALU/MAC, ASTAT, both
  DAGs, and a waited logical DM boundary; plus deterministic differential
  vectors, directed unknown/reset/conflict tests, a stateful formal harness,
  and a constrained Cyclone V project.

- A primary-backed original Type 4 action database, independent model,
  synthesizable exact decoder, two manual-derived fixtures, exhaustive Python
  and RTL partitions, algebraic assembler/disassembler support, formal
  assertions, and a constrained Cyclone V decoder project.

- A bounded Type 12/native-DM composition in independent Python and portable
  RTL, connecting old-value shifter/DREG/DAG issue at state 8-to-1 to native
  read/write phases and atomic state-7 completion, with directed/random
  differential tests, a formal harness, and a constrained Cyclone V project.

- A bounded Type 2/native-DM composition in independent Python and portable
  RTL, connecting state-8 descriptor acceptance to state-7 native completion,
  with directed/random differential tests, a formal harness, and a constrained
  Cyclone V project.

- A source-backed native DM phase controller and structurally independent
  model implementing DMA/DMS states 1–8, DMRD/DMWR states 4–7, DMACK
  qualification at 6–7, DMD read sampling at 7–8, write drive states 5–8,
  and complete eight-substate state-seven extensions; plus a machine-readable
  contract, directed/random differential tests, formal harness, and
  constrained Cyclone V project.

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
- A primary-backed exact Type 25 `IF MV SAT MR;` semantic record and main-ISA
  entry, hand-reviewed opcode/result fixtures, independent decoder and
  selected-bank state model, portable bounded execution RTL, exhaustive
  24-bit decoder test, formal recipes, assembler/disassembler round trip, and
  constrained Cyclone V synthesis project.
- A primary-backed parameterized Type 18 MODE CONTROL semantic record covering
  all 256 original field-defined words, 81 distinct action bundles, and both
  no-change aliases; an independent model, exact decoder, bounded stateful RTL
  slice, exhaustive decode, formal recipes, and constrained Cyclone V project.
- A primary-backed Type 21 MODIFY semantic record covering all 32 same-DAG
  I/M selections, an exact decoder, independent state model, exact-width
  I/M/L register file with reset validity, bounded stateful RTL execution,
  exhaustive decode, formal recipes, and constrained Cyclone V project.
- A primary-backed Type 17 internal-MOVE action database, independent decoder,
  all-register assembler/disassembler syntax, portable exact RTL decoder,
  exhaustive 24-bit fail-closed test, bounded formal recipe, and constrained
  Cyclone V project.
- An independent Type 17 cross-store state model and portable bounded RTL
  slice connecting both computational banks, both DAG register files,
  ASTAT/MSTAT/ICNTL/IMASK, PX, CNTR/count-stack, and composed SSTAT. Narrow
  status-source zero-extension is isolated behind an observable OQ-016
  provisional flag.
- A deterministic Type 17 vector generator, stateful Verilator comparison,
  bounded formal harness/recipe, and constrained Cyclone V state-slice project.
- A primary-backed full Type 6 immediate-to-DREG semantic entry, independent
  decoder/state model, portable exact decoder and bounded execution RTL,
  assembler/disassembler support, two hand-transcribed opcode fixtures,
  exhaustive class decode, deterministic stateful differential vectors,
  formal harness/recipe, and constrained Cyclone V synthesis project.
- A primary-backed bounded Type 15 immediate LSHIFT/ASHIFT semantic entry,
  independent selected-bank state model, exact fail-closed decoder, portable
  execution RTL, original-syntax assembler/disassembler support, two manual
  opcode fixtures, deterministic differential vectors, formal harness/recipe,
  and constrained Cyclone V synthesis project.
- A primary-backed Type 16 conditional-shifter semantic entry covering all
  sixteen SF functions and seven documented X operands; an independent
  unknown-preserving state model, exact fail-closed decoder, portable bounded
  execution RTL, complete algebraic assembler/disassembler support, two hand
  fixtures, deterministic differential vectors, formal harness/recipe, and
  constrained Cyclone V synthesis project.
- A bounded Type 14 shifter-plus-internal-DREG semantic entry covering 25,648
  canonical noncolliding words; an independent unknown-preserving parallel
  state model, exact fail-closed decoder, portable execution RTL, complete
  algebraic assembler/disassembler support, two hand fixtures, deterministic
  differential vectors, formal harness/recipe, and constrained Cyclone V
  synthesis project.
- A bounded original Type 12 shifter-plus-DM semantic/transaction entry
  covering 108,640 source-closed words; an independent unknown-preserving
  model with pending DMACK waits, exact fail-closed decoder, portable stateful
  RTL, all supported assembler/disassembler forms, two hand-derived fixtures,
  deterministic state/bus differential vectors, a bus-stability formal
  harness/recipe, and a constrained Cyclone V synthesis project.
- A bounded original Type 13 shifter-plus-PM semantic/transaction entry
  covering 54,320 source-closed words; an independent unknown-preserving
  model with explicit cache-hit/miss recovery, exact fail-closed decoder,
  portable stateful RTL, all supported assembler/disassembler forms, two
  hand-derived fixtures, deterministic state/cache/bus differential vectors,
  a fixed-cycle/recovery formal harness, and a constrained Cyclone V project.
- A source-bounded original instruction-cache model and portable RTL block
  implementing the documented 16-by-24 array, PMA[3:0] indexing, single
  contiguous valid region, discontinuity restart, sequential fill, and
  circular oldest-word replacement; plus deterministic differential vectors,
  invariant harness, machine-readable contract, and Quartus smoke project.
- A composed Type 13/cache boundary that replaces caller-supplied cache
  validity with the real pre-cycle monitor lookup, returns the actual cached
  instruction, fills recovery fetches, accepts ordinary external fetch fills,
  and reports deterministic PM-fill ownership conflicts; plus an independent
  composition model, directed/random differential tests, formal invariants,
  and a constrained Cyclone V project.
- A source-backed native PM phase controller with a shared eight-state model
  enum, independent request/response model, active-low PMS/PMRD/PMWR mapping,
  PMA/PMDA timing, state-7 read sampling, states-5-through-8 write-data drive,
  back-to-back PMS continuity, separate FPGA output enables, and externally
  directed bus-relinquishment masking; plus directed/random differential
  tests, a machine-readable contract, formal invariants, and a constrained
  Cyclone V project.
- A bounded Type 13/cache/native-PM composition model and portable RTL wrapper
  that admits issue at state 8-to-1, retains the complete old-value action and
  cache-hit word, commits at state 7-to-8, and accepts miss recovery
  back-to-back; plus directed/random differential tests, attachment
  invariants, a formal recipe, and a constrained Cyclone V project.
- A primary-backed, class-complete original Type 2 immediate-DM-write action
  database, independent decoder, three hand-derived fixtures, portable RTL
  decoder, algebraic assembler/disassembler support, exhaustive 24-bit
  fail-closed simulation, and formal recipe; plus an independent waited-DMACK
  execution model, portable logical transaction/DAG state slice, deterministic
  differential generator, formal stability harness, and constrained Cyclone V
  project.
- A bounded Type 8 ALU/MAC-plus-internal-DREG semantic entry covering 476,672
  source-closed noncolliding words; an independent unknown-preserving parallel
  state model, exact fail-closed decoder, portable execution RTL, canonical
  algebraic assembler/disassembler support with raw-word alias preservation,
  two hand-derived fixtures, exhaustive deterministic differential vectors,
  a formal harness/recipe, and a constrained Cyclone V synthesis project.
- A class-complete original Type 9 conditional ALU/MAC semantic entry covering
  all 32,768 words, including 31,744 conditional computations and 1,024
  documented AMF-zero no-operation aliases; an independent unknown-preserving
  state model, exact decoder, portable execution RTL, complete canonical
  assembler/disassembler support with lossless raw aliases, two hand-derived
  fixtures, deterministic exhaustive differential vectors, a formal
  harness/recipe, and a constrained Cyclone V synthesis project.
- A bounded original Type 10 direct JUMP/CALL semantic entry covering 507,904
  source-closed words; an independent exact-width PC/CNTR/stack model, exact
  fail-closed decoder, portable stateful RTL slice, numeric-target assembler/
  disassembler support, two hand-derived fixtures, deterministic exhaustive
  differential vectors, a formal harness/recipe, and a constrained Cyclone V
  synthesis project. The 16,384 CALL NOT CE words remain OQ-012.
- A class-complete original Type 11 DO UNTIL setup entry covering all 262,144
  address/termination words; independent exact-width model, exact decoder,
  portable PC/CNTR/PC-stack/loop-stack RTL slice, complete numeric-target
  assembler/disassembler support, two hand-derived fixtures, deterministic
  exhaustive differential vectors, a formal harness/recipe, and a constrained
  Cyclone V synthesis project.
- A bounded original Type 19 DAG2-indirect JUMP/CALL semantic entry covering
  124 source-closed words; an independent exact-width PC/CNTR/I4-I7/stack
  model, exact fixed-bit fail-closed decoder, portable stateful RTL with PMA
  target observation, complete supported assembler/disassembler syntax, two
  hand-derived fixtures, deterministic differential vectors, a formal recipe,
  and a constrained Cyclone V synthesis project. Four CALL NOT CE words remain
  OQ-012, and bit-5-one words remain reserved under SC-007.
- A class-complete original Type 20 conditional RTS/RTI semantic entry
  covering all 32 words; an independent exact-width PC/status/CNTR/stack
  model, exact decoder, portable stateful RTL slice, complete assembler/
  disassembler support, two hand-derived fixtures, deterministic differential
  vectors, a bounded formal recipe, and a constrained Cyclone V synthesis
  project. Missing taken-return stack context remains fail-closed under
  OQ-013.
- A class-complete, phase-aware original Type 22 conditional TRAP semantic
  entry covering all sixteen words; an independent PC/ASTAT/CNTR/TRAP/HALT
  model, exact decoder, portable stateful RTL, complete assembler/disassembler
  support, two hand-derived fixtures, deterministic phase-level differential
  vectors, a bounded formal recipe, and a constrained Cyclone V project.
- A class-complete original Type 23 DIVQ semantic entry covering all eight
  ALU-X divisor selections; an independent unknown-preserving state model,
  exact decoder, portable selected-bank RTL with atomic AF/AY0/AQ writeback,
  complete assembler/disassembler support, two hand-derived fixtures,
  deterministic differential vectors, a formal harness/recipe, a composed
  signed DIVS-plus-DIVQ sequence test, and a constrained Cyclone V project.
- A source-closed original Type 24 DIVS semantic entry covering sixteen legal
  AY1/AF-by-ALU-X operand combinations; an independent unknown-preserving
  model, exact 32-word partition decoder, portable selected-bank RTL with
  atomic AF/AY0/AQ writeback, complete legal assembler/disassembler forms,
  two hand-derived fixtures, deterministic differential vectors, a formal
  harness/recipe, and a constrained Cyclone V project.
- Original RGP/REG general-MOVE table accounting for 48 register encodings,
  reserved holes, storage widths, and verified narrow-register extension
  behavior.
- Independent Python exact-width state, authentic reset-unknown
  classification, deterministic random-state/replay foundation, PM fetch
  transactions, program/data image loading, reserved-code rejection, and the
  verified NOP execution slice.
- Partial database-driven assembler/disassembler that round-trips the
  independent NOP fixture and fails closed for unimplemented/reserved words.
- Original Type 18 algebraic ENA/DIS assembly and disassembly, including
  deterministic omitted-field encoding and raw `.WORD` preservation for
  otherwise indistinguishable MCC=01 binary aliases.
- Original Type 21 `MODIFY (Ix, My);` assembly and disassembly for all 32 legal
  same-DAG register combinations, with cross-DAG and out-of-range operands
  rejected.
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
- Exact-width stateful storage for all eight I, eight M, and eight L registers,
  with per-register validity rather than invented reset data and a fail-closed
  bounded setup/writeback collision boundary.
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

- Corrected the independent model's ordinary linear-flow contract: NOP and
  legal Type 6/7 words now execute at the current PC while the trace records
  the overlapped instruction fetch at PC+1, and their state effects and PC
  progression commit in the same one-cycle boundary. Ordinary PM fetch waits
  now fail closed because the original interface has no acknowledge input.

- The Type 4 execution boundary now captures every cycle-start compute,
  memory, bank, and DAG input once; DMACK-low clocks freeze the descriptor and
  all destinations, while acknowledgment atomically commits compute/status,
  optional read data, and selected-I postmodify. AMF-zero remains a
  memory-only transaction.

- Type 13 and its cache wrapper now support an explicit delayed PM-cycle
  completion input. The compatibility path remains a one-clock logical cycle,
  while the native attachment holds descriptors and defers every architectural
  write, recovery fill, and next-instruction event until the source-backed
  state-7-to-state-8 boundary.

- Corrected the Type 23/24 machine-readable operand roles: XOP is the divisor
  for both primitives, while Type 24 YOP is the upper dividend.

- Expanded the initial README to state the exact ADSP-2100 scope and current
  non-complete status.
- Factored the documented one-shot MR saturation transform into one shared
  synthesizable primitive used by both the MAC compute block and Type 25
  execution boundary.
- Identified the contemporary original ADSP-2100 data sheet within the 1987
  ADI data book at printed pages 2-15 onward.

### Fixed

- Replaced two stale `TASKS.md` references to the nonexistent
  `tests/test_architecture_claims.py` with the implemented documentation
  presence check and explicitly left semantic device-scope/matrix validation
  as unfinished work.

- Preserved an explicit per-descriptor PM data-access qualifier through the
  shared owner instead of deriving PMDA from the Type 5/Type 13 owner ID. The
  prior derivation incorrectly marked a retained Type 13 recovery instruction
  fetch as a PM data access. Updated selector and BR/BG differentials now cover
  1,113 and 1,264 accepted Type 5/Type 13 descriptors with PMDA deasserted,
  respectively, and the attached Type 13 recovery test requires PMDA low.

- Removed the prior model expectation that treated the currently executing
  word as a same-cycle instruction fetch and allowed a caller to extend that
  fetch by arbitrary instruction cycles. The 1989 manual instead defines the
  PC as the executing address and PMA as the sequencer-selected following
  address during normal flow.

- Invalid Type 3 DM read data now invalidates a CNTR destination without
  fabricating a value or pushing a phantom count-stack entry. The counter has
  an explicit fail-closed invalidation action, and all existing sequencer
  clients retain their prior behavior by tying that action inactive.

- Type 3 general-register validity now follows the selected computational bank
  at the cycle-start MSTAT boundary. A deterministic differential vector that
  switches banks protects against leaking validity from the inactive bank.

- Corrected the Type 5 logical test expectation for the issuing edge of a
  subsequently held PM transaction. Observable event fields describe pre-edge
  state, so `held_transaction` becomes true on the following clock; the RTL
  and independent model already agreed on that contract and were unchanged.

- Moved the assembler/disassembler legal-but-unimplemented sentinel from
  newly supported Type 5 to then-unimplemented Type 3. The distinction from
  reserved-unshown encodings remains tested; no expected opcode behavior was
  weakened.

- Scoped the Type 4/native-DM wait-state commit assertion outside the
  synchronous reset pre-edge. The native pins remain masked immediately, while
  the retained bus state clears on the reset clock edge as the independent
  model specifies.

- Re-ran the Type 4 logical-DM smoke project with Standard Fit after Auto Fit
  exposed a -0.215 ns multicorner hold violation; the verified fit now has
  +0.104 ns worst hold slack without weakening its constraints.

- Scoped the Type 12 pending-descriptor stability assertion outside reset.
  Reset intentionally masks transaction outputs before the synchronous edge
  clears the retained descriptor; the connected reset vector now protects
  that distinction without weakening normal pending-state invariants.

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
- Promoted legal Type 17 disassembly from the stale action-decode-only marker
  to its verified bounded-execution classification.
- The generic sequencer boundary now rejects nested loops sharing the active
  loop's terminal instruction, matching the original documented restriction;
  a directed model/RTL vector prevents regression.
- Corrected progress wording that mislabeled Types 12/13 as indirect-flow and
  return formats; those are the original shifter-plus-DM/PM forms, while
  indirect flow and conditional return are Types 19/20.

### Verified

- The attached Type 13/shared-PM/BR-BG slice passes strict RTL and 71-harness
  assertion syntax lint. SymbiYosys/Yosys remain unavailable, so no new proof
  or open-source synthesis result is claimed; Quartus full compilation and
  TimeQuest complete with zero errors and all primary timing paths constrained.

- The shared-PM-owner/BR/BG composition passes six directed checks, 50,002
  deterministic model/RTL clocks, the complete 661-check `make test`
  regression, strict module/formal-harness lint, and a fully constrained
  Quartus Cyclone V fit at 20 ns. Formal proof execution and Yosys synthesis
  remain unavailable in this environment.

- The shared-PM owner passes eight directed checks, 50,007 deterministic
  model/RTL clocks, the complete 655-check `make test` regression, strict
  Verilator/text lint, and all 69 formal-harness syntax checks. Its fully
  constrained Quartus Cyclone V fit closes at 20 ns with positive multicorner
  setup/hold slack and zero unconstrained paths; proof execution and Yosys
  synthesis remain unavailable in this environment.

- Sixteen integrated-model foundation tests and the complete `make test`
  regression pass after composing linear NOP/Type 6/Type 7 execution with the
  corrected PC+1 fetch trace. Strict Verilator/text lint passes; the 60 formal
  recipes remain syntax-only and Yosys synthesis remains skipped because
  SymbiYosys/Yosys are unavailable.

- All 4,194,304 Type 1 words decode as source-closed parallel actions with
  fixed DAG1 DM and DAG2 PM reads, DD/PD input-register destinations, implicit
  AR/MR computation destinations, and AMF-zero dual fetch. Six model/schema
  tests, two independent fixtures, 1,024 representative dual-read-only forms,
  685 canonical computation forms, a contemporary `0xe89800` listing
  cross-check, raw aliases, exhaustive RTL decode, and strict formal syntax
  lint pass.
- Quartus full compilation closes the Type 1 combinational decoder at 20 ns
  on Cyclone V: 53 ALMs, no registers/RAM/DSPs, +11.769 ns worst setup,
  +4.309 ns worst multicorner hold, and no unconstrained paths.

- All 1,048,576 Type 5 words partition into 1,017,344 source-closed
  ALU/MAC-plus-PM or PM-only actions and 31,232 prohibited read-destination
  collisions. Seven model/schema tests, two independent fixtures, 512
  canonical memory-only forms, 2,649 representative compute forms, raw
  aliases, exhaustive RTL decode, and strict formal syntax lint pass.
- Fourteen Type 5 logical, six cache-composition, and five native-PM directed
  tests plus 50,071 logical and 50,083 native model/RTL clocks pass. Three new
  assertion harnesses pass strict syntax lint; proof execution remains skipped
  because SymbiYosys/Yosys are unavailable.
- Quartus Standard Fit closes the bounded Type 5 logical/cache/native projects
  at 25 ns with respectively 1,681/1,912/1,894 ALMs,
  1,262/1,672/1,746 registers, one DSP, no RAM, positive multicorner setup/hold
  slack, and fully constrained setup/hold paths.
- Quartus full compilation closes the Type 5 combinational decoder at 20 ns
  on Cyclone V: 51 ALMs, no registers/RAM/DSPs, +12.323 ns worst setup,
  +4.281 ns worst hold, 130.26 MHz worst slow-corner Fmax, and no
  unconstrained paths.

- Type 4/native-DM attachment passes six directed tests and 50,082 connected
  model/RTL clocks spanning memory-only and ALU/MAC reads/writes, old-value
  stores, state-8 issue, native strobes, full-cycle waits, state-7 atomic
  compute/status/read/I completion, reset, late ACK, off-boundary controls,
  debug-port conflicts, and relinquishment.
- Quartus Standard Fit closes the Type 4/native-DM attachment at 25 ns on
  Cyclone V: 1,693 ALMs, 1,226 registers, one DSP block, no RAM, +1.121 ns
  worst setup, +0.167 ns worst multicorner hold, 41.88 MHz worst slow-corner
  Fmax, and zero unconstrained clocks, inputs, outputs, or paths.

- The bounded Type 4 state model and RTL agree for 50,072 clocks spanning
  immediate and arbitrary waits, reads/writes, all selected-bank compute
  paths, both DAGs, DAG1 bit reversal, old-value write overlap, memory-only
  aliases, reset cancellation, integration conflicts, and unknown-dependent
  invalidation. Twelve model/schema/directed tests and strict assertion lint pass.
- Quartus Standard Fit closes the bounded Type 4 logical-DM slice at 25 ns on
  Cyclone V: 1,677 ALMs, 1,258 registers, one DSP block, no RAM, +3.644 ns
  worst setup, +0.104 ns worst multicorner hold, 46.83 MHz worst slow-corner
  Fmax, and zero unconstrained clocks, inputs, outputs, or paths.

- All 2,097,152 Type 4 words partition into 2,034,688 supported actions and
  62,464 prohibited compute/read destination collisions; AMF-zero memory-only
  actions and old-value same-register writes remain supported. Quartus fits
  the combinational decoder in 53 ALMs at 20 ns with +15.103 ns worst setup,
  +0.286 ns worst multicorner hold, 204.21 MHz worst slow-corner Fmax, and no
  unconstrained paths.

- Type 12/native-DM attachment passes six directed tests and 50,064 connected
  model/RTL clocks spanning reads, writes, old-value store data, state-7 read
  sampling, atomic shifter/DREG/I completion, complete-cycle waits, invalid
  read data, reset, phase conflicts, and relinquishment.
- Quartus full compilation passes for the Type 12/native-DM attachment on
  Cyclone V at 20 ns: 1,739 ALMs, 1,139 registers, no RAM/DSP blocks,
  +1.262 ns worst setup, +0.167 ns worst hold, 53.37 MHz worst slow-corner
  Fmax, and no unconstrained clocks, ports, or paths.

- Type 2/native-DM attachment passes five directed tests and 50,027
  deterministic model/RTL clocks covering state-8 issue, state-7 commit,
  complete-cycle DMACK extensions, late-ACK rejection, stable old values,
  off-boundary rejection, and relinquishment. Its 20 ns Cyclone V fit uses
  608 ALMs and 466 registers, has +2.590 ns worst setup and +0.159 ns worst
  hold slack, and reports no unconstrained clocks, ports, or paths.

- Native DM timing passes nine directed model tests and 50,039 deterministic
  model/RTL phase clocks, including repeated full-cycle DMACK extensions,
  late-ACK rejection, stable strobes/data, back-to-back DMS, phase holds,
  reset, explicit unknowns, and relinquishment masking. Its formal harness
  passes strict assertion syntax lint; a 20 ns Cyclone V fit uses 100 ALMs and
  57 registers, meets setup/hold across all timing models, and has no
  unconstrained clocks, ports, or paths.

- The Type 13/cache/native-PM attachment passes five directed tests and 50,081
  deterministic model/RTL clocks covering read and write phases, issue-time
  hit capture, miss recovery, state holds, off-boundary rejection, reset, and
  bus relinquishment. Existing 50,070 base, 50,086 cache-integrated, and
  50,032 standalone PM-phase differentials remain green.
- Quartus full compilation passes for the attached Type 13/cache/native-PM
  boundary at 20 ns: 2,055 ALMs, 1,648 fitted registers, no RAM/DSP blocks,
  +3.925 ns worst setup and +0.162 ns worst multicorner hold slack, 62.21 MHz
  worst slow-corner Fmax, and zero unconstrained clocks, ports, or paths.
- The expanded `make test` passes 484 distinct Python checks and every existing
  RTL regression. `make formal` syntax-checks 45 recipes; proof execution
  remains skipped because SymbiYosys/Yosys are unavailable.

- Type 2 exhaustive RTL decode traverses all 16,777,216 program words,
  identifies exactly 2,097,152 field-defined actions, and proves all other
  words action-free. Six model/metadata tests cover both DAGs, all I/M
  selections, raw 16-bit immediate boundaries, hand fixtures, and failures.
- Type 2 bounded execution passes eleven directed tests and 50,035
  deterministic model/RTL clocks covering all I/M selections, both DAGs,
  DAG1 bit reversal, raw immediate writes, immediate and multi-clock DMACK
  completion, stable stalls, completion-only I updates, reset aborts,
  conflicts, and unknown/invalid DAG state.
- Quartus full compilation passes for the bounded Type 2 logical DM-write
  slice at its 20 ns standalone constraint: 581 ALMs, 430 fitted registers,
  no RAM/DSP blocks, +3.590 ns worst setup and +0.165 ns worst multicorner
  hold slack, 60.94 MHz worst slow-corner Fmax, and zero unconstrained clocks,
  ports, or paths.
- Type 13/cache integration passes ten directed tests and 50,086 deterministic
  model/RTL clocks covering prefilled hits, miss/forced-fetch recovery fills,
  actual 24-bit instruction selection, sequential replacement, unknown
  entries/addresses, reset, and competing external/recovery fill ownership.
- Quartus full compilation passes for the cache-integrated Type 13 boundary at
  20 ns: 1,937 ALMs, 1,446 fitted registers, no RAM/DSP blocks, +2.615 ns
  worst setup and +0.166 ns worst multicorner hold slack, 57.52 MHz worst
  slow-corner Fmax, and zero unconstrained clocks, ports, or paths.
- Native PM phase generation passes ten directed tests and 50,032
  deterministic model/RTL clocks covering fetch/data-read/data-write pin
  maps, state holds, read sampling, write drive, back-to-back select
  continuity, unknown validity, reset, and bus-output masking.
- Quartus full compilation passes for the native PM phase controller at
  20 ns: 112 ALMs, 71 fitted registers, no RAM/DSP blocks, +12.825 ns worst
  setup and +0.167 ns worst multicorner hold slack, 139.37 MHz worst
  slow-corner Fmax, and zero unconstrained clocks, ports, or paths.
- The expanded `make test` passes 484 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint,
  twenty-two exhaustive 24-bit decode traversals, and every existing
  model/RTL vector regression.
- The instruction-cache regression passes ten directed tests and 50,028
  deterministic model/RTL clocks covering reset invalidation, all 16 slots,
  region fill and wrap, inside-region refresh, seventeenth-word replacement,
  discontinuous fetches, 14-bit PM-address wrap, and unknown address/data.
- Quartus full compilation passes for the standalone instruction cache at its
  20 ns constraint: 310 ALMs, 429 fitted registers, no RAM/DSP blocks,
  +7.071 ns worst setup and +0.163 ns worst multicorner hold slack, 77.35 MHz
  worst slow-corner Fmax, and zero unconstrained clocks, ports, or paths.
  The asynchronous lookup intentionally leaves the small array in registers.
- Type 13 exhaustive RTL decode traverses all 16,777,216 program words and
  partitions its 65,536-word class into 54,320 supported actions, 8,192
  unavailable-XOP words, and 3,024 PM-read destination collisions. The
  50,070-clock model/RTL differential covers both banks, all DAG2 selections,
  read DREG/PX packing, old write data, fixed-cycle architectural commits,
  cache-hit completion, one-cycle miss/forced-fetch recovery, reset aborts,
  conflicts, and unknown propagation.
- Quartus full compilation passes for the bounded Type 13 logical PM/cache
  slice at its 21 ns standalone constraint: 1,640 ALMs, 1,002 fitted
  registers, no RAM/DSP blocks, +1.172 ns worst setup and +0.168 ns worst
  multicorner hold slack, 50.43 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths. The unassigned clock pin and constant
  DM-access output are expected for the standalone smoke project.
- Type 12 exhaustive RTL decode traverses all 16,777,216 program words and
  partitions its 131,072-word class into 108,640 supported actions, 16,384
  unavailable-XOP words, and 6,048 DM-read destination collisions. The
  50,069-clock model/RTL differential covers both banks and DAGs, immediate
  and multi-clock DMACK completion, bit reversal, old write data, atomic
  shifter/read/I commits, reset aborts, and unknown propagation.
- Quartus full compilation passes for the bounded Type 12 logical DM slice at
  its 21 ns standalone constraint: 1,704 ALMs, 1,091 fitted registers, no
  RAM/DSP blocks, +1.377 ns worst setup and +0.166 ns worst multicorner hold
  slack, 50.96 MHz worst slow-corner Fmax, and zero unconstrained clocks, ports,
  or paths. The sole unassigned physical pin is the expected smoke-test clock.
- Type 23 exhaustive RTL decode traverses all 16,777,216 program words and
  identifies exactly eight source-closed actions; 50,081 deterministic
  stateful model/RTL cycles cover both banks, reset unknowns, all divisors,
  both old-AQ branches, invalid words, and integration conflicts.
- Quartus full compilation passes for the bounded Type 23 DIVQ slice at its
  20 ns standalone constraint: 316 ALMs, 338 design registers plus three
  routing duplicates, no RAM/DSP blocks, +7.009 ns worst setup and +0.164 ns
  worst multicorner hold slack, 77.71 MHz worst slow-100C Fmax, and zero
  unconstrained clocks, ports, or paths.
- Type 24 exhaustive RTL decode traverses all 16,777,216 program words and
  identifies exactly 32 field words, partitioned into sixteen source-closed
  actions and sixteen unsupported YOP words; 50,109 deterministic stateful
  model/RTL cycles cover both banks, reset unknowns, all legal operands,
  unsupported words, and integration conflicts.
- Quartus full compilation passes for the bounded Type 24 DIVS slice at its
  20 ns standalone constraint: 351 ALMs, 372 design registers plus nine
  routing duplicates, no RAM/DSP blocks, +8.448 ns worst setup and +0.168 ns
  worst multicorner hold slack, 86.81 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths.
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
- The Type 25 regression proves that only `0x050000` activates saturation
  across all 16,777,216 words and passes nine directed/schema/random model
  tests plus 50,112 stateful model-versus-RTL cycles. Both MR signs and banks,
  false MV, status preservation, invalid opcodes, reset unknowns, and atomic
  fail-closed setup collisions are covered.
- The expanded `make test` passes 248 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint, six
  exhaustive 24-bit decode traversals, and every existing model/RTL vector
  regression including the Type 18, Type 21, and Type 25 stateful comparisons.
- Quartus full compilation passes for the bounded Type 25 integration slice:
  144 ALMs, 92 registers, no RAM/DSPs, +11.443 ns worst setup and +0.246 ns
  worst hold slack across four timing models, with zero unconstrained clocks,
  ports, or paths against the 20 ns constraint.
- The Type 18 regression checks all 256 field-defined encodings, all 4,096
  opcode/initial-MSTAT transforms, both no-change codes, algebraic and raw-word
  round trips, invalid-word suppression, reset/setup conflicts, and 58,248
  stateful model-versus-RTL cycles.
- Quartus full compilation passes for the bounded Type 18 integration slice:
  46 ALMs, 30 combinational ALUTs, exactly four MSTAT registers, no RAM/DSPs,
  +12.168 ns worst setup and +0.173 ns worst hold slack across four timing
  models, with zero unconstrained clocks, ports, or paths.
- The Type 21 regression proves that exactly 32 words activate MODIFY across
  all 16,777,216 program words, checks every I/M selection from independent
  fixtures, passes ten directed/schema/random model tests, and compares 50,124
  stateful model/RTL cycles covering linear and circular updates, both modify
  signs, reset-invalid state, unsupported configurations, invalid words, and
  atomic collision suppression.
- Quartus full compilation passes for the bounded Type 21 integration slice:
  526 ALMs, 543 design combinational ALUTs, exactly 360 architectural
  data/valid registers plus fourteen fitted routing duplicates, no RAM/DSPs,
  +2.361 ns worst setup and +0.185 ns worst hold slack across four timing
  models, with zero unconstrained clocks, ports, or paths.
- The Type 17 regression partitions all 4,096 class words into exactly 2,256
  legal register moves and 1,840 reserved/read-only-destination
  subencodings, round-trips every legal register pair, and proves across all
  16,777,216 words that no non-Type-17 word emits an action.
- Seven Type 17 state-model tests execute all 2,256 legal moves with each bank
  selected, preserve unknown reset state, check MR1/CNTR side effects, and
  reject invalid/conflicting requests. The stateful RTL agrees for 59,430
  deterministic cycles.
- Quartus full compilation passes for the Type 17 action decoder: 42 ALMs, 24
  combinational ALUTs, no registers/RAM/DSPs, +15.704 ns worst setup and
  +0.462 ns worst hold slack across four timing models, with zero
  unconstrained clocks, ports, or paths.
- Quartus full compilation passes for the bounded Type 17 state slice: 816
  ALMs, 906 registers, no RAM/DSPs, +6.401 ns worst setup and +0.151 ns worst
  hold slack across four timing models, with zero unconstrained clocks, ports,
  or paths.
- Type 6 Python and RTL decoders exhaust all 1,048,576 field-defined words;
  six directed/model checks cover both banks, every DREG destination, reset
  unknowns, SE/MR2 truncation and sign-extension, MR1 sign-fill, invalid words,
  and setup collisions. Stateful RTL agrees with the independent model for
  50,204 deterministic cycles.
- The expanded `make test` passes 255 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint, seven
  exhaustive 24-bit decode traversals, and every existing model/RTL vector
  regression including Type 6 execution.
- Quartus full compilation passes for the bounded Type 6 execution slice: 302
  ALMs, 484 registers, no RAM/DSPs, +8.167 ns worst setup and +0.133 ns worst
  hold slack across four timing models, with zero unconstrained clocks, ports,
  or paths.
- Type 15 Python and RTL decoders exhaustively partition all 32,768 class
  words into 14,336 source-closed actions and 18,432 unsupported
  subencodings. Eight directed/model checks, 280 syntax forms, two manual
  fixtures, and 58,709 stateful model-versus-RTL cycles cover every supported
  word in both banks, all signed exponents, PASS/OR feedback, invalid words,
  reset unknowns, and setup collisions.
- Quartus full compilation passes for the bounded Type 15 immediate-shift
  slice: 774 ALMs and 501 fitted registers, no RAM/DSPs, +3.728 ns worst setup
  and +0.057 ns worst hold slack across four timing models, with zero
  unconstrained clocks, ports, or paths against the 20 ns constraint.
- The expanded `make test` passes 265 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint, eight
  exhaustive 24-bit decode traversals, and every existing model/RTL vector
  regression including bounded Type 15 execution.
- Type 16 Python and RTL decoders exhaustively partition all 2,048 class words
  into 1,792 supported actions and 256 unavailable-XOP subencodings. Ten
  directed/model checks, all 1,792 syntax forms, two hand fixtures, and 54,403
  stateful model-versus-RTL cycles cover every supported word in both banks,
  all conditions, all SR/SE/SB/SS side effects, reset unknowns, invalid words,
  and setup collisions.
- Quartus full compilation passes for the bounded Type 16 conditional-shift
  slice: 840 ALMs and 520 fitted registers, no RAM/DSPs, +2.304 ns worst setup
  and +0.173 ns worst hold slack across four timing models, with zero
  unconstrained clocks, ports, or paths against the 20 ns constraint.
- The expanded `make test` passes 277 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint, nine
  exhaustive 24-bit decode traversals, and every existing model/RTL vector
  regression including bounded Type 16 execution.
- Type 14 Python and RTL decoders exhaustively partition all 65,536 class words
  into 25,648 supported canonical actions, 32,768 unresolved bit-15 forms,
  4,096 unavailable-XOP forms, and 3,024 same-destination forms. Ten directed
  model checks, all 25,648 syntax forms, two hand fixtures, and 82,597 stateful
  model-versus-RTL cycles cover every supported word in both banks, old-value
  ordering in both parallel clauses, all shifter side effects, reset unknowns,
  invalid words, and setup collisions.
- Quartus full compilation passes for the bounded Type 14 shift-move slice:
  1,032 ALMs and 565 fitted registers, no RAM/DSPs, +3.041 ns worst setup and
  +0.171 ns worst hold slack across four timing models, with zero unconstrained
  clocks, ports, or paths against the 20 ns constraint.
- The expanded `make test` passes 289 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint, ten
  exhaustive 24-bit decode traversals, and every existing model/RTL vector
  regression including all 82,597 bounded Type 14 execution cycles.
- Type 8 Python and RTL decoders exhaustively partition all 524,288 class
  words into 476,672 supported actions, 16,384 AMF-zero words held under
  OQ-022, and 31,232 same-destination collision words held under OQ-014. Ten
  directed model checks, 20,513 representative canonical syntax packets, two
  hand-derived fixtures, and 983,386 stateful model-versus-RTL cycles cover
  every supported word in both banks, old-value source ordering, ALU/MAC
  result and status writeback, reset unknowns, invalid words, and conflicts.
- Quartus full compilation passes for the bounded Type 8 compute-move slice at
  its documented 22 ns standalone constraint: 983 ALMs, 693 fitted registers,
  one DSP block, no RAM, +1.131 ns worst setup and +0.177 ns worst hold slack,
  47.92 MHz worst slow-corner Fmax, and zero unconstrained paths. The same
  monolithic slice missed a 20 ns constraint by 1.721 ns; no whole-core or
  MiSTer timing claim is made.
- The expanded `make test` passes 301 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint, eleven
  exhaustive 24-bit decode traversals, and every existing model/RTL vector
  regression including all 983,386 bounded Type 8 execution cycles.
- Type 9 Python and RTL decoders classify all 32,768 words without unsupported
  subencodings. Ten directed model checks, 21,920 canonical syntax forms, two
  hand-derived fixtures, and 283,996 stateful model-versus-RTL cycles cover
  every word in both banks, every nonconstant condition's true/false paths,
  atomic result/status writeback, false preservation, reset unknowns, invalid
  words, and conflicts.
- Quartus full compilation passes for the bounded Type 9 conditional-compute
  slice at its documented 22 ns standalone constraint: 970 ALMs, 697 fitted
  registers, one DSP block, no RAM, +1.140 ns worst setup and +0.165 ns worst
  hold slack, 47.94 MHz worst slow-corner Fmax, and zero unconstrained paths.
  The initial 20 ns fit missed setup by 1.735 ns and measured a 46.01 MHz worst
  slow-corner Fmax; no whole-core or MiSTer timing claim is made.
- The expanded `make test` passes 313 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint, twelve
  exhaustive 24-bit decode traversals, and every existing model/RTL vector
  regression including all 283,996 bounded Type 9 execution cycles.
- Type 10 Python and RTL decoders partition all 524,288 class words into
  507,904 supported direct transfers and 16,384 OQ-012 CALL NOT CE words.
  Twelve directed model checks, all supported assembler/disassembler forms,
  two hand-derived fixtures, and 554,412 stateful model-versus-RTL cycles
  cover every supported word, predicate outcomes, PC wrap/targets, CALL stack
  effects, JUMP NOT CE counter transitions, reset unknowns, and conflicts.
- Quartus full compilation passes for the bounded Type 10 direct-transfer
  slice at its 20 ns standalone constraint: 284 ALMs, 334 fitted registers,
  no RAM/DSP blocks, +8.138 ns worst setup and +0.167 ns worst multicorner
  hold slack, 84.3 MHz worst slow-corner Fmax, and zero unconstrained paths.
- Type 11 Python and RTL decoders accept all 262,144 class words and preserve
  exact ADDR/TERM fields. Twelve directed model checks, every assembler/
  disassembler form, two hand-derived fixtures, and 554,309 stateful
  model-versus-RTL cycles cover simultaneous PC+1/descriptor pushes, all
  TERM codes, legal and illegal nesting, CE context, OQ-018, overflow, reset,
  invalid opcodes, and setup conflicts.
- Quartus full compilation passes for the bounded Type 11 setup slice at its
  20 ns standalone constraint: 308 ALMs, 402 fitted registers, no RAM/DSP
  blocks, +7.263 ns worst setup and +0.074 ns worst multicorner hold slack,
  78.51 MHz worst slow-corner Fmax, and zero unconstrained paths.
- Type 19 Python and RTL decoders accept exactly 128 original fixed-bit words,
  partitioning them into 124 supported actions and four OQ-012 CALL NOT CE
  words. Twelve directed model checks, all supported assembler/disassembler
  forms, two hand-derived fixtures, exhaustive 24-bit RTL decode, and 50,259
  stateful model/RTL cycles cover I4-I7 targets and validity, false/taken flow,
  PMA drive intent, no I modification, CALL stacking, JUMP NOT CE transitions,
  overflow, reset, invalid conditions/targets, and conflicts.
- Quartus full compilation passes for the bounded Type 19 slice at its 20 ns
  standalone constraint: 353 ALMs, 400 fitted registers, no RAM/DSP blocks,
  +7.520 ns worst setup and +0.045 ns worst multicorner hold slack, 80.93 MHz
  worst slow-corner Fmax, and zero unconstrained clocks, ports, or paths.
- Type 20 Python and RTL decoders accept exactly all 32 conditional RTS/RTI
  words. Twelve directed model checks, all assembler/disassembler forms, two
  hand-derived fixtures, exhaustive 24-bit RTL decode, and 50,254 stateful
  model/RTL cycles cover false/taken flow, valid PC/status pops, atomic RTI
  status restoration, return NOT CE counter preservation, reset, invalid
  context, and conflicts.
- Type 22 Python and RTL decoders accept exactly all sixteen conditional TRAP
  words. Twelve directed model checks, all assembler/disassembler forms, two
  hand-derived fixtures, exhaustive 24-bit RTL decode, and 50,168 model/RTL
  clocks cover false/taken conditions, held state 7, state-7/state-8 assertion,
  observable PC+1, state-8 halt, HALT acknowledgment/release, reset, invalid
  phase/opcode, unknown predicates, and setup conflicts.
- Quartus full compilation passes for the bounded phase-aware Type 22 slice at
  its 20 ns standalone constraint: 116 ALMs, 53 design registers plus fourteen
  routing duplicates, no RAM/DSP blocks, +7.592 ns worst setup and +0.069 ns
  worst multicorner hold slack, 80.59 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths.
- Quartus full compilation passes for the bounded Type 20 slice at its 20 ns
  standalone constraint: 318 ALMs, 417 fitted registers, no RAM/DSP blocks,
  +7.725 ns worst setup and +0.136 ns worst multicorner hold slack, 81.47 MHz
  worst slow-corner Fmax, and zero unconstrained clocks, ports, or paths.
- The expanded `make test` passes 368 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint,
  sixteen exhaustive 24-bit decode traversals, and every existing model/RTL
  vector regression including all 50,254 bounded Type 20 execution cycles.
- The expanded `make test` passes 381 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint,
  seventeen exhaustive 24-bit decode traversals, and every existing model/RTL
  vector regression including all 50,168 phase-aware Type 22 clocks.
- The expanded `make test` passes 355 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint,
  fifteen exhaustive 24-bit decode traversals, and every existing model/RTL
  vector regression including all 50,259 bounded Type 19 execution cycles.
- The expanded `make test` passes 327 distinct Python checks, 14 local
  reference hashes, all generated-data checks, strict Verilator lint,
  thirteen exhaustive 24-bit decode traversals, and every existing model/RTL
  vector regression including all 554,412 bounded Type 10 execution cycles.

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
- `make formal` passes strict assertion syntax lint for all 56 harnesses,
  including Type 1 action decode, exact Type 6/Type 17/Type 21 decode,
  bounded Type 5/Type 6/Type 8/
  Type 14/Type 17/Type 21 state execution, Type 5/Type 13 cache ownership, and
  native PM phase/strobe stability;
  proof execution remains explicitly skipped without SymbiYosys/Yosys.

### Documentation

- Added the machine-readable Type 13/shared-PM/BR-BG attachment contract and
  recorded that PMDA is a captured transaction qualifier, not an owner-class
  shortcut.

- Recorded the exact Type 1 dual-read fields, fixed DAG ownership, DD/PD
  destination restrictions, implicit AR/MR result, AMF-zero dual-fetch form,
  cycle-start/cycle-end ordering, PX effect, exhaustive action count, and
  OQ-023 native PM/DMACK timing boundary.

- Recorded the exact Type 5 PM/DAG2 fields, AMF-zero PM-only behavior,
  `{DREG,PX}` transfer packing, old-value store ordering, read collision rule,
  objective action counts, fixed PM/cache recovery timing, native state-8 issue
  and state-7 completion, and the boundary between closed bounded execution and
  open whole-core ownership.

- Updated the Type 4 execution, memory, wait-state, cycle, confidence,
  verification, synthesis, and backlog records to distinguish the closed
  bounded native client from still-open whole-core ownership and event timing.

- Closed original Type 4 field placement, memory-only AMF-zero behavior,
  cycle-start/cycle-end ordering, read-collision rule, and legal old-value
  write overlap from the 1989 primary manual, and recorded the bounded waited
  logical execution evidence while keeping native phases and whole-core event
  arbitration explicitly open.

- Distinguished the now-attached bounded Type 12 native read/write path from
  still-open whole-core DM/PM ownership, event arbitration, BR/BG, and analog
  I/O timing throughout memory, cycle, wait-state, DAG, confidence, synthesis,
  and verification status.

- Distinguished the attached Type 2 native write path from the still-logical
  Type 12 path throughout the memory, cycle, wait-state, interface, confidence,
  verification, and synthesis records.

- Transcribed the original DM state-edge table and Figure 5.7 state-seven
  extension notation into a machine-readable native-interface contract and
  updated timing/interface status without claiming electrical-delay closure.

- Recorded the bounded Type 13 state-8 issue/state-7 commit contract in the
  memory, multifunction, pipeline, external-interface, instruction-cycle, and
  PM-cycle specifications and in the cycle-model ADR. Ordinary fetch, other PM
  owners, BR/BG, HALT/interrupt arbitration, and analog timing remain explicit
  nonclaims.

- Bounded the original cache monitor's observable contract to one contiguous
  up-to-16-word PM region with low-four-bit indexing, discontinuity restart,
  and circular oldest replacement using original pp. 4-26–4-30. Hidden
  ahead/behind encodings, self-modifying PM, and unified event arbitration
  remain OQ-008.
- Closed the original Type 13 field partition, PM read/write packing,
  old-value parallel semantics, PM-read collision restriction, fixed PM data
  action, same-cycle cached-next-fetch completion, and exactly one recovery
  fetch after a miss or forced fetch with exact-device citations. Connected
  the standalone monitor for real hit/data selection, ordinary/recovery fills,
  and explicit ownership; attachment to the separate native PM phase
  controller and whole-core event arbitration remain open under OQ-008.
- Closed the original Type 12 field partition, old-value parallel semantics,
  read-collision restriction, logical DM bus ordering, completion-only DAG
  post-modification, and DMACK wait extension with exact-device citations;
  physical sub-cycle pins and whole-core PM/event arbitration remain open.
- Closed the original Type 23 DIVQ add/subtract selection, quotient-bit
  recurrence, operand set, one-cycle boundary, and non-AQ status preservation;
  retained Appendix B quotient correction as software-visible sequence
  behavior rather than inventing a primitive-instruction correction.
- Closed the original Type 24 DIVS state transformation, operand set, one-cycle
  boundary, and non-AQ status preservation with exact-device citations; added
  SC-014 for the conflicting later-device flag description.

- Established primary-source precedence, clean-room rules, clock/reset policy,
  signedness policy, verification expectations, and provenance requirements.
- Added first-pass original-device programmer, compute, DAG, sequencer,
  bus/timing, scope/matrix, and Hard Drivin' host/SIM/SOM/interrupt/PAL notes
  with explicit confidence boundaries.
- Closed the condition-field encoding and predicate table while leaving
  counter update, loop-stack, and instruction timing explicitly open.
- Closed original Type 18 AS/OL/BR/SR bit placement and action semantics,
  explicitly excluding later timer, GO, and multiplier-placement controls.
- Closed original Type 21 G/I/M bit placement, all same-DAG selector mappings,
  corresponding-L selection, no-memory-access behavior, and cycle-end
  selected-I writeback. The later Cross-Software wording is retained only as
  corroboration, and unsupported circular configurations remain explicitly
  unclaimed.
- Closed original Type 17 field placement and register-direction legality from
  the original REG table and SSTAT read-only rule, then composed bounded
  computational/DAG/status/PX/CNTR/count-stack execution. OQ-016 narrow
  status-source extension remains open and visibly provisional rather than
  being promoted by implementation.
- Closed original Type 6 `0100 DATA[19:4] DREG[3:0]` placement, full-width
  immediate semantics, one-cycle selected-bank writeback, no PM/DM data
  transfer, exact SE/MR2 storage behavior, and MR1-to-MR2 sign-fill side effect
  from the original manual.
- Closed the source-supported Type 15 LSHIFT/ASHIFT immediate subset: SF/XOP/
  exponent placement, signed count, seven X operands, old-SR OR feedback,
  cycle-end selected-bank SR writeback, SE/status preservation, and no PM/DM
  data transfer. SF 8–15 and unavailable XOP `001` remain explicitly
  unsupported pending original-tool or hardware evidence.
- Closed the source-supported Type 8 ALU/MAC-plus-DREG packet boundary: exact
  field placement, one-cycle unconditional execution, cycle-start reads,
  cycle-end atomic writes, ALU/MAC operand and feedback maps, and no PM/DM data
  transfer. Same-destination writes remain fail-closed under OQ-014, and the
  AMF-zero mismatch between the Type 8 requirement and the Appendix A no-op
  table remains fail-closed under OQ-022.
- Closed original Type 9 field placement and action semantics: the standard
  COND predicate reads cycle-start status/NOT CE, true nonzero-AMF words commit
  one ALU/MAC result plus selected ASTAT fields at cycle end, false words
  preserve state for the same one-cycle boundary, AMF zero is a documented
  no-operation, and the format performs no PM-data or DM transfer.
- Closed the source-backed Type 10 direct-transfer boundary: exact field
  placement, 14-bit direct targets, condition-false PC+1, taken CALL PC+1
  stacking, authentic PC reset, and JUMP NOT CE counter transitions. CALL NOT
  CE remains explicitly fail-closed under OQ-012, and active-loop/fetch/
  interrupt/bus timing remains outside the bounded slice.
- Closed original Type 20 field placement and bounded action semantics: false
  returns advance PC+1 without stack actions, taken RTS pops PC, taken RTI
  simultaneously pops PC/status and restores ASTAT/MSTAT/IMASK, and return
  NOT CE never mutates CNTR/count-stack state. Physical empty-pop effects,
  active-loop attachment, interrupt entry/vectoring, fetch, and bus timing
  remain explicit gaps.
- Closed original Type 22 field placement, phase timing, and external
  handshake semantics: false TRAP advances to PC+1; true TRAP asserts at the
  state-7/state-8 boundary and halts in state 8; recognized HALT clears TRAP;
  HALT release resumes at PC+1; and TRAP NOT CE does not mutate CNTR. General
  HALT synchronization and BR/BG/interrupt/loop arbitration remain explicit
  gaps. A separate controller now closes bounded PM bus pin phases without
  claiming Type 22/fetch ownership attachment.
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
- Recorded pinned MAME's omission of original Type 22 TRAP as SC-013 and kept
  the original ADI manual authoritative for the exact device.
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

- Type 1 action selection is source-closed and exhaustive, but architectural
  state execution, cache recovery, and native dual-bus attachment are not
  implemented. OQ-023 withholds a guess about PM address/strobe/data behavior
  while DMACK extends the simultaneous DM transaction.

- Type 5 action legality, selected-bank compute, DAG2 postmodify, PX effects,
  cache recovery, and native PM phases are source-bounded, but whole-core PM
  ownership, fetch/control-event arbitration, hidden cache cases, and physical
  hardware comparison remain unattached.

- Type 4 now has selected-register/DAG state, waited logical DM execution, and
  a separately verified native eight-state attachment, but fetch, shared-DM
  ownership, and control events are not attached.

- Type 2, Type 3, Type 4, and Type 12 are independently attached to the native
  DM controller,
  but no whole-core owner selects among them or coordinates simultaneous PM,
  fetch, control-event, interrupt, HALT, and BR/BG activity.

- The exact original ADSP-2100 Cross-Software manual, evaluation-board manual,
  independent data-sheet revisions, and errata remain unavailable. Appendix A
  bit placement is complete, but semantic extraction remains incomplete.
- No instruction-completeness, external-cycle, bus, interrupt, or Hard Drivin'
  compatibility claim is complete. Type 26 action decode and bounded stateful
  execution are verified, but fetch/PC, automatic-flow, interrupt/RTI, and bus
  integration are not connected.
- Register/status instruction-decode connectivity, ICNTL consumer wiring,
  integrated multi-class PC/fetch connectivity, status-stack interrupt-entry
  arbitration, architectural SSTAT reads, narrow status reads, and
  interrupt recognition/cycle integration are not implemented. Sequencer and
  MSTAT consumer wiring exists only in bounded integration slices, not a
  whole instruction execution core.
- Type 12 now supplies verified logical DM transactions and wait stability,
  but not a native active-low state-phase interface, PM fetch concurrency,
  interrupt/BR/HALT latching during waits, or whole-core instruction issue.
- Type 13 now supplies cache-integrated logical PM data/recovery transactions,
  and a bounded client now attaches them to the native active-low PM phase
  interface, but no whole-core instruction/fetch owner or multi-class PM arbiter
  exists.
  The exact hidden ahead/behind counter encoding, self-modifying PM behavior,
  and branch/loop/interrupt/HALT/BR arbitration remain unresolved under OQ-008.
- Open-source synthesis and formal tools are not installed in this environment.
- Type 8 AMF-zero legality and same-destination results are unresolved and are
  rejected rather than assigned invented behavior. Its standalone combined
  compute/register slice also does not meet 50 MHz without internal phase
  scheduling; the successful 45.45 MHz unit constraint is not target closure.

[Unreleased]: https://github.com/birdybro/adsp-2100_sv/compare/HEAD...HEAD
