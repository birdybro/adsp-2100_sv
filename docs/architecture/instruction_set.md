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
MR saturation, all Type 6 immediate DREG loads, the source-closed Type 15
immediate-shift subset, 25,648 bounded Type 14 shifter-plus-DREG words, all
1,792 source-backed Type 16 conditional shifter words, 476,672 bounded Type 8
ALU/MAC-plus-DREG words, parameterized Type 18
mode control, and all 32 Type 21
MODIFY selections. The companion
`docs/generated/adsp2100_instruction_formats.yaml` records all 106 named
fields across the 30 diagrams, including every one of their 393 variable bit
positions [ADI-UM-1989, printed pp. A-1–A-5, scan PDF pp. 140–144].

Automated checks compare those field positions with a separate hand-reviewed
fixture, require them to partition each class mask exactly, and exhaustively
compare the synthesizable class decoder over all 16,777,216 program words with
an independent SystemVerilog transcription.

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
provide bounded evidence
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 6-4–6-7, A-3, and A-7]. Fetch,
loop-terminal, interrupt-abort, wait, and external bus phases remain outside
the slice; bit 15 remains OQ-021.

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

Type 26 stack control is the first bounded semantic class beyond NOP.
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
assembler/disassembler round trip.

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
Type 6, Type 18, Type 21, and Type 25 are the only class-complete source-backed
semantic entries in the main instruction table. Type 16 has a bounded semantic
entry for its 1,792 documented words while 256 unassigned-XOP subencodings fail
closed. Type 14 has a bounded semantic entry for 25,648 canonical words while
39,888 unresolved or unsupported words fail closed. Type 15 has a bounded semantic entry
for its 14,336 source-closed words while 18,432 subencodings fail closed.
Type 8 has a bounded semantic entry for 476,672 words while 47,616 unresolved
or unsupported words fail closed; most
other legal combinations, register effects, parallel ordering, cycle counts,
and bus transactions still require primary-backed entries.
