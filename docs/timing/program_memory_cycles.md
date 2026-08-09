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

## Bounded shared-owner selector

`adsp2100_program_owner_bus` composes exactly one native controller with three
uniform descriptor inputs: ordinary fetch, Type 5 PM transactions, and Type 13
PM transactions. PMDA is an explicit captured descriptor qualifier rather
than an inference from owner identity, because a Type 5/13 recovery fetch is
an instruction access. Request capture remains the enabled state-8-to-state-1 edge. An accepted
owner remains stable through the active eight-state transaction and receives
the sole completion/read-sample event at state 7-to-state-8. Bus
relinquishment masks native outputs while preserving both owner and descriptor;
the next enabled state-8 boundary may replace the owner for a back-to-back
transaction without deasserting PMS.

The selector accepts only an exactly-one request set. Two or three concurrent
requests produce no transaction and raise `request_conflict_o`; a request at
any other boundary raises `request_out_of_phase_o` and cannot replace an active
owner. This fail-closed rule is not presented as original-device request
priority. It provides deterministic mutual exclusion until architectural
sequencing ensures legal one-hot requests. Eight directed tests and 50,007
model/RTL clocks pass with all three requesters, 1,097 boundary conflicts,
1,346 off-boundary rejections, 3,248 completions, 2,576 owner switches, 611
active relinquishment holds, and 1,113 accepted Type 5/13 descriptors with
PMDA low. Priority among fetch, PM data recovery, branch, loop, interrupt,
HALT, TRAP, and BR/BG remains open.

Within the separate real Type 5 and Type 13 native/cache owners, interrupt
recognition is gated by the same event boundary: a cache hit completes the
instruction with the PM-data cycle, while a miss commits the data action but
cannot service a sampled request until the following recovery fetch completes.
This bounded rule is verified across 50,100 and 50,098 model/RTL clocks
[ADI-UM-1989, printed pp. 4-26–4-30 and 5-15–5-16]. It does not establish
shared-owner priority or PC/status entry ownership.

The bounded BR/BG composition keeps those capture and completion boundaries
distinct from bus relinquishment. BR recognition at state 3 does not disturb
the active descriptor; it completes at state 7. All later state-8 captures are
inhibited through the request/grant/release delay, PM output enables are masked
only while native BG is asserted, and the state-8 resume event may accept one
held descriptor. A held request remains the client's responsibility and is
reported with `request_blocked_o`; the composition does not create an
unsourced retry queue. Six directed tests and 50,002 model/RTL clocks cover all
three owners, 111 complete handshakes, and 1,264 accepted Type 5/13
instruction-access descriptors. DM-bus masking and priority with HALT, TRAP,
interrupts, loops, and reset release remain open.

The bounded Type 13/cache client is now connected to that composition. It
retains any descriptor rejected by a collision or issue inhibition and
re-presents it on a later enabled state-8 boundary. Routed Type 13 completion
is the only interface event allowed to advance the client, while completed
ordinary fetches fill its cache. Six directed tests and 50,061 model/RTL
clocks cover data and recovery retries, exactly-once architectural commit,
ordinary-fetch fill, raw Type 5 isolation, and 88 BR handshakes. Ordinary
fetch and Type 5 architectural request generation plus complete event priority
remain open.

The bounded Type 5/cache client is attached in a symmetric but separate
composition. Its captured ALU/MAC/PM descriptor or later recovery descriptor
survives a fail-closed collision or issue inhibition, only routed Type 5
completion advances client state, and completed ordinary fetches fill its
cache. Six directed tests and 50,063 model/RTL clocks cover 2,742 accepts, 713
retries, 1,371 one-time data completions, 290 ordinary-fetch fills, 322 raw
Type 13 completions, and 78 BR handshakes.

`adsp2100_program_clients_owner_control_slice` now places all three real PM
clients behind one instance of the 16-word cache and one native PM/BR-BG
owner, while fetched Type 2/3/4/12 descriptors share one attached native DM
controller. Ordinary external fetch completion and either client's pure recovery
completion fill that same cache; an issue-time Type 5 or Type 13 lookup uses
the same cache state. Captured Type 5 and Type 13 descriptors survive a
rejected exactly-one selection and retry, while only the routed owner receives
completion. State-external Type 5 and Type 13 clients commit into the retained
fetch client's sole architectural-state owner with explicit reset-unknown
validity sidecars. In sequential automatic mode, the retained opcode selects a
legal Type 5/Type 13 client and PC+1 supplies its next instruction address. A
hit installs the cache word at the PM-data completion edge; a miss commits the
data action once and delays instruction retirement until the pure external
recovery completes. HALT recognition during ordinary fetch completes that
fetch before state-8 stop. Recognition during Type 5/Type 13 PM data overrides
an issue-time hit, commits the data action once, forces exactly one external
recovery for that client, and stops at recovery completion. Forty-five directed
checks and 51,587 independent-model/RTL clocks cover hit/miss installation,
`0x3fff` PC wrap, following fetched execution, retained retries, both explicit
collision classes, 179 fills, 53
Type 5 and 38 Type 13 data completions, nine paired fetched-PM/native-DM
completions, one full-cycle DMACK extension, cross-client state visibility,
and 2,217 grant-masked clocks. The DM wait holds PM and architectural progress
but retains physical state-3/state-7 event sampling; BR/HALT service waits for
paired completion and grant masks both buses. Three HALT cases cover ordinary stop, one Type 5 and
one Type 13 forced recovery, DMACK-qualified release, and fail-closed BR/HALT
overlap. One IRQ2 case remains pending from PM-data
completion through recovery, then discards that sequential word and enters the
shared PC/status/vector path. This is one transaction/cache/architectural-state
owner with bounded sequential PM issue and HALT. A second IRQ2 case enters with
invalid ASTAT/MSTAT, fetches RTI from vector 2, and restores the captured
validity before dependent PM work. Fetched Type 8/Type 9/Type 14/
Type 15/Type 16/Type 17/Type 21/Type 23/Type 24/Type 25 result, predicate, operand, and
write-possibility-dependent validity now reaches following Type 5/Type 13 PM
stores. Type 16 EXP LO preserves a known destination when old SE is known not
to select a write; Type 21 carries valid I/M/L/configuration into the selected
I and invalidates a following PM address when those dependencies are unknown;
Type 25 preserves MR validity when MV is known false and invalidates all MR
segments when MV is unknown. Type 17 propagates unknown source validity through
DREG, DAG, status/control, SB, and PX, and unknown MSTAT rejects bank-dependent
fetched and PM-client issue. Type 3 returned-DMD validity and the independently
classified Type 4 compute/read and Type 12 shift/read destinations are each
covered at paired native-PM/native-DM retirement. Accepted status pushes now retain the associated
ASTAT/MSTAT/IMASK validity beside the documented 16-bit word, and a directed
intervening-known-write sequence proves the later pop restores that captured
classification. Fetched Type 17 also observes live SSTAT status-stack
empty/nonempty/overflow transitions; only its documented low byte is claimed.
OQ-016 narrow-source extension, active-loop issue, additional DM requesters,
Type 1 behavior under OQ-023, and legal TRAP/interrupt/HALT/BR cross-event
priority remain open
[ADI-UM-1989, printed pp. 4-26–4-30 and 5-3–5-14, Figures 5.3, 5.5,
5.6, and 5.7; ADI-DATABOOK-1987, printed pp. 2-33–2-43].

The bounded combined owner, including the fetched native-DM attachment plus
the register and status-stack validity extensions, is
implementation-qualified against a 20 ns virtual-pin constraint on Cyclone V
`5CSEBA6U23I7`. Quartus 17.0.2 reported
9,903 ALMs, 3,313 fitted registers, four DSP blocks, no block memory, +0.639
ns worst multicorner setup, +0.165 ns worst hold, +9.045 ns worst minimum-
pulse-width slack, 51.65 MHz worst slow-corner Fmax, and zero unconstrained
clocks, ports, or paths. The verification-only aggregate conflict observation
has an explicit second-edge sampling exception; all architectural and owner-
event outputs retain the 20 ns one-cycle constraint. Issue-time action capture
and dedicated PM-data DREG/DAG reads plus direct selection of captured pending
descriptors at completion
close implementation paths inside the already documented state-8 issue to
state-7 completion interval. The independent second DAG read port removes a
structurally impossible PM-client-to-fetched-address cone; it does not change
any logical PM phase or
architectural cycle count. This remains bounded FPGA synthesis evidence, not an
original-device hidden-latch claim or whole-core physical timing closure.

The ordinary-fetch architectural owner is also attached in a third separate
composition. Its current instruction retains the selected PC+1, Type 10
direct target, Type 19 DAG2-indirect target, Type 20 valid return-stack target,
or automatic loopback/exit request after a
fail-closed collision or BR/BG issue inhibition, and only the routed fetch
completion advances PC and installs the returned opcode. Seven directed tests
and 50,054 model/RTL clocks cover 4,389 accepted fetches, 743 retries, 4,387
completions, 27 raw Type 5 and 31 raw Type 13 accepts, 90 BR handshakes, 3,318
masked grant clocks, and one IRQ2 retained through BG into vector entry. This closes retained fetch request/completion
routing on the shared electrical owner. Type 11 setup and automatic terminal
actions remain architectural state changes inside that retained request; the
legal three-client priority and unified cache/system-event composition remain
open.

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

Six directed tests and 50,098 deterministic model/RTL clocks cover PM reads,
PM writes, hit capture, miss recovery, state holds, reset, off-boundary
controls, externally directed bus relinquishment, and interrupt recognition
deferral from uncached data completion through recovery. Request acceptance and
architectural commit are checked against the independently modeled native
controller. This evidence does not establish ordinary-PC fetch arbitration,
other PM instruction classes, HALT/TRAP/interrupt entry, or BR/BG timing.

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

Fourteen logical, seven cache-composition, and six native directed tests pass;
50,071 logical and 50,100 native model/RTL clocks cover ALU/MAC and PM-only
reads/writes, old-value overlap, cache hit/miss/forced recovery, reset,
off-boundary controls, relinquishment, and interrupt-recognition deferral from
uncached data completion through recovery. Ordinary fetch/other PM owners,
branch/loop/interrupt-entry/HALT/BR arbitration, and hidden self-modifying-cache
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
restart boundary. Six directed tests and 50,054 differential clocks exercise
87 complete request/grant/release/resume sequences, including fetched Type 14,
Type 15, and Type 16 retirement and one state-7-sampled IRQ retained through
grant into post-release vector entry. PM-data/cache owners, control transfers,
HALT, reset-first-fetch, capture without a state-7 sample, and simultaneous
events are not part of that composition.

## Ordinary-fetch HALT attachment

The separate `adsp2100_linear_halt_control_slice` attaches the original
active-low HALT sequence to the bounded ordinary-fetch owner. HALT is sampled
at enabled state 3. The in-flight PM read remains active and completes at the
state-7-to-state-8 edge, after which logical state 8 is held. PMA, PMS, PMRD,
and their output enables therefore retain their state-8 levels; this is a
halted driven bus, not the tristated BG condition. When HALT is inactive and
DMACK is high, the next state-8-to-state-1 edge accepts the following fetch.

Eleven directed tests and 50,048 deterministic independent-model/RTL clocks
cover 789 ordinary recognize/stop sequences, 790 combined resume events, 150
DMACK-low blocked-release observations, and 819 held clocks with stable PM
signals. A state-7-sampled IRQ2 is retained without entry through one stop and
enters on resume. A taken fetched Type 22 retires the PC+1 fetch and asserts TRAP at
state 7-to-8; HALT assertion clears TRAP into a retained handoff, and a
DMACK-qualified release issues the already-fetched word without replay.
Fetched Type 14, Type 15, and Type 16 words retain their prior coverage.

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
has an equivalent bounded HALT attachment. A superseding combined owner now
attaches ordinary fetch and both PM-data clients behind one cache/native-PM/
BR-BG/HALT boundary; its three directed HALT paths pass within 51,587 clocks.
HALT during BG or DMACK waits, simultaneous ordinary-HALT/TRAP
recognition, interrupt priority, BR while
stopped, and reset interaction also remain outside this attachment
[ADI-UM-1989, printed pp. 5-13–5-15].
