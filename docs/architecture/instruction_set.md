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
MR saturation, parameterized Type 18 mode control, and all 32 Type 21
MODIFY selections. The companion
`docs/generated/adsp2100_instruction_formats.yaml` records all 106 named
fields across the 30 diagrams, including every one of their 393 variable bit
positions [ADI-UM-1989, printed pp. A-1–A-5, scan PDF pp. 140–144].

Automated checks compare those field positions with a separate hand-reviewed
fixture, require them to partition each class mask exactly, and exhaustively
compare the synthesizable class decoder over all 16,777,216 program words with
an independent SystemVerilog transcription.

Type 17 internal data MOVE now has a bounded action-decode record. Its twelve
payload bits select independent destination/source RGP and REG fields. The
original REG table provides 48 readable registers; excluding read-only SSTAT
leaves 47 writable destinations, so 2,256 of the 4,096 field-defined words
emit a legal move action. The other 1,840 contain a reserved selector or an
SSTAT destination and remain action-free without being treated as NOP
[ADI-UM-1989, printed pp. 6-1–6-2, 6-12, A-3, A-9]. Independent model and RTL
decoders agree for every selector and an exhaustive 24-bit traversal proves
that no non-Type-17 word emits an action. Complete state execution remains
open because it must compose banked computational registers, DAG storage,
status/control, PX, CNTR/count-stack effects, and OQ-016 narrow status reads.

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
Type 18, Type 21, and Type 25 are the only full semantic entries in the main
instruction table; most legal combinations, register effects, parallel
ordering, cycle counts, and bus transactions still require primary-backed
entries.
