# Arithmetic/logic unit

**Status: specification baseline; RTL not started**

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

Operands and destinations use the old/new timing in
`multifunction_instructions.md`. Boundary fixtures must independently cover
`0`, `1`, `-1`, `0x7fff`, `0x8000`, carry/borrow, both overflow directions,
ABS minimum, saturation, sticky AV, and every condition. DIVS/DIVQ exact
iteration state and exception handling remain unimplemented.
