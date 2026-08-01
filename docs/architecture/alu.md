# Arithmetic/logic unit

**Status: standard function and both division primitives implemented in
bounded model/RTL; Type 1 action selection and Type 4 native-DM execution
closed; Type 8 and Type 9 integrations plus fetched Type 23/24 execution
complete within the bounded ordinary owner**

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
[ADI-UM-1989, printed pp. 2-6–2-9]. The bounded Type 4 slice selects every ALU
X/Y/Z field, rejects AR read-load collisions, captures cycle-start operands,
and commits AR/AF plus ASTAT atomically with the acknowledged DM action. Its
50,072-clock logical and 50,082-clock native comparisons include immediate and
wait-extended completion. Outside the bounded Type 4, Type 8, and Type 9
slices, ALU multifunction execution remains excluded. Both Type 23 DIVQ and
Type 24 DIVS are attached to the bounded ordinary-fetch owner.

The Type 5 path covers every ALU AMF/X/Y/Z selection paired with one PM
transfer, rejects AR/PM-read double destinations, samples the selected-bank
operands and old PM-store word at issue, and commits AR/AF plus ASTAT together
with the fixed PM data action. Its cache/native composition passes 50,083
phase clocks with state-8 issue and state-7-only ALU/status/read/I completion;
whole-core PM ownership and event arbitration remain open
[ADI-UM-1989, printed pp. 6-3–6-7, A-1, A-5–A-7].

The Type 1 action decoder covers every ALU AMF/X/Y selection with an implicit
AR destination, one DD-selected DAG1 DM read, and one PD-selected DAG2 PM
read. Both loads occur after the old computation operands are consumed. The
action graph is exhaustive, but ALU/status execution and dual-bus completion
are not yet connected because OQ-023 leaves native PM behavior during a
DMACK extension unresolved
[ADI-UM-1989, printed pp. 2-6–2-7, 6-3–6-5, A-1, A-5–A-7].

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
not folded into a single DIVQ instruction. The Type 23 transformation is
additionally attached to the bounded native ordinary-fetch owner. Two directed
tests and 442,392 phase clocks cover all eight divisors in both banks, both
old-AQ paths, and a following DIVQ that reads the just-retired AF/AY0/AQ state.
The same owner now executes all sixteen legal DIVS operand combinations through
distinct divisor, AY0, and upper-dividend reads; a fetched DIVS-to-DIVQ test
proves the quotient step sees the just-retired seed state. Active-loop,
interrupt, reset-first-fetch, and unified PM/cache/event behavior remain open.
Unknown divisor, AF, AY0, or AQ invalidates only AF, AY0, and AQ in the
standalone unknown-aware slices.

The separate `adsp2100_compute_move_slice` connects every standard ALU AMF
to original Type 8 X/Y/Z selection, selected-bank AR/AF writeback, ASTAT
updates, and one simultaneous old-value DREG move. The fail-closed boundary
rejects Z=0 packets whose move also targets AR and retains AMF zero as OQ-022.
All supported operand and move combinations execute in the exhaustive
983,386-cycle standalone Type 8 comparison. The fetched owner additionally
traverses every compute-field tuple and every move source/destination pair in
both banks within its 442,392-clock comparison, committing the computation,
status, move, PC, and next word atomically at state 7-to-8. Active control
flow, interrupts, and unified PM/cache ownership remain open
[ADI-UM-1989, printed pp. 6-4–6-10, A-2, A-5–A-7, A-11].

The independent `conditional_compute` model and
`adsp2100_conditional_compute_slice` apply the same ALU field maps to every
Type 9 word. COND reads cycle-start ASTAT/NOT CE; true nonzero-AMF actions
commit AR/AF and AZ/AN/AV/AC plus ABS-only AS at cycle end, while false and
AMF-zero actions preserve state. Exhaustive decode covers all 32,768 words,
and the 283,996-cycle differential exercises every word in both banks and
both available predicate outcomes [ADI-UM-1989, printed pp. 2-6–2-13,
4-25, 6-8–6-10, A-2, A-5–A-7].
