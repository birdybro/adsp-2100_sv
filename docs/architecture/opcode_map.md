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
