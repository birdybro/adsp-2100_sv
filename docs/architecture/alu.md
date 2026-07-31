# Arithmetic/logic unit

**Status: standard function and both division primitives implemented in
bounded model/RTL; Type 8, Type 9, Type 23, and Type 24 integrations complete**

The original ALU has 16-bit X and Y inputs, a 16-bit result, and carry input
from ASTAT.AC. It generates AZ, AN, AV, AC, AS, and AQ
[ADI-UM-1989, printed pp. 2-5–2-6, 2-13].

Documented standard functions are add, add-with-carry, both subtraction
directions with/without borrow, negate, increment, decrement, pass X/Y/zero,
absolute value, AND, OR, XOR, and NOT; DIVS/DIVQ are iterative primitives
[ADI-UM-1989, printed pp. 2-7, 2-9–2-13].

Carry is the unsigned carry from bit 15 while overflow is the exclusive-OR of
the carries from the two most significant adder stages
[ADI-UM-1989, printed p. 2-13]. AR saturation is controlled by MSTAT and maps
overflow to `0x7fff` or `0x8000`; AV may be sticky in the separate latch mode
[ADI-UM-1989, printed pp. 2-8–2-9, 4-22–4-23].

The later family manual explicitly identifies computational-unit chapters as
shared by all ADSP-2100 family members and gives per-instruction flag behavior
[ADI-UM-FAMILY-1995, printed p. 1-11; printed pp. 15-21–15-37]. For the
original standard AMF functions, logical, NOT, and PASS operations clear AV
and AC; negate sets AC only for a zero operand and AV only for `0x8000`; ABS
clears AC, records the X sign in AS, and sets AN/AV for `0x8000`.

`sim/reference_models/adsp2100_model/alu.py` and
`rtl/core/adsp2100_alu.sv` implement AMF `0x10`–`0x1f`, raw AZ/AN/AV/AC,
ABS-only AS update, sticky AV, and AR-only saturation. Saturation is driven by
overflow generated on the current operation, not an already-sticky AV bit
[ADI-UM-1989, printed pp. 2-8–2-9, Table 2.2].

This combinational block alone is not an instruction implementation. The bounded
`adsp2100_mode_slice` integration connects current MSTAT bits 2/3 to sticky AV
and AR saturation, routes a valid result to cycle-end AR/AF writeback in the
MSTAT-selected bank, and commits AZ/AN/AV/AC plus the ABS-only AS update at the
same boundary. A mode change becomes effective for ALU behavior on the next
cycle, consistent with cycle-start operand use and cycle-end register writes
[ADI-UM-1989, printed pp. 2-6–2-9]. Outside the bounded Type 8 and Type 9
slices, memory multifunction operand selection and complete multifunction
legality remain excluded. Type 23 DIVQ and Type 24 DIVS are implemented in
separate bounded execution slices.

Operands and destinations will use the old/new timing in
`multifunction_instructions.md`. Boundary fixtures must independently cover
`0`, `1`, `-1`, `0x7fff`, `0x8000`, carry/borrow, both overflow directions,
ABS minimum, saturation, sticky AV, and every condition.

## Division initialization

Original Type 24 `DIVS upper, divisor;` initializes a signed 32-by-16
non-restoring divide. The legal upper-dividend sources are AY1 and AF; the
divisor is any of AX0, AX1, AR, MR0, MR1, MR2, SR0, or SR1. AY0 supplies the
low dividend word. With all operands sampled from the cycle-start selected
bank, `qsign = divisor[15] XOR upper[15]`; cycle end writes
`AF={upper[14:0],old AY0[15]}`, `AY0={old AY0[14:0],qsign}`, and
`ASTAT.AQ=qsign`. AZ, AN, AV, AC, AS, MV, and SS are preserved
[ADI-UM-1989, printed pp. 2-9–2-13, 4-21, 6-6–6-9, A-4, B-1–B-8].

Appendix A exposes four YOP field codes, but the exact-device instruction
text lists only AY1 and AF. Contemporary later-device Cross Software material
independently lists the same two permissible Y operands and all eight X
operands [ADI-2101-CROSS-1990, printed pp. 9-17–9-18]. The AY0 and zero YOP
codes therefore remain explicit unsupported Type 24 subencodings, not guessed
aliases. The model and RTL preserve authentic reset unknowns with validity
sideband metadata: an unknown operand invalidates AF, AY0, and AQ only.

## Division quotient iteration

Original Type 23 `DIVQ divisor;` performs one non-restoring quotient
iteration. It accepts all eight ALU-X sources. All values are sampled from the
cycle-start selected bank. When old AQ is one, the 16-bit ALU result `R` is
old AF plus divisor; otherwise `R` is old AF minus divisor. Carry or borrow
beyond bit 15 is discarded. New AQ is `divisor[15] XOR R[15]`; the quotient
bit is its complement. Cycle end atomically writes
`AF={R[14:0],old AY0[15]}`, `AY0={old AY0[14:0],quotient_bit}`, and new AQ
while preserving all other ASTAT bits and the inactive bank
[ADI-UM-1989, printed pp. 2-9–2-13, 4-21, 6-9, A-4, B-1–B-8].

The signed sequence is one DIVS followed by fifteen DIVQ instructions; the
unsigned sequence starts with software clearing AQ and performs sixteen DIVQ
instructions. A composed model regression covers positive and negative signed
examples. Appendix B documents exceptional inputs for which the primitive
sequence can be off by one; those software correction rules are deliberately
not folded into a single DIVQ instruction. The separate slices establish the
two atomic instruction transformations, not integrated consecutive fetch,
loop, interrupt, wait-state, or bus behavior. Unknown divisor, AF, AY0, or AQ
invalidates only AF, AY0, and AQ.

The separate `adsp2100_compute_move_slice` connects every standard ALU AMF
to original Type 8 X/Y/Z selection, selected-bank AR/AF writeback, ASTAT
updates, and one simultaneous old-value DREG move. The fail-closed boundary
rejects Z=0 packets whose move also targets AR and retains AMF zero as OQ-022.
All supported operand and move combinations execute in the exhaustive
983,386-cycle Type 8 comparison; memory multifunction classes remain
unintegrated [ADI-UM-1989, printed pp. 6-4–6-10, A-2,
A-5–A-7, A-11].

The independent `conditional_compute` model and
`adsp2100_conditional_compute_slice` apply the same ALU field maps to every
Type 9 word. COND reads cycle-start ASTAT/NOT CE; true nonzero-AMF actions
commit AR/AF and AZ/AN/AV/AC plus ABS-only AS at cycle end, while false and
AMF-zero actions preserve state. Exhaustive decode covers all 32,768 words,
and the 283,996-cycle differential exercises every word in both banks and
both available predicate outcomes [ADI-UM-1989, printed pp. 2-6–2-13,
4-25, 6-8–6-10, A-2, A-5–A-7].
