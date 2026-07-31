# Programmer's model

**Status: partial inventory; computational-bank, status/control, and CNTR
storage slices implemented**

| Group | Original registers | Width | Initial sourced facts |
|---|---|---:|---|
| ALU | AX0, AX1, AY0, AY1, AR, AF | 16 | all banked; AF not generally movable |
| MAC | MX0, MX1, MY0, MY1, MR0, MR1, MR2, MF | 16 except MR2 = 8 | combined MR is 40 bits; all banked |
| Shifter | SI, SE, SB, SR0, SR1 | SI/SR halves 16, SE 8 signed, SB 5 signed | banked |
| DAG1 | I0–I3, M0–M3, L0–L3 | 14 | DM only; optional bit reverse |
| DAG2 | I4–I7, M4–M7, L4–L7 | 14 | PM or DM; no bit reverse |
| Exchange | PX | 8 | preserves low PM byte |
| Sequencer | PC, CNTR, PC/count/loop/status stacks | PC/CNTR 14 | PC stack 16 words; count/status/loop stacks 4 words |
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

The exact Type 17 selector audit confirms 48 readable REG-coded registers and
47 writable destinations. SSTAT is the only encoded read-only destination;
AF, MF, and PC have no general-MOVE code, while blank REG-table cells remain
reserved. This closes register direction and action decode. A bounded execution
slice now composes write effects across computational, DAG, status, PX, CNTR,
and count-stack state. It deliberately does not close the data value for
OQ-016 narrow status reads: those five sources use an observable provisional
zero-extension hypothesis
[ADI-UM-1989, printed pp. 4-22, 6-12, A-3, A-9].

On documented reset, PC-visible PMA is 0x0004 if the bus is not granted, stack
pointers reset, IMASK and MSTAT clear, and ICNTL is undefined. ASTAT is not
listed among the initialized state and remains architecturally unknown
[ADI-UM-1989, printed p. 5-13]. No source in the current corpus says that
computational or DAG registers reset to zero, so the authentic model keeps them
unknown until written.

The independent model and RTL retain MR0/MR1/MR2 and SR0/SR1 as separate
exact-width segments so a partial preload does not initialize untouched
segments. They have no computational-register reset assignment and implement
the documented MR1-preload sign extension into MR2
[ADI-UM-1989, printed p. 2-18]. AF, MF, and SB are also stored in both banks;
unit-specific writes commit ALU results to AR/AF, MAC results to MR/MF, and
shifter results to SR/SE/SB at cycle end. A separate status/control block now
stores exact-width ASTAT/MSTAT/ICNTL/IMASK state, applies the four original
MODE CONTROL fields, commits ALU, divide, MAC, and shifter status at cycle end,
and exposes the documented ASTAT/MSTAT/IMASK interrupt snapshot and mask
transformation [ADI-UM-1989, printed pp. 4-9–4-10, 4-20–4-24, A-8].
The exact Type 25 saturation boundary now uses cycle-start MSTAT bit 0 to
select primary or alternate MR and writes only that bank at cycle end when
cycle-start ASTAT.MV is set; it does not alter ASTAT
[ADI-UM-1989, printed pp. 2-5–2-7, 2-18–2-19, A-4].
The exact Type 6 boundary similarly samples MSTAT at cycle start and writes
the selected computational bank at cycle end for every DREG code. Its full
16-bit immediate is truncated only at the authentic SE/MR2 eight-bit storage
boundary, whose subsequent DREG read sign-extends; an MR1 write also fills MR2
with the MR1 sign bit
[ADI-UM-1989, printed pp. 2-6–2-7, 2-15, 2-18, 6-12–6-13,
A-2, and A-9]. The bounded reset path clears MSTAT without assigning either
bank a fabricated value.
The bounded Type 15 immediate-shift path likewise samples MSTAT and its X
operand at cycle start and commits SR0/SR1 together at cycle end. PASS forms
replace SR, OR forms also consume the old selected-bank SR, and the signed
instruction exponent leaves SE unchanged. Only the seven documented shifter
X operands and SF codes 0–7 execute; the remaining class subencodings fail
closed pending stronger evidence
[ADI-UM-1989, printed pp. 2-23–2-30, 6-11 Table 6.5, A-3, and A-7].
The bounded Type 16 path uses the same cycle-start bank selection for every
LSHIFT/ASHIFT/NORM/EXP/EXPADJ source and feedback register. Condition-false
preserves both banks. Condition-true writes only the SF-selected SR, SE, or SB
destination at cycle end, while EXP HI/HIX update unbanked ASTAT.SS on that
same edge. Unknown reset ASTAT remains unknown in the independent model
[ADI-UM-1989, printed pp. 2-20–2-35, 4-21, 4-25, 6-11, A-3, A-6–A-7].
The exact Type 18 boundary independently applies all AS/OL/BR/SR fields to
cycle-start MSTAT and commits one four-bit result at cycle end. Both
documented no-change encodings preserve their raw decode identity, while
later-family Type 18 controls remain excluded
[ADI-UM-1989, printed pp. 4-22–4-23, 6-14–6-15, A-3, A-8].
A separate DAG register-file boundary stores all eight I, eight M, and eight L
registers at their exact 14-bit widths and tracks per-register validity because
their reset data is not documented. Exact Type 21 execution reads the selected
I and M plus the I-corresponding L from cycle-start state and writes only the
selected I at cycle end. Unknown inputs or inputs outside the documented
circular-placement and `abs(M) <= L` restrictions invalidate that destination
instead of silently inventing a value
[ADI-UM-1989, printed pp. 3-1–3-5, 6-14–6-15, A-4, A-7–A-8].
A separate exact four-by-sixteen status stack and a combined exact
16-by-14 PC/four-by-14 count/four-by-18 loop-stack boundary implement LIFO
storage, pointer saturation, loss of the newest overflowing push, sticky
overflow, and all eight SSTAT sources [ADI-DATABOOK-1987, printed
pp. 2-21–2-22; ADI-UM-1989, printed pp. 4-3–4-7, 4-22]. The two SSTAT
fragments are now composed in the bounded Type 17 and Type 26 execution
slices. This is not yet a whole-core fetch/execute path.

CNTR has 14 value bits plus a separate validity state. Reset invalidates CNTR
without assigning a documented value. A load pushes the old count only when
valid; CE is sampled before the cycle-end decrement, and true CE restores the
count-stack top or leaves CNTR invalid when the stack is empty
[ADI-UM-1989, printed pp. 4-4–4-5]. The independent model and portable RTL
implement this boundary. A bounded sequencer slice physically connects CNTR
to count-stack storage and IF/DO flow for sourced cases, but instruction
decode and a stateful PC remain absent.

Direction-specific restrictions outside the now-bounded Type 17 path, exact
interrupt recognition and priority logic, empty-pop architectural effects,
narrow status-register DMD extension, full
multifunction legality, and every
instruction field using these paths still require machine-readable extraction
and tests.
