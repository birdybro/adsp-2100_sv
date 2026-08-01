# Multifunction execution semantics

**Status: key ordering rule and Type 1 action selection verified; bounded Type 4 ALU/MAC-plus-DM,
Type 5 ALU/MAC-plus-PM/cache, Type 8 ALU/MAC-plus-DREG,
Type 12 shifter-plus-DM, Type 13
shifter-plus-PM/cache, and Type 14 shifter-plus-DREG forms integrated**

All computational register reads take their values at the beginning of a cycle
and all writes become visible at the end. Therefore a simultaneous memory load
may overwrite an input only after that input has participated in the
computation [ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 2-28].

For a compute-plus-write using the computation's destination as the store
source, memory receives the old register value and the computation result
becomes the new register value. The original manual illustrates this exact
Type 4 overlap with `DM(I0,M0)=AR, AR=AX0+AY0` and states that the old AR is
written before AR is updated [ADI-UM-1989, printed pp. 6-5–6-6].

The original explicitly supports:

- ALU/MAC plus DM and PM reads;
- DM plus PM reads without computation;
- compute plus one PM or DM read;
- compute plus one PM or DM write;
- compute plus an internal data-register move.

[ADI-UM-1989, printed pp. 6-3–6-7 and Appendix A types 1, 4, 5, 8, 12–14.]

## Type 1 dual-read action boundary

Original Type 1 is the widest multifunction format: fixed prefix `11`, PM
destination PD, DM destination DD, AMF/YOP/XOP, independent DAG2 PM I/M, and
independent DAG1 DM I/M fields. PD maps only to AY0/AY1/MY0/MY1, DD maps only
to AX0/AX1/MX0/MX1, and a nonzero AMF result is restricted to AR or MR. The
three destination sets therefore cannot collide. AMF zero is explicitly the
dual-fetch-only special case. Every computation operand is read at cycle
start; the two newly fetched operands overwrite their input registers only at
cycle end and are first available to the following instruction. A PM read
also loads PX with PMD7-0, while PD receives PMD23-8
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 3-6–3-7, 6-3–6-5,
A-1, A-7–A-11].

The independent action decoder and portable RTL decoder expose every field,
both fixed DAG mappings, selected computation operands, forced AR/MR result,
and both read destinations. Exhaustive Python and RTL traversals classify all
4,194,304 Type 1 words as source-closed. Two hand-derived manual examples,
1,024 representative dual-read-only round trips, every 685 uniquely
spellable result-register computation form, raw aliases, a formal harness,
and a constrained Cyclone V decoder project verify this boundary. This does
not yet execute state. The manual says DMACK extends processor state seven by
one complete processor cycle but does not explicitly state whether the
simultaneous PM read strobe is retained, repeated, or internally completed
during that extension; OQ-023 prevents the native dual-bus attachment from
inventing that behavior.

## Bounded Type 4 execution and logical DM transaction

Original Type 4 has fixed class `011`, DAG selector G, memory direction D,
result selector Z, AMF/YOP/XOP computation fields, one memory DREG, and
same-DAG I/M selectors. AMF zero selects the documented no-operation compute
function, leaving a memory-only indirect read or write. Every operation is
unconditional. A read may not load AR while a Z=0 ALU operation writes AR, or
load MR0/MR1/MR2 while a Z=0 MAC operation writes MR; the corresponding write
overlap is legal because memory observes the cycle-start DREG value
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 5-9–5-12, 6-1,
6-3–6-7, Tables 6.1–6.2 and 6.7, A-1, A-5–A-11].

The independent action model and portable RTL decoder exhaustively partition
all 2,097,152 class words into 2,034,688 supported actions and 62,464 read
destination collisions. They expose both computation operands, direction,
memory DREG, and exact I/M selections. Two manual-derived opcode fixtures,
canonical assembler/disassembler forms, lossless raw alias handling, a
24-bit RTL traversal, and a bounded assertion harness verify this action
boundary.

The bounded state model and portable RTL slice capture the selected bank,
compute operands and result, old DM-write DREG, and selected DAG I/M/L values
when the transaction issues. Every DMACK-low clock preserves the descriptor,
logical bus outputs, and all architectural destinations. The first
acknowledged clock samples a read and atomically commits the optional ALU/MAC
result and ASTAT effects, optional DREG load, and selected-I postmodify. AMF
zero follows the same transaction path without a computational effect.
Directed checks and 50,072 deterministic model/RTL clocks cover immediate and
arbitrarily waited reads/writes, old-value overlap, both banks and DAGs, DAG1
bit reversal, reset abort, integration conflicts, and unknown-dependent
destination invalidation. A separate bounded composition accepts the captured
descriptor only at native state 8-to-1, repeats the complete physical substate
sequence for every DMACK-low sample, and returns only qualified state-7-to-8
completion to the logical client. Six directed tests and 50,082 additional
model/RTL clocks cover reads, old-value writes, memory-only actions, waits,
reset cancellation, off-boundary controls, late ACK, and relinquishment.
Instruction fetch, multiple DM owners, and event arbitration remain open.

## Bounded Type 5 execution

Original Type 5 mirrors the single-memory ALU/MAC action restrictions of
Type 4 but fixes the memory space and address generator to PM and DAG2. Its
fields are fixed `0101`, direction D, result selector Z, AMF/YOP/XOP, one
memory DREG, and local I/M selectors mapping to I4-I7/M4-M7. AMF zero is a
PM-only transfer. A PM read writes DREG from PMD23-8 and PX from PMD7-0; a PM
write reads old `{DREG,PX}`. A read targeting AR while a result-register ALU
operation writes AR, or MR0/MR1/MR2 while a result-register MAC operation
writes MR, is unsupported. The corresponding store overlap is legal because
the PM word uses cycle-start values
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 3-6–3-7, 6-3–6-7,
Tables 6.1–6.2, A-1, A-5–A-11].

Independent Python and synthesizable RTL decoders exhaustively partition all
1,048,576 class words into 1,017,344 source-closed actions and 31,232 read
collisions. Two hand-concatenated fixtures, canonical and raw toolchain
round trips, a depth-one assertion harness, and a constrained Cyclone V fit
verify action selection. The bounded execution paths capture selected-bank
ALU/MAC inputs and feedback, the old PM-store DREG/PX word, and old DAG2 state
once; commit compute/status, optional PM-read DREG/PX, and selected-I
postmodify atomically; preserve all of that state over a held logical PM
transaction; and use the shared 16-word monitor for an issue-time cache hit or
one pure recovery fetch. The native attachment accepts the descriptor only at
state 8-to-1 and exposes its sole architectural completion at state 7-to-8.
Fourteen logical, seven cache, and five native directed tests plus 50,071 logical
and 50,083 native model/RTL clocks cover both banks, ALU/MAC and PM-only forms,
old-value store overlap, read/PX split, cache hits/misses, recovery, reset,
off-boundary rejection, late forced-fetch conversion, and bus relinquishment.
A bounded HALT wrapper adds five directed tests and 50,126 deterministic
model/RTL clocks. All 197 late PM-data recognitions override an issue-time hit,
commit ALU/MAC/PM/PX/DAG2 actions once, and issue one external recovery fetch;
387 stops/resumes complete with no replay. Ordinary fetch ownership, branches,
loops, interrupt/BR arbitration, self-modifying PM, and physical hardware
confirmation remain outside this bounded client under OQ-008.

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
A stateless parallel-action boundary now attaches every canonical packet to
the shared ordinary-fetch owner. Twenty directed tests and 443,740 model/RTL
phase clocks cover native state-8 PC+1 issue, cycle-start reads, and atomic
state-7 DREG/shifter/status/PC/next-word retirement; 50,003-clock BR/BG,
shared-PM/BR-BG, and HALT compositions separately preserve the packet across
their control sequences. Loop-terminal behavior, interrupt abort, unified
PM/cache/event ownership, and OQ-021 bit-15 behavior remain outside this
bounded attachment.

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

Nine directed base-model tests and 50,070 deterministic model/RTL clocks cover PM
read/write packing, PX, both banks, all DAG2 selections, fixed cache-hit and
cache-miss timing, forced fetch, unknown operands/data, reset abort, and live
input conflicts during recovery. A composed independent-model/RTL boundary
connects the next-fetch address to the 16-word monitor, returns the actual
cached word on a hit, fills recovery words on a miss/forced fetch, and accepts
ordinary external instruction fills while Type 13 does not own PM. Ten
directed integration tests and 50,086 additional clocks cover selection,
replacement, unknown entries, reset, and fill ownership.

The phase-attached wrapper captures the complete old-value Type 13 action and
PM descriptor on an enabled state-8-to-state-1 boundary. Shifter, PM-read/PX,
and DAG2 results remain architecturally invisible until the corresponding
state-7-to-state-8 completion. A hit word is captured at issue rather than
re-read from a possibly changed monitor; a miss recovery becomes the next
back-to-back PM transaction and its completion alone fills the monitor and
exposes the next instruction. Five directed tests and 50,081 deterministic
model/RTL clocks exercise read/write drive windows, hit/miss ownership, held
phases, off-boundary rejection, reset, and relinquishment
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8].

A bounded HALT wrapper composes this same owner with the primary-backed
PM-data stop sequence. HALT recognized at state 3 sets recovery on the
in-flight descriptor even when lookup hit at issue. The cached word is not
released, the Type 13 data/shifter/PX/DAG action commits exactly once, and one
external instruction fetch follows without replay. Its completion fills the
cache and enters held state 8. Five directed tests and 50,124 deterministic
model/RTL clocks cover 210 hit overrides/forced fetches and 397 complete
stop/resume sequences. Unified branches, loops, interrupts, self-modifying PM,
ordinary fetch ownership, and whole-core arbitration remain open
under OQ-008.

## Tests still required for the remaining multifunction classes

- source/destination overlap execution for Type 1;
- old store value versus new computation result execution outside Types 12 and 13;
- dual PM/DM loads and independent DAG post-modifies;
- status from the computation visible only to the next cycle;
- condition-false preservation and cycle/bus activity;
- PM cache branch, loop-end, interrupt, BR, tag-fill, and replacement boundaries;
- illegal destination collisions and reserved field combinations beyond the
  bounded Type 8 and Type 12–14 partitions.
