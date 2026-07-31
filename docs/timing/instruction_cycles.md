# Instruction-cycle timing

**Status: baseline, not complete cycle table**

An ordinary instruction occupies one processor cycle, but PM-data/cache-miss
fetches, waits, and control events add externally visible cycles
[ADI-UM-1989, printed pp. 1-2, 6-21]. The project therefore records both
architectural execution and bus-phase count.

Known cases:

| Case | Current sourced timing |
|---|---|
| ordinary instruction | one eight-state processor cycle |
| Type 8 ALU/MAC plus internal DREG move | one processor cycle; both clauses read at cycle start and commit at cycle end; no PM-data or DM transfer |
| Type 9 conditional ALU/MAC | one processor cycle whether true, false, or AMF-zero no-operation; no PM-data or DM transfer |
| Type 10 direct JUMP/CALL | one processor cycle at the bounded instruction boundary for true or false supported conditions; no PM-data or DM data transfer |
| Type 11 DO UNTIL setup | one processor cycle; PC+1 and `{TERM,ADDR}` push simultaneously while PC advances to the first loop instruction; no PM-data or DM data transfer |
| Type 19 indirect JUMP/CALL | one processor cycle for true or false supported conditions; a taken transfer makes DAG2 supply PMA/PC from I4-I7 without modifying I; no PM-data or DM data transfer |
| Type 20 conditional RTS/RTI | one processor cycle whether true or false; a taken RTS pops PC, a taken RTI pops PC/status and restores status atomically; return NOT CE never post-decrements CNTR; no PM-data or DM data transfer |
| Type 6 immediate DREG load | one processor cycle; no PM-data or DM transfer |
| Type 14 shifter plus internal DREG move | one processor cycle; both clauses read at cycle start and commit at cycle end; no PM-data or DM transfer |
| Type 15 immediate LSHIFT/ASHIFT | one processor cycle; no PM-data or DM transfer |
| Type 16 conditional shifter | one processor cycle whether true or false; no PM-data or DM transfer |
| Type 17 internal data MOVE | one processor cycle; no PM-data or DM transfer |
| Type 18 combined MODE CONTROL | one processor cycle for all selected original mode fields |
| Type 21 `MODIFY (Ix, My);` | one processor cycle; no PM-data or DM transfer |
| Type 25 `IF MV SAT MR;` | one processor cycle whether MV is true or false |
| Type 26 combined stack control | one processor cycle for any field-defined action combination |
| PM data access, next instruction valid in cache | no fetch overhead |
| PM data access, invalid cache | one additional instruction-fetch cycle |
| interrupt vectoring | two cycles described, including vector jump |
| DMACK low | extend state 7 by whole processor cycles until high |
| HALT during PM data | forced instruction-fetch cycle before stop |

Sources: [ADI-UM-1989, printed pp. 4-9–4-10, 4-26–4-28, 5-9,
5-13–5-16, 6-14–6-15, 6-21, A-4, A-8–A-10]. The Type 26
combination wording is corroborated, but not extended, by
[ADI-2101-CROSS-1990, printed pp. 9-26–9-27 and 9-61].

The bounded Type 25 model/RTL slice verifies that cycle-start MV, selected
bank, and MR determine a single cycle-end MR write, while false MV preserves
state without changing the one-cycle boundary, across 50,112 stateful cycles.
This is instruction-boundary evidence, not external fetch-phase evidence
[ADI-UM-1989, printed pp. 2-18–2-19 and A-4].

The bounded Type 6 model/RTL slice verifies one cycle-start bank selection and
one cycle-end DREG write across all immediate values and destinations, with no
PM-data or DM transaction. Its 50,204-cycle state comparison establishes this
instruction boundary but does not model overlapped fetch, waits, interrupts,
or external bus phases
[ADI-UM-1989, printed pp. 1-2, 2-6–2-7, 6-12–6-13, A-2, and A-9].

The bounded Type 15 model/RTL slice verifies a cycle-start selected-bank
operand read, optional old-SR read for OR forms, and one cycle-end SR write.
Its signed immediate does not access SE and it emits no PM-data or DM request.
The 58,709-cycle comparison covers all 14,336 supported words in both banks;
fetch overlap, loop-terminal handling, interrupts, waits, and external bus
phases remain outside the boundary
[ADI-UM-1989, printed pp. 2-23–2-30, 6-11 Table 6.5, A-3, and A-7].

The bounded Type 16 model/RTL slice verifies cycle-start condition, bank,
operand, SE/SR/SB, and ASTAT inputs followed by function-selected cycle-end
SR/SE/SB/SS writes. A false predicate preserves all of those destinations
without changing the one-cycle boundary. Its exhaustive decoder partitions
all 2,048 class words, and 54,403 model/RTL cycles cover every one of the 1,792
supported words in both banks. This is still an instruction-boundary result;
fetch overlap, loop termination, interrupt recognition/abort, wait extension,
and pin-level phase sequencing remain open
[ADI-UM-1989, printed pp. 2-20–2-35, 4-21, 4-25, 6-1–6-2, 6-11, A-3, A-6–A-7].

The bounded Type 14 model/RTL slice verifies simultaneous cycle-start shifter
and move reads followed by noncolliding cycle-end DREG, SR/SE/SB, and SS
writes. Its exhaustive decoder partitions all 65,536 class words, and 82,597
model/RTL cycles cover every one of the 25,648 supported canonical words in
both banks. This remains an instruction-boundary result; fetch overlap,
loop-terminal handling, interrupts, waits, and pin-level phases remain open
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 6-4–6-7, A-3, and A-7].

The bounded Type 8 model/RTL slice verifies simultaneous cycle-start ALU/MAC
and DREG-move reads followed by atomic noncolliding computation, status, and
move writes. Exhaustive decode partitions all 524,288 class words and 983,386
model/RTL cycles execute every one of the 476,672 supported words in both
banks. This remains instruction-boundary evidence; fetch overlap,
loop-terminal handling, interrupts, waits, and pin-level phases remain open
[ADI-UM-1989, printed pp. 2-6–2-20, 6-4–6-10, A-2, A-5–A-7, A-11].

The bounded Type 9 model/RTL slice verifies cycle-start condition, bank,
operands, feedback, and arithmetic modes followed by true-only cycle-end
result/status writes. False and AMF-zero paths preserve state without changing
the one-cycle boundary. Exhaustive decode covers all 32,768 class words, and
283,996 model/RTL cycles execute every word in both banks and both available
condition outcomes. Fetch overlap, counter-valid integration, loop-terminal
handling, interrupts, waits, and pin-level phases remain open
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
not fetch-phase or external-pin timing evidence.

The bounded Type 26 model/RTL execution slice verifies that every selected
status/count/loop/PC action reads cycle-start state and commits on the same
cycle-end edge across 50,015 stateful cycles. This is instruction-boundary
evidence only; fetch overlap, the eight logical internal states, wait
extension, and external bus phases are not yet connected to that slice.

Every opcode/taken/false/cache/loop/interrupt combination still needs a
machine-readable row and automated assertion.
