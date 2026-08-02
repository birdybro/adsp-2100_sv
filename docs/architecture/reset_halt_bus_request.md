# Reset, halt, trap, and bus request

**Status: reset phase, HALT sequence control, ordinary-fetch plus bounded
Type 5/Type 13 PM-data HALT attachments both separately and in the combined
PM owner, normal BR/BG, and Type 22 handshake bounded in RTL**

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

The original data-sheet review does not close that gap. Its RESET Figure 9
shows RESET and CLKIN only and says the processor starts from state 4 after
release; its separate PM-read figures define ordinary state-edge timing but
do not show PMS or PMRD during RESET or the partial state-4-to-state-5 release
sequence [ADI-DATABOOK-1987, printed pp. 2-32 and 2-36–2-39, Figures 9 and
14]. Treating either ordinary-PM hypothesis as authentic would therefore be
an unsupported inference. An original combined waveform, simulator pin trace,
or physical capture remains required by OQ-024.

HALT is recognized at state 3 and stops at state 8. If the current cycle is PM
data, a forced instruction fetch completes first; this makes the stopped PMA
observable. Releasing HALT resumes, with DMACK required high
[ADI-UM-1989, printed pp. 5-13–5-14].

## Ordinary-fetch HALT attachment

The original HALT input is active low, as shown by the pin-name overbar and
pin/timing figures [ADI-UM-1989, printed pp. 5-17–5-20;
ADI-DATABOOK-1987, printed pp. 2-24–2-25 and Figure 10 p. 2-33]. For an
ordinary external instruction-fetch cycle, the source sequence is now
implemented independently in Python and portable RTL:

- an asserted HALT input is sampled only at the enabled end of state 3;
- recognition is latched even if the input is released before the stop edge;
- the already-active instruction fetch remains driven and retires at the
  enabled state-7-to-state-8 edge;
- no following instruction is issued while stopped;
- the controller holds logical state 8, preserving the stopped PMA, PMS, and
  PMRD levels rather than relinquishing the bus; and
- release advances from state 8 to state 1 only when HALT is inactive and
  DMACK is high. A DMACK-low release request fails closed by retaining the
  stopped state; this is a protective digital contract for the manual's
  requirement that DMACK be high, not a characterization of an out-of-spec
  board sequence.

`rtl/core/adsp2100_halt_control.sv` separates new-issue inhibition from phase
hold. `rtl/core/adsp2100_linear_halt_control_slice.sv` attaches both effects
to the bounded ordinary NOP/Type 6/Type 7/Type 9/Type 14/Type 15/Type 16/Type
17/Type 18/Type 22 PM owner without
gating a clock. Eleven directed tests and 50,048 deterministic independent-
model/RTL clocks cover 789 ordinary recognitions/stops, 790 combined resumes,
150 DMACK-low blocked-release observations, 819 held state-8 clocks, one
complete fetched Type 22 TRAP assertion/HALT acknowledgment/handoff/restart,
one IRQ2 recognized at state 7 and retained through stop/release into entry,
370 fetched Type 9 no-op retirements, 655 Type 14 retirements, 619 Type 15
retirements, and 586 Type 16 retirements.
The
machine-readable boundary is `docs/generated/adsp2100_halt_control.yaml`.

## PM-data forced-fetch sequencing boundary

The same standalone controller now represents the distinct PM-data rule. A
HALT recognized at state 3 during a PM-data cycle enters a forced-fetch-pending
state. The current data cycle may reach state 7 without producing a stop. At
the following enabled state-8-to-state-1 issue edge the controller emits
exactly one forced external instruction-fetch request, then stops only after
that fetch reaches its state-7-to-state-8 completion. Instruction issue is
inhibited before and after that single request, so a cache hit cannot suppress
the required external observation [ADI-UM-1989, printed pp. 5-13–5-14].

Eight directed contract/model tests and a standalone 50,033-clock independent-
model/RTL comparison cover both ordinary and PM-data recognition, 335 PM-data
recognitions and forced fetch issues, 667 total stops, 665 releases, 291
DMACK-low blocked releases, and 2,269 held clocks. Formal invariants cover the
four control states and require the forced request to occur only on an enabled
state-8 boundary.

`rtl/core/adsp2100_shifter_pm_halt_slice.sv` now attaches this scheduler to
the bounded Type 13 cache/native-PM owner. A late recognition latches recovery
even if issue-time lookup hit, suppresses release of that stale hit, commits
the shifter/PM/PX/DAG action once at the data-cycle state-7 edge, accepts one
external fetch at the following state-8 edge, fills the cache from that fetch,
and enters the stopped state only at its state-7 completion. Five directed
tests and 50,124 independent-model/RTL clocks cover 210 late recognitions,
210 hit overrides/forced fetches, 397 stops/resumes, 209 DMACK-blocked
releases, and 580 held clocks. The combined attachment below supersedes this
previously separate-only shared-PM status.

`rtl/core/adsp2100_compute_pm_halt_slice.sv` independently attaches the same
scheduler to the bounded Type 5 cache/native-PM owner. It uses the identical
late-recognition recovery rule while committing the ALU/MAC/PM/PX/DAG2 action
exactly once. Five directed tests and 50,126 independent-model/RTL clocks cover
197 late recognitions, hit overrides, and forced fetches, 1,996 data-cycle
completions, 387 stops/resumes, 196 DMACK-blocked releases, and 577 held
clocks. The combined attachment below supersedes the previously separate-only
shared-PM status.

`rtl/core/adsp2100_program_clients_owner_control_slice.sv` now attaches the
same controller to the one retained-fetch/Type 5/Type 13 cache/native-PM/BR-BG
owner. An ordinary-fetch recognition lets that fetch complete and then holds
state 8. A recognition during either PM-data client records the captured
owner, suppresses an issue-time cache hit, commits the architectural PM-data
action exactly once, accepts one pure external recovery for that same client,
fills the shared cache, and stops at its state-7 completion. HALT-high and
DMACK-high qualify release. Three directed combined-owner tests within a 38-
test, 51,428-clock independent-model/RTL comparison cover the ordinary stop,
Type 5 and Type 13 forced recoveries, one blocked release, four held clocks,
and three resumes with zero attachment conflicts. Because no original-device
source establishes BR/HALT priority, simultaneous or cross-owned requests are
rejected and conflict-reported as an implementation invariant rather than
assigned an architectural order [ADI-UM-1989, printed pp. 4-26–4-30 and
5-3–5-14; ADI-DATABOOK-1987, printed pp. 2-33–2-39].

General HALT support still excludes HALT recognition while BG is active or a
DMACK wait is incomplete, simultaneous ordinary-HALT/Type-22 priority, BR
recognition while already halted, reset interaction, and electrical
synchronization/metastability. A request sampled at state 7 while an ordinary
HALT stop is pending is now retained without entry during the stopped state
and serviced on the qualified restart; pulses with no state-7 sample and
simultaneous IRQ/TRAP priority remain open. Those other cases require
composition with their respective owners and are not inferred from either
bounded result
[ADI-UM-1989, printed pp. 5-13–5-15].

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

The ordinary fetched owner and HALT composition now provide the bounded
attachment that the standalone Type 22 slice intentionally omitted. All
sixteen Type 22 forms issue the selected PC+1 word through the native PM
controller, a taken form emits TRAP only on routed state-7 completion, and the
following state 8 remains held. HALT assertion clears TRAP into a retained
handoff; release remains blocked while DMACK is low and resumes the already-
fetched PC+1 word when DMACK is high. Three fetched-owner tests within the
48-test, 444,003-clock comparison and two HALT-composition additions within
the eleven-test, 50,048-clock comparison cover the attachment. An overlap with
ordinary state-3 HALT recognition is explicitly conflict-reported rather than
assigned a priority. BR/BG, cache, simultaneous interrupts, reset-first-fetch,
and analog pin synchronization remain outside this bounded composition
[ADI-UM-1989, printed pp. 4-3–4-4, 4-25, 5-13–5-15, Figure 5.10, 6-14,
A-4, and A-6].

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

The bounded composition in
`rtl/core/adsp2100_linear_bus_control_slice.sv` attaches those two distinct
effects to the ordinary linear PM owner. A request recognized in state 3 does
not cancel or mask the current fetch: its PM read remains driven through state
7 and retires at state 7-to-8. The next state-8 issue is inhibited. Once BG is
asserted, all PM output enables are masked while the architectural and PM
transaction state remains preserved. After release recognition and the full
release interval, BG deasserts and the next fetch is accepted on the documented
state-8-to-state-1 restart edge. Six directed composition tests and 50,054
independent-model/RTL clocks cover 87 complete request/grant/release/resume
handshakes, 5,440 retirements, 5,442 issues, 2,841 masked grant clocks, one
IRQ2 recognized at state 7 and retained through grant/release into entry,
593 Type 14 retirements, 591 Type 15 retirements, and 592 Type 16 retirements.
This evidence applies only to the bounded NOP/Type 6/Type 7/Type
9/Type 14/Type 15/Type 16/Type 17/Type 18
linear fetch owner; PM-data,
DM, transfer, loop, HALT, reset-first-fetch, capture without a state-7 sample,
and simultaneous-event ownership remain unconnected.

`rtl/core/adsp2100_program_owner_bus_control.sv` independently attaches the
same controller to the single fail-closed PM selector shared by ordinary
fetch, Type 5 PM data, and Type 13 PM data descriptors. Recognition does not
cancel the active owner's transaction; descriptor capture is inhibited only
after recognition, all PM drivers are masked during native grant, and exactly
one requester held by its architectural client may be accepted on the
state-8-to-state-1 resume edge. Six directed tests and 50,002 independent-
model/RTL clocks cover all owners, 111 complete handshakes, 80 active
transactions completed after recognition, 1,417 blocked requests, 3,536
masked grant clocks, 79 resume-edge accepts, and 530 fail-closed collisions.
The composition reports a blocked request but deliberately does not store it;
the separately attached Type 13/cache, Type 5/cache, and ordinary-fetch
clients each retain and retry their own rejected descriptor without replaying
completed architectural work. The ordinary-fetch attachment adds seven
directed tests and 50,054 model/RTL clocks covering 90 BR handshakes, 743
retained fetch retries, 4,387 routed fetch completions, and one IRQ2 retained
through BG into vector entry. No one composition yet
contains all three architectural clients. DM-driver masking and priority
against HALT, TRAP, loops, reset release, new recognition without state-7
sampling, or simultaneous raw PM data remain outside these bounded results
[ADI-UM-1989, printed pp. 5-3–5-8, Figures 5.3 and 5.5;
ADI-DATABOOK-1987, printed pp. 2-33–2-39].

The Type 5/cache client is now attached in a separate composition and likewise
retains rejected data/recovery work without replaying ALU/MAC/PM/PX/DAG2
effects. Six directed tests and 50,063 model/RTL clocks cover 78 additional
BR recognize/release/resume handshakes and 2,727 grant clocks with every PM
driver masked. A unified composition with both PM-data clients, the retained
ordinary-fetch client, and HALT/TRAP/loop/interrupt priority remains open.

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
