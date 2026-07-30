# Barrel shifter

**Status: specification baseline; RTL not started**

The original shifter maps a 16-bit input into a 32-bit result with 49 placements
from off-scale right through off-scale left. SR is split into SR0/SR1
[ADI-UM-1989, printed pp. 2-20–2-21]. SE is an 8-bit signed two's-complement
shift count; SB is a 5-bit signed block exponent. Both sign-extend on DMD reads
[ADI-UM-1989, printed p. 2-21].

Positive counts shift left and negative counts shift right. HI/LO selects which
half of SR is the reference, and PASS/OR either replaces SR or combines a
shifted piece with the old SR [ADI-UM-1989, printed pp. 2-23–2-24].
Arithmetic/logical shift, normalization, exponent detection, block exponent,
and immediate shift behavior is described in printed pp. 2-26–2-35.

Tests must cover counts across the full signed range, 49 in-range placements,
off-scale fill, HI/LO, PASS/OR with old SR, logical zero fill, arithmetic sign
fill, HIX behavior using AV/AC, exponent extremes, and bank switching.
