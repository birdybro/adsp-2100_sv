# Reset, halt, trap, and bus request

**Status: reset phase, normal BR/BG, and Type 22 handshake bounded in RTL**

RESET is recognized on a CLKIN rising edge, must remain asserted for at least
four CLKIN cycles, holds state 4 and CLKOUT low, and releases into state 5 on
the second rising edge after release [ADI-UM-1989, printed p. 5-13].

Reset initializes clocking, resets stack pointers, invalidates cache monitoring,
clears IRQ/HALT latches, drives PMA=0x0004 unless BG is active, clears IMASK
and MSTAT, and leaves ICNTL undefined [ADI-UM-1989, printed p. 5-13].

The standalone cache RTL clears only monitor/data-valid state on reset. It
does not fabricate zeros in the 16-by-24 data array, matching the documented
monitor invalidation without inventing a cache-data reset value [ADI-UM-1989,
printed p. 5-13].

## Reset and logical-phase implementation boundary

`rtl/core/adsp2100_reset_phase.sv` and the structurally independent
`sim/reference_models/adsp2100_model/reset_phase.py` implement the exact
source-backed digital boundary that can be represented portably:

- one synchronous FPGA clock enable represents one CLKIN edge, with an
  explicit input indicating whether that edge is rising;
- RESET recognition occurs only on an enabled rising edge;
- four sampled asserted rising edges are required by the bounded digital
  contract, the recognized state is state 4, and CLKOUT is low;
- the first enabled rising edge after deassertion remains in state 4;
- the second enabled rising edge after deassertion advances to state 5; and
- subsequent enabled edges traverse states 5, 6, 7, 8, 1, 2, 3, and 4 without
  a generated or gated clock.

The authentic pre-RESET FPGA state is deliberately not initialized. The first
recognized RESET edge establishes valid phase state. A RESET pulse that does
not meet the documented minimum fails closed in state 4 and exposes a sticky
duration-error output; this is implementation protection, not a claim about
the real device after its specified minimum has been violated. A new asserted
rising edge restarts qualification.

Because a synthesis tool cannot preserve a portable architectural `X` as a
runtime validity state, it may optimize `phase_valid_o` after observing that
every defined transition sets it. Integrators must assert RESET before using
any phase output; `phase_valid_o` is a simulation/formal observation, not a
substitute for that system requirement. The Quartus smoke fit reports this
constant-output optimization explicitly.

Six directed model tests and 50,034 deterministic model/RTL clocks cover
recognition, minimum duration, both release edges, ordinary phase traversal,
disabled edges, mid-run RESET, too-short RESET, and restart. The accompanying
formal harness states reset/phase invariants; proof execution remains pending
because SymbiYosys/Yosys are unavailable in the current environment.

This module does **not** yet own program memory. The manual explicitly fixes
PMA at `0x0004` during RESET when the bus is not granted, but does not provide
a reset-specific PMRD/PMS waveform between recognition and the state-5 release
boundary [ADI-UM-1989, printed p. 5-13]. OQ-024 therefore withholds that pin
attachment instead of borrowing the ordinary-fetch waveform.

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

## Normal BR/BG sequence

BR and BG are active low. A BR level meeting setup at the end of state 3 is
recognized there; the current instruction finishes and the processor stops in
state 8. BG asserts at the end of state 3 of what would have been the following
instruction, exactly four CLKIN cycles (one complete eight-state processor
cycle) after recognition. While BG is low, every PM and DM address, control,
and data-driver signal is tristated and internal processor state is preserved
[ADI-UM-1989, printed pp. 5-3–5-6, Figure 5.3; ADI-DATABOOK-1987, printed
pp. 2-17, 2-33–2-35].

BR release is recognized at the corresponding enabled end-of-state-3 sample.
BG deasserts four CLKIN cycles later and instruction issue resumes at the next
state-8-to-state-1 boundary [ADI-UM-1989, printed pp. 5-4–5-5, Figure 5.3].
`rtl/core/adsp2100_bus_control.sv` implements this normal-operation sequence
without gated clocks. It inhibits only new instruction issue after recognition
so a transaction belonging to the current instruction can finish, exposes
the grant interval separately for PM/DM output-enable masking, and re-enables
issue on the state-8 restart edge.

The machine-readable contract is
`docs/generated/adsp2100_bus_control.yaml`. Seven directed tests and 50,084
deterministic model/RTL clocks cover request/grant and release/restart latency,
phase holds, reset, the output-enable mask, and invalid early withdrawal or
reassertion. Invalid handshake changes fail closed with explicit protocol
events; that protective behavior is an implementation contract, not a claim
about unspecified real-device input sequences.

The original RESET-time BR/BG path is asynchronous: BG follows an asserted BR
without waiting for the normal state-3 sequence, and BR must be removed before
or with RESET release [ADI-UM-1989, printed p. 5-6].
`rtl/wrappers/adsp2100_reset_bus_grant.sv` confines that direct native-pin path
to a wrapper and does not feed asynchronous control into architectural state.
It models the logical relationship, not analog propagation delay. The normal
controller assumes BR satisfies the documented sampling boundary; metastability
and board-level synchronization remain integration responsibilities.
