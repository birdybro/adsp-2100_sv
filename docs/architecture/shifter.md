# Barrel shifter

**Status: function block implemented and independently cross-checked; bounded
Type 12–16 instruction forms integrated**

The original shifter maps a 16-bit input into a 32-bit result with 49
placements from off-scale right through off-scale left. SR is split into
SR0/SR1 [ADI-UM-1989, printed pp. 2-20–2-21]. SE is an 8-bit signed
two's-complement shift count; SB is a 5-bit signed block exponent. Both
sign-extend on DMD reads [ADI-UM-1989, printed p. 2-21].

The original 4-bit SF table assigns all sixteen codes, in order, to four
LSHIFT variants, four ASHIFT variants, four NORM variants, EXP HI, EXP HIX,
EXP LO, and EXPADJ [ADI-UM-1989, Appendix A, printed p. A-10]. The same
function field is used by conditional and multifunction shifter instructions.
Immediate ASHIFT/LSHIFT supplies its signed 8-bit instruction field in place
of SE and does not modify SE [ADI-UM-1989, printed pp. 2-29–2-30].

## Array semantics

For HI reference and shift zero, input bit 15 maps to SR31 and input bit 0 to
SR16. For LO reference and shift zero, those bits map to SR15 and SR0.
Positive counts move this placement toward SR31; negative counts move it
toward SR0. Bits to the right of the input are zero, while left-extension is
instruction-specific [ADI-UM-1989, Table 2.4, printed pp. 2-24–2-25].

- LSHIFT uses zero extension.
- ASHIFT uses input bit 15.
- NORM negates signed SE for its count. NORM HI uses AC as the extension bit;
  NORM LO uses zero. The AC bit becomes observable in the documented
  normalization sequence after EXP HIX reports AV and writes `SE=+1`
  [ADI-UM-1989, printed pp. 2-31–2-35; ADI-UM-FAMILY-1995, printed p. 2-38].
- PASS replaces SR. OR combines the array output with the pre-operation SR
  value [ADI-UM-1989, printed pp. 2-23–2-26].

Counts span the entire signed 8-bit range. Table 2.4 explicitly defines
off-scale outputs: right-off-scale results become all extension bits, and
left-off-scale results become zero. These are defined behaviors, not
host-language oversized-shift behavior.

One writable-state edge remains provisional. NORM negates SE, but the primary
manual does not say whether `SE=0x80` produces mathematical +128 or wraps as
an 8-bit negation to -128. The implementation uses mathematical +128, hence a
left-off-scale zero result. This agrees with pinned MAME but is not primary
proof [MAME-ADSP2100-OPS, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 1994–2093]. EXP-generated
SE values are limited to +1 through -31, so documented normalization sequences
never encounter this edge. See OQ-011.

## Exponent semantics

EXP HI writes SE with the negative count of redundant leading sign bits,
ranging from zero to -15, and writes SS from input bit 15. EXP HIX behaves
identically when AV is clear. When AV is set, HIX writes `SE=+1` and writes SS
with the inverse of input bit 15 [ADI-UM-1989, Table 2.5 and surrounding text,
printed pp. 2-24–2-27].

EXP LO treats the existing SS as the sign of a double-precision input. It
updates SE only if the preceding upper-half operation left `SE=-15`; the
result ranges from -15 when the first lower-half bit differs from SS through
-31 when all sixteen bits equal SS. EXP LO does not update SS
[ADI-UM-1989, printed pp. 2-26–2-27, 2-32–2-34].

EXPADJ derives the same exponent as EXP HI and writes SB only when that signed
value is greater than the existing signed 5-bit SB. Software initializes SB to
-16; a completed scan therefore yields a value from -15 through zero
[ADI-UM-1989, printed pp. 2-27–2-29].

## Implemented boundary

The independent model and combinational RTL implement all sixteen function
codes, exact-width SE/SB/SR behavior, explicit SR/SE/SB/SS write enables, and
pre-operation SR feedback. The regression covers every function over boundary
operands, all 256 signed counts for every shift/NORM code, the complete 16-bit
operand space for every exponent mode, all flag combinations, and
deterministic random values.

This is not yet a complete shifter-instruction implementation. Type 13 PM
multifunction execution is bounded through the implemented 16-word cache,
one-cycle miss recovery, native PM phases, and a HALT attachment that replaces
an issue-time hit with one forced external fetch before stopping. Shared PM
ownership, BR/BG and interrupt priority, and whole-core timing remain outside
the implemented boundaries. The separate register file now
accepts the explicit result enables for selected-bank SR, SE, or SB
writeback, and the separate status block accepts EXP's explicit SS update;
instruction connectivity remains to be verified during core integration.

The separate `adsp2100_immediate_shift_slice` now connects source-backed Type
15 immediate LSHIFT/ASHIFT decode to selected-bank operand reads and SR
writeback. It supports SF codes 0–7 and the seven Appendix A X operands
available to the shifter, for 14,336 executable words. The signed instruction
exponent is used directly; SE is neither read nor written. OR forms read the
old SR and all writes become visible at the cycle-end edge
[ADI-UM-1989, printed pp. 2-23–2-30, 6-11 Table 6.5, A-3, and A-7].

The complete 32,768-word Type 15 class is exhaustively partitioned. XOP code
`001` and SF codes 8–15 do not have a source-backed original immediate-shift
action in the current corpus, so those 18,432 words assert the unsupported
classification and preserve state. The supported words pass both-bank
model/RTL comparison over 58,709 cycles, including the manual's logical and
arithmetic negative-five examples, PASS/OR feedback, every exponent, reset
unknowns and warm-reset bank retention, invalid words, and collision
suppression. A stateless action boundary is additionally attached to the
ordinary linear owner: all 14,336 supported words retire within a 443,607-
clock independent-model/RTL run while PC+1 is fetched through the native PM
phases. Unsupported SF/XOP words still fail closed. Multifunction attachment,
loop-terminal behavior, interrupt timing, and unified event priority remain
unintegrated.

The separate `adsp2100_conditional_shift_slice` connects every source-backed
Type 16 field combination to condition logic, both computational banks, the
all-function shifter, and ASTAT.SS. Type 16 encodes SF `[14:11]`, XOP
`[10:8]`, fixed-zero bits `[7:4]`, and COND `[3:0]`. All sixteen SF codes and
the seven documented X operands form 1,792 executable words. XOP `001` has no
entry in the original shifter operand table, so the other 256 class words fail
closed under OQ-020
[ADI-UM-1989, printed p. 6-11 Table 6.5, pp. A-3 and A-7].

COND is evaluated from cycle-start ASTAT and NOT CE. A false condition remains
a valid one-cycle instruction boundary but suppresses every SR, SE, SB, and SS
write. A true condition samples the selected-bank X operand and the
function-dependent old SE/SR/SB plus AV/AC/SS, then commits the documented
function-selected outputs together at cycle end. EXP HI/HIX update SE and SS;
EXP LO conditionally updates only SE; EXPADJ conditionally updates only SB.
The complete class partition is exhaustively checked, all 1,792 supported
words round trip through the assembler/disassembler, and 54,403 deterministic
model/RTL cycles execute every supported word in both banks under true/false
status patterns plus randomized reset/conflict cases. A stateless action
boundary is additionally attached to the ordinary linear owner: all 1,792
supported words retire within a 443,607-clock independent-model/RTL run while
PC+1 is fetched through the native PM phases. Loop-terminal behavior,
interrupt abort, and unified event priority remain outside the attachment
[ADI-UM-1989, printed pp. 2-20–2-35, 4-25, 6-1–6-2, 6-11, A-3, A-6–A-7].

The bounded `adsp2100_shift_move_slice` implements the canonical Type 14
shifter-plus-internal-DREG form. Both the shifter X operand and move source are
sampled from the cycle-start selected bank. The move may overwrite a shifter
source or read a shifter result register because neither write becomes visible
until cycle end. Noncolliding DREG, SR/SE/SB, and SS results commit together.
The slice executes 25,648 bit-15-zero words and fails closed for all unresolved
bit-15-one, unavailable-XOP, and same-destination words. Its exhaustive decode
and 82,597 stateful comparison cycles cover every supported word in both banks
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 6-4–6-7, A-3, and A-7]. A stateless
parallel-action boundary is additionally attached to the ordinary linear
owner: all 25,648 canonical packets retire within a 443,607-clock independent-
model/RTL run while PC+1 is fetched through the native PM phases. OQ-021
bit-15-one words, unavailable XOP `001`, and same-destination packets remain
fail-closed; loop-terminal behavior, interrupt abort, and unified event
priority remain outside the attachment
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 6-4–6-7, A-3, and A-7].

The separate `adsp2100_shifter_dm_slice` implements the original Type 12
shifter-plus-DM form for all 108,640 source-closed, noncolliding words. It
captures shifter, memory-write, and DAG sources at transaction start; exposes
stable logical DM bus signals through arbitrary DMACK-low extensions; and
commits shifter/status, optional read DREG, and I post-modification together
at acknowledgment. The complete Type 12 class is exhaustively partitioned and
50,069 deterministic state/bus clocks agree with the independent model
[ADI-UM-1989, printed pp. 5-9–5-12, 6-3–6-7, A-2].
