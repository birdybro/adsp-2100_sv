# Architectural memory model

**Status: original-device baseline**

Program words are 24 bits; data words are 16 bits. PMA and DMA are each 14 bits
[ADI-UM-1989, printed pp. 1-5–1-6]. PM can contain instructions or data.
PMDA distinguishes data access and can act as a fifteenth address bit, creating
separate 16K code and 16K data regions when used that way
[ADI-UM-1989, printed pp. 5-6–5-7].

PM data read/write bridges through the PMD-DMD exchange. The upper 16 PM bits
transfer directly and PX carries the low eight bits; PM data reads automatically
load PX and PM writes append PX [ADI-UM-1989, printed pp. 3-6–3-8].

The architectural model exposes separate PM instruction fetch, PM data read,
PM data write, DM read, and DM write transactions. It does not embed RAM into
the CPU. Uninitialized memory is a model input, not silently zero.

The bounded Type 1 state slice exposes simultaneous logical DM and PM read
descriptors from fixed DAG1 and DAG2 selections. It captures both old-I
addresses, postmodify results, computation operands/results, and destinations
at issue. One implementation/test completion signal holds both descriptors
and all architectural state together, then atomically commits the two DREG
loads, PX, both selected-I writes, and optional compute/status result. Twelve
directed/model checks and 51,069 model/RTL clocks cover 27,309 held clocks,
independent DAG1 bit reversal, both banks, circular updates, reset, conflicts,
and unknown data. This boundary intentionally does not map completion to
DMACK or PM pins: native PM behavior during a Type 1 DMACK extension remains
OQ-023, and cache/fetch/event ownership remains outside the slice
[ADI-UM-1989, printed pp. 2-6–2-7, 3-1–3-7, 5-5–5-12, 6-3–6-5, A-1].

The original Type 4 boundary decodes both DM directions, both DAGs, every
DREG, and all standard ALU/MAC fields. AMF zero supplies memory-only indirect
moves; compute-plus-write captures the old DREG, and a colliding
compute-plus-read fails closed. The bounded logical transaction captures
cycle-start selected-bank compute and DAG state, holds address/direction/write
data and every destination over arbitrary DMACK-low clocks, and atomically
commits computation/status, optional read data, and selected-I postmodify on
the first acknowledged clock. Twelve model/schema/directed checks and 50,072
deterministic model/RTL clocks cover this boundary. A separate native
composition adds six directed checks and 50,082 clocks covering state-8 issue,
documented read/write pin phases, complete-cycle DMACK extension, state-7
atomic commit, reset, off-boundary rejection, and relinquishment. Whole-core
fetch/event and multi-owner DM arbitration remain open
[ADI-UM-1989, printed pp. 5-9–5-12, 6-3–6-7, 6-12–6-13, A-1,
A-5–A-11].

The original Type 3 boundary selects one absolute 14-bit DM address directly
from the instruction and one general-register source or destination; it has no
DAG effect. The complete class partitions into 770,048 supported reads,
786,432 supported writes, and 540,672 reserved/read-only-destination words.
The bounded logical implementation reuses the complete Type 17 register-state
semantics, including selected computational banks, MR1-to-MR2 sign fill,
status-field narrowing, PX, CNTR/count-stack load effects, and explicit reset
unknowns. A write captures the cycle-start register value and address; a read
updates its destination only on acknowledged completion. Invalid read data
invalidates the destination, including CNTR, without fabricating data or a
count-stack push. Nine directed tests and 50,151 deterministic model/RTL clocks
cover every legal selector, both directions, banking, waits, side effects,
reset, conflicts, and unknowns.

The native Type 3 composition accepts only at state 8-to-1 and returns the
qualified state-7-to-8 completion to the logical slice. Five directed tests and
50,077 connected clocks cover physical read/write phases, complete-cycle
DMACK extension, late-ACK and off-boundary rejection, reset, relinquishment,
and completion-only register writes. Writes sourced by narrow status/control
registers remain executable with an observable provisional flag because
OQ-016 has not closed their upper-DMD-bit values. Whole-core request ownership,
fetch, and event arbitration remain outside this bounded client
[ADI-UM-1989, printed pp. 1-5–1-6, 4-22, 5-9–5-12, 6-1–6-2,
6-12–6-13, A-1, A-7, and A-9].

A further bounded ordinary-fetch/native-DM composition decodes legal Type 3
and source-closed Type 4/Type 12 words from the retained instruction. At state
8 it captures the Type 3 direct descriptor or Type 4/Type 12 old compute/
shifter/store/DAG operands; qualified state-7 completion commits the load,
compute/shifter/status, and selected-I effects together with PC and the returned
instruction. Twenty-two tests and 50,000 clocks include all legal Type 3
register selectors, all 2,048 Type 4 compute tuples, all 112 sourced Type 12
shifter tuples, every applicable DAG/I/M and DREG selector, both directions,
old-value overlap, alternate-bank operation, bit reversal, circular wrap, and
complete waits. The run covers 2,612 DM accepts, 2,611 completions, 111 wait
extensions/state-7 IRQ samples, 1,169 reads, 1,443 writes, and 889 holds;
generated ownership contributes 73 Type 2 accepts/72 completions, 149 Type 3,
2,057 Type 4, and 119 Type 12 transfers. BR remains recognizable at physical
state 3 during a wait, service is deferred through paired completion, and
native grant masks every PM/DM output enable. The composed run also recognizes
one ordinary HALT during a real Type 2 wait, defers stop until
paired completion/retirement, holds driven state 8, blocks low-DMACK release,
and resumes at state 8-to-1; same-boundary and cross-owner BR/HALT requests
fail closed while preserving an already active owner. Deterministic fetched vectors
initialize Type 3/4/12 sources and
supply valid DMD; their standalone boundaries remain the evidence for reset-
unknown source and invalid-DMD propagation.

The bounded Type 2 immediate-write path drives the old selected I (or DAG1
bit reversal), raw 16-bit immediate, and write direction. It holds those
signals over every DMACK-low extension and commits only the selected-I
post-modification at the first acknowledged boundary. The 50,035-clock
model/RTL differential covers every I/M selection, both DAGs, immediate and
multi-clock completion, reset cancellation, and invalid/unknown DAG state
[ADI-UM-1989, printed pp. 3-1–3-5, 5-9–5-12, 6-1, 6-12, A-1, and A-6].
Its native composition accepts that old-value descriptor only on the enabled
state-8-to-state-1 boundary and returns the physical completion event to the
architectural slice only on state 7-to-state-8. Five directed tests and 50,027
connected model/RTL clocks cover qualified and extended writes, late ACK,
phase conflicts, stable old values, and relinquishment.

The bounded Type 12 boundary adds the multifunction DM transaction path. It
drives the old selected I (or the DAG1 bit-reversal of that value), direction,
select, and old write-source data. A missing DMACK holds all valid bus outputs
and all architectural destinations. The first acknowledged boundary samples
read data and atomically commits the optional DREG load, shifter action, and
selected-I post-modification [ADI-UM-1989, printed pp. 5-9–5-12,
6-3–6-7]. Its native composition accepts that old-value descriptor only at
state 8-to-1, samples a read at the native state 7-to-8 edge, and presents that
same completion event to the architectural slice. Six directed tests and
50,064 connected model/RTL clocks cover read/write direction, old-value
stores, complete-cycle waits, invalid read data, reset with an outstanding
transaction, off-boundary controls, and relinquishment. It does not yet
include PM fetch concurrency, BR/BG ownership, or interrupt/HALT latching.

The separate native DM controller captures one selected descriptor at its
implementation state-8-to-state-1 boundary and produces DMA, active-low
DMS/DMRD/DMWR, and DMD output-enable timing over the documented substates.
DMACK is qualified only at 6-to-7. Each low sample retains architectural state
seven while all eight physical substates repeat; a high sample permits the
read sample/completion at the following 7-to-8 edge. Nine directed tests and
50,039 model/RTL clocks cover normal reads/writes, repeated extensions,
late-ACK rejection, back-to-back select, reset, unknowns, and external
relinquishment. Type 2, Type 3, Type 4, and Type 12 are attached through
separate bounded wrappers and additionally share the bounded fetched owner
described above. Whole-core PM/DM arbitration remains outside these boundaries
[ADI-UM-1989, printed pp. 5-9–5-12,
Figures 5.6–5.7; ADI-DATABOOK-1987, printed pp. 2-40–2-43,
Figures 16–17].

A separate shared-DM owner places two retained descriptor inputs in front of
that one controller. Exact-one selection is accepted only when the native bus
is ready; simultaneous requests fail closed, and an out-of-phase request is
reported. Unlike the non-waited PM selector, the DM owner is retained when a
low DMACK causes the physical phase sequence to revisit state 8, because the
native controller is not ready to replace the outstanding transaction. All
DMACK and completion events are one-hot routed to that retained owner. Nine
directed/model tests and 50,010 RTL/model clocks cover 1,642 fetched-owner and
1,660 companion-owner accepts, 494 rejected collisions, 814 wait extensions,
3,302 completions, and unknown/relinquished cases. The bounded fetched
Type 2/3/4/12 composition now attaches through this owner. Its conservative
preflight rejects a simultaneous structural-companion descriptor before the
overlapped PM fetch or either DM request is accepted, leaves the retained
instruction pending for retry, and reports the conflict. The sources do not
authorize a requester priority or partial issue, so this fail-closed behavior
is an implementation invariant rather than an original-device priority claim
[ADI-UM-1989, printed pp. 1-5–1-7, 5-9–5-12;
ADI-DATABOOK-1987, printed pp. 2-36–2-43].

The bounded Type 13 boundary implements the corresponding PM-data path with
fixed original-device timing. It exposes the old DAG2 I address, PM data
direction, and the old `{DREG,PX}` 24-bit write word. A read atomically loads
the upper 16 bits into the selected DREG and the low eight bits into PX while
the shifter and selected-I post-modify commit. There is no invented PM
acknowledge input [ADI-UM-1989, printed pp. 3-6–3-7, 5-5–5-8,
6-3–6-7]. A cache hit completes in that cycle; a miss adds one instruction
fetch cycle without repeating the data action [ADI-UM-1989, printed
pp. 4-26–4-30]. A composed boundary now connects the separate source-bounded
monitor: it uses a pre-cycle lookup for the next instruction, routes the actual
cached 24-bit word on a hit, and fills the monitor from either ordinary
external instruction-fetch completion or the single recovery cycle after a
miss. Scheduled recovery owns PM over a conflicting ordinary fill; a
standalone fill owns PM over a newly requested bounded Type 13/setup action
and reports the conflict. Ten directed tests and 50,086 integration clocks
cover this ownership boundary. That conflict priority is a fail-closed harness
policy for an integration error, not claimed original-device arbitration;
whole-core issue must prevent the collision. Unified whole-core PM ownership,
hidden monitor encoding, and self-modifying PM remain OQ-008.

The separate native PM phase controller accepts one selected logical request
at its implementation state-8-to-state-1 boundary and produces active-low
PMS/PMRD/PMWR plus PMA, PMDA, and PMD output-enable timing over the documented
eight states. A bounded Type 13/cache wrapper now connects this request owner:
the data descriptor and all architectural old values are captured on that
8-to-1 edge, remain stable through the phase sequence, and commit only on the
7-to-8 completion edge. A cache hit releases its issue-time captured word at
that edge; a miss schedules a pure recovery fetch that is accepted on the
following 8-to-1 edge without deasserting PMS. Six directed tests and 50,098
model/RTL clocks cover read, write, hit, miss, phase hold, off-boundary
rejection, and externally directed relinquishment. This closes only the Type
13 attachment, not ordinary fetch, other PM-transfer classes, or whole-core
control arbitration [ADI-DATABOOK-1987, ADSP-2100 data sheet, printed
pp. 2-36–2-39, Figures 14–15; ADI-UM-1989, printed pp. 5-5–5-8,
Figure 5.5].

The bounded combined composition reuses exactly one instance of that monitor
across retained ordinary fetch, Type 5, and Type 13, and now attaches fetched
Type 2/3/4/12 descriptors from the same architectural owner to one native DM
controller. Any routed
external instruction completion—ordinary fetch or a Type 5/Type 13
recovery—fills it, and either PM-data client can consume a pre-cycle lookup.
State-external Type 5 and Type 13 clients also commit into the retained fetch
client's sole architectural-state owner. Forty-five directed checks plus 51,587
independent-model/RTL clocks cover both
ordinary-fill cross-client hits, a Type 13 miss/recovery/fill sequence, retained
descriptor retry, fail-closed request collisions, 179 accepted cache fills,
completion isolation, both directions of Type 5/Type 13 `{DREG,PX}`
visibility, fetched-Type-6-to-Type-13 visibility, and Type-5-to-fetched-Type-17
visibility. Known and unknown fetched Type 21 postmodify results, Type 23/Type
24 division results, and Type 25 true/false/unknown-MV results are also
observed by a following PM client through the same validity paths. Type 17
unknown DREG/DAG/status/control/SB/PX destinations and unknown-MSTAT rejection
are now covered through the same owner. The fetched-DM sidecars propagate an
unknown Type 3 DMD result to its selected destination and independently track
the compute or shift result against the parallel Type 4 or Type 12 DM-read
destination: one side can remain known while the other becomes invalid.
Sequential automatic mode now
issues the retained Type 5/Type 13
opcode, installs the same-cycle hit or one-cycle recovery word, advances and
wraps PC, and connects recovery retirement to shared interrupt entry. The
attached HALT path overrides an issue-time hit, leaves the PM-data action one-
shot, fills through exactly one external recovery, then stops. Active loops
and unsourced BR/HALT overlap fail closed under OQ-008. Hidden monitor
encoding, self-modifying PM, OQ-016 narrow-source extension, TRAP/interrupt/
HALT/BR cross-event priority, additional DM requesters, Type 1 simultaneous
PM/DM timing under OQ-023, and whole-core ownership remain open. For the four
attached DM classes, PM fetch and DM accept and complete together; a low
state-6 DMACK sample freezes architectural/PM progress while the physical DM
cycle and event samples continue. The shared-state evidence additionally preserves captured ASTAT/MSTAT/
IMASK validity across an accepted status push, intervening known writes, and
valid pop
[ADI-UM-1989, printed pp. 4-26–4-30 and 5-3–5-14;
ADI-DATABOOK-1987, printed pp. 2-33–2-43].

The bounded Type 13/HALT composition adds the exceptional late owner handoff
specified for a state-3 stop request during PM data. It records recovery in
the active descriptor, suppresses an issue-time cached instruction, commits
the PM data action once, then accepts exactly one native external fetch at the
next state-8 boundary. That fetch fills the monitor and its state-7 completion
enters stopped state 8. Five tests and 50,124 model/RTL clocks verify this
sequence, including stable halted outputs and DMACK-qualified release. Type 5
has an independent equivalent attachment: five tests and 50,126 clocks verify
197 hit overrides/forced fetches, one-time ALU/MAC/PM/PX/DAG2 completion, and
387 stop/resume handshakes. The superseding three-client owner now contains
both behaviors behind the one shared cache/native-PM boundary; broader
simultaneous-event arbitration remains outside the bounded result
[ADI-UM-1989, printed pp. 4-26–4-30 and 5-13–5-14].
