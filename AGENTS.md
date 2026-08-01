# AGENTS.md

## Mission and exact-device scope

This repository implements the **original Analog Devices ADSP-2100**, including
its complete documented instruction set and externally visible logical timing,
as portable synthesizable SystemVerilog. Atari Hard Drivin' is an integration
qualification target, not the definition of the supported instruction subset.

The default and currently only architectural configuration is the external
memory original ADSP-2100 identified by original-device sources. ADSP-2100A is
not assumed identical until its differences are closed. Do not silently add
ADSP-2101, ADSP-2103, ADSP-2104, ADSP-2105, ADSP-2111,
ADSP-2115, ADSP-217x, ADSP-218x, or ADSP-219x features. Later-device material
is comparative evidence only unless it explicitly says that a behavior applies
to the original ADSP-2100.

## Required reading before work

Before modifying RTL, the executable model, ISA data, or an architectural
expectation:

1. read this file;
2. read `TASKS.md` and `CHANGELOG.md`;
3. read the relevant documents under `docs/architecture/` and `docs/timing/`;
4. read every applicable ADR under `docs/decisions/`;
5. inspect `docs/research/open_questions.md` and
   `docs/research/source_conflicts.md`;
6. inspect current verification and confidence reports under `artifacts/`.

Every meaningful development cycle must update `TASKS.md` and `CHANGELOG.md`.
Update the progress artifacts after each major milestone.

## Source precedence and claim taxonomy

Use this authority order:

1. original ADI ADSP-2100-specific manuals, data sheets, errata, and timing
   documents;
2. ADI family manuals with an explicit applicability statement for ADSP-2100;
3. original Atari schematics, engineering records, PAL equations, and service
   manuals;
4. contemporary ADI toolchain and application documentation;
5. physical-chip measurements or die evidence;
6. original Atari engineering commentary;
7. maintained emulators;
8. academic or prior FPGA implementations;
9. community summaries.

Label claims as one of: original-device documented, explicit family-wide,
later-family only, reference-software observed, Atari schematic inferred, Hard
Drivin' software observed, MAME observed, physical-hardware confirmed,
implementation convenience, or unverified. Confidence is one of
`VERIFIED_PRIMARY`, `VERIFIED_HARDWARE`, `CORROBORATED`, `INFERRED`,
`PROVISIONAL`, or `UNKNOWN`.

Every architectural statement needs a citation precise enough to recover the
publication, revision, page, chapter/section/table/figure, schematic sheet, or
MAME commit and line. Never turn `PROVISIONAL` into `VERIFIED_*` without new
evidence.

## Clean-room and copyright policy

- Implement from specifications and independently derived tests.
- Do not copy MAME or other emulator source into RTL, the model, or tools.
- External implementations may be isolated differential oracles, subject to
  their licenses.
- Do not commit manuals, game ROMs, PAL dumps, or legacy tool binaries unless
  redistribution permission is explicit and recorded.
- Put redistribution-unclear downloads only in gitignored `reference_cache/`.
- Record URL, retrieval date, checksum, applicability, authority, license, and
  redistribution status in `docs/references/manifest.yaml`.
- Never evade authentication, paywalls, robots restrictions, or access
  controls.
- Never execute downloaded legacy binaries on the host. Use an isolated
  emulator/VM/container without credentials or sensitive mounts when a task
  explicitly requires execution.
- Prefer paraphrase and precise citation over copied manual text.

## Ambiguities and conflicts

Never invent or silently infer architectural behavior. Record incomplete or
contradictory evidence in `docs/research/open_questions.md` or
`docs/research/source_conflicts.md`, including competing hypotheses, affected
tests, and whether Hard Drivin' depends on the distinction. A provisional
implementation is permitted only when clearly labeled in code, documentation,
task status, and tests. Reserved encodings are not no-ops without authoritative
evidence.

## SystemVerilog conventions

The generic core targets the common synthesizable subset supported by current
Verilator, Icarus Verilog where practical, Yosys, and Intel Quartus:

- use `logic`, `always_ff`, `always_comb`, packages, explicit-width types, and
  enumerated state machines;
- use explicit signedness at declarations and arithmetic boundaries;
- size every literal; do not rely on unsized arithmetic constants;
- extend operands explicitly before arithmetic and slice results explicitly;
- document every intentional truncation, rounding point, guard bit, and
  signed/unsigned conversion;
- give combinational outputs defaults and avoid inferred latches;
- declare every net; implicit nets are prohibited;
- avoid multiple procedural drivers and combinational loops;
- avoid `initial` state in architectural RTL;
- no `#` delays, real-number constructs, `force/release`, DPI dependencies, or
  testbench-only constructs in synthesizable RTL;
- no vendor primitives in `rtl/core/` or `rtl/packages/`;
- assertions may be guarded for synthesis, but normal simulation must keep
  them enabled.

Use lower_snake_case signals and module names. Module filenames match module
names. Active-low external signals use an `_n` suffix only after original pin
polarity is sourced. Constants and enum members use upper snake case.

## Clocking and reset

The portable core has one primary FPGA clock. Represent historical instruction
cycles, bus phases, stalls, and arbitration with explicit state and synchronous
clock enables. **Gated clocks and logic-generated internal clocks are
prohibited.** CDC logic belongs only in a wrapper with a real clock-domain
crossing.

Reset behavior must distinguish asynchronous pin behavior, synchronous
architectural updates, documented reset values, unknown power-up state, and
wrapper-only deterministic initialization. Do not turn undocumented or
power-up-unknown state into zero. Any deterministic FPGA convenience belongs
behind an explicit wrapper parameter and must not change the default authentic
model.

## Synthesis requirements

Architectural RTL must be portable and synthesizable without vendor libraries.
Inference of RAMs, adders, and multipliers is allowed if their behavior is
fully specified independently of the mapping. Keep latch count and accidental
clock count at zero. Treat unconstrained paths, width warnings, and
synthesis/simulation mismatches as defects. RTL commits require a Verilator
lint/build and an available Yosys smoke synthesis; target work additionally
requires the applicable Quartus project and SDC checks.

## Verification requirements

- Every encoding claim needs automated decode coverage based on independently
  reviewed fixtures.
- Every arithmetic claim needs boundary tests.
- Every cycle-count claim needs an automated timing assertion.
- Every external memory transaction must be trace-testable.
- Every multifunction ordering rule needs documentation and directed tests.
- Model, assembler, RTL, and MAME must not validate each other circularly.
- Random tests use deterministic seeds and preserve reduced failures.
- Never bypass a failing test, weaken an assertion to pass, or change expected
  output without documenting why the old expectation was wrong.
- RTL existence never makes a task complete. Completion requires source-backed
  documentation and objective passing tests named in `TASKS.md`.

The default verification ladder is:

1. manifest/schema and generated-data consistency;
2. independent model unit tests;
3. hand-fixture assembler/disassembler/decode tests;
4. computational-unit, DAG, sequencer, bus, and interrupt unit tests;
5. instruction and program regressions;
6. randomized RTL/model differential tests;
7. independent MAME comparison where applicable;
8. formal properties;
9. synthesis and timing qualification.

## Formal verification

Use SVA plus SymbiYosys-compatible harnesses when available. At minimum, cover
decode uniqueness, legal state transitions, stalled-bus stability, legal PM/DM
controls, bus grant/relinquishment, stack bounds, PC/loop rules, interrupt
priority/masking, bank selection, DAG wrapping, condition-false preservation,
write-conflict exclusion, and arithmetic identities. Every proof report must
state assumptions, engine, depth, bounded state, and uncovered state. A bounded
proof is not a complete proof.

## Documentation discipline

Architecture documents are specifications, not marketing. Attach each claim to
evidence and list unresolved cases near the claim. Machine-readable ISA data is
the intended source for generated opcode tables, decode constants,
assembler/disassembler tables, and coverage reports. Do not maintain
contradictory handwritten opcode definitions.

Timing documentation distinguishes logical bus phase accuracy from analog
setup/hold/access/pulse-width limits. Hard Drivin'-specific maps and behavior
remain in integration documents and wrappers, never in the generic core.

## Commit discipline

Use small coherent commits with prefixes such as `chore`, `docs`, `research`,
`model`, `tools`, `rtl`, `test`, `formal`, `synth`, `integration`, or `fix`.
Do not rewrite published history.

Before every commit:

1. inspect the full diff and staged file list;
2. run the focused tests;
3. run `make test` and `make lint`;
4. run `make synth-yosys` for RTL changes when Yosys is available;
5. run applicable formal checks;
6. ensure no manual, ROM, dump, or downloaded binary is staged;
7. update `TASKS.md`, `CHANGELOG.md`, citations, and assumptions;
8. ensure the repository remains buildable and testable.

A commit message must state the engineering change and its verification.

## Repository layout

- `docs/{architecture,timing,research,references,decisions,integration}`:
  specifications, provenance, and decisions
- `docs/generated/`: reviewed generated architecture artifacts
- `rtl/{packages,core,wrappers}`: synthesizable implementation
- `sim/reference_models/`: structurally independent executable model
- `sim/`: HDL testbenches and differential adapters
- `tools/`: assembler, disassembler, trace, generators, converters
- `tests/`: fixtures, vectors, programs, traces, regressions, fuzz cases
- `formal/`: properties and harnesses
- `synthesis/`: Yosys, Quartus, and MiSTer projects
- `third_party/`: permitted source dependencies and notices
- `reference_cache/`, `build/`: gitignored local products
- `artifacts/`: tracked concise status reports, not large generated outputs

## Current architectural status and risk

No integrated multi-owner fetch/decode/execute instruction core exists. A
bounded steady-state owner now executes NOP, legal Type 6/7, every legal Type
17 internal MOVE, and every Type 18 MODE CONTROL word while fetching PC+1
through the native PM phase controller. Type 17 narrow status/control-source
extension remains an observable OQ-016 provisional behavior; reset
first-fetch, transfers, loops, interrupts, and PM-data/cache remain outside
that owner. Normal BR/BG and ordinary-fetch HALT are attached separately only
to this bounded linear
owner: the current fetch completes, new issue is inhibited, PM output enables
are masked during grant, HALT instead holds driven PM outputs in state 8, and
restart occurs at state 8-to-1. A standalone primary-backed HALT sequencer now
distinguishes PM-data recognition, admits exactly one forced external fetch on
the following state-8 boundary, and stops after that fetch. Bounded Type 5 and
Type 13 attachments now consume this late request, discard any
issue-time cache hit, complete the PM data action once, fill the cache from
the forced external fetch, and stop after its state-7 completion. Cross-event
priority and shared-PM ownership remain open. Other bounded
source-backed RTL
execution slices implement all
original Type 2
immediate-DM-write words, all original Type 18 mode
controls, all 32 original Type 21 MODIFY selections, exact Type 25 conditional
MR saturation, all Type 6 immediate-to-DREG loads, all 507,904 supported
Type 7 immediate-to-non-data-register loads, the 14,336 source-closed
Type 15 immediate LSHIFT/ASHIFT words, 25,648 canonical Type 14
shifter-plus-DREG words, 108,640 source-closed Type 12 shifter-plus-DM words,
54,320 source-closed Type 13 shifter-plus-PM words,
all 4,194,304 source-closed Type 1 dual-read action words,
1,556,480 source-closed Type 3 direct-DM words with bounded state and native-DM
execution,
2,034,688 source-closed Type 4 action words with waited logical DM execution,
1,017,344 source-closed Type 5 ALU/MAC-plus-PM words with bounded
cache/native-PM execution,
all 1,792 source-backed Type 16 conditional shifter words, 476,672
source-closed Type 8 ALU/MAC-plus-DREG words, all 32,768 Type 9
conditional ALU/MAC words, 507,904 source-closed Type 10 direct JUMP/CALL
words, all 262,144 Type 11 DO UNTIL setup words, 124 source-closed Type 19
DAG2-indirect JUMP/CALL words, all 32 Type 20 conditional RTS/RTI words, all
16 Type 22 conditional TRAP words, all eight Type 23 DIVQ words, sixteen
source-closed Type 24 DIVS words,
and all Type 26 stack-control actions,
but they do not establish
whole-core PC, pipeline, bus, interrupt, or wait-state behavior. Type 18
excludes later timer, GO, and multiplier-placement fields and exhaustively
covers all 256 original words. Type 21 uses an exact-width I/M/L register file
with authentic reset-invalid state and cycle-start-read/cycle-end-write
ordering; ordinary data transfers and multifunction DAG updates are not yet
attached except for the bounded Type 12 shifter-plus-DM and Type 13
shifter-plus-PM transaction paths.
Type 4 field/action decode and bounded logical execution are exhaustive and
primary-backed, including AMF-zero memory-only moves, selected-bank ALU/MAC
state, old-value write overlap, fail-closed read destination collisions,
arbitrary DMACK-low waits, and atomic compute/read/I completion. A separate
bounded wrapper now attaches that descriptor to the native eight-state DM
controller: issue occurs only at state 8-to-1, waits repeat a complete native
substate sequence, and compute/status/read/I effects commit only at qualified
state 7-to-8 completion. Whole-core fetch, multi-owner arbitration, and event
handling remain open.
Type 5 field/action decode is independently closed for its complete
1,048,576-word class: 1,017,344 memory-only or ALU/MAC-plus-PM actions are
supported and 31,232 same-destination PM-read collisions fail closed. DAG2
I/M selection, AMF-zero behavior, old-value PM writes through `{DREG,PX}`,
and PM-read `{DREG,PX}` destinations are source-backed. A bounded logical,
cache, and native-PM composition now captures old state at issue, commits
compute/status/read/PX/I effects atomically at data completion, and selects an
issue-time cache hit or one pure recovery fetch. A bounded HALT attachment
adds five directed tests and 50,126 deterministic clocks covering 197 late
hit overrides/forced fetches, one-time ALU/MAC/PM/PX/DAG2 completion, and 387
stop/resume handshakes. Whole-core fetch/PC/control-event ownership, hidden
cache behavior, and physical validation remain open.
Type 1 field/action decode is independently closed for its complete
4,194,304-word class. Every word selects fixed DAG1 DM and DAG2 PM reads,
restricted DD/PD input destinations, and either AMF-zero dual fetch or an
implicit AR/MR ALU/MAC result using cycle-start operands. State, cache, and
native dual-bus execution remain withheld because OQ-023 has not established
the PM transaction behavior while DMACK extends state seven.
Type 3 field/action decode is independently closed for its complete
2,097,152-word class: 770,048 direct reads and 786,432 direct writes are
supported, while 540,672 reserved-selector or read-only-SSTAT-destination
words fail closed. Its bounded execution composes the complete general-register
state, captures write sources at state 8-to-1, retains transactions through
full-cycle DMACK extensions, and commits reads only at state 7-to-8. OQ-016
still governs narrow status/control write-source extension, and whole-core
ownership remains pending.
Type 7 field/action and bounded state execution are independently closed for
its complete 1,048,576-word class: 507,904 words target the 31 writable
original non-data registers, while 540,672 computational-group, reserved, or
read-only-SSTAT destinations fail closed. The shared general-register state
preserves exact storage widths, selected-bank SB writes, CNTR/count-stack load
effects, and reset unknowns. Whole-core fetch, interrupt-abort, active-loop,
and phase ownership remain pending.
Type 15 exhaustively partitions its 32,768-word class: XOP `001` and SF 8–15
remain explicit unsupported subencodings rather than receiving invented
behavior. Its bounded state slice samples the selected bank and OR feedback at
cycle start, commits SR at cycle end, and leaves SE/status unchanged; other
shifter instruction classes remain unintegrated. Type 16 exhaustively
partitions its 2,048-word class into 1,792 supported actions and 256 XOP `001`
subencodings held under OQ-020. Its bounded slice evaluates cycle-start
conditions, samples selected-bank SE/SR/SB and ASTAT feedback, preserves all
destinations when false, and commits the SF-selected SR/SE/SB/SS writes at
cycle end. The bounded Type 13 slice additionally covers the original
PM-access shifter multifunction class at the logical cycle boundary.
The bounded Type 14 slice is the first integrated multifunction instruction:
both shifter and DREG-move sources read cycle-start selected-bank state, and
noncolliding move plus SR/SE/SB/SS writes commit together at cycle end. Its
canonical bit-15-zero subset contains 25,648 supported words. The remaining
32,768 bit-15-one, 4,096 unavailable-XOP, and 3,024 same-destination words fail
closed; OQ-021 tracks the original diagram's unnamed bit 15. Type 12–13 memory
multifunction work is now split into bounded logical DM and PM transaction
paths below.
The bounded Type 12 slice partitions all 131,072 words into 108,640 supported
actions, 16,384 unavailable-XOP words, and 6,048 illegal DM-read destination
collisions. It exposes a logical DM request/address/read-write/data/ack
boundary, holds all bus outputs and architectural state over arbitrary ACK-low
extensions, samples read data and commits the selected shifter, DREG, and DAG-I
postmodify writes atomically on the first ACK-high boundary, and uses the old
DREG value for a simultaneous store. A separate native DM controller now
implements DMA/DMS states 1–8, DMRD/DMWR states 4–7, DMACK qualification at
6–7, DMD read sampling at 7–8, write drive states 5–8, and the original
full-eight-substate state-seven extension. A bounded wrapper attaches Type 2
writes at state 8-to-1 and returns only the qualified state 7-to-8 completion
to the architectural slice. A second bounded wrapper attaches Type 12 reads
and writes at the same sourced phase boundary; its shifter, optional read
DREG, and selected-I destinations remain frozen through full-cycle wait
extensions and commit together at state 7-to-8. Instruction-fetch concurrency
and whole-core interrupt/bus arbitration remain open.
The bounded Type 13 slice partitions all 65,536 words into 54,320 supported
actions, 8,192 unavailable-XOP words, and 3,024 illegal PM-read destination
collisions. It performs the fixed logical PM data cycle, reads a 24-bit PM
word into old-selected-bank DREG upper 16 bits plus PX lower 8 bits, writes an
old `{DREG,PX}` word, and commits DAG2 post-modification with the shifter
action. A composed cache boundary now derives a hit from the pre-cycle
standalone monitor, supplies its 24-bit instruction in the same data cycle,
and feeds every miss/forced-fetch recovery word back into that monitor without
repeating architectural actions. It also accepts ordinary external fetch
completions when Type 13 does not own PM; 50,086 integration clocks cover
lookup/fill ownership. A further bounded native wrapper captures the Type 13
data descriptor on the enabled state-8-to-state-1 edge, holds old-value
operands through all eight pin phases, commits the architectural action only
on the state-7-to-state-8 completion edge, and issues a miss recovery fetch on
the following state-8-to-state-1 edge. Five directed tests and 50,081
model/RTL clocks cover that attachment. Unified fetch/PC/control-event
arbitration remains open under OQ-008. A further Type 13/HALT composition adds
five directed tests and 50,124 deterministic clocks covering 210 late
PM-data recognitions, 210 cache-hit overrides and forced issues, 397 stops and
resumes, and no replay of shifter, PM-data, PX, or DAG actions.
A parallel Type 5/HALT composition adds five directed tests and 50,126
deterministic clocks covering 197 late PM-data recognitions, issue-time cache-
hit overrides, and forced fetches, 387 stops/resumes, and no replay of
ALU/MAC, PM-data, PX, or DAG actions.
The source-bounded cache monitor implements the documented
16-by-24 array, PMA[3:0] indexing, single contiguous valid region,
out-of-region invalidation, sequential extension, and circular oldest-word
replacement. It preserves authentic invalid data state and passes 50,028
standalone model/RTL clocks. Its Type 13 wrapper now passes a further 50,086
model/RTL clocks. The manual's hidden ahead/behind register encoding,
self-modifying PM effects, and unified branch/loop/interrupt/HALT/BR
arbitration remain OQ-008.
A separate source-backed native PM controller uses an implementation request
boundary aligned to the state-8-to-state-1 edge, holds PMA/PMDA/PMS for states
1–8, asserts
active-low PMRD/PMWR for states 4–7, samples reads at the 7-to-8 edge, and
drives write data for states 5–8. It preserves PMS across back-to-back requests
and masks all FPGA output enables during externally directed bus
relinquishment. Ten directed tests and 50,032 model/RTL clocks pass. This block
has bounded Type 13/cache and ordinary linear-fetch clients, but it does not
yet provide whole-core PM arbitration or attach other PM instruction classes.
The normal BR/BG controller passes 50,084 standalone model/RTL clocks, and its
bounded linear-owner composition passes 50,003 more clocks for current-fetch
completion, next-issue inhibition, grant-time PM masking, and state-1 resume.
The separate ordinary-fetch HALT composition passes seven directed tests and
50,003 clocks with 790 recognize/stop/resume handshakes, DMACK-qualified
release, and stable driven state-8 PM outputs.
No PM-data/cache or DM client is attached to BR/BG, analog delays are not
modeled, and the request boundaries are not claims about hidden device
latches. HALT after Type 5 or Type 13 PM data is bounded and attached; HALT
during BG or DMACK waits, and TRAP/interrupt/reset arbitration remain
unimplemented.
The RESET-time direct pin path is confined to a wrapper.
Original Type 2 immediate DM-write execution is bounded and class-complete:
all 2,097,152 words select the raw 16-bit data field and a same-DAG I/M/L
tuple. Its logical DM request holds captured address/data over arbitrary
DMACK-low clocks and commits the selected I only on acknowledgment across
50,035 logical model/RTL clocks. Its native attachment adds 50,027 clocks of
state-8 issue, full-cycle wait extension, and state-7 completion coverage.
Fetch/event concurrency and whole-core arbitration remain unimplemented.
The bounded Type 8 slice executes documented ALU and fractional-MAC
computations in parallel with one internal DREG move. Both clauses sample the
cycle-start selected bank; noncolliding DREG/AR/AF/MR/MF and ASTAT writes
commit atomically at cycle end. The exact 524,288-word class partitions into
476,672 supported words, 16,384 AMF-zero words held under OQ-022, and 31,232
same-destination collision words held under OQ-014. It does not establish
conditional-computation, PM/DM-data, fetch, interrupt, or bus timing.
A generated
synthesizable class decoder recognizes all 30 original Appendix A format
classes and fails closed for unshown words; it has exhaustive 24-bit membership
comparison. A separate exact Type 17 decoder partitions its 4,096 words into
2,256 legal moves and 1,840 reserved/read-only-destination subencodings. A
bounded Type 17 state slice now connects both computational banks, both DAG
register files, status/control, PX, CNTR/count-stack, and SSTAT with
cycle-start read/cycle-end write ordering. Its narrow status-source
zero-extension is visibly PROVISIONAL under OQ-016; fetch, interrupts, PC, and
bus phases remain unintegrated. Source-backed condition,
standard ALU, fractional MAC, all-function shifter, DAG arithmetic, and
sequencer-flow combinational blocks exist with independent model comparison,
and a stateful two-bank storage slice exists for the complete computational
bank, including AF/MF/SB and unit-specific ALU/MAC/shifter writeback. A
stateful status/control slice also implements original ASTAT/MSTAT/ICNTL/IMASK
fields, reset classifications, exact Type 18 MODE CONTROL, computational flag writes,
interrupt-entry snapshot/masking, and status restore. MSTAT consumer
integration now covers its four original outputs at an ordinary
cycle-start/cycle-end boundary; ICNTL consumer wiring, interrupt recognition,
and complete operand/decode connectivity do not exist. A separate original
four-by-sixteen status stack and exact PC/count/loop stack-storage slice
implement LIFO state, saturating depth, sticky overflow, and all eight SSTAT
sources. A separate stateful CNTR slice implements reset validity,
pre-decrement CE/NOT CE evaluation, post-decrement, and count-stack request
generation. A bounded sequencer integration slice connects IF/DO condition
evaluation, explicit flow, DO setup, CNTR, and PC/count/loop stack storage for
source-backed cases. It rejects conditional-CALL CE (OQ-012), empty-pop
effects remain OQ-013, and competing automatic/manual actions are held and
flagged under OQ-018. Type 26 now connects manual status-stack push/restore to
live ASTAT/MSTAT/IMASK in its bounded slice; interrupt/RTI arbitration remains
absent. A bounded Type 10 slice is the first semantic decoder connected to a
14-bit PC register, CALL PC-stack pushes, and JUMP NOT CE counter-stack
transitions. It fails closed for all 16,384 CALL NOT CE encodings under
OQ-012 and excludes active-loop, fetch/cache, interrupt, bus, and phase
integration. A separate bounded Type 11 slice executes every DO UNTIL setup,
including PC+1/descriptor pushes and source-backed nesting legality, while
holding DO-on-active-terminal under OQ-018. A bounded Type 19 slice connects
I4-I7 targets, conditional PC flow, taken CALL return stacking, JUMP NOT CE
transitions, and a PMA-drive observation; four CALL NOT CE words remain
OQ-012 and active-loop/fetch/bus phases remain outside the slice. A bounded
Type 20 slice connects conditional RTS/RTI to PC/status stacks and exact live
status restoration; it fails closed for missing taken-return context under
OQ-013 and does not integrate interrupt entry, active loops, fetch, or bus
phases.
Type 22 is the first decoder-connected phase-aware instruction boundary: it
retains a condition decision through logical phases, asserts TRAP at the
state-7/state-8 transition, holds state 8, and implements the recognized-HALT
clear/release handshake. General HALT synchronization, BR/BG interaction,
interrupt/loop arbitration, and attachment to the separate PM strobe and
BR/BG controllers remain unconnected. SC-013 records that pinned
MAME incorrectly classifies these original-device words reserved.
The bounded Type 23/24 division boundaries implement all eight ALU-X divisor
sources, DIVS AY1/AF upper-dividend selection and sign seeding, DIVQ old-AQ
add/subtract iteration, atomic old-value AF/AY0/AQ writes, selected-bank
behavior, and authentic unknown validity. Type 24 AY0/zero YOP field words
fail closed, and SC-014 preserves the original-device non-AQ flag rule over
conflicting later-device prose. No
whole-core PC/fetch path,
integrated multi-class semantic
decode, interrupt recognition, or phase-level sequencer timing exists.
Multifunction legality, ordering, and whole-core cycle integration remain
incomplete. The executable
instruction model establishes
exact-width state, reset unknowns, deterministic traces, PM fetch
transactions, and only the hand-verified all-zero NOP in its top-level step
method. Independent bounded models cover Type 17 action/state selection and
Type 6, Type 8, Type 9, Type 10, Type 11, Type 14, Type 15, Type 16, Type 18,
Type 19, Type 20, Type 21, Type 22, Type 23, Type 24,
Type 25, and
Type 26 state/action behavior outside that
top-level step path; all other opcodes still fail closed. Architectural
documents marked partial or provisional remain research inputs until their
named evidence gates pass.

Highest risks are:

1. separating original ADSP-2100 behavior from later ADSP-21xx behavior;
2. semantic completion and legal multifunction combinations after the
   source-closed 24-bit class/field-placement inventory;
3. pre-instruction versus same-cycle value ordering;
4. pipeline, wait-state, interrupt, halt, and bus-arbitration timing;
5. arithmetic edge behavior, especially MAC alignment/rounding/guard bits;
6. lack of physical ADSP-2100 measurements for undocumented cases;
7. reconstructing Atari PAL/host/SIM/SOM behavior without treating MAME as
   primary proof.

## Completion

Do not call the core instruction-complete, cycle-accurate, Hard Drivin'-ready,
or release-ready until the corresponding criteria in `TASKS.md` and README
status artifacts have objective evidence. At a minimum release requires full
legal/reserved encoding accounting, directed and differential coverage,
documented cycle/bus behavior, passing lint/formal/regressions, successful
Yosys and Quartus synthesis, timing constraints and closure evidence,
provenance/license audits, synthetic board tests, and authorized local-ROM
qualification where ROMs are available.
