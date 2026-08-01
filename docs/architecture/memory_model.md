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
relinquishment. Type 2, Type 3, Type 4, and Type 12 are attached through separate bounded
wrappers; whole-core PM/DM arbitration remains outside this standalone
boundary
[ADI-UM-1989, printed pp. 5-9–5-12,
Figures 5.6–5.7; ADI-DATABOOK-1987, printed pp. 2-40–2-43,
Figures 16–17].

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
following 8-to-1 edge without deasserting PMS. Five directed tests and 50,081
model/RTL clocks cover read, write, hit, miss, phase hold, off-boundary
rejection, and externally directed relinquishment. This closes only the Type
13 attachment, not ordinary fetch, other PM-transfer classes, or whole-core
control arbitration [ADI-DATABOOK-1987, ADSP-2100 data sheet, printed
pp. 2-36–2-39, Figures 14–15; ADI-UM-1989, printed pp. 5-5–5-8,
Figure 5.5].
