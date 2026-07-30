# Open architecture questions

| ID | Question | Competing hypotheses | Evidence needed | Hard Drivin' impact | Status |
|---|---|---|---|---|---|
| OQ-001 | What changed between ADSP-2100 and ADSP-2100A? | speed/process only; functional mask fixes; package-only ordering | original combined data-sheet revisions, errata, mask records | potentially timing/reset | OPEN |
| OQ-002 | What are power-up values of unlisted registers? | retained unknown; device-dependent; implicitly cleared | original reset table, simulator/hardware signatures | low for ROM boot, high for authenticity | OPEN |
| OQ-003 | What occurs for reserved opcodes? | trap, undefined state, no-op, alias | Cross-Software diagnostics and physical-chip test | unknown | OPEN |
| OQ-004 | What are status-stack depth and overflow side effects? | four like loop/count; another depth; undefined | original detailed diagram/manual revision or hardware test | interrupt nesting diagnostics | OPEN |
| OQ-005 | Does DMACK affect all Hard Drivin' DM ranges identically? | tied high globally; PAL-selected waits; asynchronous host region | drawing A044421 net tracing and PAL equations | high | OPEN |
| OQ-006 | Exact ADSP/ADSP II package and mask markings? | 2100 PGA vs 2100 PQFP; possible 2100A production substitution | board photos/BOMs/repair records | qualification identity | OPEN |
| OQ-007 | What are PAL/GAL equations for host, SIM, SOM, and banking? | recoverable from archived equations; infer from schematics; only MAME behavior available | Atari archives, JEDEC dumps, physical board | critical wrapper behavior | OPEN |
| OQ-008 | What is the exact original PM-data cache miss transaction sequence for every control-flow interaction? | two-cycle fixed sequence; branch/interrupt-dependent abort rules | 1989 timing figures, directed original simulator/hardware traces | cycle accuracy | OPEN |
| OQ-009 | Does the original assembler/cross-software accept every algebraic form later tools accept? | strict original subset; compatible superset | ADSP-2100 Cross-Software Manual or isolated tool run | ROM/source reconstruction | OPEN |
| OQ-010 | Are ADSP-2100 TRAP/HALT mechanisms used by Atari host control beyond direct pins? | pin-only host stop; TRAP diagnostic handshake; both | schematic/ROM/MAME trace comparison | high | OPEN |
| OQ-011 | How does NORM negate manually loaded `SE=0x80`? | mathematical +128 gives left-off-scale zero; 8-bit wrap gives right-off-scale extension | original simulator or physical-chip signature | low; EXP never generates this value | OPEN |
| OQ-012 | Does a conditional CALL using CE test and post-decrement CNTR? | CALL behaves like JUMP; CALL belongs to the excluded return/trap/arithmetic set; condition is illegal | original instruction reference, tool diagnostics, or hardware signature | low/unknown | OPEN |
| OQ-013 | What value/state results from popping an already-empty stack? | pointer saturates and stale bottom is exposed; no data change; undefined | original simulator and physical-chip signatures for each stack | low unless corrupt code or diagnostics rely on it | OPEN |

Provisional behavior must cite one of these IDs in code and tests. Resolving an
item requires updating the relevant architecture document, task confidence, and
changelog.
