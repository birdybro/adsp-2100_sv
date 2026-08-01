# Multifunction execution semantics

**Status: key ordering rule verified; bounded Type 8 ALU/MAC-plus-DREG,
Type 12 shifter-plus-DM, Type 13 shifter-plus-PM/cache, and Type 14
shifter-plus-DREG forms integrated**

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

## Bounded Type 12 execution and DM transaction

Original Type 12 combines one unconditional non-immediate shifter operation
with one DAG-addressed DM read or write. The shifter source, DM-write DREG,
and selected I/M/L values are cycle-start values. A read loads its DREG only
at completion; a write drives the old DREG value even if the shifter replaces
that register. The selected I is post-modified only when the transaction
completes. A read may not target the same SR half or SE result written by the
shifter, while the corresponding write overlap is legal because it creates no
second register write [ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 2-28,
6-3–6-7, Tables 6.1–6.2, A-2].

The exact `0001001` class contains 131,072 words. The bounded decoder executes
108,640: both DAGs, both directions, all sixteen SF functions, seven documented
shifter X operands, all DREGs, and all same-DAG I/M pairs, excluding only read
destination collisions. It fails closed for 16,384 unavailable-XOP words and
6,048 read-collision words. Two independent fixtures and every supported
assembler/disassembler form round trip; exhaustive RTL decode traverses all
24-bit words.

The transaction boundary exposes separate logical DM select/read/write,
14-bit address, and 16-bit write data. DMACK-low cycles preserve every
architectural destination and retain address, direction, select, and valid
write data. The first acknowledged boundary samples read data and atomically
commits the memory read, shifter result/status, and DAG post-modify. Directed
tests and 50,069 deterministic model/RTL clocks cover zero and multiple waits,
both banks/DAGs, bit reversal, reset abort, exact and unknown operands, and
randomized legal transactions [ADI-UM-1989, printed pp. 5-9–5-12]. This is
logical bus-cycle evidence; physical eight-state pin waveforms, fetch overlap,
interrupt/BR/HALT latching, and whole-core composition remain open.

## Bounded Type 13 execution and PM/cache transaction

Original Type 13 combines one unconditional non-immediate shifter operation
with a DAG2-addressed PM read or write. The shifter X operand, PM-write DREG,
PX, and I/M/L registers are cycle-start values. A PM read sends bits 23–8 to
the DREG and bits 7–0 to PX; a PM write combines the old DREG as bits 23–8
with old PX as bits 7–0. The selected I4–I7 post-modifies when the PM data
cycle completes. Read collisions with an SR half or SE written by the
shifter fail closed; write overlap is legal because the memory observes the
old DREG/PX values [ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 3-6–3-7,
6-3–6-7, Tables 6.1–6.2, A-3].

The exact `00010001` class contains 65,536 words. The bounded decoder executes
54,320: both directions, all sixteen SF functions, seven documented shifter X
operands, every DREG, and all I4–I7/M4–M7 pairs, excluding only read
destination collisions. It fails closed for 8,192 unavailable-XOP words and
3,024 read-collision words. Two independent fixtures, every supported
assembler/disassembler form, and exhaustive 24-bit RTL decode verify the
partition.

PM data has fixed timing and no DMACK-like acknowledge. On a valid cache hit,
the shifter, PM transfer, PX effect, and DAG2 post-modify commit in one cycle
while the cached next instruction is selected. On a cache miss, those data
actions still commit in the first cycle and exactly one external instruction
fetch recovery cycle follows; the recovery cycle does not repeat any data or
compute action. HALT handoff forces that fetch even if a cache entry is valid.
Interrupt/event recognition occurs only after the completing hit cycle or
after the miss recovery cycle [ADI-UM-1989, printed pp. 4-26–4-30,
5-5–5-8, 5-13–5-16].

Nine directed model tests and 50,070 deterministic model/RTL clocks cover PM
read/write packing, PX, both banks, all DAG2 selections, fixed cache-hit and
cache-miss timing, forced fetch, unknown operands/data, reset abort, and live
input conflicts during recovery. The caller still supplies the next fetch
address and cache-valid decision. Cache tag monitoring, fills/replacement,
branches, loops, interrupts, self-modifying PM, physical eight-state pin
phases, and whole-core arbitration remain open under OQ-008.

## Tests still required for the remaining multifunction classes

- source/destination overlap for Types 1, 4, and 5;
- old store value versus new computation result outside Types 12 and 13;
- dual PM/DM loads and independent DAG post-modifies;
- status from the computation visible only to the next cycle;
- condition-false preservation and cycle/bus activity;
- PM cache branch, loop-end, interrupt, BR, tag-fill, and replacement boundaries;
- illegal destination collisions and reserved field combinations beyond the
  bounded Type 8 and Type 12–14 partitions.
