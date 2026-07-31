# Open architecture questions

| ID | Question | Competing hypotheses | Evidence needed | Hard Drivin' impact | Status |
|---|---|---|---|---|---|
| OQ-001 | What changed between ADSP-2100 and ADSP-2100A? | speed/process only; functional mask fixes; package-only ordering | original combined data-sheet revisions, errata, mask records | potentially timing/reset | OPEN |
| OQ-002 | What are power-up values of unlisted registers? | retained unknown; device-dependent; implicitly cleared | original reset table, simulator/hardware signatures | low for ROM boot, high for authenticity | OPEN |
| OQ-003 | What occurs for reserved opcodes? | trap, undefined state, no-op, alias | Cross-Software diagnostics and physical-chip test | unknown | OPEN |
| OQ-004 | What are status-stack depth and overflow side effects? | Resolved: four 16-bit entries; pointer saturates, newest overflowing pushes are lost, overflow sticks until reset | ADI-DATABOOK-1987 printed pp. 2-21–2-22 and ADI-UM-1989 printed p. 4-22 | interrupt nesting diagnostics | RESOLVED_PRIMARY |
| OQ-005 | Does DMACK affect all Hard Drivin' DM ranges identically? | tied high globally; PAL-selected waits; asynchronous host region | drawing A044421 net tracing and PAL equations | high | OPEN |
| OQ-006 | Exact ADSP/ADSP II package and mask markings? | 2100 PGA vs 2100 PQFP; possible 2100A production substitution | board photos/BOMs/repair records | qualification identity | OPEN |
| OQ-007 | What are PAL/GAL equations for host, SIM, SOM, and banking? | recoverable from archived equations; infer from schematics; only MAME behavior available | Atari archives, JEDEC dumps, physical board | critical wrapper behavior | OPEN |
| OQ-008 | What is the exact original PM-data cache miss transaction sequence for every control-flow interaction? | two-cycle fixed sequence; branch/interrupt-dependent abort rules | 1989 timing figures, directed original simulator/hardware traces | cycle accuracy | OPEN |
| OQ-009 | Does the original assembler/cross-software accept every algebraic form later tools accept? | strict original subset; compatible superset | ADSP-2100 Cross-Software Manual or isolated tool run | ROM/source reconstruction | OPEN |
| OQ-010 | Are ADSP-2100 TRAP/HALT mechanisms used by Atari host control beyond direct pins? | pin-only host stop; TRAP diagnostic handshake; both | schematic/ROM/MAME trace comparison | high | OPEN |
| OQ-011 | How does NORM negate manually loaded `SE=0x80`? | mathematical +128 gives left-off-scale zero; 8-bit wrap gives right-off-scale extension | original simulator or physical-chip signature | low; EXP never generates this value | OPEN |
| OQ-012 | Does a conditional CALL using CE test and post-decrement CNTR? | CALL behaves like JUMP; CALL tests without decrement; condition is illegal | original pp. 4-3–4-5 identify conditional JUMP but not CALL as decrementing, while later-device ADI-2101-CROSS-1990 permits CALL NOT CE syntax; original tool diagnostics or hardware signature still required | low/unknown | OPEN; all 16,384 Type 10 and all four Type 19 CALL NOT CE encodings fail closed |
| OQ-013 | What value/state results from popping an already-empty stack? | pointer saturates and stale bottom is exposed; no data change; undefined | original simulator and physical-chip signatures for each stack | low unless corrupt code or diagnostics rely on it | OPEN |
| OQ-014 | What happens if an illegal multifunction encoding writes one computational destination twice, including an MR1 preload colliding with MR2? | one source wins; both writes combine; undefined result | original assembler rejection, original simulator behavior, or physical-chip signature | low unless diagnostics execute illegal encodings | OPEN |
| OQ-015 | At which exact boundary does an MSTAT bank-select change become visible relative to interrupt recognition and context stacking? | end-of-instruction before interrupt entry; interrupt entry sees old bank; device-specific ordering | original instruction/timing reference or physical-chip trace around MODE CONTROL plus IRQ | context-switch timing | OPEN |
| OQ-016 | What values occupy unused upper DMD bits when narrow ASTAT, MSTAT, SSTAT, IMASK, or ICNTL is read by a general MOVE? | zero extension; sign extension; retained bus bits; device-specific undefined | original Cross-Software/instruction reference, original simulator signature, or physical-chip register test | low for normal software, relevant to exact register reads | OPEN; PROVISIONAL zero-extension isolated in Type 17 slice |
| OQ-017 | Can any original legal encoding request competing direct/automatic ASTAT writes or direct MSTAT plus active MODE CONTROL, and if so what wins? | encodings are illegal; direct move wins; automatic update wins; undefined | complete original instruction legality table, assembler diagnostics, or hardware signature | low unless diagnostics use an unusual multifunction form | OPEN |
| OQ-018 | What is the architectural ordering when one instruction boundary requests competing automatic and explicit sequencer-state actions, such as CNTR load at a CE loop end, manual stack pop plus automatic loop pop, or DO UNTIL setup on an outer loop's end instruction? | encoding/context is illegal; explicit action wins; automatic loop action wins; multiple ordered updates occur | original instruction legality/reference text, original simulator diagnostics, or physical-chip signature | low for normal compiler output, relevant to adversarial cycle accuracy | OPEN; Type 11 and generic sequencer slices fail closed for DO on an active outer terminal, while the independently sourced same-terminal nesting restriction is now enforced separately |
| OQ-019 | What does the original device do for Type 15 SF 8–15 or XOP `001` subencodings? | reserved/illegal; alias another shifter action; undocumented execution | original ADSP-2100 instruction reference/tool diagnostics or physical-chip signature | unknown; likely low for assembled software | OPEN; all 18,432 affected words fail closed |
| OQ-020 | What does the original device do for Type 16 XOP `001` subencodings? | reserved/illegal; hidden X operand; undocumented execution | original ADSP-2100 instruction reference/tool diagnostics or physical-chip signature | unknown; likely low for assembled software | OPEN; all 256 affected words fail closed |
| OQ-021 | Does original Type 14 bit 15 behave as an ignored don't-care, require zero, or select undocumented behavior? | ignored with both values equivalent; zero-only canonical encoding; bit one reserved or undocumented | original ADSP-2100 Cross-Software opcode output/diagnostics or physical-chip signatures comparing otherwise identical bit-15 pairs | unknown; normal assembler output is expected to use zero | OPEN; canonical bit-zero words may execute, all 32,768 bit-one words fail closed |
| OQ-022 | Is `AMF=00000` a legal no-computation alias in original Type 8, and if so does its DREG move still execute? | move-only alias; reserved/illegal because Type 8 requires a computation; result depends on undocumented compute destination behavior | original ADSP-2100 Cross-Software assembly/diagnostics, original simulator trace, or physical-chip signature | unknown; likely low for assembled software | OPEN; all 16,384 affected Type 8 words fail closed |

Provisional behavior must cite one of these IDs in code and tests. Resolving an
item requires updating the relevant architecture document, task confidence, and
changelog.

OQ-016 remains open after reviewing the original 1989 manual's register and
MOVE sections. They establish the stored widths and DMD readability but do not
state the unused upper-bit values for these five sources
[ADI-UM-1989, printed pp. 4-20–4-24, 6-1–6-2, 6-12, A-9]. As a lower-authority
observation, pinned MAME commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab` dispatches Type 17 through its
register accessors and returns ASTAT, MSTAT, SSTAT, IMASK, and ICNTL as
nonnegative integer members, which effectively zero-extends them at that
boundary [MAME-ADSP2100-CORE, `adsp2100.cpp` lines 1375–1394;
MAME-ADSP2100-OPS, `2100ops.hxx` lines 440–450 and 532–543]. The independent
model and bounded RTL therefore implement zero-extension only as a labeled
provisional hypothesis and assert an observable provisional flag whenever one
of those sources is selected. MAME does not promote the hypothesis to
primary-verified or physical-hardware evidence.
