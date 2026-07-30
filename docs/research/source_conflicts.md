# Source conflicts and applicability hazards

## SC-001 — Original package summary versus contemporary ordering table

The 1989 manual's key-feature list names a 100-pin PGA
[ADI-UM-1989, printed p. 1-3], while the 1987 data-book ordering table also
lists 100-lead PLCC order codes [ADI-DATABOOK-1987, ADSP-2100 data-sheet
ordering information following printed p. 2-35]. This may reflect manual
revision lag rather than an architectural conflict. Do not infer pin identity
until the original data-sheet package tables are indexed.

## SC-002 — “Every instruction is single cycle” versus visible overhead cycles

Original literature markets single-cycle instructions
[ADI-UM-1989, printed pp. 1-2, 1-7], but the same manual documents an extra
fetch cycle for a PM-data access when cache cannot supply the next instruction
[ADI-UM-1989, printed pp. 1-7, 6-21]. The implementation must distinguish
instruction execution latency from instruction-fetch/bus overhead.

## SC-003 — Later unified family ISA is a superset

The 1995 instruction reference includes IDLE, bit manipulation, I/O-space,
programmable flags, timer mode, and multiplier mode
[ADI-UM-FAMILY-1995, printed pp. 15-1, 15-16–15-17]. The original appendix
instead lists TRAP and a smaller MSTAT/opcode set
[ADI-UM-1989, printed pp. 4-22–4-23, A-1–A-4]. Later assembler or MAME
decode must not define original legality.

## SC-004 — Family bus grant behavior differs from original

The later family overview says execution may continue during bus grant while
internal memory suffices [ADI-UM-FAMILY-1995, printed p. 1-3]. The original
ADSP-2100 stops after the current instruction and tristates both external
interfaces [ADI-UM-1989, printed pp. 5-3–5-5]. Default RTL follows the latter.

## SC-005 — Board-name/package statements need schematic/BOM corroboration

Original engineer commentary says the ADSP board is PGA and ADSP II is PQFP
[ATARI-MARGOLIN, “ADSP Board”]. The acquired schematic set contains both a
100-pin ADSP2100 CPU sheet and a separate ADSP2100 PQFP pinout sheet
[ATARI-ADSP-SCHEM, drawing A044421 sheet 3 left PDF p. 6; PQFP pinout PDF
p. 19]. Board revisions and fitted markings remain to be mapped.

## SC-006 — Original reserved opcodes are later-family instructions

The original Appendix A assigns every word beginning with top byte `0x01`,
`0x02`, or `0x03` to reserved Types 29, 28, and 27 respectively
[ADI-UM-1989, printed p. A-5, scan PDF p. 144]. MAME's family disassembler
uses these bytes for later I/O-space, flag/IDLE, and flag-input branch
instructions [MAME-ADSP2100-DASM, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 245–294]. The original
decoder must classify the whole three-byte regions as reserved, regardless of
what a later-family oracle prints.

## SC-007 — MAME accepts an original fixed bit in indirect jumps

Original Type 19 shows opcode bit 5 fixed at zero
[ADI-UM-1989, printed p. A-3, scan PDF p. 142]. MAME checks only that bits
15–8 are zero and then decodes I selection from bits 7–6, call/jump from bit 4,
and the condition from bits 3–0; it does not reject bit 5
[MAME-ADSP2100-DASM, same commit, lines 363–379]. The original database follows
the primary diagram, so a word such as `0x0b0020` is `RESERVED_UNSHOWN`.
Physical or original-tool behavior remains desirable evidence, but MAME does
not override the fixed primary-source bit.

## SC-008 — MAME rounded MAC midpoint test omits the MR low word

The original manual says the 40-bit accumulator result R is rounded at the
MR0/MR1 boundary and illustrates midpoint parity using the complete result
[ADI-UM-1989, printed pp. 2-19–2-20]. In rounded accumulate and subtract
paths, pinned MAME forms the full result but tests the product temporary's low
16 bits when applying the midpoint correction
[MAME-ADSP2100-OPS, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 1409–1439].

These differ whenever MR0 changes the result's fractional word. The clean-room
model and RTL follow the primary description and include a zero-product,
nonzero-MR midpoint test. MAME differential tooling must classify this case as
a known reference divergence unless original hardware or tools establish an
erratum.

## SC-009 — MAME leaves MV unchanged for MAC results directed to MF

The original ASTAT table says MV is updated by every MAC operation except SAT
MR [ADI-UM-1989, printed p. 4-21]. The explicitly common family instruction
reference likewise lists MV as generated for multiply, accumulate, and
subtract with either MR or MF destination
[ADI-UM-FAMILY-1995, printed pp. 15-41–15-46].

Pinned MAME updates MV at the end of its MR-destination path
[MAME-ADSP2100-OPS, same commit, lines 1530–1534], but its corresponding
MF-destination path writes MF and returns without updating MV
[MAME-ADSP2100-OPS, same commit, lines 1690–1842]. Instruction integration
will follow the original ASTAT rule for both destinations and will retain a
dedicated MF-destination MV regression. Hardware confirmation remains useful,
but MAME does not override the explicit original table.

## SC-010 — Later-family and MAME circular-base masks differ from ADSP-2100

The original manual defines a circular-buffer base by clearing the number of
low bits required to represent unsigned L and explicitly says L=8 requires
four cleared bits and a multiple-of-16 base
[ADI-UM-1989, printed pp. 3-3–3-4]. The contemporary toolchain manual calls
this the one circular-placement difference between the ADSP-2100 and every
other ADSP-21xx: later parts require only a multiple-of-8 base for L=8
[ADI-ASM-1994, section 3.7.2.2, printed pp. 3-29–3-32].

Pinned MAME's mask table uses the later rule: its L=8 case returns mask
`0x3ff8`, not the original `0x3ff0`
[MAME-ADSP2100-CORE, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 1089–1106].
The default clean-room model and RTL implement the primary-backed original
rule. Differential tooling must classify power-of-two placements in the
later-only half-block as a known MAME divergence.

## SC-011 — Original and later manuals differ at modify-equals-length

The original ADSP-2100 manual permits a modify value “less than or equal to”
the circular-buffer length and explains that this limits one operation to one
wrap [ADI-UM-1989, printed p. 3-4]. The later family manual states the
restriction as `|M| < L` [ADI-UM-FAMILY-1995, printed pp. 4-4–4-6].

The original-device model therefore treats `abs(M) == L` as valid; one wrap
returns the same I. This case has a directed model/RTL vector. Original hardware
confirmation remains desirable, and no later-family rule is generalized back
to the ADSP-2100.
