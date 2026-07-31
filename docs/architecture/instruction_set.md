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
and tool tables. It contains all 30 original Appendix A class masks and the
independently visible all-zero NOP semantic fixture. The companion
`docs/generated/adsp2100_instruction_formats.yaml` records all 106 named
fields across the 30 diagrams, including every one of their 393 variable bit
positions [ADI-UM-1989, printed pp. A-1–A-5, scan PDF pp. 140–144].

Automated checks compare those field positions with a separate hand-reviewed
fixture, require them to partition each class mask exactly, and exhaustively
compare the synthesizable class decoder over all 16,777,216 program words with
an independent SystemVerilog transcription.

Type 26 stack control is the first bounded semantic class beyond NOP.
`docs/generated/adsp2100_stack_control.yaml` records the 32 field-defined
words, the behavioral alias between `SPP=00` and `SPP=01`, the independent
status/count/PC/loop stack actions, their combined one-cycle execution, and
the absence of PM/DM data transfers [ADI-UM-1989, printed pp. 1-2,
4-3–4-10, 6-14–6-15, A-4, A-8–A-10]. A separate executable model and
synthesizable action decoder agree with independent fixtures for all 32 words;
exhaustive RTL testing also proves that all other 24-bit words emit no Type 26
actions.

A bounded stateful execution slice now connects Type 26 to all four stack
classes, live CNTR, ASTAT/MSTAT/IMASK, and composed SSTAT. It samples all
sources at cycle start and atomically commits selected actions at cycle end;
nine model checks and 50,015 model-versus-RTL cycles cover all combinations
under valid, empty, full, reset, invalid-opcode, and conflicting-request
conditions. This still does not make the whole processor instruction-complete:
empty-stack pop effects (OQ-013), arbitration with automatic
sequencer/interrupt actions (OQ-018), PC/fetch sequencing,
assembler/disassembler syntax, and logical bus phases remain open. NOP remains
the sole full semantic entry in the main instruction table; most legal
combinations, register effects, parallel ordering, cycle counts, and bus
transactions still require primary-backed entries.
