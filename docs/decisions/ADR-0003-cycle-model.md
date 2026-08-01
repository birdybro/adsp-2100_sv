# ADR-0003: Eight-state logical cycle model on one FPGA clock

- **Status:** Accepted; bounded PM phase implementation exists, unified core
  sequencing pending
- **Date:** 2026-07-30
- **Tasks:** TIME-001, RTL-PMBUS-001, RTL-DMBUS-001

## Context

The original input clock runs at four times the instruction-cycle frequency,
and its edges define eight processor states per instruction. State 8 is the
neutral halt state. `CLKOUT` is one quarter of `CLKIN`, falling between states
3/4 and rising between states 7/8 [ADI-UM-1989, printed pp. 5-2–5-3,
Figure 5.2].

Recognition and bus actions occur at named states: for example, HALT and BR are
recognized at the end of state 3, DMACK is checked at the end of state 6, and
interrupts at the end of state 7 [ADI-UM-1989, printed pp. 5-3, 5-9,
5-13–5-16].

## Decision

The portable RTL will have one rising-edge FPGA clock and a synchronous phase
enable. An explicit state variable represents original states 1 through 8.
Exactly eight enabled phase transitions form a non-stalled instruction cycle.
Waits, halt, and bus grant extend or hold explicit state; they do not create or
gate clocks. `CLKOUT` and optional trace phase are derived from registered phase
state.

The independent model records the same logical states and external
transactions, but remains structurally independent from RTL state-machine code.
Electrical nanosecond limits stay in wrapper/board timing documentation rather
than delay constructs.

The first concrete native-interface application is the bounded program-bus
controller. It accepts a transaction descriptor on the state-8-to-state-1
edge, generates the sourced PM pin levels for all eight states, samples reads
on the state-7-to-state-8 edge, and masks output enables during externally
commanded bus relinquishment. It does not own or advance the phase counter and
does not decide fetch/data/cache/BR/HALT/interrupt arbitration.

## Consequences

Wrappers must supply a phase-enable rate adequate to represent the original
state edges. Hard Drivin's schematic shows a 32 MHz oscillator feeding CLKIN,
which corresponds to an 8 MHz instruction rate under the sourced divide-by-four
relationship [ATARI-ADSP-SCHEM, drawing A044421, sheet 3 left, PDF p. 6;
ADI-UM-1989, printed p. 5-2]. MiSTer clock selection and PLL constraints remain
open until wrapper synthesis.
