# Instruction-cycle timing

**Status: baseline, not complete cycle table**

An ordinary instruction occupies one processor cycle, but PM-data/cache-miss
fetches, waits, and control events add externally visible cycles
[ADI-UM-1989, printed pp. 1-2, 6-21]. The project therefore records both
architectural execution and bus-phase count.

“Waits” here means sourced DMACK-low data-memory extensions. The original
program-memory interface has no acknowledge input, so the ordinary overlapped
instruction fetch is fixed at one processor cycle. The integrated reference
model now rejects its former synthetic PM-fetch wait argument rather than
recording behavior the original interface cannot request
[ADI-UM-1989, printed pp. 4-3, 4-10, 5-5–5-12].

Known cases:

| Case | Current sourced timing |
|---|---|
| ordinary instruction | one eight-state processor cycle; the retained bounded fetch client retries PC+1 after shared-owner collision or BR/BG issue inhibition and retires only on the routed state-7 completion |
| Type 1 ALU/MAC plus DM and PM reads | one processor cycle with full-speed DMACK; computation consumes old operands and both reads complete at cycle end; DMACK-low extends state 7 by whole processor cycles, but the native PM strobe/data behavior during that extension remains OQ-023 |
| Type 2 immediate DM write | one processor cycle when DMACK is sampled asserted; every DMACK-low sample extends state 7 by one processor cycle while captured address/immediate and the selected I remain stable |
| Type 4 ALU/MAC plus DM read/write | one processor cycle when DMACK is sampled asserted; every DMACK-low state-6 sample repeats a complete eight-substate state-seven extension while preserving the captured bus/compute/DAG descriptor, and the qualified state-7-to-state-8 edge atomically commits compute/status, optional read, and selected-I postmodify |
| Type 5 ALU/MAC plus PM read/write, cache hit | one processor cycle; compute/status, optional DREG/PX read, and DAG2 postmodify commit together at state 7-to-8 while the issue-time cached next instruction is selected |
| Type 5 ALU/MAC plus PM read/write, cache miss or forced fetch | PM data actions commit in the first processor cycle; exactly one back-to-back external instruction-fetch cycle follows without repeating compute, read/PX, or DAG actions |
| Type 8 ALU/MAC plus internal DREG move | one processor cycle; both clauses read at cycle start and commit at cycle end; no PM-data or DM transfer |
| Type 9 conditional ALU/MAC | one processor cycle whether true, false, or AMF-zero no-operation; no PM-data or DM transfer |
| Type 10 direct JUMP/CALL | one processor cycle at the bounded instruction boundary for true or false supported conditions; no PM-data or DM data transfer |
| Type 11 DO UNTIL setup | one processor cycle; PC+1 and `{TERM,ADDR}` push simultaneously while PC advances to the first loop instruction; no PM-data or DM data transfer |
| Type 12 shifter plus DM read/write | one processor cycle when DMACK is sampled asserted; every DMACK-low sample extends state 7 by one processor cycle while bus outputs and all architectural destinations remain stable |
| Type 13 shifter plus PM read/write, cache hit | one processor cycle; PM/PX, shifter/status, and DAG2 post-modify commit in that cycle while the next cached instruction is selected |
| Type 13 shifter plus PM read/write, cache miss or forced fetch | PM data actions commit in the first processor cycle; exactly one external instruction-fetch cycle follows without repeating those actions |
| Type 19 indirect JUMP/CALL | one processor cycle for true or false supported conditions; a taken transfer makes DAG2 supply PMA/PC from I4-I7 without modifying I; no PM-data or DM data transfer |
| Type 20 conditional RTS/RTI | one processor cycle whether true or false; a taken RTS pops PC, a taken RTI pops PC/status and restores status atomically; return NOT CE never post-decrements CNTR; no PM-data or DM data transfer |
| Type 22 conditional TRAP | one processor cycle whether true or false; accepted condition is retained through phase holds, PC+1 commits at the state-7/state-8 boundary, and a taken form asserts TRAP and holds state 8 until the HALT handshake; TRAP NOT CE never post-decrements CNTR |
| Type 23 `DIVQ divisor;` | one processor cycle; old selected-bank AF/AY0/divisor/AQ values produce simultaneous cycle-end AF, AY0, and AQ writes; no PM-data or DM transfer |
| Type 24 `DIVS upper, divisor;` | one processor cycle; old selected-bank upper/AY0/divisor values produce simultaneous cycle-end AF, AY0, and AQ writes; no PM-data or DM transfer |
| Type 6 immediate DREG load | one processor cycle; no PM-data or DM transfer; bounded integrated linear flow executes the current word while fetching PC+1 |
| Type 7 immediate non-data-register load | one processor cycle; no PM-data or DM transfer; a valid CNTR load performs its count-stack push at the same cycle-end boundary; bounded integrated linear flow executes the current word while fetching PC+1 |
| Type 14 shifter plus internal DREG move | one processor cycle; both clauses read at cycle start and commit at cycle end; no PM-data or DM transfer |
| Type 15 immediate LSHIFT/ASHIFT | one processor cycle; no PM-data or DM transfer |
| Type 16 conditional shifter | one processor cycle whether true or false; no PM-data or DM transfer |
| Type 17 internal data MOVE | one processor cycle; no PM-data or DM transfer; bounded integrated linear flow executes the current word while fetching PC+1 |
| Type 18 combined MODE CONTROL | one processor cycle for all selected original mode fields |
| Type 21 `MODIFY (Ix, My);` | one processor cycle; no PM-data or DM transfer |
| Type 25 `IF MV SAT MR;` | one processor cycle whether MV is true or false |
| Type 26 combined stack control | one processor cycle for any field-defined action combination |
| PM data access, next instruction valid in cache | no fetch overhead |
| PM data access, invalid cache | one additional instruction-fetch cycle |
| interrupt vectoring | two cycles described, including vector jump |
| DMACK low | extend state 7 by whole processor cycles until high |
| HALT during ordinary instruction fetch | asserted active-low input is recognized at state 3; the current cycle completes at state 7-to-8, stopped outputs hold state 8, and a DMACK-high release resumes at state 8-to-1 |
| HALT during PM data | current PM-data cycle completes; exactly one forced external instruction-fetch cycle issues at the following state-8-to-state-1 edge and the processor stops after its state-7-to-state-8 completion; scheduling and bounded Type 5/Type 13 native-PM attachments are verified, and the retained ordinary-fetch plus both PM-data clients are each separately attached to shared PM plus normal BR/BG, while unified three-client and combined shared-PM/HALT priority remain open |

Sources: [ADI-UM-1989, printed pp. 4-9–4-10, 4-26–4-28, 5-9,
5-13–5-16, 6-14–6-15, 6-21, A-4, A-8–A-10]. The Type 26
combination wording is corroborated, but not extended, by
[ADI-2101-CROSS-1990, printed pp. 9-26–9-27 and 9-61].

The bounded Type 25 model/RTL slice verifies that cycle-start MV, selected
bank, and MR determine a single cycle-end MR write, while false MV preserves
state without changing the one-cycle boundary, across 50,112 stateful cycles.
This is instruction-boundary evidence, not external fetch-phase evidence
[ADI-UM-1989, printed pp. 2-18–2-19 and A-4].

The bounded Type 24 model/RTL slice verifies 50,109 one-clock transactions.
It treats AF/AY0/AQ as one atomic state action, preserves every non-AQ ASTAT
bit, and does not emit PM-data or DM activity. This establishes sourced
instruction-boundary timing only; the ordinary PM fetch and any acknowledged
wait extension remain outside the slice [ADI-UM-1989, printed pp. 2-9–2-13,
4-21, 6-9, A-4].

The bounded Type 23 model/RTL slice verifies 50,081 one-clock transactions.
It applies the old-AQ-selected 16-bit add/subtract and commits AF/AY0/AQ as a
single action while preserving all non-AQ ASTAT bits and emitting no PM-data
or DM access. One DIVS plus fifteen DIVQ model steps are additionally checked
as a signed division sequence. The ordinary-fetch owner adds two directed
tests and a 442,392-clock comparison covering every divisor in both banks,
both old-AQ paths, and consecutive DIVQ dependency through native state-8
issue/state-7 retirement. The owner also executes every legal DIVS operand
combination and a dependent DIVS-to-DIVQ sequence; loops, interrupts, and
unified PM/cache/event ownership remain outside that result
[ADI-UM-1989, printed pp. 2-9–2-13, 4-21, 6-9, A-4, B-1–B-8].

The bounded Type 12 model/RTL slice verifies 50,069 logical clocks. An
immediately acknowledged access commits in one clock; every unacknowledged
clock holds address, direction, select, valid write data, shifter destination,
DM-read destination, and selected I. The first acknowledged clock atomically
commits all three parallel actions. This verifies the sourced logical wait
contract, not physical sub-cycle setup/hold timing or whole-core PM-fetch and
event arbitration [ADI-UM-1989, printed pp. 5-9–5-12, 6-3–6-7].

The bounded Type 4 model/RTL slice verifies 50,072 logical clocks. Immediate
acknowledgment commits the captured ALU/MAC or memory-only action, optional
read data, and selected-I postmodify together. Each DMACK-low clock retains
the old-value compute/store/DAG descriptor and stable valid logical bus
outputs without any architectural write. A separate six-test, 50,082-clock
native composition admits the descriptor only at state 8-to-1, qualifies ACK
at state 6-to-7, and commits only at state 7-to-8 through zero or repeated
complete-cycle waits. Ordinary fetch overlap, shared-DM arbitration, and event
arbitration remain open
[ADI-UM-1989, printed pp. 2-6–2-7, 5-9–5-12, 6-3–6-7].

The bounded Type 2 model/RTL slice verifies 50,035 logical clocks. An
immediately acknowledged write drives the old selected I (bit reversed for
DAG1 when enabled), drives the raw immediate, and commits the post-modified I
on that boundary. Every unacknowledged clock retains the captured address,
immediate, selected-I destination, and next-I validity/value without a write.
This establishes logical DMACK extension and completion-only post-modification,
not physical state-6/state-7 pin timing, fetch concurrency, or event
arbitration [ADI-UM-1989, printed pp. 3-1–3-5, 5-9–5-12, 6-1, 6-12, A-1,
and A-6].

The standalone native DM controller closes the physical-substate mapping for
these clients. Its 50,039-clock model/RTL comparison checks DMACK only
at the enabled 6-to-7 edge, holds address/select/strobe/write data across each
complete eight-substate state-seven extension, and samples reads only on the
qualified 7-to-8 completion edge. The bounded Type 2 wrapper adds five
directed tests and 50,027 connected clocks: issue occurs only at 8-to-1 and
the selected-I postmodify occurs only at qualified 7-to-8 completion. The
bounded Type 12 wrapper adds six directed tests and 50,064 connected clocks:
both read and write descriptors issue only at 8-to-1, old write data remains
stable through waits, read data is sampled at 7-to-8, and the shifter,
optional DREG load, and selected-I postmodify commit only on that same edge
[ADI-UM-1989, printed pp. 5-9–5-12, Figures 5.6–5.7;
ADI-DATABOOK-1987, printed pp. 2-40–2-43, Figures 16–17]. The bounded Type 4
wrapper adds six directed tests and 50,082 clocks: memory-only and ALU/MAC
reads/writes issue only at 8-to-1, old store/compute/DAG state stays fixed
through waits, and compute/status, optional DREG read, and selected I commit
only on the native 7-to-8 completion
[ADI-UM-1989, printed pp. 5-9–5-12, Figures 5.6–5.7;
ADI-DATABOOK-1987, printed pp. 2-40–2-43, Figures 16–17].

The bounded Type 5 model/RTL slice verifies 50,071 logical clocks. A cache hit
commits ALU/MAC status/result, optional PM-read DREG/PX, and DAG2 postmodify in
the fixed data cycle and selects the issue-time cached next instruction. A
miss or forced fetch commits those data actions once, then schedules exactly
one pure instruction-recovery cycle. Its native attachment adds 50,083 phase
clocks: the descriptor is captured at state 8-to-1, architectural effects
commit only at state 7-to-8, and recovery is accepted on the following
state 8-to-1. A bounded HALT attachment adds five directed tests and 50,126
phase clocks: 197 late issue-time hits become one external fetch, all data and
compute actions commit once, and 387 stop/resume handshakes complete. Ordinary
fetch, branch/loop/interrupt/BR ownership remains
outside this bounded timing claim under OQ-008
[ADI-UM-1989, printed pp. 3-6–3-7, 4-26–4-30, 5-5–5-8,
6-3–6-7, A-1].

The bounded Type 13 model/RTL slice verifies 50,070 logical clocks, and the
connected cache boundary verifies another 50,086. A pre-cycle monitor hit
supplies the actual cached word and completes the PM-data instruction in one
clock. A miss or HALT-forced
fetch commits the PM read/write, PX, shifter/status, and DAG2 I update in that
first clock, then emits exactly one pure instruction-fetch clock before the
instruction-complete/event boundary. The recovery clock never repeats the data
actions and fills the monitor with its fetched instruction. Ordinary external
fetch completion fills that same monitor when Type 13 does not own PM. The
exhaustive decoder partitions all 65,536 words into 54,320
source-closed actions, 8,192 unavailable-XOP words, and 3,024 read collisions
[ADI-UM-1989, printed pp. 3-6–3-7, 4-26–4-30, 5-5–5-8,
5-13–5-16, 6-3–6-7, A-3]. Hidden monitor/event behavior and attachment to the
whole-core fetch/control owner remain outside this bounded evidence under
OQ-008. The native attachment adds 50,081 phase clocks: data issue is captured
at state 8-to-1 and commits at state 7-to-8; a miss recovery is accepted on the
following state 8-to-1 and completes at its state 7-to-8 edge. Hit data is
captured at issue so a later monitor update cannot change the in-flight next
instruction. A bounded HALT attachment can invalidate that captured hit after
state-3 recognition: it commits the data action once, issues one external
fetch at the next state-8 edge, and stops after the fetch's state-7
completion. Five directed tests and 50,124 clocks cover 210 late hit overrides
and forced fetches without architectural replay. Ordinary fetch, branches,
loops, interrupts, and BR/BG are not integrated into this owner.

The bounded Type 6 model/RTL slice verifies one cycle-start bank selection and
one cycle-end DREG write across all immediate values and destinations, with no
PM-data or DM transaction. Its 50,204-cycle state comparison establishes this
instruction boundary but does not model overlapped fetch, waits, interrupts,
or external bus phases
[ADI-UM-1989, printed pp. 1-2, 2-6–2-7, 6-12–6-13, A-2, and A-9].

The bounded Type 7 model/RTL slice applies the same one-cycle boundary to a
right-justified fourteen-bit immediate and one legal non-data destination.
It verifies following-cycle MSTAT visibility, cycle-start selected-bank SB,
and same-boundary CNTR/count-stack load effects without adding a data-memory
or PM-data transaction. It likewise does not yet connect normal fetch overlap,
active-loop/interrupt arbitration, or external PM fetch phases
[ADI-UM-1989, printed pp. 4-4, 4-22, 6-1–6-2, 6-12–6-13, A-2, and A-9].

The top-level independent model additionally composes NOP, legal Type 6/7,
every source-closed Type 8 packet, every Type 9 conditional compute word, every canonical Type 14 shifter-plus-
DREG packet, every supported Type 15/16 shifter word, known-source legal Type
17 internal MOVE, all Type 18 MODE CONTROL, all Type 23 DIVQ forms, all
source-closed Type 24 DIVS forms, and the
exact Type 25 MR-saturation
word with ordinary linear PC progression and the overlapped next-instruction
fetch.
Nineteen foundation tests verify PC/fetch
separation, loaded next-word visibility, fixed one-cycle timing, atomic MSTAT
changes, selected-bank and narrow-register effects, DAG/status writes, CNTR
stack saturation/SSTAT, fail-closed reserved Type 7 destinations, legal Type
17 execution, and unknown-source/reserved-selector rejection. A separate
phase-level composition and bounded RTL owner add twenty-three directed tests
and 442,392 differential clocks: every Type 8 compute-field tuple and every
move source/destination pair in both banks, every Type 9 AMF/condition combination, every
canonical Type 14 packet, every supported Type 15 and Type 16 word, and all
2,256 legal Type 17 source/
destination pairs execute from fully initialized state, every Type 18 encoding
executes, Type 23 covers all divisors/banks and both old-AQ paths plus a
dependent following iteration, Type 24 covers every legal divisor/upper-source
form in both banks plus dependent DIVS-to-DIVQ, and Type 25 covers MV true/false, both signs,
and both banks; the next
fetch is admitted only at enabled state 8-to-1, PM pins follow the native
controller, and the current action plus PC/next-word state retire only at
state 7-to-8. Type 17 ASTAT/MSTAT/SSTAT/IMASK/ICNTL source use raises a
dedicated OQ-016 provisional-behavior pulse at retirement. Phase holds preserve
the transaction, and a distinct new-issue inhibit does not mask the active
fetch. The bounded BR/BG composition adds five directed tests and 50,003
clocks with 86 complete handshakes: the recognized request permits current
retirement, blocks the next issue, masks PM output enables only during grant,
and restarts at state 8-to-1 after release. This still is not a multi-owner
core; reset first-fetch, loop/transfer/event selection, PM-data/cache,
DM ownership, and interrupt arbitration remain open. The bounded ordinary-
fetch HALT attachment adds seven directed tests and 50,003 clocks with 788
recognized stops and restarts: active-low HALT is sampled at state 3, the
current fetch retires at state 7-to-8, state 8 and its PM levels hold static,
and release advances only when DMACK is high. The standalone HALT controller
adds eight directed tests and 50,033 clocks across both cycle classes. Its 335
PM-data recognitions each schedule one state-8 forced-fetch issue before the
later state-7 stop. A bounded Type 13 composition adds five directed tests and
50,124 clocks: 210 late recognitions override 210 issue-time hits, complete
the data action once, drive one native recovery fetch, fill the cache, and
stop after that fetch. A parallel Type 5 attachment adds five directed tests
and 50,126 clocks: 197 late hits become forced fetches, the compute/data action
commits once, and 387 stops/resumes complete. HALT during grant/waits, TRAP,
BR while stopped, interrupts, reset, and shared-PM arbitration remain outside
this evidence
[ADI-UM-1989, printed
pp. 1-5, 2-6, 2-15, 2-18,
2-21, 3-2–3-3, 3-7, 4-3–4-4, 4-10, 4-20–4-24, 5-5–5-8,
5-13–5-14, 6-1–6-2,
6-12, 6-14–6-15, A-3, and A-9].

The bounded Type 15 model/RTL slice verifies a cycle-start selected-bank
operand read, optional old-SR read for OR forms, and one cycle-end SR write.
Its signed immediate does not access SE and it emits no PM-data or DM request.
The 58,709-cycle standalone comparison covers all 14,336 supported words in
both banks. The integrated linear owner additionally retires every supported
word within its 442,392-clock native-fetch comparison. Loop-terminal handling,
interrupts, and cross-event priority remain outside that attachment
[ADI-UM-1989, printed pp. 2-23–2-30, 6-11 Table 6.5, A-3, and A-7].

The bounded Type 16 model/RTL slice verifies cycle-start condition, bank,
operand, SE/SR/SB, and ASTAT inputs followed by function-selected cycle-end
SR/SE/SB/SS writes. A false predicate preserves all of those destinations
without changing the one-cycle boundary. Its exhaustive decoder partitions
all 2,048 class words, and 54,403 model/RTL cycles cover every one of the 1,792
supported words in both banks. The integrated linear owner additionally
retires every supported word within its 442,392-clock native-fetch comparison,
including true and false forms at the sourced one-cycle boundary. Loop
termination, interrupt recognition/abort, and cross-event priority remain open
[ADI-UM-1989, printed pp. 2-20–2-35, 4-21, 4-25, 6-1–6-2, 6-11, A-3, A-6–A-7].

The bounded Type 14 model/RTL slice verifies simultaneous cycle-start shifter
and move reads followed by noncolliding cycle-end DREG, SR/SE/SB, and SS
writes. Its exhaustive decoder partitions all 65,536 class words, and 82,597
model/RTL cycles cover every one of the 25,648 supported canonical words in
both banks. The fetched owner additionally retires every canonical word within
its 442,392-clock native-fetch comparison while committing the noncolliding
DREG and shifter/status results atomically with PC and the next word. OQ-021
bit-15-one behavior, loop-terminal handling, interrupts, and cross-event
priority remain open
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 6-4–6-7, A-3, and A-7].

The bounded Type 8 model/RTL slice verifies simultaneous cycle-start ALU/MAC
and DREG-move reads followed by atomic noncolliding computation, status, and
move writes. Exhaustive decode partitions all 524,288 class words and 983,386
model/RTL cycles execute every one of the 476,672 supported words in both
banks. The bounded fetched owner separately traverses every compute-field
tuple and every move source/destination pair in both banks across its
442,392-clock phase comparison, committing the computation, status, move, PC,
and next word together at state 7-to-8. Reset-first-fetch, loop-terminal
handling, interrupts, and unified PM/cache/event ownership remain open
[ADI-UM-1989, printed pp. 2-6–2-20, 6-4–6-10, A-2, A-5–A-7, A-11].

The bounded Type 9 model/RTL slice verifies cycle-start condition, bank,
operands, feedback, and arithmetic modes followed by true-only cycle-end
result/status writes. False and AMF-zero paths preserve state without changing
the one-cycle boundary. Exhaustive decode covers all 32,768 class words, and
283,996 model/RTL cycles execute every word in both banks and both available
condition outcomes. The integrated ordinary-fetch owner now accepts every
Type 9 word and uses the shared validity-aware CNTR predicate; the 23 directed
owner tests and 442,392 model/RTL phase clocks exercise every AMF/condition
combination with native state-8 fetch issue and atomic state-7 computation,
status, PC, and next-word retirement. Active-loop termination, interrupts,
PM-data ownership, and cross-event priority remain open
[ADI-UM-1989, printed pp. 2-6–2-20, 4-21, 4-25, 6-8–6-10, A-2, A-5–A-7].

The bounded Type 10 model/RTL slice verifies cycle-start condition, PC, CNTR,
and stack-top sampling followed by one cycle-end PC/counter/stack commit.
Exhaustive decode covers all 524,288 class words: 507,904 source-closed words
execute, while 16,384 CALL NOT CE words fail closed under OQ-012. The 554,412
stateful comparison cycles cover true/false predicates, sequential 14-bit
wrap, direct target selection, CALL return pushes, and JUMP NOT CE counter
transitions. This is instruction-boundary evidence only; fetch redirection,
cache invalidation, loop-terminal arbitration, interrupt recognition, waits,
and external logical bus phases remain open
[ADI-UM-1989, printed pp. 4-3–4-5, 4-12–4-13, 6-13–6-14, A-2, A-6].

The bounded Type 11 model/RTL slice verifies cycle-start PC and active-loop
context followed by simultaneous cycle-end PC, PC-stack, and loop-stack
updates. Exhaustive decode covers all 262,144 class words and 554,309
stateful cycles execute every word while also exercising nesting restrictions,
CE-context validity, overflow, reset, and conflicts. This establishes the
one-cycle setup boundary, not subsequent loop-terminal, interrupt, wait, or
external logical bus timing [ADI-UM-1989, printed pp. 4-5–4-8,
4-16–4-19, 6-1, 6-13–6-14, A-2, A-10].

The bounded Type 19 model/RTL slice verifies cycle-start condition, PC, CNTR,
stack tops, and selected DAG2 I sampling followed by one cycle-end PC/counter/
stack commit. All 128 class words are exhaustively classified; 124 execute and
four CALL NOT CE words fail closed. The 50,259 stateful cycles verify false
flow without a valid I, true flow from each I4-I7 value, no I modification,
PMA indirect-drive intent, CALL pushes, and JUMP NOT CE transitions. This is
instruction-boundary evidence: the subsequent instruction fetch, cache,
active-loop arbitration, interrupt recognition, wait extension, and logical
PMA/PMS phases remain open [ADI-UM-1989, printed pp. 3-1–3-2, 4-3–4-4,
4-20, 6-13–6-14, A-3, A-6].

The bounded Type 20 model/RTL slice verifies cycle-start condition, PC, CNTR,
PC-stack, and status-stack sampling followed by one cycle-end state commit.
All 32 words decode, and 50,254 stateful cycles verify false PC+1 flow, taken
RTS PC pop, taken RTI simultaneous PC/status pops and status restore, and
non-mutating return `NOT CE`. Missing taken-return context fails closed under
OQ-013. This establishes one instruction boundary, not active-loop
arbitration, interrupt entry/vector timing, redirected fetch, waits, or
logical bus phases [ADI-UM-1989, printed pp. 4-3–4-4, 4-7, 4-9–4-10,
6-14 Table 6.8, A-4, A-6].

The Type 22 model/RTL slice exposes the manual's logical phases directly. An
instruction is accepted in state 1; a disabled transition in state 7 preserves
the pending decision; an enabled state-7/state-8 transition commits PC+1 and,
when true, asserts TRAP and holds state 8. An externally recognized HALT clears
TRAP while retaining the hold, and HALT release resumes at the already
committed PC+1. The 50,168-clock comparison covers both outcomes for every
condition plus reset, unknown status, invalid phase/opcode, and handshake
cases. It does not supply the general HALT synchronizer, phase generator,
PMS/PMRD fetch control, BR/BG, or interrupt arbitration
[ADI-UM-1989, printed pp. 4-3–4-4, 4-25, 5-14–5-15, Figure 5.10, 6-14,
A-4, A-6].

The bounded Type 18 model/RTL slice verifies that all four fields read
cycle-start MSTAT and atomically commit one cycle-end result across every
field combination and initial MSTAT value. The contemporary Cross-Software
reference corroborates that any number of comma-separated controls execute in
one cycle, but it is used only for that shared behavior; its later-device
timer, GO, and multiplier controls are excluded
[ADI-UM-1989, printed pp. 4-22–4-23, 6-14–6-15, A-3, A-8;
ADI-2101-CROSS-1990, printed pp. 9-63–9-64].

The Type 17 action database records the original one-cycle register-to-register
MOVE and absence of PM-data/DM activity. Exhaustive decode verifies action
selection. The bounded state slice verifies a single cycle-start
read/cycle-end write boundary, no PM-data or DM request, old-bank selection for
the current move, and count-stack update at the commit edge. It does not model
fetch overlap, interrupts, waits, or external bus phases, so Type 17 execution
timing is not claimed complete
[ADI-UM-1989, printed pp. 2-6, 6-1–6-2, 6-12, A-3, A-9].

The bounded Type 21 model/RTL slice verifies that selected I, M, and
corresponding L are sampled at cycle start and that only the selected I is
committed at cycle end. Its 50,124-cycle stateful comparison covers all 32
selections plus seeded linear, circular, invalid, reset, and conflict cases.
The original manual establishes that MODIFY performs address arithmetic
without an actual memory access; the later Cross-Software manual is used only
to corroborate the explicit corresponding-L and writeback wording
[ADI-UM-1989, printed pp. 3-1–3-5, 6-14–6-15, A-4;
ADI-2101-CROSS-1990, printed p. 9-65]. This is instruction-boundary evidence,
and the fetched attachment now adds explicit native phase evidence: operands
are captured with the PC+1 request at enabled state 8-to-1 and selected-I,
PC, and next-word state commit together at state 7-to-8. The superseded
twenty-four-test, 442,405-clock run covers all 32 selections with no PM-data
or DM transaction. Reset-first-fetch and cross-event priority remain open.

The bounded Type 26 model/RTL execution slice verifies that every selected
status/count/loop/PC action reads cycle-start state and commits on the same
cycle-end edge across 50,015 stateful cycles. The bounded fetched owner adds
native state-8 issue and state-7 retirement evidence for all 32 payloads across
25 directed tests and 442,383 phase clocks. Its valid status/count actions
commit atomically with PC and the fetched next word; its PC/loop stacks are
empty, so valid PC/loop pops remain standalone-only evidence. No Type 26 form
starts a PM-data or DM transaction. Automatic flow/interrupt arbitration and
the OQ-013 physical empty-pop result remain open.

Every opcode/taken/false/cache/loop/interrupt combination still needs a
machine-readable row and automated assertion.
