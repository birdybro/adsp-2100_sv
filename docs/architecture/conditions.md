# Conditions and visibility

**Status: original encodings and predicates verified; bounded CNTR/sequencer,
Type 9 ALU/MAC, Type 10 direct-flow, Type 11 loop setup, Type 16 shifter, and
Type 19 indirect-flow, and Type 20 return integrations pass**

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
passes 50,014 additional stateful model-versus-RTL cycles. Conditional JUMP
with field `0xe` updates CNTR, conditional RETURN checks the same predicate
without updating CNTR, and conditional CALL is rejected under OQ-012. Opcode
decode for remaining arithmetic/TRAP consumers and phase-level timing remain
unimplemented.

The bounded Type 16 conditional-shifter slice is the first complete
computational condition consumer. It evaluates COND from cycle-start status
and NOT CE, retains the ordinary one-cycle boundary when false, suppresses all
shifter/status writes on that path, and applies true-path SR/SE/SB/SS writes at
cycle end. All sixteen conditions are exercised with both outcomes where the
predicate is nonconstant, and the stateful regression covers 54,403 cycles.
Unknown reset ASTAT remains unknown in the independent model; it is never
silently coerced to a deterministic predicate
[ADI-UM-1989, printed pp. 4-21, 4-25, 6-11, A-3, A-6].

The bounded Type 9 conditional-compute slice evaluates the same cycle-start
COND input before selecting any ALU/MAC write. False predicates preserve the
selected-bank result registers and ASTAT while retaining a one-cycle boundary;
true predicates commit the result and unit-selected status together. The
1,024 AMF-zero words remain no-operation aliases regardless of predicate.
All 32,768 Type 9 words execute in both banks in 283,996 stateful comparison
cycles, with both outcomes for every nonconstant condition
[ADI-UM-1989, printed pp. 4-21, 4-25, 6-8–6-10, A-2, A-6].

The bounded Type 10 direct-flow slice consumes all sixteen condition codes at
cycle start. A false predicate advances PC without pushing; a true predicate
selects the direct target and a true CALL pushes the return address. JUMP with
field `0xe` additionally performs the sourced post-test CNTR transition. CALL
with field `0xe` remains unsupported under OQ-012 because only a later-device
Cross manual explicitly permits the syntax and the original ADSP-2100 source
does not close its counter side effect. Unknown ASTAT or invalid CNTR context
therefore holds state and reports an invalid boundary instead of inventing a
predicate [ADI-UM-1989, printed pp. 4-3–4-5, 4-12–4-13, 4-25, 6-13–6-14,
A-2, A-6; ADI-2101-CROSS-1990, printed instruction-reference CALL syntax,
later-device evidence only].

The Type 19 slice applies the identical IF and CNTR rules to DAG2-indirect
JUMP/CALL. When the predicate is false, sequential PC+1 is valid even if the
selected I4-I7 value is reset-unknown. A true predicate requires a known
selected I value and otherwise fails closed. JUMP NOT CE post-updates CNTR;
the four CALL NOT CE forms remain OQ-012. This distinction is covered in both
directed tests and the 50,259-cycle model/RTL comparison
[ADI-UM-1989, printed pp. 4-3–4-5, 4-20, 4-25, 6-13–6-14, A-3, A-6].

The Type 20 conditional-return slice samples the same IF predicates at cycle
start. False RTS and RTI advance PC+1 without requiring stack context. A true
predicate requires a valid PC-stack top and RTI additionally requires a valid
status-stack top; missing context fails closed under OQ-013. Return `NOT CE`
samples a valid CNTR value but, unlike JUMP, never post-decrements CNTR or
touches the count stack. All sixteen conditions and both return kinds are
covered across the 50,254-cycle model/RTL comparison
[ADI-UM-1989, printed pp. 4-3–4-4, 4-9–4-10, 4-25, 6-14 Table 6.8,
A-4, A-6].

The Type 11 decoder accepts every inverse-sense DO termination field. Setup
stores TERM without evaluating ASTAT or CNTR; `CE` therefore needs a valid
counter only when that descriptor later becomes the active outer loop context,
not when the first DO is issued. Every one of the 262,144 address/termination
forms round-trips through the tools and executes in the bounded differential
regression [ADI-UM-1989, printed pp. 4-5–4-8, A-2, A-10].
