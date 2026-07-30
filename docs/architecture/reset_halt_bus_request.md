# Reset, halt, trap, and bus request

**Status: logical behavior source-backed**

RESET is recognized on a CLKIN rising edge, must remain asserted for at least
four CLKIN cycles, holds state 4 and CLKOUT low, and releases into state 5 on
the second rising edge after release [ADI-UM-1989, printed p. 5-13].

Reset initializes clocking, resets stack pointers, invalidates cache monitoring,
clears IRQ/HALT latches, drives PMA=0x0004 unless BG is active, clears IMASK
and MSTAT, and leaves ICNTL undefined [ADI-UM-1989, printed p. 5-13].

HALT is recognized at state 3 and stops at state 8. If the current cycle is PM
data, a forced instruction fetch completes first; this makes the stopped PMA
observable. Releasing HALT resumes, with DMACK required high
[ADI-UM-1989, printed pp. 5-13–5-14].

TRAP is an output asserted by the TRAP instruction at the state 7/8 boundary
and cleared by asserting HALT; release of HALT resumes
[ADI-UM-1989, printed pp. 5-14–5-15].

BR recognition halts after the current instruction, then BG asserts and all PM
and DM drive signals tristate. Release restores the same internal state and
resumes [ADI-UM-1989, printed pp. 5-3–5-5]. Reset-time BR is asynchronous and
has special ordering constraints [ADI-UM-1989, printed p. 5-6].
