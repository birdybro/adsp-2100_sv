# Barrel shifter

**Status: function block implemented and independently cross-checked;
instruction integration incomplete**

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

This is not yet a complete shifter-instruction implementation. Operand-field
decode, conditional-false behavior, complete multifunction ordering, and
cycle/bus timing remain outside this block. The separate register file now
accepts the explicit result enables for selected-bank SR, SE, or SB
writeback, and the separate status block accepts EXP's explicit SS update;
instruction connectivity remains to be verified during core integration.
