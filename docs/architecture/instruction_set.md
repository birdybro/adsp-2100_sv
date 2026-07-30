# Original ADSP-2100 instruction set

**Status: encoding-class inventory started; no completeness claim**

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

`docs/generated/adsp2100_isa.yaml` is the only future source for generated
decode and tool tables. It currently contains a schema and the independently
visible all-zero NOP fixture only. The original scan's field diagrams require
image-assisted transcription and two-person or independent-tool review before
bulk opcode entry.
