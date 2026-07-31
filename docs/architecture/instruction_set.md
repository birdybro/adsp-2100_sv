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
an independent SystemVerilog transcription. These are bit-placement and class
membership results only. NOP remains the sole complete semantic instruction
record; legal combinations, register effects, parallel ordering, cycle counts,
and bus transactions still require primary-backed entries.
