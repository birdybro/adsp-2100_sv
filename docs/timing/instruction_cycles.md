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
| Type 26 combined stack control | one processor cycle for any field-defined action combination |
| PM data access, next instruction valid in cache | no fetch overhead |
| PM data access, invalid cache | one additional instruction-fetch cycle |
| interrupt vectoring | two cycles described, including vector jump |
| DMACK low | extend state 7 by whole processor cycles until high |
| HALT during PM data | forced instruction-fetch cycle before stop |

Sources: [ADI-UM-1989, printed pp. 4-9–4-10, 4-26–4-28, 5-9,
5-13–5-16, 6-14–6-15, 6-21, A-4, A-8–A-10]. The Type 26
combination wording is corroborated, but not extended, by
[ADI-2101-CROSS-1990, printed p. 9-61].

Every opcode/taken/false/cache/loop/interrupt combination still needs a
machine-readable row and automated assertion.
