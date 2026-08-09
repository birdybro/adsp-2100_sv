# Opcode map

**Status: all 30 top-level masks and diagrammed field positions transcribed
and mechanically checked; field semantics and legal subencodings remain
incomplete**

| Original type | Class |
|---:|---|
| 1 | ALU/MAC + DM read + PM read |
| 2 | DM write, immediate data |
| 3 | direct DM read/write |
| 4 | ALU/MAC + DM read/write |
| 5 | ALU/MAC + PM read/write |
| 6 | data-register immediate |
| 7 | non-data-register immediate |
| 8 | ALU/MAC + internal data-register move |
| 9 | conditional ALU/MAC |
| 10 | conditional direct jump/call |
| 11 | DO UNTIL |
| 12–13 | shifter + DM/PM read/write |
| 14 | shifter + internal data-register move |
| 15 | immediate shift |
| 16 | conditional shift |
| 17 | internal data move |
| 18 | mode control |
| 19 | conditional indirect jump/call |
| 20 | conditional return |
| 21 | modify address register |
| 22 | conditional TRAP |
| 23–26 | DIVQ, DIVS, saturate MR, stack control |
| 27–29 | reserved |
| 30 | NOP |

Source: [ADI-UM-1989, printed pp. A-1–A-5, scan PDF pp. 140–144].
The reviewed masks and values are maintained in
`docs/generated/adsp2100_isa.yaml` and rendered into
`docs/generated/opcode_classes.md`. Validation checks pattern/mask agreement,
pairwise non-overlap, representative boundary fixtures, and the all-zero NOP.
An independent SystemVerilog classifier exhaustively checks all 16,777,216
program words against the generated synthesizable class decoder.

The 30 shown classes cover only part of the 24-bit space. The original manual
states that every code not shown is reserved. The database therefore has an
explicit `RESERVED_UNSHOWN` fallback whose execution behavior is
`UNDOCUMENTED`; model and RTL must fail closed rather than treating it as NOP.

The masks are not instruction completeness. Function meanings, register
effects, legality constraints, timing, and parallel-action semantics remain to
be independently transcribed into complete semantic instruction records.

Type 1 has mask/value `0xc00000`/`0xc00000`. PD, DD, AMF, YOP, XOP, PM-I,
PM-M, DM-I, and DM-M occupy bits 21 through 0 without gaps. PD maps to the
four Y-input registers, DD maps to the four X-input registers, PM I/M map to
DAG2, and DM I/M map to DAG1. A nonzero AMF is forced to AR or MR; AMF zero
retains the two reads. These disjoint destinations make all 4,194,304 class
words source-closed at the action boundary. Exhaustive independent Python and
RTL traversal closes field/action selection. A bounded logical state slice
additionally captures both DAG/read descriptors and optional computation,
holds them together, and atomically commits both loads, PX, both I updates,
and compute/status across 51,069 model/RTL clocks. Cache/fetch/events and
native dual-bus phases remain OQ-023 [ADI-UM-1989, printed pp. 6-3–6-5, A-1,
A-5–A-11].

Type 4 has mask/value `0xe00000`/`0x600000`. Its G, D, Z, AMF, YOP,
XOP, DREG, I, and M fields occupy bits 20 through 0 without gaps. The sourced
destination rule partitions all 2,097,152 class words into 2,034,688 bounded
actions and 62,464 prohibited DM-read/computation destination collisions;
AMF zero retains memory-only transfers. Exhaustive model and RTL checks close
this field/action partition, and bounded logical/native execution covers the
supported partition; whole-core ownership and event arbitration remain open
[ADI-UM-1989, printed pp. 6-3–6-7, 6-12–6-13, A-1, A-5–A-11].

Type 5 has mask/value `0xf00000`/`0x500000`. D, Z, AMF, YOP, XOP, DREG, I,
and M occupy bits 19 through 0 without gaps; I/M always map to DAG2. Its
source-backed destination rule partitions all 1,048,576 class words into
1,017,344 bounded actions and 31,232 prohibited PM-read/computation
destination collisions. AMF zero retains PM-only transfers. Exhaustive model
and RTL checks close action decode, while bounded state/cache/native-PM
execution covers the supported partition; whole-core PM ownership remains
open [ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8, 6-3–6-7,
A-1, A-5–A-11].

The 19 finite abbreviation tables for AMF, data registers, DAG selectors,
stack controls, jump/return types, shifter functions, and X/Y/Z operands are
now fully transcribed in `docs/generated/adsp2100_isa_fields.yaml`
[ADI-UM-1989, printed pp. A-5–A-11, scan PDF pp. 144–150]. Condition and
general-register tables remain separately machine-readable because they carry
additional predicate and register-width/access metadata. Instruction-format
bit placement for all 30 types is machine-readable in
`docs/generated/adsp2100_instruction_formats.yaml`; it contains 106 named
fields covering all 393 variable positions. Its validator proves that the
fields exactly partition each class mask and compares every position with an
independently maintained visual-review fixture. Legal cross-field
combinations remain incomplete.

The field audit corrected Type 26. The original stack-control diagram places
PC-stack pop `PP` at bit 4, followed by `LP[3]`, `CP[2]`, and `SPP[1:0]`.
The correct class mask is therefore `0xffffe0`, not the earlier local
`0xfffff0` transcription. The 30 shown classes cover 15,473,178 words, leaving
1,304,038 explicitly reserved-unshown words.

Type 17 has mask/value `0xfff000`/`0x0d0000`. DEST_RGP, SOURCE_RGP,
DEST_REG, and SOURCE_REG occupy bits `[11:10]`, `[9:8]`, `[7:4]`, and
`[3:0]`. Applying the original REG table and SSTAT's read-only restriction
partitions its 4,096 field-defined words into 2,256 legal moves and 1,840
reserved/read-only-destination subencodings. The exact RTL decoder has been
checked over all 16,777,216 words; this closes action selection, not composed
register-state execution [ADI-UM-1989, printed pp. 4-22, 6-12, A-3, A-9].

All 32 Type 26 payloads are now represented by the bounded
`docs/generated/adsp2100_stack_control.yaml` semantics database. `SPP[1:0]`
selects status-stack no-change/no-change/push/pop; `CP`, `LP`, and `PP`
independently request count-, loop-, and PC-stack pops. The original combined
syntax and one-cycle instruction rule support parallel assertion of these
actions [ADI-UM-1989, printed pp. 1-2, 6-14–6-15, A-4, A-8–A-10].
This closes action selection, not stateful underflow behavior or whole-core
instruction execution.

Type 25 is the exact single word `0x050000`, with no variable fields.
`docs/generated/adsp2100_mr_saturation.yaml` records its fixed MV condition,
selected-bank MR source/destination, two saturation limits, status
preservation, and one-cycle action [ADI-UM-1989, printed pp. 2-18–2-19 and
A-4]. An independent exhaustive RTL decoder proves that this word alone
activates the Type 25 execution slice.

Type 18 has mask/value `0xfff00f`/`0x0c0000`, leaving exactly four two-bit
MCC fields. AS, OL, BR, and SR occupy bits `[11:10]`, `[9:8]`, `[7:6]`, and
`[5:4]`, respectively. Each independently selects no-change (`00` or `01`),
deactivate (`10`), or activate (`11`) for MSTAT bits 3 through 0
[ADI-UM-1989, printed pp. A-3 and A-8]. The semantic validator accounts for
all 256 words, 81 distinct action bundles, and 16 actionless aliases. An
exhaustive RTL traversal proves that no other 24-bit word emits a Type 18
action.

Type 21 has mask/value `0xffffe0`/`0x090000`. Its five payload bits are
`G[4]`, `I[3:2]`, and `M[1:0]`, giving exactly 32 same-DAG address-modify
selections. `G=0` maps the two-bit selectors to I0–I3 and M0–M3; `G=1` maps
them to I4–I7 and M4–M7. The corresponding L register is selected by I.
The semantic validator and exhaustive RTL traversal prove that all 32 words
decode exactly and that every other 24-bit word emits no Type 21 action
[ADI-UM-1989, printed pp. A-4 and A-7–A-8].
