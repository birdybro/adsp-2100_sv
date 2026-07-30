# Opcode map

**Status: all 30 top-level masks transcribed and mechanically checked; field
semantics and legal subencodings remain incomplete**

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

The 30 shown classes cover only part of the 24-bit space. The original manual
states that every code not shown is reserved. The database therefore has an
explicit `RESERVED_UNSHOWN` fallback whose execution behavior is
`UNDOCUMENTED`; model and RTL must fail closed rather than treating it as NOP.

The masks are not instruction completeness. Function, register, condition,
address, legality, and parallel-action tables remain to be independently
transcribed.
