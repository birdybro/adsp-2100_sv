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
7-to-8, and accepts a miss recovery back-to-back. Five directed tests and
50,081 model/RTL clocks cover the attachment. A separate phase-aware BR/BG
controller now provides normal grant/release timing and a RESET-time native-pin
wrapper provides the documented asynchronous relationship. That controller is
now composed with the bounded ordinary NOP/Type 6/Type 7/Type 17/Type 18 fetch
owner: a recognized request lets the current fetch retire, inhibits the next
issue, masks all PM output enables during grant, and restarts issue at state
8-to-1 after release. Five directed tests and 50,003 model/RTL clocks cover 93
complete handshakes. A separate composition described below now attaches the
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

A separate active-low HALT controller is now composed with the same bounded
ordinary-fetch owner. It samples HALT at the enabled end of state 3, lets the
current PM read complete at state 7-to-8, holds the owner and its driven PM
outputs in state 8, and resumes at state 8-to-1 only when HALT is inactive and
DMACK is high. Seven directed tests and 50,003 model/RTL clocks cover 790
stops/resumes, including 161 DMACK-low blocked releases and 742 held clocks.
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
or DM waits, TRAP/interrupt priority, reset interaction, and analog input timing
remain uncomposed
[ADI-UM-1989, printed pp. 5-13–5-14, 5-17–5-20].

Pin-compatible electrical timing belongs in a separate I/O wrapper. The generic
core exposes phase and transaction trace signals without a generic modern bus
that would erase original PM/DM concurrency.
