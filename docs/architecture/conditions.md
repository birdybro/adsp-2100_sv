# Conditions and visibility

**Status: original condition encodings and predicates verified; sequencer
integration pending**

The original 4-bit condition selection derives EQ/NE, LT/GE, LE/GT, AC/NOT AC,
AV/NOT AV, MV/NOT MV, NEG/POS, and NOT CE/TRUE for `IF`
[ADI-UM-1989, printed p. 4-25, Table 4.3]. DO UNTIL uses the inverse sense and
offers CE/FOREVER [ADI-UM-1989, printed pp. 4-5–4-6, Table 4.1].

ASTAT writes at cycle end, so a conditional instruction sees flags from a
previous cycle [ADI-UM-1989, printed pp. 4-21, 4-25]. At a loop end, a true
explicit control transfer takes precedence over implicit loop action
[ADI-UM-1989, printed p. 4-7].

The exact 4-bit IF encoding is `EQ`, `NE`, `GT`, `LE`, `LT`, `GE`, `AV`,
`NOT AV`, `AC`, `NOT AC`, `NEG`, `POS`, `MV`, `NOT MV`, `NOT CE`, and
`TRUE` at codes `0x0` through `0xf`, respectively
[ADI-UM-1989, printed p. A-6, scan PDF p. 145]. `NEG`/`POS` use ASTAT.AS,
not ASTAT.AN. Signed comparisons use `AN XOR AV`, with AZ included for
less-than-or-equal and greater-than [ADI-UM-1989, printed p. 4-25,
Table 4.3].

DO UNTIL stores the inverse-sense condition at the same field value: for
example, source termination `NE` uses field `0x0`, the same field used by
`IF EQ`. `FOREVER` at `0xf` never terminates
[ADI-UM-1989, printed pp. 4-6–4-7, Table 4.1; printed pp. A-10–A-11,
scan PDF pp. 149–150].

The reviewed source of record is
`docs/generated/adsp2100_condition_codes.yaml`. The independent Python
evaluator and combinational RTL are exhaustively compared for all 2,048
condition/flag combinations by `make compute-tests`. This closes the
predicate truth table, not counter post-decrement, loop-stack, or instruction
timing.
