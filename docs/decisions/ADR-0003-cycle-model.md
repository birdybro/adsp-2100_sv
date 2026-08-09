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

A parallel bounded shared-DM selector now places two descriptor sources in
front of exactly one native DM controller. It uses the same exact-one,
fail-closed collision rule, but owner replacement is gated by the native
controller's ready signal. A DMACK-low extension revisits physical state 8
while the transaction is still active, so clearing the owner merely because
the phase is state 8 would lose acknowledgement and completion routing. The
accepted owner is instead retained through every extension and the qualified
state-7 completion. This decision establishes a reusable structural owner; it
does not attach fetched execution. The retained fetch client's concurrent PM
request and DM descriptor must be admitted atomically before that attachment
can avoid partial architectural issue, and no source-backed priority or
rollback rule currently supplies that contract.

Normal BR/BG is composed above that selector by gating only future descriptor
valids after state-3 recognition while continuing to advance an already-active
native PM transaction. Native grant remains a separate output-enable mask.
The composition reports request attempts during issue inhibition but does not
store or prioritize them; retry is an architectural-client responsibility.
This preserves the original distinction between completing the current
instruction and relinquishing pins without introducing an undocumented queue.

The bounded Type 13/cache architectural client is now attached to that
composition. Its already captured PM-data or recovery descriptor remains in
the client after selector collision or BR/BG issue inhibition and is presented
again only at a later enabled state-8 boundary. Only the routed Type 13
completion advances the client; completed ordinary fetches instead fill the
same instruction cache. PMDA is captured per descriptor, not derived from the
owner ID, so a Type 13 recovery fetch remains an instruction access. Ordinary
fetch and Type 5 are still raw descriptor inputs, and no whole-core priority
decision is added by this attachment.

The bounded Type 5/cache client is attached by the same rule in a separate
composition: captured data/recovery descriptors remain in the client after
rejection, only routed Type 5 completion advances it, ordinary fetch
completion fills its cache, and PMDA comes from the retained descriptor. The
two client attachments deliberately remain separate until ordinary-fetch,
Type 5, Type 13, and system-event priority can be sourced and verified as one
processor-level decision.

The ordinary-fetch owner is now also separated into a retained architectural
client and attached in a third composition. Its current instruction owns the
unaccepted selected request—PC+1, a Type 10 direct target, a Type 19 DAG2-
indirect target, a Type 20 valid return-stack target, or automatic loopback/
exit—so selector collision
or BR/BG inhibition cannot lose or
duplicate architectural work; only the routed fetch completion retires the
instruction and installs the returned word. The prior bounded linear-core API
is retained as a compatibility composition of this client with one private PM
controller. Type 11 setup and automatic loop state changes commit only with
that routed fetch completion. Type 5 and Type 13 remain raw descriptors in the
new attachment,
so this extraction does not yet decide legal priority among all three real
clients or system events.

A superseding bounded composition attaches those three retained clients behind
one cache/native-PM/BR-BG owner and routes the Type 5 and Type 13 state-external
read/action bundles into the retained fetch client's single
`adsp2100_architectural_state` instance. The shared module boundary and its
fail-closed write-conflict detector are implementation conveniences; the
architectural ordering remains the original cycle-start-read/cycle-end-write
rule. Directed fetched-Type-6-to-Type-13 and Type-5-to-fetched-Type-17
dependencies demonstrate cross-client register visibility. Sequential
automatic mode now selects a retained Type 5/Type 13 opcode, requests PC+1,
installs a cache-hit or external-recovery word, advances the shared PC, and
uses whole-instruction retirement as the existing IRQ entry boundary. The
same composition now owns HALT scheduling. Ordinary fetch stops after its
routed completion; PM-data recognition commits the data action once, forces
one external recovery for the captured client even on an issue-time hit, and
stops after that recovery. A combined BR/HALT request is rejected and
conflict-reported because the sources do not establish priority. The
implementation fails closed whenever a loop is active because the sources do
not establish whether its termination condition belongs at PM-data issue or
recovery completion. Complete reset-unknown validity accounting and sourced
simultaneous system-event priority remain open.

Type 22 now uses the same retained ordinary-fetch boundary. Its condition is
sampled before state-8 issue, both outcomes request the selected PC+1 word,
and only routed state-7 completion may emit the taken TRAP event. A small
synchronous hold/handoff state above the existing HALT controller retains
state 8 and the fetched word: HALT assertion clears TRAP, while HALT release
with DMACK high removes the hold and admits the retained instruction at the
normal 8-to-1 issue edge. An overlap with ordinary state-3 HALT recognition is
reported as a conflict; this decision does not assign priority among TRAP,
ordinary HALT, BR/BG, cache, interrupts, or reset.

The original state-7 interrupt recognizer is now connected above the ordinary-
fetch HALT and normal BR/BG wrappers. A request actually sampled at state 7
while stop or grant is pending remains in the recognizer, cannot issue a vector
or push context while the issue boundary is disabled, and is consumed only by
the normal vectoring-NOP request accepted at the qualified state-8-to-state-1
resume. This composition does not add an asynchronous pulse latch or define
simultaneous IRQ/TRAP/raw-PM priority; those require separate source evidence.

A separate bounded composition first paired an accepted ordinary fetch with a
raw native-DM descriptor to exercise the sourced DMACK/interrupt overlap. It
now also derives real fetched Type 2, legal Type 3, source-closed Type 4, and
source-closed Type 12 descriptors. Native
DM state seven may repeat complete physical substate cycles while the ordinary
fetch client's architectural phase is disabled; a second, sampling-only
advance reaches the state-7 interrupt recognizer on each physical pass. It
cannot issue or retire an instruction, complete PM, vector, or mutate entry
context. Once DMACK permits the paired PM and DM state-7-to-state-8 completion,
the normal state-8 issue boundary may consume the pending interrupt. The raw
descriptor remains structural verification scaffolding. A conservative
state-8 preflight now attaches the shared-DM owner: simultaneous fetched and
raw descriptors inhibit the PM request and are both rejected by the DM
selector, so the retained instruction may retry without cross-bus rollback.
Fetched ownership is bounded to those four classes and the documented
initialized-operand/valid-DMD qualification; this decision does not assign an
architectural requester priority or resolve unsourced cross-event priority.

The native DM controller applies the same physical-substate contract with one
additional state bit: DMACK is sampled at 6-to-7, and a low sample retains
architectural state seven while the physical phase input traverses one complete
8/1/2/3/4/5/6/7 sequence. A qualified high sample releases completion only at
the next 7-to-8 edge. This encodes Figure 5.7 directly without gated clocks or
collapsing a full processor-cycle wait into one FPGA clock. Type 2, Type 3,
Type 4, and Type 12 now use this boundary for issue and completion. Standalone
attachments remain available, while one bounded ordinary-fetch/native-DM owner
now selects all four classes from retained opcodes. The normal BR/BG controller
recognizes a request at physical state 3 during an incomplete DM cycle, while a
service inhibit defers grant follow-up until paired completion. Grant masks all
PM/DM output enables, and BR overlap with interrupt/TRAP service is conflict-
reported. The ordinary HALT controller now uses the same separation between
physical phase sampling and incomplete-service follow-up. Recognition remains
live at each repeated physical state 3, while a reusable service inhibit
defers stop until the paired PM/DM state-7 completion and architectural
retirement. HALT then holds driven state 8 and release remains blocked until
DMACK is high. A simultaneous new BR/HALT request is rejected and reported;
this is a fail-closed implementation invariant, not a sourced architectural
priority. A whole-core request arbiter, HALT during BG, and sourced cross-event
priority are still not verified. The Type 4 attachment captures selected-bank ALU/MAC, old DREG store
data, and DAG state only at the enabled 8-to-1 boundary. The native 7-to-8
completion is its sole compute/status, optional-read, and selected-I commit
event. The Type 3 attachment similarly captures an absolute address and
cycle-start general-register write source at 8-to-1, but has no DAG or
computational action; its read destination changes only at qualified 7-to-8.
The Type 12 attachment captures selected-bank shifter/feedback, ASTAT, old DREG
store data, and DAG state at 8-to-1; its shifter/status, optional-read, and
selected-I effects share the qualified 7-to-8 commit event.

Type 1 uses a deliberately narrower logical boundary pending OQ-023. Its
standalone state slice captures both fixed-DAG read descriptors and the
optional computation at issue, holds all outputs and destinations together,
and atomically commits both loads, PX, both I updates, and compute/status on
one implementation/test completion input. That input is not a native DMACK
sample or PM-controller event. This closes architectural old/new-value and
hold/commit behavior without choosing whether PM holds, repeats, or completes
internally while DMACK extends the simultaneous DM read. A native Type 1
composition requires new primary or physical evidence. SC-015 explicitly
rejects the later-family multiplexed external-bus sequence as a substitute for
that missing original-device evidence.

## Consequences

Wrappers must supply a phase-enable rate adequate to represent the original
state edges. Hard Drivin's schematic shows a 32 MHz oscillator feeding CLKIN,
which corresponds to an 8 MHz instruction rate under the sourced divide-by-four
relationship [ATARI-ADSP-SCHEM, drawing A044421, sheet 3 left, PDF p. 6;
ADI-UM-1989, printed p. 5-2]. MiSTer clock selection and PLL constraints remain
open until wrapper synthesis.
