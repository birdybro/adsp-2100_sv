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
| Type 18 combined MODE CONTROL | one processor cycle for all selected original mode fields |
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

The bounded Type 18 model/RTL slice verifies that all four fields read
cycle-start MSTAT and atomically commit one cycle-end result across every
field combination and initial MSTAT value. The contemporary Cross-Software
reference corroborates that any number of comma-separated controls execute in
one cycle, but it is used only for that shared behavior; its later-device
timer, GO, and multiplier controls are excluded
[ADI-UM-1989, printed pp. 4-22–4-23, 6-14–6-15, A-3, A-8;
ADI-2101-CROSS-1990, printed pp. 9-63–9-64].

The bounded Type 26 model/RTL execution slice verifies that every selected
status/count/loop/PC action reads cycle-start state and commits on the same
cycle-end edge across 50,015 stateful cycles. This is instruction-boundary
evidence only; fetch overlap, the eight logical internal states, wait
extension, and external bus phases are not yet connected to that slice.

Every opcode/taken/false/cache/loop/interrupt combination still needs a
machine-readable row and automated assertion.
