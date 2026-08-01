# Original ADSP-2100 instruction set

**Status: encoding-class and bit-placement inventory complete; semantic
instruction inventory incomplete**

The original manual groups instructions as computational, moves, program flow,
multifunction, and miscellaneous [ADI-UM-1989, printed pp. 6-1–6-15].
Appendix A identifies 30 top-level formats and says all unshown codes are
reserved [ADI-UM-1989, printed pp. A-1–A-4].

The original set includes ALU/MAC/shifter operations, register/immediate/PM/DM
moves, direct/indirect conditional jump, DO UNTIL, conditional return, address
modify, conditional TRAP, DIVQ/DIVS, MR saturation, explicit stack control,
mode control, and NOP [ADI-UM-1989, printed pp. A-1–A-4].

Later-family IDLE, I/O-space, programmable flag, timer-mode, integer multiplier
mode, and bit-test/set/clear/toggle forms are not accepted solely from the 1995
family reference [ADI-UM-FAMILY-1995, printed pp. 15-1, 15-16–15-17].

`docs/generated/adsp2100_isa.yaml` is the source for generated class decode
and tool tables. It contains all 30 original Appendix A class masks plus
independently reviewed semantic entries for all-zero NOP, exact Type 25
MR saturation, all Type 2 immediate DM writes, all Type 6 immediate DREG
loads, 507,904 supported Type 7 immediate non-data-register loads, the
source-closed Type 15
immediate-shift subset, all 4,194,304 source-closed Type 1 action words,
1,556,480 source-closed Type 3 direct-DM words with bounded state/native execution,
2,034,688 source-closed Type 4 action words,
1,017,344 source-closed Type 5 action words,
25,648 fetched-bounded Type 14 shifter-plus-DREG words, all
1,792 source-backed Type 16 conditional shifter words, 476,672 bounded Type 8
ALU/MAC-plus-DREG words, all 32,768 Type 9 conditional ALU/MAC words,
507,904 source-closed Type 10 direct JUMP/CALL words, all 262,144 Type 11
DO UNTIL setup words, 124 source-closed Type 19 DAG2-indirect JUMP/CALL words,
all 32 Type 20 conditional RTS/RTI words,
all 16 Type 22 conditional TRAP words, all eight Type 23 DIVQ words,
16 source-closed Type 24 DIVS words,
parameterized Type 18
mode control, and all 32 Type 21
MODIFY selections. The companion
`docs/generated/adsp2100_instruction_formats.yaml` records all 106 named
fields across the 30 diagrams, including every one of their 393 variable bit
positions [ADI-UM-1989, printed pp. A-1–A-5, scan PDF pp. 140–144].

Automated checks compare those field positions with a separate hand-reviewed
fixture, require them to partition each class mask exactly, and exhaustively
compare the synthesizable class decoder over all 16,777,216 program words with
an independent SystemVerilog transcription.

Type 1 encodes `11 PD[1:0] DD[1:0] AMF[4:0] YOP[1:0] XOP[2:0]
PM-I[1:0] PM-M[1:0] DM-I[1:0] DM-M[1:0]`. PD selects AY0, AY1, MY0,
or MY1 for the PM read; DD independently selects AX0, AX1, MX0, or MX1 for
the DM read. PM always uses DAG2 and DM always uses DAG1. A nonzero AMF is an
unconditional ALU or MAC operation whose result is forced to AR or MR; AMF
zero retains both reads without a computation. All computation operands and
DAG values are cycle-start values, while both data loads, PX, compute/status,
and both I postmodifications are cycle-end effects. The three destination sets
are disjoint, so every one of the class's 4,194,304 words has a source-closed
parallel action. An independent exhaustive model decoder, two primary-derived
fixtures, algebraic/raw assembler-disassembler paths, exhaustive RTL, formal
assertions, and a constrained Cyclone V project verify action selection.
Architectural execution, cache recovery, and the native PM relationship while
DMACK extends state seven remain unimplemented under OQ-023
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 3-1–3-7, 6-3–6-5,
A-1, A-5–A-11].

Type 2 encodes `101 G DATA[19:4] I[3:2] M[1:0]`. Every one of its
2,097,152 field combinations is defined: G selects DAG1 or DAG2, DATA is the
raw sixteen-bit value written to DMD, and I/M select registers within that
same DAG. The corresponding L register follows I. The source-backed action
decoder does not assign signedness to DATA and fails closed for every other
instruction class. Six model/metadata tests, three hand-derived fixtures, 160
boundary/selector assembler-disassembler round trips, a formal field harness,
and exhaustive 24-bit RTL traversal close action decode. The bounded execution
model and RTL capture old-I address generation, the raw immediate, and the
post-modified I result once; hold address/data and all architectural state over
arbitrary DMACK-low extensions; and commit only the selected I validity/value
on the first acknowledged boundary. Eleven directed model checks and 50,035
deterministic model/RTL clocks cover both DAGs, DAG1 bit reversal, linear and
invalid circular configurations, every I/M selection, reset cancellation,
request conflicts, immediate completion, and multi-clock waits.
Native active-low phases, fetch/event concurrency, and whole-core arbitration
remain implementation work
[ADI-UM-1989, printed pp. 3-1–3-5, 5-9–5-12, 6-1, 6-12, A-1, and A-6].

Type 3 encodes `100 D RGP[1:0] ADDR[13:0] REG[3:0]`. ADDR is an
absolute 14-bit data-memory address and does not use or modify either DAG.
`D=0` reads DM into a writable general register; `D=1` writes a readable
general register to DM. Applying the original 48-readable/47-writable REG
table to all addresses partitions the 2,097,152 class words into 770,048
legal reads, 786,432 legal writes, and 540,672 unsupported words. The latter
are 262,144 writes from reserved source selectors, 262,144 reads to reserved
destination selectors, and 16,384 reads to read-only SSTAT. They are not
assigned no-op behavior. Independent model/database decoders, two legal and
two invalid hand-derived fixtures, representative assembler/disassembler
round trips, exhaustive 24-bit RTL traversal, formal assertions, and a
constrained Cyclone V decoder project close the action boundary. A separate
bounded execution composition shares the complete general-register state,
captures write data at issue, commits reads only at acknowledgment, and attaches
to native state-8-to-1 issue/state-7-to-8 completion. Its 50,151 logical and
50,077 native model/RTL clocks cover both banks/directions, complete-cycle
waits, register side effects, invalid data, reset, and relinquishment. OQ-016
still applies to writes sourced by narrow status/control registers
[ADI-UM-1989, printed pp. 1-5–1-6, 4-22, 6-1–6-2, 6-12–6-13, A-1,
A-7, and A-9].

Type 4 encodes `011 G D Z AMF[4:0] YOP[1:0] XOP[2:0] DREG[3:0]
I[1:0] M[1:0]`. G maps I/M to DAG1 or DAG2 and D selects a DM read or write.
AMF zero is the documented no-operation computation and therefore closes the
memory-only indirect forms; otherwise AMF selects the standard ALU or MAC
action. The complete 2,097,152-word class partitions into 2,034,688 supported
parallel actions and 62,464 prohibited read-destination collisions. A write
from the computation destination remains supported and supplies the old DREG
value. The independent model, synthesizable exact decoder, two manual-derived
fixtures, exhaustive Python and RTL partitions, assembler/disassembler, and
formal assertions close action selection. A bounded independent state model
and portable RTL slice capture all cycle-start operands, preserve the logical
transaction across DMACK-low clocks, and atomically commit computation/status,
optional DM read, and selected-I postmodify on acknowledgment. Twelve
model/schema/directed checks and 50,072 deterministic model/RTL clocks pass.
Its bounded native attachment adds six directed checks and 50,082 clocks for
state-8 issue, full-cycle DMACK extension, read/write phases, and state-7
atomic completion. Fetch, shared-bus arbitration, and events are not yet
implemented [ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 5-9–5-12,
6-1, 6-3–6-7, 6-12–6-13, A-1, A-5–A-11].

Type 5 encodes `0101 D Z AMF[4:0] YOP[1:0] XOP[2:0] DREG[3:0]
I[1:0] M[1:0]`. Its memory action always uses DAG2, mapping the local I/M
fields to I4-I7 and M4-M7. D selects a 24-bit PM read or write; a read loads
the upper sixteen bits into DREG and the lower eight into PX, while a write
uses cycle-start `{DREG,PX}`. AMF zero is the documented no-operation and
therefore yields a PM-only transfer. The complete 1,048,576-word class
partitions into 1,017,344 supported actions and 31,232 prohibited PM-read
destination collisions. The independent decoder, two manual-derived field
fixtures, assembler/disassembler paths, exhaustive 24-bit RTL traversal,
formal assertions, and constrained Cyclone V fit close action selection.
A bounded independent state model and portable RTL slice capture all
selected-bank ALU/MAC operands, feedback, old `{DREG,PX}`, and DAG2 state;
atomically commit computation/status, optional PM read/PX, and selected-I
postmodify at data completion; select an issue-time cache hit or one pure
recovery fetch; and attach issue/commit to native PM state 8-to-1 and
state 7-to-8. Fourteen logical, six cache, and five native directed tests,
plus 50,071 logical and 50,083 native model/RTL clocks pass. Whole-core fetch,
shared-PM ownership, control-event arbitration, and hidden cache cases remain
open
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 3-6–3-7, 6-3–6-7,
6-12–6-13, A-1, A-5–A-11].

Type 6 loads one full 16-bit immediate into one of the sixteen DREG-coded
computational registers. Its exact format is `0100 DATA[19:4] DREG[3:0]`, so
all 1,048,576 words in the class are field-defined. The bounded model and RTL
sample MSTAT bank selection at cycle start and commit one DREG write at cycle
end without PM-data or DM activity. They preserve the exact eight-bit storage
and sign-extended read behavior of SE and MR2 and the documented MR1-load
sign-fill into MR2. Reset selects the primary bank through cleared MSTAT but
does not invent reset values for either computational bank
[ADI-UM-1989, printed pp. 1-2, 2-6–2-7, 2-15, 2-18,
6-1–6-2, 6-12–6-13, A-2, and A-9]. Two hand-transcribed opcode fixtures,
exhaustive Python and RTL field decode, assembler/disassembler round trips,
and 50,204 stateful model-versus-RTL cycles provide the bounded execution
evidence. Fetch, interrupts, stalls, and external bus phases remain outside
this slice.

Type 7 encodes `0011 RGP[1:0] DATA[13:0] REG[3:0]`. DATA is a raw,
right-justified fourteen-bit immediate. RGP/REG selects one writable original
non-data register: I0-I7, M0-M7, L0-L7, ASTAT, MSTAT, IMASK, ICNTL, CNTR, SB,
or PX. RGP zero denotes the computational-register group handled by Type 6;
blank REG-table cells and read-only SSTAT have no documented Type 7 write
action and fail closed. This partitions all 1,048,576 class words into
507,904 supported and 540,672 unsupported words. The bounded model and RTL
right-justify DATA on the internal 16-bit move path, then retain only the
selected register's exact storage width. An SB destination uses the
cycle-start selected bank; an MSTAT load affects consumers on the following
cycle; and a CNTR load pushes the old count when it is valid before installing
the new fourteen-bit count. No PM-data or DM transfer occurs
[ADI-UM-1989, printed pp. 4-4, 4-22, 6-1–6-2, 6-12–6-13, A-2, and
A-9; ADI-2101-CROSS-1990, printed pp. 9-43–9-44, corroboration only]. Two
hand-derived legal fixtures and three fail-closed fixtures, exhaustive Python
and RTL decode, assembler/disassembler round trips, eight directed tests, and
50,299 stateful model-versus-RTL clocks close this bounded state slice. Fetch,
interrupt abort, active-loop arbitration, and physical instruction-fetch
phases remain outside it.

Type 11 encodes `000101 ADDR[13:0] TERM[3:0]`. All 262,144 field
combinations are defined because the original termination table assigns all
sixteen TERM codes, including `CE` and `FOREVER`. In one cycle the instruction
pushes wrapped PC+1 on the PC stack, pushes `{TERM, ADDR}` on the loop stack,
and advances PC to that same first-loop address. The setup instruction itself
is not part of the loop body and performs no computation or data move. Nested
loops with distinct terminal addresses are accepted; the documented
same-terminal restriction fails closed. Executing a nested DO on the active
outer terminal remains OQ-018. Two hand-derived fixtures, every numeric-target
assembler/disassembler form, exhaustive 24-bit RTL decode, twelve directed
model tests, and 554,309 model-versus-RTL cycles cover the bounded setup state
[ADI-UM-1989, printed pp. 4-5–4-8, 4-16–4-19, 6-1, 6-13–6-14, A-2,
A-10]. Loop-terminal execution is verified separately; fetch overlap,
interrupts, waits, and external bus phases remain outside this slice.

Type 8 encodes Z `[18]`, AMF `[17:13]`, YOP `[12:11]`, XOP `[10:8]`, and
two four-bit DREG move selectors. The model and RTL execute all 476,672
noncolliding words with AMF `0x01`–`0x1f`: ALU/MAC operands and the move
source use cycle-start selected-bank state, while computation result, status,
and move destination commit atomically at cycle end. The other 47,616 words
remain action-free: 16,384 `AMF=0` aliases are OQ-022 and 31,232 request two
writes to the same AR or segmented MR destination. Two hand fixtures,
exhaustive Python/RTL partitioning, canonical algebraic assembly plus raw
alias preservation, and 983,386 model-versus-RTL cycles provide bounded
evidence [ADI-UM-1989, printed pp. 2-6–2-20, 6-4–6-10, A-2, A-5–A-7,
A-11]. Fetch, PC, loop, interrupt, wait, and external bus phases remain
outside the slice.

Type 9 encodes Z `[18]`, AMF `[17:13]`, YOP `[12:11]`, XOP `[10:8]`,
fixed-zero bits `[7:4]`, and COND `[3:0]`. All 31,744 nonzero-AMF words
conditionally execute the sourced standard ALU or MAC action; the remaining
1,024 `AMF=00000` words are documented no-operation aliases. Condition,
operands, feedback, and modes use cycle-start state. A true predicate commits
the Z-selected result and function-selected ASTAT flags at cycle end, while a
false predicate and every AMF-zero word preserve architectural state without
losing the ordinary one-cycle boundary. The format performs no PM-data or DM
transaction. Two hand-derived examples, exhaustive 24-bit RTL decode, ten
directed model tests, all 21,920 uniquely spellable assembler/disassembler
forms, lossless raw alias handling, and 283,996 model-versus-RTL cycles cover
every Type 9 word in both banks and both outcomes for every nonconstant
condition [ADI-UM-1989, printed pp. 2-6–2-20, 4-3–4-5, 4-25, 6-8–6-10,
A-2, A-5–A-7]. Fetch, PC, counter-valid integration, loop-terminal,
interrupt-abort, wait, and external bus phases remain outside the slice.

Type 10 encodes `00011 S ADDR[13:0] COND[3:0]`, where `S=0` selects a
direct JUMP and `S=1` selects a direct CALL. The target is the complete
14-bit instruction address. Every supported instruction reads its predicate
and PC at cycle start. A false predicate selects wrapped PC+1 without a stack
action; a true JUMP selects ADDR; and a true CALL selects ADDR while pushing
wrapped PC+1 on the 16-entry PC stack. JUMP with `COND=0xe` tests cycle-start
NOT CE and performs the documented CNTR post-decrement/restore transition.
The original manual does not unambiguously establish whether CALL with that
condition mutates CNTR, so all 16,384 `S=1, COND=0xe` words remain explicitly
unsupported under OQ-012. This partitions the 524,288-word class into 507,904
source-closed actions and 16,384 fail-closed words. Two hand-derived fixtures,
all supported numeric-target assembler/disassembler forms, exhaustive 24-bit
RTL decode, twelve directed model tests, and 554,412 model-versus-RTL cycles
cover the bounded execution state [ADI-UM-1989, printed pp. 4-3–4-5,
4-12–4-13, 6-13–6-14, A-2, and A-6]. Active-loop terminal arbitration,
fetch overlap, interrupts, wait states, and external bus phases remain outside
this slice.

Type 19 encodes fixed prefix `0000101100000000`, I `[7:6]`, fixed-zero bit
`[5]`, S `[4]`, and COND `[3:0]`. I selects I4 through I7, S selects JUMP or
CALL, and a taken transfer makes DAG2 drive the cycle-start I value onto PMA
so PC loads that address without modifying I. A false predicate advances to
wrapped PC+1 without requiring a known I value; a taken CALL simultaneously
pushes PC+1. JUMP NOT CE performs the same sourced CNTR post-test transition
as the direct form. Four CALL NOT CE words remain OQ-012, partitioning the
128-word class into 124 bounded actions and four fail-closed words. Bit-5-one
words remain `RESERVED_UNSHOWN` under SC-007 even though pinned MAME accepts
them. Two hand-derived fixtures, all 124 assembler/disassembler forms,
exhaustive 24-bit RTL decode, twelve directed tests, and 50,259 model/RTL
cycles cover selected-I validity, all targets, conditions, PMA drive intent,
CALL stacking, CNTR transitions, overflow, reset, and conflicts
[ADI-UM-1989, printed pp. 3-1–3-2, 4-3–4-4, 4-20, 6-13–6-14, A-3,
A-6]. Active-loop arbitration, the following instruction fetch, interrupts,
waits, and PMA pin phases remain outside the bounded slice.

Type 20 encodes fixed prefix `0000101000000000000`, T `[4]`, and COND
`[3:0]`; T selects RTS when zero and RTI when one. All 32 field combinations
are documented. Both forms sample the predicate and stack tops at cycle start.
A false predicate advances to wrapped PC+1 without touching either stack. A
taken RTS loads PC from and pops the PC stack. A taken RTI performs that same
PC action while simultaneously popping the 16-bit status stack and restoring
ASTAT, MSTAT, and IMASK. Unlike conditional JUMP, `NOT CE` on a return only
tests cycle-start CNTR and never decrements it or pops the count stack. A taken
return with missing required stack context fails closed under OQ-013 rather
than inventing empty-pop behavior. Two hand-derived fixtures, all 32 assembler/
disassembler forms, exhaustive 24-bit RTL decode, twelve directed tests, and
50,254 model/RTL cycles cover false/taken flow, RTS/RTI stack differences,
atomic status restoration, NOT CE preservation, reset, and conflicts
[ADI-UM-1989, printed pp. 4-3–4-4, 4-7, 4-9–4-10, 6-14 Table 6.8,
A-4, A-6]. Active-loop arbitration, interrupt recognition/vectoring, the
following instruction fetch, waits, and external bus phases remain outside
the bounded slice.

Type 22 encodes `00001000000000000000 COND[3:0]`. All sixteen condition
forms are source-backed. The phase-aware boundary samples the condition at
accepted cycle start, preserves the decision through a disabled phase
transition, and commits PC+1 at the state-7/state-8 boundary. If true, TRAP
asserts at that boundary and the processor remains in state 8 until an
external HALT is recognized; that recognition clears TRAP but retains halt,
and releasing HALT resumes at PC+1. `NOT CE` does not mutate CNTR. Two
hand-derived fixtures, every assembler/disassembler form, exhaustive 24-bit
RTL decode, twelve directed model tests, and 50,168 model/RTL clocks pass
[ADI-UM-1989, printed pp. 4-3–4-4, 4-25, 5-14–5-15, Figure 5.10, 6-14,
A-4, A-6]. General HALT synchronization, BR/BG, interrupt arbitration, and
attachment to the separate PM bus controller remains open. SC-013 records
MAME's lower-authority
reserved classification.

Type 23 encodes fixed `DIVQ` with XOP `[10:8]`. All eight ALU-X source codes
are legal divisors, so every field-defined word is a source-closed action. Old
AQ selects old AF plus divisor when one and old AF minus divisor when zero;
the low 16-bit result determines new AQ and the quotient bit, then AF and AY0
shift atomically from cycle-start values. Every other ASTAT bit, the inactive
bank, and PM/DM data state are preserved. Two hand-derived fixtures, all eight
algebraic forms, exhaustive 24-bit RTL decode, ten directed model tests, and
50,081 model/RTL cycles provide bounded standalone evidence. A composed test
executes one DIVS plus fifteen DIVQ operations for positive and negative signed
cases. The ordinary-fetch owner now also retires every divisor form from both
banks and both old-AQ paths; a consecutive pair proves that the second DIVQ
reads the first iteration's retired AF/AY0/AQ state within the 443,607-clock
native-fetch comparison
[ADI-UM-1989, printed pp. 2-9–2-13, 4-21, 6-9, A-4, B-1–B-8]. Appendix B's
documented quotient-correction exceptions remain software responsibilities;
A fetched DIVS-to-DIVQ dependency is also covered; active loops, interrupts,
and unified PM/cache/event ownership remain outside this attachment.

Type 24 encodes fixed `DIVS` with YOP `[12:11]` and XOP `[10:8]`. Original
prose permits AY1 or AF as the upper dividend and all eight ALU-X sources as
the divisor, defining sixteen source-closed actions inside the 32 field words.
Each action reads the old selected-bank upper word, divisor, and AY0, then
atomically writes shifted AF/AY0 and the sign XOR to AQ. No other ASTAT bit,
the inactive bank, or PM/DM data state changes. The AY0 and zero upper-source
codes fail closed. Two hand-derived fixtures, every legal algebraic form,
exhaustive 24-bit RTL decode, eleven directed model tests, and 50,109 stateful
model/RTL cycles provide bounded standalone evidence. The ordinary-fetch owner
also retires every legal divisor/upper-source combination in both banks and a
dependent DIVS-to-DIVQ sequence within its 443,607-clock comparison
[ADI-UM-1989, printed pp. 2-9–2-13,
4-21, 6-6–6-9, A-4, B-1–B-8; ADI-2101-CROSS-1990, printed pp. 9-17–9-18,
later-device operand corroboration only]. Reset-first-fetch, active-loop,
interrupt, PM-data/cache, and unified event priority remain outside this
attachment.

Type 15 encodes `SF[14:11]`, `XOP[10:8]`, and a signed eight-bit immediate
exponent in bits `[7:0]`. The original instruction summary permits the eight
LSHIFT/ASHIFT PASS/OR HI/LO functions and the Appendix A X-operand table
permits SI, AR, MR0, MR1, MR2, SR0, and SR1 as shifter sources. These fields
define 14,336 executable words. They sample the selected-bank source and,
for OR forms, SR at cycle start, write selected-bank SR at cycle end, leave
SE and status unchanged, and issue no PM-data or DM transaction
[ADI-UM-1989, printed pp. 2-23–2-30, 6-11 Table 6.5, A-3, and A-7].
The other 18,432 Type 15 class words—XOP `001` or SF `1000` through `1111`—
remain explicitly unsupported rather than being assigned invented behavior.
Two hand-transcribed manual examples, exhaustive Python/RTL partitioning, 280
assembler/disassembler forms, and 58,709 deterministic model-versus-RTL
cycles provide bounded evidence. Fetch, interrupt, loop-terminal, and
external wait-state timing remain outside this slice.

Type 14 encodes an unconditional shifter computation in parallel with one
internal DREG move. The canonical bit-15-zero subset accepts all sixteen SF
functions, seven documented X operands, and all move source/destination pairs
that do not request two writes to SR or SE. Both clauses read cycle-start
selected-bank state and commit together at cycle end. This defines 25,648
executable words; 32,768 unresolved bit-15-one words, 4,096 XOP `001` words,
and 3,024 same-destination words fail closed. Two hand fixtures, all supported
syntax forms, exhaustive Python/RTL partitioning, and 82,597 stateful cycles
provide bounded evidence. A separate 443,607-clock fetched comparison retires
every canonical packet with PC+1 native PM overlap and atomic DREG/shifter/
status/PC/next-word commit
[ADI-UM-1989, printed pp. 1-5, 2-6–2-7, 2-18, 5-5–5-8, 6-4–6-7, A-3,
and A-7]. Loop-terminal and interrupt-abort priority remain outside the
attachment; bit 15 remains OQ-021.

Type 16 encodes SF `[14:11]`, XOP `[10:8]`, fixed-zero bits `[7:4]`, and COND
`[3:0]`. All sixteen SF functions are legal: LSHIFT, ASHIFT, and NORM
PASS/OR HI/LO write SR; EXP HI/HIX write SE and SS; EXP LO conditionally
writes SE; and EXPADJ conditionally writes SB. Combined with the seven
documented shifter X operands this defines 1,792 executable words. The 256
XOP `001` words fail closed under OQ-020. Condition evaluation and all operand
reads use cycle-start state; a true action commits its selected-bank result and
SS at cycle end, while a false action preserves all destinations without
losing its normal one-cycle timing
[ADI-UM-1989, printed pp. 2-20–2-35, 4-25, 6-1–6-2, 6-11 Table 6.5,
A-3, and A-6–A-7]. Two hand fixtures, all 1,792 assembler/disassembler forms,
exhaustive Python/RTL class partitioning, and 54,403 deterministic stateful
cycles provide bounded evidence. Fetch, loop-terminal, interrupt-abort, wait,
and external bus phases remain outside the slice.

Type 17 internal data MOVE now has a bounded action-decode record. Its twelve
payload bits select independent destination/source RGP and REG fields. The
original REG table provides 48 readable registers; excluding read-only SSTAT
leaves 47 writable destinations, so 2,256 of the 4,096 field-defined words
emit a legal move action. The other 1,840 contain a reserved selector or an
SSTAT destination and remain action-free without being treated as NOP
[ADI-UM-1989, printed pp. 6-1–6-2, 6-12, A-3, A-9]. Independent model and RTL
decoders agree for every selector and an exhaustive 24-bit traversal proves
that no non-Type-17 word emits an action. A bounded stateful slice now composes
both computational banks, both DAG register files, status/control, PX, CNTR,
count-stack effects, and SSTAT. It samples the source and MSTAT bank at cycle
start and commits the selected destination at cycle end, including MR1's MR2
sign-fill and CNTR's old-count push. The model executes all 2,256 legal pairs
in both banks, and 59,430 deterministic cycles agree with RTL. OQ-016 remains
open: narrow status sources use explicitly flagged provisional zero-extension,
corroborated but not established by pinned MAME
[MAME-ADSP2100-CORE, commit
030fefcbd14e47c01ec9d67655be90f64a1dc8ab, lines 1375–1394;
MAME-ADSP2100-OPS, same commit, lines 440–450 and 532–543]. Fetch, PC,
interrupt adjacency, and bus phases remain outside this slice.

Type 26 stack control is a bounded semantic class beyond NOP.
`docs/generated/adsp2100_stack_control.yaml` records the 32 field-defined
words, the behavioral alias between `SPP=00` and `SPP=01`, the independent
status/count/PC/loop stack actions, their combined one-cycle execution, and
the absence of PM/DM data transfers [ADI-UM-1989, printed pp. 1-2,
4-3–4-10, 6-14–6-15, A-4, A-8–A-10]. A separate executable model and
synthesizable action decoder agree with independent fixtures for all 32 words;
exhaustive RTL testing also proves that all other 24-bit words emit no Type 26
actions.

A separate primary-backed Type 25 record closes the sole exact
`IF MV SAT MR;` word at `0x050000`. Its independent decoder and RTL exhaustive
test prove that every other 24-bit word is action-free at that boundary. The
stateful model/RTL slice samples cycle-start MV, MSTAT bank selection, and MR,
commits a positive or negative MR limit only when MV is set, preserves status,
and retains the instruction's one-cycle boundary when MV is clear
[ADI-UM-1989, printed pp. 1-2, 2-18–2-19, A-4; ADI-ASM-1994, printed
pp. 3-47 and A-4]. The hand fixture also drives the database-based
assembler/disassembler round trip. The shared ordinary-fetch owner now also
retires this exact word at its native state-7 completion; directed sequences
cover positive and negative saturation in both banks plus the MV-false path
within the 443,607-clock fetched comparison.

A primary-backed Type 18 record closes all 256 field-defined mode-control
words. The four independent two-bit fields are AS `[11:10]`, OL `[9:8]`,
BR `[7:6]`, and SR `[5:4]`; `00` and `01` preserve the corresponding
cycle-start MSTAT bit, `10` clears it, and `11` sets it at cycle end. This
produces 81 distinct action bundles and 16 actionless aliases
[ADI-UM-1989, printed pp. 4-22–4-23, 6-14–6-15, A-3, A-8]. The bounded
model/RTL slice exhausts all 4,096 opcode/initial-MSTAT transforms and adds
seeded state sequences. Later timer, GO, and multiplier-placement fields are
fixed zero and excluded from the original-device decoder.

A primary-backed Type 21 record closes all 32 `MODIFY (Ix, My);` words.
Bit 4 selects DAG1 or DAG2, bits `[3:2]` select one of that DAG's four I
registers, and bits `[1:0]` select one of its four M registers. The
corresponding L register follows the I selection. Execution reads cycle-start
I, M, and L values, applies the original-device linear or circular
post-modification rule, and writes only the selected I register at cycle end.
It performs no PM-data or DM transaction and generates no status
[ADI-UM-1989, printed pp. 3-1–3-5, 6-14–6-15, A-4, A-7–A-8].
The bounded model/RTL slice checks every selection, positive and negative
modifiers, circular wrap in both directions, reset-invalid storage, unsupported
configuration invalidation, and deterministic mixed state sequences.

A bounded stateful execution slice now connects Type 26 to all four stack
classes, live CNTR, ASTAT/MSTAT/IMASK, and composed SSTAT. It samples all
sources at cycle start and atomically commits selected actions at cycle end;
nine model checks and 50,015 model-versus-RTL cycles cover all combinations
under valid, empty, full, reset, invalid-opcode, and conflicting-request
conditions. This still does not make the whole processor instruction-complete:
empty-stack pop effects (OQ-013), arbitration with automatic
sequencer/interrupt actions (OQ-018), PC/fetch sequencing,
assembler/disassembler syntax, and logical bus phases remain open. NOP,
Type 2 bounded logical execution, Type 6, Type 7, Type 9, Type 18, Type 21,
and Type 25 are the class-complete
source-backed semantic entries in the main instruction table. Type 16 has a bounded semantic
entry for its 1,792 documented words while 256 unassigned-XOP subencodings fail
closed. Type 14 has a bounded semantic entry for 25,648 canonical words while
39,888 unresolved or unsupported words fail closed. Type 15 has a bounded semantic entry
for its 14,336 source-closed words while 18,432 subencodings fail closed.
Type 8 has a bounded semantic entry for 476,672 words while 47,616 unresolved
or unsupported words fail closed. Type 9 has a class-complete semantic entry
for all 32,768 words, including the 1,024 documented AMF-zero no-operation
aliases; most
other legal combinations, register effects, parallel ordering, cycle counts,
and bus transactions still require primary-backed entries.
