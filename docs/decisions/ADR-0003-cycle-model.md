# ADR-0003: Eight-state logical cycle model on one FPGA clock

- **Status:** Accepted; bounded PM and DM phase implementations exist, unified
  core sequencing pending
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

The first bounded architectural client is the Type 13/cache attachment. It
admits an instruction action only on state 8-to-1, captures its complete
old-value PM descriptor, commits that data action only on state 7-to-8, and
uses the following state 8-to-1 for a required back-to-back recovery fetch.
This validates the selected request/commit contract while leaving ordinary
fetch and whole-core control arbitration outside the decision boundary.

The Type 5/cache attachment now applies the same sourced PM boundary to
ALU/MAC-plus-PM actions. It captures selected-bank computation, old
`{DREG,PX}`, and DAG2 state at state 8-to-1; makes state 7-to-8 the sole
compute/status/read/PX/I commit edge; and accepts a miss recovery on the next
state 8-to-1 without repeating the architectural data action. This remains an
independent bounded client, not a shared PM-owner decision.

A bounded shared-PM selector now places ordinary instruction fetch, Type 5 PM
data, and Type 13 PM data descriptors in front of exactly one native PM
controller. It accepts a descriptor only when exactly one requester is
asserted on the enabled state-8-to-state-1 boundary, retains that owner through
the state-7 completion, and routes acceptance/read/completion events only to
that owner. Simultaneous requests and out-of-phase requests are rejected and
reported. Rejecting a collision is deliberately an implementation invariant,
not a claim that the original device discarded such work: architectural
request generation and branch/loop/interrupt/event priority remain outside
this decision until sourced and composed.

Normal BR/BG is composed above that selector by gating only future descriptor
valids after state-3 recognition while continuing to advance an already-active
native PM transaction. Native grant remains a separate output-enable mask.
The composition reports request attempts during issue inhibition but does not
store or prioritize them; retry is an architectural-client responsibility.
This preserves the original distinction between completing the current
instruction and relinquishing pins without introducing an undocumented queue.

The native DM controller applies the same physical-substate contract with one
additional state bit: DMACK is sampled at 6-to-7, and a low sample retains
architectural state seven while the physical phase input traverses one complete
8/1/2/3/4/5/6/7 sequence. A qualified high sample releases completion only at
the next 7-to-8 edge. This encodes Figure 5.7 directly without gated clocks or
collapsing a full processor-cycle wait into one FPGA clock. Type 2, Type 3,
Type 4, and Type 12 now use this boundary for issue and completion; each attachment is
deliberately separate until a whole-core request arbiter can be sourced and
verified. The Type 4 attachment captures selected-bank ALU/MAC, old DREG store
data, and DAG state only at the enabled 8-to-1 boundary. The native 7-to-8
completion is its sole compute/status, optional-read, and selected-I commit
event. The Type 3 attachment similarly captures an absolute address and
cycle-start general-register write source at 8-to-1, but has no DAG or
computational action; its read destination changes only at qualified 7-to-8.

## Consequences

Wrappers must supply a phase-enable rate adequate to represent the original
state edges. Hard Drivin's schematic shows a 32 MHz oscillator feeding CLKIN,
which corresponds to an 8 MHz instruction rate under the sourced divide-by-four
relationship [ATARI-ADSP-SCHEM, drawing A044421, sheet 3 left, PDF p. 6;
ADI-UM-1989, printed p. 5-2]. MiSTer clock selection and PLL constraints remain
open until wrapper synthesis.
