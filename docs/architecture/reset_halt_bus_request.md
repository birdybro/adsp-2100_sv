# Reset, halt, trap, and bus request

**Status: logical behavior source-backed; Type 22 handshake bounded in RTL**

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

The independent Type 22 model and
`rtl/core/adsp2100_conditional_trap_slice.sv` accept an instruction decision
in logical state 1, retain it through phase holds, commit PC+1 and a taken
TRAP at the enabled state-7/state-8 transition, hold state 8, clear TRAP on an
already-recognized HALT, and resume at PC+1 when that HALT is released. The
50,168-clock model/RTL comparison includes a disabled state-7 transition and
the complete external handshake. The input is deliberately named
`halt_recognized_i`: HALT synchronization, general pin-driven halt, BR/BG,
interrupt arbitration, and PMS/PMRD control are not invented inside this
bounded slice [ADI-UM-1989, printed pp. 4-3–4-4, 4-25, 5-14–5-15, Figure
5.10, 6-14, A-4, and A-6].

Pinned MAME treats the exact original Type 22 words as reserved; SC-013 records
that reference divergence.

BR recognition halts after the current instruction, then BG asserts and all PM
and DM drive signals tristate. Release restores the same internal state and
resumes [ADI-UM-1989, printed pp. 5-3–5-5]. Reset-time BR is asynchronous and
has special ordering constraints [ADI-UM-1989, printed p. 5-6].
