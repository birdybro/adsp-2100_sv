# Multiplier/accumulator

**Status: specification baseline; RTL not started**

The multiplier has two 16-bit inputs and a 32-bit product. A 40-bit
adder/subtractor accumulates into MR, segmented as 16-bit MR0, 16-bit MR1, and
8-bit MR2 [ADI-UM-1989, printed pp. 2-13–2-15].

The original accepts signed/signed, signed/unsigned, unsigned/signed, and
unsigned/unsigned inputs selected per instruction
[ADI-UM-1989, printed p. 2-17]. Before accumulation, the 32-bit product is
sign-extended and shifted left one bit; product bit 31 aligns with MR bit 32 and
product bit 0 with MR bit 1, while MR bit 0 is zero-filled
[ADI-UM-1989, printed pp. 2-16–2-17]. Later integer/fractional M_MODE behavior
must not be imported.

MV is set when the 40-bit result is not a sign extension of its low 32 bits.
Conditional saturation maps it to the documented positive or negative 40-bit
limit according to MR2's sign [ADI-UM-1989, printed pp. 2-18–2-19,
Table 2.3].

Rounding occurs at the MR0/MR1 boundary and uses unbiased round-to-even
[ADI-UM-1989, printed pp. 2-19–2-20]. Tests must cover every sign combination,
alignment bit, guard segment, MV boundary, both saturation directions, MR1
preload sign extension into MR2, all midpoint parity cases, and MR/MF
destinations.
