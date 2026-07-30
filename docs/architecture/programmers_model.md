# Programmer's model

**Status: partial inventory; computational DREG access audit implemented**

| Group | Original registers | Width | Initial sourced facts |
|---|---|---:|---|
| ALU | AX0, AX1, AY0, AY1, AR, AF | 16 | all banked; AF not generally movable |
| MAC | MX0, MX1, MY0, MY1, MR0, MR1, MR2, MF | 16 except MR2 = 8 | combined MR is 40 bits; all banked |
| Shifter | SI, SE, SB, SR0, SR1 | SI/SR halves 16, SE 8 signed, SB 5 signed | banked |
| DAG1 | I0–I3, M0–M3, L0–L3 | 14 | DM only; optional bit reverse |
| DAG2 | I4–I7, M4–M7, L4–L7 | 14 | PM or DM; no bit reverse |
| Exchange | PX | 8 | preserves low PM byte |
| Sequencer | PC, CNTR, PC/count/loop/status stacks | PC/CNTR 14 | PC stack 16 words; count/loop stacks 4 words |
| Status | ASTAT, SSTAT, MSTAT, ICNTL, IMASK | 8, 8, 4, 5, 4 | SSTAT read-only/reset `0x55`; ICNTL undefined at reset |

Computational and exchange registers:
[ADI-UM-1989, printed pp. 2-5–2-8, 2-13–2-20, 2-20–2-30,
3-6–3-8]. DAG widths/roles: [ADI-UM-1989, printed pp. 3-1–3-3].
Sequencer widths/depths: [ADI-UM-1989, printed pp. 4-3–4-6]. Status fields:
[ADI-UM-1989, printed pp. 4-20–4-24].

MR2 drives a 16-bit internal/data bus by sign extension. SE and SB are signed
two's-complement values and likewise sign-extend on DMD reads
[ADI-UM-1989, printed pp. 2-15, 2-21]. Appendix A's general MOVE table assigns
the four-bit REG code within four RGP groups and confirms reserved holes and
that AF, MF, and PC are not generally movable [ADI-UM-1989, printed p. A-9,
scan PDF p. 148].

On documented reset, PC-visible PMA is 0x0004 if the bus is not granted, stack
pointers reset, IMASK and MSTAT clear, and ICNTL is undefined
[ADI-UM-1989, printed p. 5-13]. No source in the current corpus says that
computational or DAG registers reset to zero, so the authentic model keeps them
unknown until written.

The independent model now retains MR0/MR1/MR2 and SR0/SR1 as separate
exact-width segments so a partial preload does not initialize untouched
segments. The DREG RTL has no reset assignment and implements the documented
MR1-preload sign extension into MR2 [ADI-UM-1989, printed p. 2-18].

Direction-specific restrictions outside DREG, AF/MF/SB writeback, MSTAT and
interrupt interactions, and every instruction field using these codes still
require machine-readable extraction and tests.
