# Multiplier/accumulator

**Status: standard fractional compute model and RTL implemented; exact Type 25
saturation integrated; general MAC instruction integration pending**

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

The later family manual explicitly identifies the computational units as
common core architecture [ADI-UM-FAMILY-1995, printed p. 1-11] and confirms
the AMF-specific signedness, accumulation, rounding, MF extraction, and MV
effects [ADI-UM-FAMILY-1995, printed pp. 15-41–15-48]. Its integer multiplier
mode is a later extension and is excluded from the original-device block.

`sim/reference_models/adsp2100_model/mac.py` and
`rtl/core/adsp2100_mac.sv` implement AMF `0x01`–`0x0f`, the fixed original
fractional product alignment, all four input signedness combinations, 40-bit
multiply/add/subtract, unbiased rounding, MF bits 31–16, MV, and the
independent one-shot SAT MR transform. `rtl/core/adsp2100_mr_saturate.sv` is
the single shared RTL primitive for that transform.

The exact original Type 25 word `0x050000`, algebraically
`IF MV SAT MR;`, now has a separate source-backed semantic record, independent
state model, exact decoder, and synthesizable bounded execution slice. It reads
cycle-start ASTAT.MV, MSTAT.SR, and selected-bank MR; `MV=0` preserves all
state, while `MV=1` writes the sign-selected saturation value to the same bank
at cycle end without changing ASTAT [ADI-UM-1989, printed pp. 2-18–2-19 and
A-4; ADI-ASM-1994, printed pp. 3-47 and A-4]. Nine directed/schema/
random tests and 50,112 model-versus-RTL cycles cover both signs, both banks,
false condition, reset unknowns, invalid words, and fail-closed setup
collisions. Exact interrupt-adjacent ordering remains OQ-015.

The separate register file accepts a full MAC result for atomic MR or
MF-middle-word writeback in the selected bank.
The separate status block accepts MV at the documented cycle-end boundary.
The compute block still does not select architectural operands, suppress a
false condition for general Type 1/4/5/8/9 computations, or implement complete
multifunction legality/timing.

The implementation rounds the complete 40-bit result, including the current
MR contribution, as the primary manual requires. Pinned MAME instead uses the
product low word for its midpoint test in rounded accumulate/subtract paths;
that disagreement is tracked as SC-008 in `docs/research/source_conflicts.md`.
The same register also tracks MAME's omission of MV updates for MF
destinations as SC-009; instruction integration will follow the original
ASTAT table and update MV for every non-saturation MAC operation.
