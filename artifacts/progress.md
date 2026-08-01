# Project progress

**Updated:** 2026-08-01

**Latest verified engineering commit:** `04084b3`

**Current milestone:** architecture extraction, executable model, and
source-backed compute/address-generation/register/status-storage blocks plus
bounded semantic instruction decode including Type 4 native-DM execution and
Type 5 logical/cache/native-PM execution,
exhaustive Type 1 dual-read action selection,
exhaustive Type 3 direct-DM state/native execution,
exhaustive Type 7 non-data-register immediate state execution,
bounded steady-state NOP/Type 6/Type 7/Type 8/Type 9/Type 10/Type 14/Type 15/Type 16/
Type 17/Type 18/Type 21/Type 23/Type 24/Type 25/Type 26 ordinary-fetch ownership with Type 8
ALU/MAC-plus-DREG and Type 9 ALU/MAC,
Type 14 parallel move/shifter, Type 15/16 shifter/status, Type 26 manual stack,
Type 23 divide-
quotient, Type 24 divide-sign, Type 25 conditional MR, and Type 21 DAG actions
attached directly to the shared architectural state,
normal-operation BR/BG request/grant/release/restart control attached to that
bounded linear fetch owner, ordinary-fetch HALT recognition/stop/restart
attached separately to that owner, standalone PM-data HALT forced-fetch
scheduling attached independently to the bounded Type 5 and Type 13
native-PM owners,
fail-closed shared native-PM transaction ownership for ordinary fetch and the
Type 5/Type 13 descriptor classes plus normal BR/BG sequencing on that shared
interface with bounded ordinary-fetch, Type 5/cache, and Type 13/cache clients
attached in separate compositions,
logical DM/PM transactions, a Type 13/
cache client attached to native PM pin phases, and Type 2, Type 3, Type 4, plus Type 12 clients
attached to native DM pin phases

**Release status:** research/implementation in progress; not instruction-,
cycle-, or Hard Drivin'-complete

## Completed increments

- all 507,904 source-closed original Type 10 direct JUMP/CALL words attached
  to the native ordinary-fetch owner and shared PC/CNTR/stack state. The owner
  issues a taken target or false-path PC+1 at state 8 and commits that selected
  PC plus CALL or JUMP NOT CE effects only at routed state-7 completion.
  Invalid CE context and all 16,384 CALL NOT CE words fail closed before issue.
  A fetched CALL followed by Type 26 POP PC proves the return address survives
  in shared PC-stack state. Twenty-eight tests and 442,330 model/RTL phase
  clocks pass; the BR/BG, retained-fetch/shared-PM/BR-BG, and HALT compositions
  remain green across 50,003 clocks each. The full `make test` regression with
  693 Python checks passes. Strict lint and all 73 formal recipes pass
  assertion syntax; SymbiYosys/Yosys are unavailable. Fully constrained
  Cyclone V fits have zero unconstrained paths. At 25 ns the 3,518-ALM private
  and 3,528-ALM BR/BG owners close with +0.062/+0.159 ns worst setup; the
  3,511-ALM HALT owner misses by 0.045 ns at 39.93 MHz. At 20 ns the 3,628-ALM
  retained/shared-PM owner misses by 4.349 ns at 41.07 MHz. All use two DSPs
  and no RAM. Active loops, cache ownership/invalidation, interrupts,
  reset-first-fetch, Types 19/20 attachment, and timing optimization remain;

- at the Type 26 checkpoint, all 32 original manual stack-control words were
  attached to native
  ordinary-fetch retirement and the shared architectural-state owner. Valid
  fetched status push/pop restores cycle-start ASTAT/MSTAT/IMASK, count pop
  restores the prior CNTR, and empty PC/loop pops preserve state under OQ-013.
  The 25-test owner suite traverses every payload across 442,383 deterministic
  model/RTL phase clocks; valid PC/loop pops were then established only by the
  standalone 50,015-cycle slice. The superseding Type 10 increment above now
  adds one fetched valid PC-pop context; loop context remains standalone-only.
  BR/BG, retained-fetch/shared-PM/BR-BG, and HALT compatibility flows
  each pass 50,003 clocks. Strict lint and 73 formal recipes pass syntax
  checking; SymbiYosys/Yosys are unavailable. Fully constrained Cyclone V
  fits have zero unconstrained paths. At 25 ns the 3,483-ALM BR/BG and
  3,485-ALM HALT compositions close with +0.062/+0.456 ns worst setup; the
  3,464-ALM private owner narrowly misses by 0.504 ns at 39.43 MHz, and the
  stricter 20 ns 3,579-ALM retained/shared-PM owner misses by 5.739 ns at
  39.55 MHz. All use two DSPs and no RAM; automatic/interrupt arbitration,
  valid fetched PC/loop context, and timing optimization remain open;

- all 32 original Type 21 MODIFY words attached to the shared architectural-
  state owner and native ordinary-fetch phases. A dedicated execution read
  selector supplies cycle-start I/M/L values independently of the debug probe;
  only the selected I commits at state 7, with no M/L, status, PM-data, or DM
  side effect. The 24-test owner suite and 442,405 deterministic model/RTL
  clocks cover every DAG/I/M selection and positive/negative linear/circular
  updates; the standalone 50,124-clock Type 21 comparison and all dependent
  Type 17/3/6/7 tests remain passing. BR/BG, retained-fetch/shared-PM/BR-BG,
  and HALT compatibility flows each pass 50,003 clocks. Strict lint is clean,
  and all 73 formal recipes pass syntax lint; SymbiYosys/Yosys are unavailable.
  The constrained 25 ns private-PM and private-PM/BR-BG Cyclone V fits close at
  3,365/3,417 ALMs and +0.359/+0.477 ns worst setup respectively. The 25 ns
  HALT fit uses 3,406 ALMs but misses setup by 0.628 ns at 39.02 MHz; the 20 ns
  retained-fetch/shared-PM/BR-BG owner uses 3,485 ALMs and misses by 4.322 ns
  at 41.12 MHz. All
  four have two DSPs, no RAM, and zero unconstrained paths; timing and shared
  Type 8/9 compute-datapath optimization remain open;

- fetched all 476,672 source-closed original Type 8 ALU/MAC-plus-DREG packets
  attached to the shared architectural-state owner and native ordinary-fetch
  phases. A stateless action producer uses three cycle-start DREG reads plus
  AF/MF/MR/ASTAT/MSTAT consumers and drives atomic computation, status, move,
  PC, and next-word retirement. The owner fails closed for all 16,384 AMF-zero
  words and 31,232 result/move destination collisions. One directed old-value
  test and the 23-test, 442,392-clock integrated model/RTL flow traverse every
  compute-field tuple and every move source/destination pair in both banks;
  the standalone 983,386-cycle comparison remains exhaustive over all legal
  words in both banks. Shared-PM/BR-BG and HALT compositions remain green,
  strict lint passes, all 689 Python checks pass, and all 73 formal recipes
  pass assertion syntax lint; SymbiYosys/Yosys remain unavailable. The fully
  constrained 25 ns Cyclone V owner fit uses 3,219 ALMs, 1,204 registers, two
  DSPs, no RAM, +0.255 ns worst setup, +0.168 ns worst hold, 40.41 MHz worst
  slow-corner Fmax, and zero unconstrained paths. Its 20 ns shared-PM/BR-BG
  composition fits at 3,381 ALMs and 1,256 registers but misses setup by 5.223
  ns; the duplicated Type 8/Type 9 compute datapath is recorded optimization
  debt, and reset-first-fetch, control flow, interrupts, and unified PM/cache/
  event ownership remain open;

- fetched all sixteen source-closed original Type 24 DIVS forms attached to
  the shared architectural-state owner and native ordinary-fetch phases. A
  fourth register-file read port supplies the independent upper-dividend read;
  two new directed tests cover every divisor, both AY1/AF upper forms, both
  banks, and dependent DIVS-to-DIVQ retirement. The 22-test owner suite and
  443,607 model/RTL clocks pass, as do the unchanged 50,003-clock BR/BG,
  shared-PM/BR/BG, and HALT compositions. Strict lint, all 688 Python checks,
  and all 73 formal-recipe syntax checks pass; SymbiYosys/Yosys remain
  unavailable. A fully constrained 25 ns Cyclone V fit uses 2,759 ALMs, 1,191
  registers, one DSP, no RAM, +1.115 ns worst setup, +0.171 ns worst hold,
  41.87 MHz worst slow-corner Fmax, and zero unconstrained clocks, ports, or
  paths. The stricter 20 ns shared-PM/BR-BG fit succeeds at 2,873 ALMs and
  1,220 registers but misses worst setup by 3.541 ns; reset-first-fetch,
  control flow, interrupts, and unified PM/cache/event ownership remain open;

- fetched all eight original Type 23 DIVQ forms attached to the shared
  architectural-state owner and native ordinary-fetch phases: two new directed
  tests cover every divisor source in both selected banks, both old-AQ
  add/subtract paths, and a dependent following iteration. The complete
  20-test owner suite and 443,740 model/RTL clocks pass, as do the unchanged
  50,003-clock BR/BG, shared-PM/BR-BG, and HALT compositions. Strict lint and
  all 686 Python checks pass. A fully constrained 25 ns Cyclone V fit uses
  2,742 ALMs, 1,182 registers, one DSP, no RAM, +2.073 ns worst setup, +0.164
  ns worst hold, 43.62 MHz worst slow-corner Fmax, and zero unconstrained
  clocks, ports, or paths. The stricter 20 ns shared-PM/BR-BG fit succeeds at
  2,856 ALMs and 1,233 registers but misses worst setup by 4.494 ns; Type 24's
  second execution read path, reset-first-fetch, control flow, interrupts, and
  unified PM/cache/event ownership remain open;

- fetched exact Type 25 conditional MR saturation attached to the shared
  architectural-state owner and native ordinary-fetch phases: two new
  directed tests cover both signs/banks and MV false, while the complete
  18-test owner suite and 443,712 model/RTL clocks retain exhaustive Type
  9/14/15/16/17/18 coverage and add atomic state-7 MR/PC/next-word retirement.
  The pre-existing nine-test, 50,112-cycle standalone Type 25 evidence remains
  passing. Strict lint is clean, and a fully constrained 25 ns Cyclone V fit
  uses 2,702 ALMs, 1,175 registers, one DSP, no RAM, +1.564 ns worst setup,
  +0.164 ns worst hold, 42.67 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths; OQ-015 interrupt adjacency,
  reset-first-fetch, control flow, and unified PM/cache/event ownership remain
  open;

- fetched Type 14 shifter-plus-DREG execution attached to the shared
  architectural-state owner and native ordinary-fetch phases: 16 directed
  tests and 443,794 model/RTL clocks traverse all 25,648 canonical packets
  while proving cycle-start reads and atomic noncolliding move/shifter/status
  retirement; bit-15-one, unavailable-XOP, and destination-collision words
  remain fail-closed. Separate 50,003-clock BR/BG, shared-PM/BR-BG, and HALT
  comparisons retire 596, 490, and 655 Type 14 packets while preserving
  request retention and control sequencing. Strict lint and all 73 formal
  recipes syntax-check, and a fully constrained 25 ns Cyclone V fit uses
  2,725 ALMs, 1,180 registers, one DSP, no RAM, +2.169 ns worst setup,
  +0.166 ns worst hold, 43.80 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths; OQ-021, reset-first-fetch, loops,
  interrupts, control transfers, and unified PM/cache/event ownership remain
  open;

- fetched Type 15 immediate-shift and Type 16 conditional-shift execution
  attached to the shared architectural-state owner and native ordinary-fetch
  phases: 15 directed tests and 177,167 model/RTL clocks traverse all 14,336
  supported Type 15 words and all 1,792 supported Type 16 words while
  preserving selected-bank, old-SR OR, condition-false, and function-selected
  SR/SE/SB/SS semantics; separate 50,003-clock BR/BG, shared-PM/BR-BG, and
  HALT comparisons respectively retire 1,305, 1,050, and 1,414 fetched
  shifter words while preserving control sequencing; strict lint passes, and
  a fully constrained 25 ns Cyclone V fit uses 2,029 ALMs, 1,180 registers,
  one DSP, no RAM, +3.388 ns worst setup, +0.166 ns worst hold, 46.27 MHz worst
  slow-corner Fmax, and zero unconstrained clocks, ports, or paths; unsupported
  Type 15 SF/XOP and Type 16 XOP words still fail closed, and reset-first-fetch,
  loops, interrupts, control transfers, and unified PM/cache ownership remain
  open;

- fetched Type 9 conditional ALU/MAC execution attached to the shared
  architectural-state owner and native ordinary-fetch phases: 14 directed
  tests and 53,662 model/RTL clocks traverse every AMF/condition combination;
  separate 50,003-clock BR/BG, shared-PM/BR-BG, and HALT comparisons cover 446,
  368, and 469 Type 9 no-op retirements while preserving control sequencing;
  strict lint and 73 formal recipes syntax-check, and a fully constrained
  25 ns Cyclone V fit uses 1,327 ALMs, 1,196 registers, one DSP, no RAM,
  +2.707 ns setup, +0.167 ns worst hold, 44.86 MHz worst slow-corner Fmax, and
  zero unconstrained paths; reset-first-fetch, active loops, control transfers,
  interrupts, and unified PM/cache ownership remain open;

- reusable shared architectural-state owner extracted from the bounded Type
  17 slice without changing its public behavior: it exclusively holds both
  computational banks, both DAG register sets, status/control, CNTR/count
  stack, SSTAT stack fragments, and PX behind the complete general selector;
  44 focused model tests, 210,084 Type 17/3/6/7 RTL clocks, and the existing
  53,985/50,003/50,003-clock linear/private-PM, linear/BR-BG, and retained-
  fetch/shared-PM regressions pass, strict lint is clean, and the re-fit uses
  808 ALMs/892 registers/no RAM or DSP at 50 MHz with +5.503 ns setup,
  +0.168 ns worst multicorner hold, 68.98 MHz worst slow-corner Fmax, and zero
  unconstrained paths; the owner now exposes and directly tests parallel
  DREG, ALU/MAC/shifter, DAG-I, automatic-status, and mode-control actions
  with cycle-start/cycle-end visibility, bank isolation, conflict
  preservation, and reset suppression; additional fetched classes and unified
  cache/PM client state remain open;

- extracted retained ordinary-fetch architectural client attached to the
  shared PM owner and normal BR/BG composition, while the prior linear-core
  API now wraps the same client with a private PM controller; six directed
  tests and 50,003 model/RTL clocks cover 4,247 fetch accepts, 781 retained
  retries/collisions, 4,246 routed completions, 62 raw Type 5 and 32 raw Type
  13 accepts, 94 BR handshakes, and 3,161 masked grant clocks, with a
  machine-readable contract, formal/Yosys recipes, and a fully constrained
  1,031-ALM/1,072-register/no-RAM-or-DSP Cyclone V fit; the unified three-
  client/cache/HALT composition and sourced cross-event priority remain open;

- bounded Type 5/cache architectural client attached to the shared PM owner
  and normal BR/BG composition, retaining rejected PM-data/recovery
  descriptors, routing only Type 5 completion, and filling its cache from
  completed ordinary fetches; six directed tests and 50,063 model/RTL clocks
  cover 2,742 accepts, 713 retries, 1,371 data completions, 290 fetch fills,
  322 isolated raw Type 13 completions, 78 BR handshakes, and 2,727 masked
  grant clocks, with a fully constrained 1,923-ALM/1,756-register/one-DSP
  Cyclone V fit;

- bounded Type 13/cache architectural client attached to the shared PM owner
  and normal BR/BG composition, retaining rejected PM-data/recovery
  descriptors for later state-8 retry, routing only Type 13 completion back to
  the client, and filling the same cache from completed ordinary fetches; six
  directed tests and 50,061 independent-model/RTL clocks cover 2,783 accepted
  Type 13 descriptors, 752 retries, 1,391 data completions, 286 ordinary-fetch
  fills, 286 raw Type 5 completions, 88 BR handshakes, and 3,126 masked grant
  clocks, with machine-readable/formal/Yosys collateral and a fully
  constrained 2,089-ALM/1,646-register Cyclone V fit; ordinary fetch and Type
  5 remain raw requesters and whole-core event priority remains open;

- primary-backed normal BR/BG composition above the shared ordinary-fetch/
  Type 5/Type 13 PM selector, completing an active owner after recognition,
  inhibiting later descriptor capture, masking every PM driver during grant,
  and accepting one held request on resume; six directed tests and 50,002
  independent-model/RTL clocks cover all owners, 111 full handshakes, 80
  post-recognition completions, 1,417 blocked requests, 3,536 masked grant
  clocks, 79 resume accepts, 530 collisions, and 1,264 accepted Type 5/13
  instruction-access descriptors, with a machine-readable
  contract, formal/Yosys recipes, and a fully constrained 190-ALM/84-register
  Cyclone V fit; the Type 13 client is attached separately above, while raw
  fetch/Type 5 retry storage, DM composition, and event priority remain open;

- bounded shared-PM transaction owner for ordinary fetch, Type 5 PM data, and
  Type 13 PM data descriptors, accepting exactly one request at state 8-to-1,
  retaining the owner through state-7 completion/relinquishment, routing
  events one-hot, and rejecting conflicts/off-boundary attempts without an
  undocumented priority; eight directed tests and 50,007 independent-model/
  RTL clocks cover 3,248 completions, 1,097 collisions, 1,346 out-of-phase
  attempts, 2,576 owner switches, 611 relinquished active holds, and 1,113
  accepted Type 5/13 instruction-access descriptors, with a
  machine-readable contract, formal/Yosys recipes, and a fully constrained
  160-ALM/77-register Cyclone V fit; one Type 13 client is attached in the
  composition above and full event priority remains unconnected;

- primary-backed bounded Type 5/cache/native-PM/HALT composition: a state-3
  recognition converts an issue-time cache hit into late recovery, commits
  ALU/MAC/PM/PX/DAG2 effects once, accepts one external fetch at the next
  state-8 boundary, fills the cache, stops after its state-7 completion, and
  resumes only with HALT inactive and DMACK high; five directed tests and
  50,126 deterministic independent-model/RTL clocks cover 197 hit overrides/
  forced fetches, 1,996 data completions, 387 stops/resumes, 196 blocked
  releases, and 577 held clocks, with formal/Yosys recipes and a fully
  constrained 1,946-ALM/1,768-register/one-DSP Cyclone V fit; shared event/PM
  arbitration remains open;
- primary-backed bounded Type 13/cache/native-PM/HALT composition: a state-3
  recognition latches recovery into the active Type 13 descriptor, overrides
  an issue-time cache hit, commits shifter/PM/PX/DAG effects once, accepts one
  external fetch at the next state-8 boundary, fills the cache, stops after
  its state-7 completion, holds driven outputs, and resumes only with HALT
  inactive and DMACK high; five directed tests and 50,124 deterministic
  independent-model/RTL clocks cover 210 hit overrides/forced fetches, 397
  stops/resumes, 209 blocked releases, and 580 held clocks, with formal/Yosys
  recipes and a fully constrained 2,094-ALM/1,655-register Cyclone V fit;
  shared event/PM arbitration remains open;
- primary-backed standalone HALT sequencing for ordinary and PM-data cycles:
  a PM-data recognition completes the data cycle, emits one forced external-
  fetch issue at the following state-8 boundary, and stops after the fetch;
  eight directed tests and 50,033 independent-model/RTL clocks cover 332
  ordinary and 335 PM-data recognitions, 335 forced issues, 667 stops, 665
  releases, 291 blocked releases, and 2,269 held clocks, with a machine-readable
  contract, formal recipe, Yosys flow, and fully constrained 26-ALM/6-register
  Cyclone V fit; Type 5 and Type 13 are attached separately, while cross-event
  priority remains open;
- primary-backed bounded ordinary-fetch HALT composition with active-low
  state-3 recognition, latched short requests, current-fetch completion,
  driven and stable stopped state-8 PM outputs, and DMACK-qualified
  state-8-to-state-1 restart; seven directed tests and 50,003 independent-
  model/RTL clocks cover 790 complete recognize/stop/resume sequences, 161
  DMACK-low blocked releases, and 742 held clocks, with a machine-readable
  contract, formal invariants, Yosys flow, and a requalified 916-ALM/
  1,026-register Cyclone V fit; PM-data scheduling and the Type 5/Type 13 owner
  attachments are verified separately, while HALT during BG/DM waits,
  TRAP/BR/interrupt/reset arbitration, and analog synchronization remain open;
- bounded structural composition of the ordinary linear PM owner and normal
  BR/BG controller, preserving the current fetch after state-3 recognition,
  inhibiting only the next issue, masking every PM output enable during grant,
  preserving state, and restarting at state 8-to-1 after release; five directed
  tests and 50,003 model/RTL clocks cover 93 complete handshakes, 5,375 retires,
  and 5,376 issues, with formal invariants, a Yosys flow, and a fully constrained
  898-ALM/1,041-register Cyclone V fit; all other PM/DM owners, cross-event
  composition, interrupts, reset-first-fetch, and analog timing remain open;
- primary-backed normal-operation BR/BG controller with active-low state-3
  recognition, complete-current/inhibit-next behavior, one-full-eight-state-
  cycle grant and release delays, all-bus-driver mask, state-8-to-state-1
  restart, separate asynchronous RESET-time native-pin wrapper, seven directed
  tests, 50,084 model/RTL clocks, formal invariants, a portable Yosys flow, and
  a fully constrained 27-ALM Cyclone V fit; whole-core PM/DM composition and
  analog input timing remain open;
- source-backed original RESET/logical-phase owner with rising-edge-only
  recognition, four-sample qualification, state-4/CLKOUT-low hold, exact
  second-rising-edge release to state 5, ordinary eight-state traversal,
  authentic invalid pre-RESET state, explicit fail-closed short-reset
  handling, six directed tests, 50,034 model/RTL clocks, formal invariants,
  a portable Yosys flow, and a fully constrained 26-ALM Cyclone V fit; PM
  initial-fetch strobes remain OQ-024;
- bounded steady-state native linear owner for NOP, legal Type 6/7, all 2,256
  legal Type 17 internal MOVE pairs, and every Type 18 MODE CONTROL word,
  executing at the current PC while the native PM controller fetches PC+1,
  with state-8 issue, state-7 atomic action/PC/next-word retirement,
  fail-closed unsupported words, thirteen directed checks, 53,985 differential
  clocks including every legal Type 17 pair and all 256 Type 18 encodings,
  an observable OQ-016 provisional-source retirement pulse, formal assertions,
  a machine-readable contract, and a fully constrained Cyclone V fit;
- required repository layout and autonomous-agent governance;
- lawful cache-only reference workflow with content and SHA-256 validation;
- initial source-precedence, exact-device, and cycle-model ADRs;
- original-versus-later-device feature-matrix first pass;
- original architecture/timing documentation framework;
- Hard Drivin' board-interface first-pass notes;
- complete 30-class mask inventory, all 106 diagrammed fields across 393
  variable bit positions, explicit unshown-reserved fallback, and one
  hand-verified NOP semantic fixture;
- complete original Type 4 action partition: 2,034,688 supported
  computation-plus-DM or memory-only words and 62,464 prohibited read
  collisions, with two manual-derived fixtures, independent model, exact RTL
  decoder, algebraic/raw toolchain paths, bounded formal assertions, and a
  fully constrained 53-ALM Cyclone V decoder fit; plus a bounded selected-bank
  ALU/MAC/DAG state model and RTL slice with arbitrary logical DMACK waits,
  old-value stores, atomic compute/read/I completion, 50,072 differential
  clocks, and a timing-clean 1,677-ALM/one-DSP Standard Fit; plus a separate
  six-test/50,082-clock native phase attachment and timing-clean
  1,693-ALM/1,226-register/one-DSP Standard Fit;
- complete original Type 5 action partition: 1,017,344 supported
  ALU/MAC-plus-PM or PM-only words and 31,232 prohibited read collisions, with
  two manual-derived fixtures, independent model, exact RTL decoder,
  algebraic/raw toolchain paths, bounded formal assertions, exhaustive 24-bit
  RTL traversal, and a fully constrained 51-ALM Cyclone V decoder fit; plus
  bounded selected-bank ALU/MAC, PX/DAG2, cache-hit/recovery, and native-PM
  execution with 26 directed logical/cache/native tests, 50,071 logical and
  50,083 native model/RTL clocks, three base formal harnesses, and fully
  constrained logical/cache/native Cyclone V fits; a fourth HALT-composition
  harness plus five tests and 50,126 clocks covers 197 late hit overrides and
  forced fetches without action replay, and its constrained fit uses 1,946
  ALMs, 1,768 registers, and one DSP; whole-core ownership remains open;
- complete original Type 1 action selection: all 4,194,304 words decode as
  source-closed fixed-DAG1-DM/DAG2-PM dual reads with DD/PD destinations,
  cycle-start computation operands, implicit AR/MR results, AMF-zero dual
  fetch, and cycle-end loads; with two primary-derived fixtures, independent
  Python, original algebraic/raw toolchain paths, exhaustive RTL traversal,
  formal assertions, and a fully constrained 53-ALM Cyclone V decoder fit;
  state/cache/native dual-bus attachment remains OQ-023;
- complete original Type 3 action selection: all 2,097,152 words partition
  into 770,048 direct reads, 786,432 direct writes, and 540,672 unsupported
  reserved/read-only-destination words, with independent model/database
  decoders, four hand fixtures, algebraic/raw tools, exhaustive RTL, formal
  assertions, and a fully constrained 46-ALM Cyclone V decoder fit; plus a
  bounded complete-general-register state/logical-DM slice and native-DM
  attachment with 14 directed tests, 50,151 logical and 50,077 native
  differential clocks, two stateful formal harnesses, and fully constrained
  849-ALM logical plus 825-ALM native Cyclone V fits;
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
- exact Type 7 immediate-to-non-data-register semantics for 507,904 supported
  and 540,672 fail-closed words, with independent database/model decode,
  hand-derived fixtures, algebraic/raw assembler/disassembler support,
  exhaustive Python/RTL partitioning, shared exact-width state, selected-bank
  SB and CNTR/count-stack effects, 50,299 differential clocks, a formal
  harness, and a fully constrained Cyclone V fit;
- bounded top-level model integration for NOP, legal Type 6/7, known-source
  legal Type 17 internal MOVE, and all Type 18 MODE CONTROL instructions:
  the executing-PC state action, wrapped PC increment, and overlapped PC+1
  program fetch now share one fixed instruction boundary; synthetic ordinary
  PM-fetch waits and active-loop contexts fail closed;
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
- composed Type 13/cache ownership with pre-cycle real-word lookup, same-cycle
  hit selection, miss/forced-fetch recovery fill, ordinary external fetch
  fill, explicit conflict priority, independent model, portable RTL, formal
  invariants, and constrained Cyclone V synthesis;
- source-backed native PM pin-phase model/RTL with state-8-to-1 descriptor
  capture, PMA/PMDA/PMS states 1–8, active-low PMRD/PMWR states 4–7,
  state-7 read sampling, PMD write drive states 5–8, back-to-back PMS
  continuity, and externally directed bus-output masking;
- source-backed native DM pin-phase model/RTL with state-8-to-1 descriptor
  capture, DMA/DMS states 1–8, active-low DMRD/DMWR states 4–7, DMACK
  qualification at 6–7, DMD read sample at 7–8, write drive states 5–8,
  complete eight-substate state-seven extensions, back-to-back DMS continuity,
  and externally directed bus-output masking;
- bounded Type 2/native-DM attachment with state-8-to-state-1 old-I/raw-data
  capture, complete-cycle DMACK extension, state-7-to-state-8 completion-only
  selected-I postmodify, late-ACK rejection, phase-conflict reporting, and
  relinquishment masking;
- bounded Type 12/native-DM attachment with state-8-to-state-1 old shifter,
  DREG, and DAG capture; sourced read/write pin phases; complete-cycle DMACK
  extension; state-7-to-state-8 DMD sampling and atomic shifter/DREG/I commit;
  phase-conflict reporting; and relinquishment masking;
- bounded Type 13/cache/native-PM attachment with state-8-to-state-1
  old-value capture, state-7-to-state-8 architectural commit, issue-time cache
  hit retention, back-to-back miss recovery, phase-hold stability, and
  fail-closed off-boundary controls;
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
- independent exact-width/reset/image-loading/reserved-rejection model
  foundation with bounded NOP, Type 6/7, and Type 18 linear fetch/execute
  integration;
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
- 693 distinct Python unit checks plus manifest/hash verification;
- 50,061 Type 13/shared-PM/BR-BG model/RTL clocks cover retained collision
  retries, PM-data and recovery completion isolation, ordinary-fetch cache
  fill, raw Type 5 isolation, PMDA-low recovery fetch, and grant masking;
- 50,002 shared-PM-owner/BR-BG model/RTL clocks cover all three descriptor
  owners, 111 handshakes, active-transaction completion after recognition,
  capture inhibition, native output masking, and resume-edge acceptance;
- all 16,777,216 program words pass independent class-decode comparison:
  15,473,178 shown-class and 1,304,038 reserved-unshown words;
- all 4,194,304 Type 1 words decode as source-closed actions in independent
  Python and exhaustive RTL; six model/schema checks, two primary-derived
  fixtures, 1,024 representative dual-read-only forms, 685 uniquely spellable
  computation forms, raw aliases, and a contemporary listing cross-check pass;
- all 2,097,152 Type 2 words decode to exact immediate/G/I/M fields in Python
  and exhaustive RTL traversal; every other 24-bit word is action-free;
- 50,035 Type 2 model/RTL clocks cover both DAGs, every I/M selection, DAG1
  bit reversal, immediate and multi-clock DMACK completion, stable captured
  address/data, completion-only I updates, reset, conflicts, and invalid state;
- 50,027 Type 2/native-DM model/RTL clocks cover state-8 descriptor issue,
  qualified state-7 completion, complete-cycle wait extensions, late-ACK
  rejection, old-value stability, off-boundary controls, and relinquishment;
- 50,064 Type 12/native-DM model/RTL clocks cover state-8 descriptor issue,
  read/write phases, old-DREG store data, qualified state-7 read sampling,
  atomic shifter/DREG/I completion, complete-cycle waits, invalid read data,
  reset, off-boundary controls, and relinquishment;
- all 32 Type 26 words produce their exact SPP/CP/LP/PP actions and every
  other 24-bit word produces no stack-control action in exhaustive RTL
  simulation;
- all 4,096 Type 17 class words partition into exactly 2,256 legal moves and
  1,840 reserved/read-only-destination subencodings; all other program words
  are action-free in exhaustive RTL simulation; all 4,512 legal pair/bank
  executions and 59,430 stateful model/RTL cycles pass; the bounded linear
  owner additionally executes all 2,256 legal pairs after complete state
  initialization and exposes OQ-016 narrow-source use at retirement;
- all 1,048,576 Type 6 words decode to exact immediate/DREG fields in both
  Python and exhaustive RTL traversal; 50,204 selected-bank model/RTL cycles
  pass with no PM-data or DM activity;
- all 1,048,576 Type 7 words partition in independent Python and exhaustive
  RTL into 507,904 legal non-data-register loads and 540,672 group-zero,
  reserved, or read-only-SSTAT destinations; 50,299 stateful model/RTL clocks
  cover all 31 legal destinations with no PM-data or DM activity;
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
  and conflict cases; the fetched owner additionally covers representative
  targets and every condition within 442,330 phase clocks, including selected-
  target issue, false PC+1, CALL/Type-26-pop context, and JUMP NOT CE retirement;
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
  address/data handling; the connected Type 13 boundary adds ten directed
  tests and 50,086 clocks for actual hit data, recovery fill, ordinary fill,
  forced fetch, replacement, reset, unknowns, and ownership conflicts; the
  native attachment adds five directed tests and 50,081 clocks for issue and
  completion edges, PM pin phases, held descriptors, hit capture, miss
  recovery, off-boundary rejection, and bus relinquishment;
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
  50,204 and the Type 7 slice adds 50,299; the Type 8 state slice adds 983,386,
  the Type 9 state slice adds
  283,996, the Type 10 state slice adds 554,412, the Type 11 state slice adds
  554,309, the Type 19 state slice adds 50,259, the Type 20 slice adds 50,254,
  the phase-aware Type 22 slice adds 50,168 clocks, the Type 23 slice adds
  50,081 cycles, the Type 24 slice adds 50,109 cycles, the Type 2 slice adds
  50,035 state/bus clocks, the Type 12 slice adds
  50,069 state/bus clocks, the Type 13 slice adds 50,070 state/cache/bus
  clocks, the standalone cache adds 50,028 clocks, and the connected Type 13/
  cache boundary adds 50,086 clocks, the native PM pin-phase boundary adds
  50,032 clocks, the native DM pin-phase boundary adds 50,039 clocks, and the
  Type 13/cache/native-PM attachment adds 50,081 clocks,
  the Type 5/cache/native-PM/HALT attachment adds 50,126 clocks,
  the bounded Type 6/7/8/9/10/14/15/16/17/18/21/23/24/25/26 linear owner adds 442,330 phase clocks,
  the linear-owner/normal-BR/BG composition adds 50,003 clocks across 86
  complete handshakes,
  the linear-owner/ordinary-fetch-HALT composition adds 50,003 clocks across
  788 stop/restart handshakes,
  the Type 2/native-DM attachment adds 50,027 clocks,
  the Type 12/native-DM attachment adds 50,064 clocks,
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
  paths, while the extracted-owner Type 17 state slice fits in 808 ALMs and
  892 registers with +5.503 ns setup, +0.168 ns hold, and no unconstrained
  paths; the Type 6 slice
  fits in 302 ALMs and 484 registers with +8.167 ns setup, +0.133 ns hold, and
  no unconstrained paths; the Type 7 slice fits in 572 ALMs and 886 fitted
  registers at 25 ns with +13.448 ns worst setup, +0.185 ns worst hold,
  86.57 MHz worst slow-100C Fmax, and no unconstrained paths; the Type 15 slice
  fits in 774 ALMs and 501 fitted
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
  the cache-integrated Type 13 boundary fits in 1,937 ALMs and 1,446 fitted
  registers with no RAM or DSP blocks, +2.615 ns setup, +0.166 ns worst
  multicorner hold, 57.52 MHz worst slow-corner Fmax, and no unconstrained
  paths against its 20 ns constraint;
  the native PM pin-phase controller fits in 112 ALMs and 71 fitted registers
  with no RAM or DSP blocks, +12.825 ns setup, +0.167 ns worst multicorner
  hold, 139.37 MHz worst slow-corner Fmax, and no unconstrained paths against
  its 20 ns constraint;
  the shared-PM-owner/BR-BG composition fits in 190 ALMs and 84 fitted
  registers with no RAM or DSP blocks, +11.053 ns worst setup, +0.167 ns worst
  multicorner hold, 111.77 MHz worst slow-corner Fmax, and zero unconstrained
  clocks, ports, or paths against its 20 ns constraint;
  the Type 13/cache/shared-PM/BR-BG attachment fits in 2,089 ALMs and 1,646
  fitted registers with no RAM or DSP blocks, +8.194 ns worst setup,
  +0.166 ns worst multicorner hold, 59.5 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths against its 25 ns constraint;
  the Type 5/cache/shared-PM/BR-BG attachment fits in 1,923 ALMs and 1,756
  fitted registers with one DSP and no RAM, +3.950 ns worst setup,
  +0.161 ns worst multicorner hold, 47.51 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths against its 25 ns constraint;
  the bounded linear owner fits in 885 ALMs and 1,020 fitted registers with no
  RAM or DSP blocks, +13.145 ns setup, +0.166 ns worst multicorner hold,
  84.35 MHz worst slow-corner Fmax, and no unconstrained paths against its
  25 ns constraint; its normal-BR/BG composition fits in 898 ALMs and 1,041
  fitted registers with no RAM or DSP blocks, +12.845 ns setup, +0.166 ns
  worst multicorner hold, 82.27 MHz worst slow-corner Fmax, and no
  unconstrained paths against 25 ns; its ordinary-fetch HALT composition fits
  in 916 ALMs and 1,026 fitted registers with no RAM or DSP blocks, +12.809 ns
  setup, +0.164 ns worst multicorner hold, 82.03 MHz worst slow-corner Fmax,
  and no unconstrained paths against 25 ns;
  the native DM pin-phase controller fits in 100 ALMs and 57 fitted registers
  with no RAM or DSP blocks, +11.895 ns worst setup, +0.169 ns worst
  multicorner hold, 123.38 MHz worst slow-corner Fmax, and zero unconstrained
  clocks, ports, or paths against its 20 ns constraint;
  the Type 2/native-DM attachment fits in 608 ALMs and 466 fitted registers
  with no RAM or DSP blocks, +2.590 ns worst setup, +0.159 ns worst
  multicorner hold, 57.44 MHz worst slow-corner Fmax, and zero unconstrained
  clocks, ports, or paths against its 20 ns constraint;
  the Type 12/native-DM attachment fits in 1,739 ALMs and 1,139 fitted
  registers with no RAM or DSP blocks, +1.262 ns worst setup, +0.167 ns worst
  multicorner hold, 53.37 MHz worst slow-corner Fmax, and zero unconstrained
  clocks, ports, or paths against its 20 ns constraint;
  the Type 13/cache/native-PM attachment fits in 2,055 ALMs and 1,648 fitted
  registers with no RAM or DSP blocks, +3.925 ns worst setup, +0.162 ns worst
  multicorner hold, 62.21 MHz worst slow-corner Fmax, and zero unconstrained
  clocks, ports, or paths against its 20 ns constraint;
  the Type 13/cache/native-PM/HALT attachment fits in 2,094 ALMs and 1,655
  fitted registers with no RAM or DSP blocks, +7.946 ns worst setup, +0.168 ns
  worst multicorner hold, 58.64 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths against its 25 ns constraint;
  the Type 5/cache/native-PM/HALT attachment fits in 1,946 ALMs and 1,768
  fitted registers with one DSP and no RAM, +3.651 ns worst setup, +0.166 ns
  worst multicorner hold, 46.84 MHz worst slow-corner Fmax, and zero
  unconstrained clocks, ports, or paths against its 25 ns constraint;
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
  Type 2 action/execution, Type 23, Type 24, standalone instruction-cache, and
  Type 13/cache-integration, native PM and DM phase/strobe, and the bounded
  Type 13, Type 2, Type 3, Type 4, and Type 12 native-attachment invariants, plus
  Type 4 action-decode and waited logical-execution plus Type 5 action,
  logical/cache/native execution invariants plus Type 1 and Type 3 action decode
  and Type 3 logical state execution plus exact Type 7 state execution and
  the bounded steady-state Type 6/7/8/9/14/15/16/17/18/23/24/25 linear fetch
  owner and original
  RESET/logical-phase, normal BR/BG, bounded linear BR/BG attachment, and
  standalone HALT sequencing, bounded ordinary-fetch HALT attachment, and
  Type 5/native-PM/HALT and Type 13/native-PM/HALT attachment invariants
  plus shared-PM-owner mutual-exclusion/routing, normal-BR/BG composition, and
  attached Type 5/Type 13/ordinary-fetch retry, completion, cache, and PMDA
  invariants (73 total)
  pass
  assertion syntax lint, but no
  formal proof ran because SymbiYosys/Yosys are unavailable;
- no integrated multi-owner architectural core, complete assembler, or
  whole-core synthesis top exists.

## Next highest-priority work

1. Locate the exact original Cross-Software/instruction reference and a
   separately identifiable original data sheet.
2. Locate primary or physical evidence for OQ-016 to replace or reject the
   bounded Type 17 slice's explicitly provisional zero-extension hypothesis.
3. Attach reset-time PMA `0x0004` and first fetch only after resolving or
   explicitly bounding OQ-024, then replace the bounded NOP/Type 6/Type 7/
   Type 9/Type 14/Type 15/Type 16/Type 17/Type 18/Type 23/Type 24/Type 25
   owner's deterministic preload.
4. Converge ordinary fetch, Type 5, and Type 13 on one owner and cache before
   composing HALT, DMACK waits, TRAP, interrupts, and reset.
5. Trace Atari schematic nets and PAL behavior before writing the board wrapper.
6. Research and connect interrupt-entry sequencing to the now-composed SSTAT
   and status-stack boundary without inventing arbitration priorities.
