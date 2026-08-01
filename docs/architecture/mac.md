# Multiplier/accumulator

**Status: standard fractional compute model and RTL implemented; Type 4 logical
execution closed; exact Type 25 saturation and bounded Type 8/Type 9 integrations
complete**

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
The combinational compute block alone does not select architectural operands.
The bounded Type 4 slice distinguishes every MAC AMF, X/Y/Z field, and
MR0/MR1/MR2 read-load collision; captures cycle-start inputs, MR feedback, and
old store data; and commits MR/MF plus ASTAT.MV atomically with the
acknowledged DM action. Immediate and waited completion pass the 50,072-clock
comparison. Type 1/5 action selection, native Type 4 DM phases, and all
remaining memory multifunction execution/timing remain unimplemented.

The implementation rounds the complete 40-bit result, including the current
MR contribution, as the primary manual requires. Pinned MAME instead uses the
product low word for its midpoint test in rounded accumulate/subtract paths;
that disagreement is tracked as SC-008 in `docs/research/source_conflicts.md`.
The same register also tracks MAME's omission of MV updates for MF
destinations as SC-009; instruction integration will follow the original
ASTAT table and update MV for every non-saturation MAC operation.

The bounded `adsp2100_compute_move_slice` selects every original standard MAC
AMF `0x01`–`0x0f`, all documented X/Y/Z fields, cycle-start MR feedback,
selected-bank MR/MF writeback, ASTAT.MV, and a simultaneous old-value DREG
move. Z=0 packets whose move also targets MR0/MR1/MR2 fail closed. All
476,672 supported Type 8 ALU/MAC words execute in both banks in the combined
983,386-cycle comparison. AMF zero remains unassigned under OQ-022, and Types
1/5 plus unimplemented memory bus timing remain open
[ADI-UM-1989, printed pp. 2-13–2-20, 6-4–6-10, A-2, A-5–A-7, A-11].

The Type 9 model and RTL select the same original MAC X/Y/Z and MR-feedback
paths behind the cycle-start condition. A true action commits MR/MF and MV at
cycle end; a false predicate or documented AMF-zero no-operation preserves
both computation and status state for the same one-cycle instruction
boundary. All 32,768 class words execute in both banks within the 283,996-cycle
differential [ADI-UM-1989, printed pp. 2-13–2-20, 4-21, 4-25, 6-8–6-10,
A-2, A-5–A-7].
