# Program-memory cycles

**Status: source-backed eight-state logical pin phases implemented; bounded
Type 5 and Type 13 cache/request attachments verified**

For a PM read, the processor drives PMA and PMDA, asserts PMS, then asserts
active-low PMRD; memory supplies PMD; the processor samples data and releases
PMRD [ADI-UM-1989, printed p. 5-7, Figure 5.5 p. 5-8].

For a PM write, the processor drives PMA/PMDA, asserts PMS, drives PMD, asserts
PMWR, then releases PMWR after its fixed interval
[ADI-UM-1989, printed pp. 5-7–5-8]. PMS normally remains asserted across
successive program accesses and is inactive only during halt/trap/bus grant
[ADI-UM-1989, printed p. 5-6].

Original PM has no DMACK-equivalent documented in this interface. The bounded
Type 13 slice therefore completes a PM-data transfer in one fixed logical
processor cycle. It exposes PM select, data-versus-instruction classification,
read/write direction, 14-bit address, and 24-bit write data. The composed cache
boundary derives the next-instruction decision from its pre-cycle 16-word
monitor: a valid hit supplies the actual cached word with no external fetch;
a miss schedules one fixed instruction-read recovery cycle and uses that
cycle's returned word to fill the monitor. Ordinary external instruction
completions populate the same monitor when Type 13 does not own PM
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8]. The Type 13 slice itself ends at
this logical request boundary; the phase-attached wrapper below connects it to
the native controller without assigning whole-core fetch ownership.

## Eight-state logical pin boundary

The independently modeled and portable `adsp2100_program_bus` controller now
implements the exact edge-to-state mapping below. Its implementation API
captures a request on an enabled state-8-to-state-1 edge, aligned with the
sourced output-change edge; this is not a claim about a hidden device latch.
PMA, PMDA, and active-low PMS then remain
valid throughout states 1–8; a back-to-back request replaces the descriptor at
the next 8-to-1 edge without deasserting PMS. With no following request, the
interface becomes inactive after that edge.

| Signal/action | Logical states or edge |
|---|---|
| PMA, PMDA, PMS valid | states 1–8 |
| PMRD low for fetch/read | states 4–7 |
| PMWR low for write | states 4–7 |
| PMD read sample | enabled state-7-to-state-8 edge |
| PMD write output enable | states 5–8 |

This transcription follows the original state-edge timing parameters: PMA,
PMDA, and PMS relative to CLKIN high (8–1); PMRD/PMWR relative to CLKIN low
(3–4 and 7–8); PMD input sampling at low (7–8); and PMD output enable/disable
relative to high (4–5 and 8–1) [ADI-DATABOOK-1987, ADSP-2100 data sheet,
printed pp. 2-36–2-39, parameters 23–60, Figures 14–15; ADI-UM-1989, printed
pp. 5-6–5-8, Figure 5.5]. Ten directed model tests and 50,032 deterministic
model/RTL clocks cover reads, writes, instruction/data selection, state-7
holds, back-to-back PMS continuity, unknown validity, reset, and bus-output
masking.

## Type 13/cache attachment

The bounded `adsp2100_shifter_pm_native_slice` admits architectural issue and
setup controls only on the enabled state-8-to-state-1 edge. It captures the
old DAG2 address/post-modify, `{DREG,PX}` store word, shifter results, and the
issue-time cache-hit word there. The native controller retains the descriptor
through states 1–8. No architectural destination changes until the active
transaction advances from state 7 to state 8; that edge samples PMD for reads
and atomically commits the Type 13 data action. If the issue-time lookup
missed, the completion schedules an instruction-read descriptor, which the
next state-8-to-state-1 edge accepts as a back-to-back PM transaction. Its
state-7-to-state-8 edge fills the monitor and produces the instruction/event
boundary without repeating the data action
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8].

Five directed tests and 50,081 deterministic model/RTL clocks cover PM reads,
PM writes, hit capture, miss recovery, state holds, reset, off-boundary
controls, and externally directed bus relinquishment. Request acceptance and
architectural commit are checked against the independently modeled native
controller. This evidence does not establish ordinary-PC fetch arbitration,
other PM instruction classes, HALT/TRAP/interrupt recognition, or BR/BG
timing.

## Type 5/cache attachment

The bounded `adsp2100_compute_pm_native_slice` applies the same phase and cache
contract to Type 5. On the enabled state-8-to-state-1 edge it captures the
selected-bank ALU/MAC inputs and feedback, old `{DREG,PX}` store word, DAG2
address/postmodify, and issue-time cache-hit instruction. The native controller
holds that descriptor through states 1–8. The state-7-to-state-8 edge is the
sole data completion and atomically commits computation/status, optional PM
read into DREG/PX, and selected-I postmodify. A miss schedules a back-to-back
instruction recovery at the following state-8-to-state-1 edge; its completion
fills the shared monitor and never repeats the computation or DAG update
[ADI-UM-1989, printed pp. 2-6–2-7, 3-6–3-7, 4-26–4-30, 5-5–5-8,
6-3–6-7].

Fourteen logical, six cache-composition, and five native directed tests pass;
50,071 logical and 50,083 native model/RTL clocks cover ALU/MAC and PM-only
reads/writes, old-value overlap, cache hit/miss/forced recovery, reset,
off-boundary controls, and relinquishment. Ordinary fetch/other PM owners,
branch/loop/interrupt/HALT/BR arbitration, and hidden self-modifying-cache
behavior remain OQ-008.

The controller exposes separate address, control, and PMD output enables so an
FPGA wrapper can implement bidirectional pins. A separate arbiter's
`bus_relinquished` input masks all three enables while preserving descriptor
state, matching the sourced external-bus release effect. The separate
`adsp2100_bus_control` owner recognizes BR at enabled state 3, asserts BG one
complete eight-state cycle later, recognizes release at state 3, removes BG
one complete cycle later, and resumes issue at the following state 8-to-1;
the native-pin wrapper supplies the special asynchronous RESET-time relation
[ADI-UM-1989, printed pp. 5-3–5-6, Figure 5.3]. Nanosecond delays,
electrical setup/hold requirements, ordinary fetch/PC ownership, other PM
instruction classes, HALT/TRAP behavior, and composition of BR/BG with every
PM owner remain outside this bounded attachment. The separate bounded linear
owner is now attached to BR/BG: its current ordinary fetch remains driven and
retires before the new-issue inhibit takes effect; grant then masks every PM
output enable, and the first post-release fetch starts at the state-8-to-state-1
restart boundary. Five directed tests and 50,003 differential clocks exercise
93 complete request/grant/release/resume sequences. PM-data/cache owners,
control transfers, interrupts, HALT, and reset-first-fetch are not part of that
composition.

## Ordinary-fetch HALT attachment

The separate `adsp2100_linear_halt_control_slice` attaches the original
active-low HALT sequence to the bounded ordinary-fetch owner. HALT is sampled
at enabled state 3. The in-flight PM read remains active and completes at the
state-7-to-state-8 edge, after which logical state 8 is held. PMA, PMS, PMRD,
and their output enables therefore retain their state-8 levels; this is a
halted driven bus, not the tristated BG condition. When HALT is inactive and
DMACK is high, the next state-8-to-state-1 edge accepts the following fetch.

Seven directed tests and 50,003 deterministic independent-model/RTL clocks
cover 790 recognize/stop/resume sequences, 161 DMACK-low blocked-release
observations, and 742 held clocks with stable PM signals.

The PM-data case is not equivalent: the original requires a forced external
instruction fetch before stopping, even if the cache held the next word. The
standalone `adsp2100_halt_control` now records this as a four-state sequence:
recognized PM data completes without a stop, exactly one forced fetch is
admitted at the next enabled state-8-to-state-1 boundary, and its later
state-7-to-state-8 completion enters the stopped state. Eight directed tests
and 50,033 independent-model/RTL clocks cover 335 PM-data recognitions and 335
forced issue pulses. The Type 13/native-PM owner now consumes that pulse in a
bounded composition: five tests and 50,124 clocks verify that a late request
overrides the issue-time hit, data commits once, one following external fetch
owns the sourced pin phases, and stop occurs at its state-7 completion. Type 5
and shared-PM arbitration remain open. HALT during BG or DMACK waits,
TRAP/interrupt priority, BR while
stopped, and reset interaction also remain outside this attachment
[ADI-UM-1989, printed pp. 5-13–5-15].
