# Conditions and visibility

**Status: original condition table transcribed semantically**

The original 4-bit condition selection derives EQ/NE, LT/GE, LE/GT, AC/NOT AC,
AV/NOT AV, MV/NOT MV, NEG/POS, and NOT CE/TRUE for `IF`
[ADI-UM-1989, printed p. 4-25, Table 4.3]. DO UNTIL uses the inverse sense and
offers CE/FOREVER [ADI-UM-1989, printed pp. 4-5–4-6, Table 4.1].

ASTAT writes at cycle end, so a conditional instruction sees flags from a
previous cycle [ADI-UM-1989, printed pp. 4-21, 4-25]. At a loop end, a true
explicit control transfer takes precedence over implicit loop action
[ADI-UM-1989, printed p. 4-7].

Exact 4-bit encodings will enter the ISA database only after visual review of
Appendix A's COND table.
