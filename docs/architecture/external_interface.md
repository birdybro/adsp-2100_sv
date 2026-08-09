# Native external interface

**Status: pin names and logical roles verified**

| Group | Signals | Direction |
|---|---|---|
| Clock | CLKIN, CLKOUT | input, output |
| PM | PMA[13:0], PMD[23:0], PMS, PMRD, PMWR, PMDA | address/control out, data bidirectional |
| DM | DMA[13:0], DMD[15:0], DMS, DMRD, DMWR, DMACK | address/control out, data bidirectional, acknowledge in |
| Control | RESET, HALT, TRAP, BR, BG | inputs except TRAP/BG outputs |
| Interrupt | IRQ[3:0] | active-low inputs |

Source: [ADI-UM-1989, printed pp. 5-17–5-20].

The synthesizable core will express bidirectional buses as separate input,
output, and output-enable signals. That is an FPGA representation choice, not a
change in pin-level transaction semantics. Polarity follows the active-low
strobes and inputs shown in the original timing/pin tables
[ADI-UM-1989, printed pp. 5-6–5-20].

The bounded Type 2, Type 3, Type 4, and Type 12 paths currently expose a
logical active-high DM select/read/write request, 14-bit address, 16-bit write data, validity, and
DMACK completion. Address/control/write data remain stable through arbitrary
wait extensions, and no architectural destination changes before completion.
This is traceable transaction-level behavior. A separate native controller
maps captured descriptors to active-low DMS/DMRD/DMWR, shared-DMD output
enable, DMACK qualification, and full-cycle state-seven extension. Bounded
Type 2, Type 3, Type 4, and Type 12 attachments now accept descriptors only at state 8-to-1
and return completion only at the qualified state 7-to-8 edge
[ADI-UM-1989, printed pp. 5-9–5-12;
ADI-DATABOOK-1987, printed pp. 2-40–2-43].

The standalone `adsp2100_data_owner_bus` puts a fetched descriptor and a
structural companion descriptor in front of exactly one native DM controller.
It accepts only one asserted requester at the enabled state-8 boundary,
rejects a collision without assigning an architectural priority, retains the
owner through every complete-cycle DMACK extension, and routes DMACK sample,
accepted-ACK, wait, completion, and read-sample events only to that owner.
Nine directed/model checks and 50,010 model/RTL clocks cover both owners, 494
collisions, 814 low-DMACK extensions, 3,302 completions, back-to-back owner
changes, relinquishment, reset, and unknown descriptors. The bounded fetched
Type 2/3/4/12 composition now uses this owner behind a conservative state-8
preflight. When its generated descriptor and the structural companion collide,
the wrapper inhibits the paired PM fetch, presents both DM candidates to the
fail-closed selector, accepts neither bus, reports the conflict, and retains
the fetched instruction for a later eligible retry. This is an implementation
invariant necessitated by the absence of a sourced requester priority; it is
not an architectural priority or rollback claim [ADI-UM-1989, printed pp. 1-5–1-7,
5-9–5-12; ADI-DATABOOK-1987, printed pp. 2-36–2-43].

An additional bounded composition attaches fetched Type 2, every legal Type 3
transfer, and every source-closed Type 4 and Type 12 action to the ordinary PM fetch and
native-DM controller. A Type 2 word captures the old selected-I address (bit
reversed for DAG1 when enabled), raw immediate, and postmodify result at the
state-8 issue boundary. A Type 3 word instead captures its absolute address,
direction, and cycle-start shared-register store source. Type 4 captures its
selected-bank compute operands, old memory DREG, same-DAG old-I address, and
postmodify result at that boundary. Type 12 similarly captures selected-bank
shifter/feedback, old memory DREG, ASTAT, and same-DAG address/postmodify state.
The PM fetch and DM transfer remain paired
through every full-cycle DMACK extension. Qualified state-7 completion commits
the Type 2 selected I, Type 3 read destination, Type 4 compute/status/read/I,
or Type 12 shifter/status/read/I effects together with PC and the fetched word;
a load samples DMD only at that
boundary. The interrupt recognizer still observes every physical state-7
boundary, but a pending IRQ cannot vector or push context until aligned
completion.

Twenty-two tests and 50,000 model/RTL clocks cover 2,612 DM accepts, 2,611
completions, 111 wait extensions/state-7 IRQ samples, 1,169 reads, 1,443 writes,
and 889 architectural holds. Generated ownership contributes 73 fetched Type 2
accepts/72 completions, 149 Type 3, 2,057 Type 4, and 119 Type 12 transactions;
all Type 2 G/I/M selections; all
48 legal Type 3 store sources and 47 legal Type 3 load destinations; all 2,048
Type 4 `(Z, AMF, YOP, XOP)` tuples; all 112 sourced Type 12 `(SF, XOP)` pairs;
all Type 4/Type 12 DAG/I/M selections; all 16 DREGs; both directions; old-value
store overlap; memory-only AMF zero;
alternate-bank MAC; bit reversal; circular wrap; and complete waits. Twelve BR
recognitions include one first sampled during a DM wait; three paired
completions precede pending grant service, 12 grants mask every PM/DM output
enable for 18,638 clocks, and 10 release/reacquire/resume handshakes complete.
A separate raw descriptor remains structural verification scaffolding; a
collision with a generated class rejects both DM candidates and the paired PM
fetch, then retains the fetched instruction for a later eligible retry.
Ordinary HALT recognition remains live during a real Type 2 wait, but stop is
deferred until one paired completion/retirement. The stopped interface holds
the driven PM/DM state-8 outputs, blocks release while DMACK is low, and
resumes at state 8-to-1. Same-boundary and cross-owner BR/HALT requests fail
closed while preserving an already active owner.
The fetched vectors initialize exercised Type 3/4/12 store and compute/shift operands
and supply valid DMD for loads; reset-unknown source and invalid-DMD propagation
remain qualified by the standalone slices. Additional architectural DM
requesters, HALT during BG, and sourced whole-core dual-bus/event ownership remain outside this
composition
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 3-1–3-5, 4-9–4-10, 4-22,
5-9–5-16, 6-1, 6-3–6-7, 6-12–6-13, A-1, A-5–A-7, and A-9].

The bounded Type 13 path exposes distinct logical active-high PM data and
recovery-fetch cycles. Its connected 16-word cache supplies the actual next
instruction on a pre-cycle hit and captures each recovery word on a miss; an
explicit ordinary-fetch-completion input populates the same monitor outside
Type 13 ownership. A bounded wrapper connects this owner to the sourced PMS,
PMDA, and active-low PMRD/PMWR phases, but it is not a unified
PC/branch/interrupt bus owner
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8].

A separate native PM controller now converts a captured fetch/read/write
descriptor into the source-defined logical pin phases: PMA/PMDA/PMS through
states 1–8, active-low PMRD or PMWR through states 4–7, read sampling on the
7-to-8 edge, and write-data drive through states 5–8. It preserves active-low
PMS across back-to-back requests and exposes independent address, control, and
PMD output enables for bus relinquishment. Eleven directed tests and 50,032
model/RTL clocks pass [ADI-DATABOOK-1987, ADSP-2100 data sheet, printed
pp. 2-36–2-39, parameters 23–60, Figures 14–15; ADI-UM-1989, printed
pp. 5-5–5-8, Figure 5.5]. Its bounded Type 13/cache client captures a data
descriptor at state 8-to-1, commits the architectural data action at state
7-to-8, and accepts a miss recovery back-to-back. Six directed tests and
50,098 model/RTL clocks cover the attachment. A separate phase-aware BR/BG
controller now provides normal grant/release timing and a RESET-time native-pin
wrapper provides the documented asynchronous relationship. That controller is
now composed with the bounded ordinary NOP/Type 6/Type 7/Type 9/Type 14/Type
15/Type 16/Type 17/Type 18 fetch
owner: a recognized request lets the current fetch retire, inhibits the next
issue, masks all PM output enables during grant, and restarts issue at state
8-to-1 after release. Six directed tests and 50,054 model/RTL clocks cover 87
complete handshakes and one state-7-sampled IRQ2 retained through grant into
post-release vector entry. A separate composition described below now attaches the
Type 13 client to the shared owner; Type 5, other PM instruction classes, and
a whole-core PM arbiter remain outside the linear owner.

The bounded `adsp2100_program_owner_bus` now provides one physical PM
controller for three descriptor classes: ordinary fetch, Type 5 PM
transactions, and Type 13 PM transactions. The descriptor carries PMDA
explicitly because a Type 5/13 recovery fetch is an instruction access despite
retaining its architectural requester. Exactly one request on an enabled state-8-to-state-1 boundary
is accepted; the two-bit owner is retained through completion; and accepted,
read-sample, and completion pulses are routed one-hot. Multiple simultaneous
requests are rejected without an invented priority, and off-boundary requests
are rejected and reported. Eight directed tests and 50,007 independent-model/
RTL clocks cover all owners, 1,097 collision rejections, 1,346 out-of-phase
rejections, 3,248 completions, 2,576 owner switches, 611 relinquished active
holds, and 1,113 accepted Type 5/13 instruction-access descriptors. This
proves a shared electrical transaction owner and mutual exclusion, but not
branch/loop/interrupt/HALT/BR priority
[ADI-UM-1989, printed pp. 1-5–1-7, 3-6–3-7, 4-26–4-30, 5-5–5-8;
ADI-DATABOOK-1987, printed pp. 2-36–2-39].

The bounded `adsp2100_program_owner_bus_control` composition applies the
source-backed normal BR/BG sequence to that one shared interface. An active
owner remains driven and completes after state-3 recognition; future
descriptor capture is inhibited; native grant masks all PM output enables;
and capture resumes at state 8-to-1 after the complete release interval. Six
directed tests and 50,002 independent-model/RTL clocks cover 111 handshakes,
80 post-recognition completions, 1,417 blocked requests, 3,536 masked grant
clocks, 79 resume-edge acceptances, 530 fail-closed collisions, and 1,264
accepted Type 5/13 instruction-access descriptors. The wrapper exposes
blocked requests without inventing storage or priority
[ADI-UM-1989, printed pp. 5-3–5-8, Figures 5.3 and 5.5;
ADI-DATABOOK-1987, printed pp. 2-33–2-39].

`adsp2100_linear_owner_control_slice` attaches a retained ordinary-fetch
architectural client to that same boundary. The client owns its current
instruction until its selected PC+1 or Type 10 target is accepted and the
routed fetch completion arrives;
a fail-closed Type 5/Type 13 collision or BR/BG issue inhibition therefore
causes a later state-8 retry rather than a dropped instruction. Seven directed
tests and 50,054 independent-model/RTL clocks cover 4,389 accepted fetches,
743 retries, 4,387 completions, isolated raw Type 5/Type 13 ownership, 90
BR recognize/release/resume handshakes, and one IRQ2 retained through BG into
vector entry. Type 5 and Type 13 are raw descriptors
in this composition, so the result proves retained ordinary-fetch attachment,
not whole-core priority [ADI-UM-1989, printed pp. 1-5–1-7, 5-3–5-8,
Figures 5.3 and 5.5; ADI-DATABOOK-1987, printed pp. 2-33–2-39].

`adsp2100_compute_pm_owner_control_slice` applies the same shared-owner/BR-BG
boundary to the bounded Type 5 ALU/MAC-plus-PM/cache client. Captured PM-data
and recovery descriptors retry after fail-closed rejection, only routed Type 5
completion may commit ALU/MAC/PM/PX/DAG2 or recovery state, and completed
ordinary fetches fill the client cache. Six directed tests and 50,063 model/
RTL clocks cover 2,742 accepts, 713 retries, 1,371 data completions, 290 fetch
fills, 322 raw Type 13 completions, and 78 BR handshakes. Ordinary fetch and
Type 13 remain raw descriptor inputs in this separate attachment; unified
event priority remains outside the result [ADI-UM-1989, printed pp. 1-5–1-7,
2-6–2-7, 4-26–4-30, 5-3–5-8, Figures 5.3 and 5.5;
ADI-DATABOOK-1987, printed pp. 2-33–2-39].

`adsp2100_shifter_pm_owner_control_slice` attaches the bounded Type 13/cache
client to that shared owner and BR/BG boundary. A collision or grant-time
inhibition leaves the captured Type 13 PM-data or recovery descriptor pending;
the client presents it again on a later enabled state-8 boundary. Only the
routed Type 13 completion advances its data/recovery state, so a raw Type 5
completion cannot commit Type 13, and a rejected recovery cannot replay the
already completed shifter/PM/PX/DAG2 action. Completed ordinary fetches fill
the same 16-word cache. Six directed tests and 50,061 independent-model/RTL
clocks cover 2,783 accepted Type 13 descriptors, 752 retries, 1,391 data
completions, 286 ordinary-fetch cache fills, 286 raw Type 5 completions, 88 BR
handshakes, and 3,126 masked grant clocks. Ordinary fetch and Type 5 remain raw
descriptor inputs; HALT/TRAP/interrupt/loop/DM priority and whole-core request
generation remain outside this attachment [ADI-UM-1989, printed pp. 1-5–1-7,
2-6–2-7, 4-26–4-30, 5-3–5-8, Figures 5.3 and 5.5;
ADI-DATABOOK-1987, printed pp. 2-33–2-39].

`adsp2100_program_clients_owner_control_slice` is the first bounded
composition containing the real retained ordinary-fetch client, both real
PM-data clients, and the fetched Type 2/3/4/12 DM clients together. It owns
exactly one 16-word instruction cache, one native PM controller, one native DM
controller, and one normal BR/BG controller. Ordinary external
fetches and both recovery-fetch classes populate the shared cache; Type 5 and
Type 13 consume pre-cycle lookups from it. Client request collisions remain
fail-closed because the sources do not establish an architectural priority.
Type 5 and Type 13 are state-external action clients of the retained fetch
client's sole architectural-state owner with explicit validity sidecars.
Sequential automatic mode selects legal Type 5/Type 13 words from the retained
opcode and requests PC+1. A cache hit retires with the lookup word; a miss
commits its data action once and retires only when the pure recovery fetch
returns. The common linear client then installs that word and advances the
14-bit PC. Forty-five directed checks and 51,587 independent-model/RTL clocks
cover this flow, exact PC wrap, following fetched execution, routed retry,
cross-client state/cache visibility, and 2,217 clocks with every PM output
enable masked during grant. The same run admits each fetched DM class with its
ordinary next-word fetch, aligns PM/DM completion, repeats one full Type 2
cycle after a low state-6 DMACK sample, and masks both native buses during
grant. Returned-DMD validity reaches the Type 3 destination, while the Type 4
compute and Type 12 shift validity classifications remain independent of the
parallel DM-read destination classification. A pending IRQ is also held across recovery and
then enters the shared PC/status/vector path at whole-instruction retirement.
HALT now shares this owner: ordinary fetch completes before stopping, while a
Type 5/Type 13 PM-data request forces one external recovery before stop and
never replays the action. Release is DMACK-qualified. Active-loop PM issue and
unsourced BR/HALT overlap fail closed. Type 8/Type 9/Type 14/Type 15/Type 16/
Type 17/Type 21/Type 23/Type 24/Type 25 validity propagates into following PM clients,
including conditional-write preservation for Type 16 EXP LO and Type 25
MV-false. Type 17 unknown sources propagate through DREG, DAG, status/control,
SB, and PX, while unknown MSTAT rejects bank-dependent issue. OQ-016,
TRAP/interrupt/HALT/BR cross-event priority, Type 1 simultaneous PM/DM timing
under OQ-023, additional DM requesters, and a unified CPU
remain unproved. The same owner now preserves ASTAT/MSTAT/IMASK validity with
each accepted status entry and restores it on a valid pop after intervening
known writes
[ADI-UM-1989, printed pp. 4-26–4-30 and 5-3–5-14, Figures 5.3, 5.5,
5.6, and 5.7; ADI-DATABOOK-1987, printed pp. 2-33–2-43].

A separate active-low HALT controller is now composed with the same bounded
ordinary-fetch owner. It samples HALT at the enabled end of state 3, lets the
current PM read complete at state 7-to-8, holds the owner and its driven PM
outputs in state 8, and resumes at state 8-to-1 only when HALT is inactive and
DMACK is high. Eleven directed tests and 50,048 model/RTL clocks cover 789
ordinary recognitions/stops, 790 combined resumes, 150 DMACK-low blocked
releases, 819 held clocks, one fetched Type 22 TRAP/HALT handoff, and one IRQ2
sampled at state 7, held without entry through stop, and serviced on resume.
Unlike BG, HALT does not mask the PM output enables in this stopped ordinary-
fetch case. The standalone HALT controller separately classifies a recognized
PM-data cycle and exposes one `force_fetch_issue_o` pulse on the following
enabled state-8 issue boundary, then stops after that fetch reaches state 7.
Eight directed tests and 50,033 independent-model/RTL clocks cover 335 PM-data
recognitions and corresponding forced issue pulses. That signal is connected
separately to the bounded Type 5 and Type 13 owners. In each, a late
recognition discards an issue-time cache hit and commits
the data action once, drives one following external fetch, fills the cache,
and stops after its state-7 completion. The Type 13 attachment passes five
directed tests and 50,124 independent-model/RTL clocks with 210 such handoffs;
the Type 5 attachment passes five and 50,126 with 197. Both cover stable
driven halted outputs and DMACK-qualified resume. Their connection to the
shared selector and cross-event priority are not yet complete. HALT during BG
or DM waits, simultaneous TRAP/interrupt priority, reset interaction, and analog input timing
remain uncomposed
[ADI-UM-1989, printed pp. 5-13–5-14, 5-17–5-20].

Pin-compatible electrical timing belongs in a separate I/O wrapper. The generic
core exposes phase and transaction trace signals without a generic modern bus
that would erase original PM/DM concurrency.
