# Conditions and visibility

**Status: original encodings and predicates verified; bounded CNTR/sequencer
integration passes**

The original 4-bit condition selection derives EQ/NE, LT/GE, LE/GT, AC/NOT AC,
AV/NOT AV, MV/NOT MV, NEG/POS, and NOT CE/TRUE for `IF`
[ADI-UM-1989, printed p. 4-25, Table 4.3]. DO UNTIL uses the inverse sense and
offers CE/FOREVER [ADI-UM-1989, printed pp. 4-5–4-6, Table 4.1].

`NOT CE` means the valid cycle-start CNTR value is not one; it does not mean
that CNTR is nonzero. CE is true at one so that a count loaded with N produces
exactly N loop passes. CNTR has no valid value after reset and after a true CE
test with an empty count stack, so the implemented counter source supplies a
separate validity output rather than inventing a predicate in those states
[ADI-UM-1989, printed pp. 4-4–4-5].

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

The reviewed condition-code source of record is
`docs/generated/adsp2100_condition_codes.yaml`. The independent Python
evaluator and combinational RTL are exhaustively compared for all 2,048
condition/flag combinations by `make compute-tests`. The independent CNTR
model/RTL additionally supplies the source predicate and is compared across
50,022 stateful cycles. The bounded sequencer integration slice connects this
predicate to explicit IF flow and stored inverse-sense DO termination and
passes 50,011 additional stateful model-versus-RTL cycles. Conditional JUMP
with field `0xe` updates CNTR, conditional RETURN checks the same predicate
without updating CNTR, and conditional CALL is rejected under OQ-012. Opcode
decode, arithmetic/trap condition consumers, and phase-level timing remain
unimplemented.
