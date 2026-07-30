# Arithmetic/logic unit

**Status: standard non-division function model and RTL implemented; instruction
integration pending**

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

This block is not yet an instruction implementation. The separate register
file now accepts its result for cycle-end AR/AF writeback in the selected
bank, but operand selection, decode connectivity, conditional suppression,
ASTAT timing, and multifunction legality remain outside it. DIVS/DIVQ are
also excluded.

Operands and destinations will use the old/new timing in
`multifunction_instructions.md`. Boundary fixtures must independently cover
`0`, `1`, `-1`, `0x7fff`, `0x8000`, carry/borrow, both overflow directions,
ABS minimum, saturation, sticky AV, and every condition. DIVS/DIVQ exact
iteration state and exception handling remain unimplemented.
