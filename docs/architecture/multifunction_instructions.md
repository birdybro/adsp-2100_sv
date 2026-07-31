# Multifunction execution semantics

**Status: key ordering rule verified; bounded Type 8 ALU/MAC-plus-DREG and
Type 14 shifter-plus-DREG moves integrated; memory multifunction classes
pending**

All computational register reads take their values at the beginning of a cycle
and all writes become visible at the end. Therefore a simultaneous memory load
may overwrite an input only after that input has participated in the
computation [ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 2-28].

For a compute-plus-write using the computation's destination as the store
source, memory receives the old register value and the computation result
becomes the new register value [ADI-UM-FAMILY-1995, printed p. 15-6]. This
later explanation is corroborated by the original generic read/write rule above
and remains `CORROBORATED` until an original instruction-reference example is
located.

The original explicitly supports:

- ALU/MAC plus DM and PM reads;
- DM plus PM reads without computation;
- compute plus one PM or DM read;
- compute plus one PM or DM write;
- compute plus an internal data-register move.

[ADI-UM-1989, printed pp. 6-3–6-7 and Appendix A types 1, 4, 5, 8, 12–14.]

## Bounded Type 8 execution

Original Type 8 combines one unconditional standard ALU or MAC computation
with one internal DREG-to-DREG move. Its exact fields are fixed `00101`, Z,
AMF, YOP, XOP, move destination, and move source. Both clauses sample the
MSTAT-selected bank at cycle start. The move may replace a computation input,
or read the old AR/MR segment while computation replaces that result; all
noncolliding register and ASTAT effects commit together at cycle end. The
instruction issues no PM-data or DM transaction
[ADI-UM-1989, printed pp. 2-6–2-20, 6-4–6-10, A-2, A-5–A-7, A-11].

The bounded decoder executes 476,672 of the 524,288 class words: every
source-backed AMF `00001` through `11111`, all X/Y/Z selections, and every
move pair except a second write to AR for a Z=0 ALU operation or MR0/MR1/MR2
for a Z=0 MAC operation. It fails closed for 31,232 such collisions. The
remaining 16,384 `AMF=00000` words fail closed under OQ-022 because the
instruction chapter requires a computation while Appendix A names that AMF
no operation; neither move-only behavior nor result priority is invented.

Two hand-derived fixtures, 20,513 representative field-exact canonical
assembly packets, raw-word preservation for algebraically ambiguous aliases,
an exhaustive 24-bit RTL traversal, ten directed/model checks, and 983,386
stateful model-versus-RTL cycles cover every supported word in both banks.
The later ADSP-2101 Cross-Software reference explicitly corroborates the
old-value and unsupported-collision rules, but does not override the original
manual [ADI-2101-CROSS-1990, printed pp. 9-71–9-73]. Fetch overlap, terminal
loops, interrupt aborts, wait extension, and external bus phases remain open.

## Bounded Type 14 execution

The original Type 14 format combines one unconditional non-immediate shifter
operation with one DREG-to-DREG move. Both clauses read the selected
computational bank at cycle start and commit their noncolliding destinations
at cycle end. It is therefore legal for the move to replace the shifter input:
the computation still consumes the old value. It is also legal for the move
to read SR0, SR1, or SE while the shifter replaces that result: the move
captures the old value. The normal one-cycle instruction has no PM-data or DM
transaction
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 6-4–6-7, A-3, and A-7].

The bounded canonical decoder accepts bit 15 equal to zero, every one of the
sixteen SF functions, the seven documented shifter X operands, and all
noncolliding DREG source/destination pairs. This produces 25,648 executable
words. It fails closed for 32,768 bit-15-one words under OQ-021, 4,096 words
using XOP `001`, and 3,024 same-destination combinations. The original manual
calls XOP `001` unavailable to the shifter and carries the previous
destination restriction into this form. A contemporary ADSP-2101 programming
reference explicitly calls simultaneous same-destination results indeterminate
and unsupported and shows bit 15 fixed zero; those later statements are
corroboration, not original-device authority
[ADI-UM-1989, printed pp. 6-5–6-7, A-3, and A-7;
ADI-2101-CROSS-1990, printed pp. 9-71–9-73].

Two hand-derived fixtures, all 25,648 canonical assembler/disassembler forms,
an exhaustive 24-bit RTL class traversal, ten model checks, and 82,597
stateful model-versus-RTL cycles cover every supported word in both banks.
Whole-core fetch overlap, loop-terminal behavior, interrupt abort, wait
extension, and bus phases remain outside this bounded instruction boundary.

PM data access can add an instruction-fetch cycle when the cache cannot source
the next instruction [ADI-UM-1989, printed pp. 1-7, 4-26, 6-21]. This external
timing effect is part of the instruction, even though the computation itself is
single-cycle.

## Tests still required for the remaining multifunction classes

- source/destination overlap for memory multifunction groups;
- old store value versus new computation result;
- dual PM/DM loads and independent DAG post-modifies;
- status from the computation visible only to the next cycle;
- condition-false preservation and cycle/bus activity;
- PM cache hit/miss, branch, loop-end, interrupt, wait, HALT, and BR boundaries;
- illegal destination collisions and reserved field combinations beyond the
  bounded Type 8 and Type 14 partitions.
