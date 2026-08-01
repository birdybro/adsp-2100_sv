# Pipeline and cache

**Status: one-stage pipeline, bounded ordinary linear fetch/BR/HALT control,
bounded Type 5/Type 13 PM-data/HALT forced-fetch attachments, and cache-
integrated PM-data hit/miss timing implemented; unified hazards pending**

An instruction fetched in one processor cycle executes in the next while the
following instruction is fetched [ADI-UM-1989, printed p. 1-5]. Computation
inputs are read at cycle start and writes/status latch at cycle end
[ADI-UM-1989, printed pp. 2-6, 4-21].

The PC names the instruction currently executing. During ordinary linear
flow, the PC incrementer drives the following address onto PMA and that value
is loaded into the PC at cycle end [ADI-UM-1989, printed pp. 4-3, 4-10]. The
integrated Python model and bounded steady-state RTL owner now enforce this
distinction for NOP, legal Type 6/7, all 476,672 source-closed Type 8
ALU/MAC-plus-DREG packets, every Type 9 conditional ALU/MAC word,
all 25,648 canonical Type 14 shifter-plus-DREG packets,
all 14,336 supported Type 15 immediate-shift words, all 1,792 supported Type
16 conditional-shift words, all 2,256 legal Type 17 internal MOVE source/
destination pairs from fully initialized state, all Type 18 MODE CONTROL
words, all eight Type 23 DIVQ forms, all sixteen source-closed Type 24 DIVS
forms, the exact Type 25 conditional MR-saturation word, and all 32 Type 21
MODIFY words:
address `N` executes while an ordinary fetch for `N+1` occupies the native PM
phases, then the state-7-to-8 edge commits the current action, PC=`N+1`, and
the fetched word. Type 18 therefore transforms cycle-start MSTAT atomically at
that completion edge and its bank-select effect is visible to the following
instruction. Type 8 samples ALU/MAC operands, feedback, ASTAT, and the
parallel DREG move source from one cycle-start selected-bank snapshot, then
commits its noncolliding result, status, and move with PC and the fetched word
at the completion edge. Type 9 samples cycle-start operands, condition, bank, MSTAT
arithmetic controls, feedback, and validity-aware CNTR predicate, then commits
true ALU/MAC result and ASTAT effects atomically with the fetched word at the
same completion edge. False and AMF-zero forms retain the same one-cycle
fetch/retire boundary without an architectural computation write. Type 14
samples both DREG sources plus SR/SE/SB and ASTAT feedback at cycle
start, then commits its noncolliding move and function-selected shifter/status
results together at that edge. Type 15
samples the selected-bank X operand, immediate exponent, and old SR for OR
forms at cycle start, then commits SR at that edge. Type 16 samples its
predicate, X operand, SE/SR/SB, and ASTAT feedback at cycle start; a true form
commits only the function-selected SR/SE/SB/SS destinations, while a false
form preserves them without changing the fetch cycle. Type 23 samples the
selected-bank divisor, AF, AY0, and AQ at cycle start, then commits AF, AY0,
and AQ together at retirement while preserving every other ASTAT bit. Type 24
similarly samples the divisor, AY0, and AY1-or-AF upper dividend through three
cycle-start DREG reads before atomically retiring AF/AY0/AQ. A following DIVQ
therefore observes the just-retired division state. Type 25 samples cycle-start MV,
selected-bank MR, and bank selection; MV true commits the sign-selected MR
limit at state 7-to-8 without altering ASTAT, while MV false retires on the
same boundary without an MR write. Type 21 samples the selected I/M pair and
I-corresponding L at cycle start and commits only the selected I at state
7-to-8, without a PM-data, DM, or status action. The request is admitted at
the enabled state-8-to-1 edge, and
neither model invents an ordinary-PM wait extension because the original
interface exposes no PM acknowledge input. Twenty-four directed tests and
442,405 phase clocks compare the independent model with RTL. They traverse
every Type 8 compute-field tuple and every move source/destination pair in both
banks, every legal Type 17 pair, every Type 9 AMF/condition combination, every canonical Type 14
packet, every supported Type 15 and Type 16 word, every Type 18 encoding,
all Type 23 divisors in both banks and both old-AQ paths, every legal Type 24
divisor/upper-source form in both banks, dependent DIVS-to-DIVQ, the Type 25
true/false paths in both banks, every Type 21 DAG/I/M selection with positive
and negative linear/circular modification, phase holds, bus-output
relinquishment, PC wrap, selected-bank state,
CNTR-stack effects, invalid fetched data, and fail-closed unsupported words. A
Type 17 move sourced from ASTAT, MSTAT,
SSTAT, IMASK, or ICNTL raises a dedicated retirement pulse so the OQ-016
zero-extension hypothesis cannot become invisible. The deterministic
instruction preload and complete state initialization are verification hooks,
not architectural interfaces. Reset release/first fetch, active-loop and branch
selection, interrupt abort, PM-data/cache ownership, HALT, and whole-core
BR/BG arbitration remain outside this bounded result. A separate bounded
composition now proves the ordinary linear owner across 50,003 more clocks and
86 complete BR/BG handshakes, including current-fetch retirement, next-issue
inhibition, grant-time PM masking, and state-8-to-state-1 restart; it does not
attach any other PM/DM owner [ADI-UM-1989, printed pp. 1-5,
2-6–2-7, 2-15, 2-18–2-19, 2-20–2-30, 3-2–3-3, 3-7, 4-3–4-4, 4-10, 4-20–4-25,
5-5–5-8, 6-1–6-2, 6-11–6-12, 6-14–6-15, A-3, A-7, and A-9].

Another bounded composition now verifies the ordinary-fetch HALT pipeline
case. Active-low HALT recognition at state 3 does not squash the word already
executing or its overlapped fetch. That fetch retires at state 7-to-8, the
pipeline then remains stopped with the fetched PC/opcode and external PM
levels stable in state 8, and a DMACK-qualified HALT release issues the next
fetch at state 8-to-1. The independent-model/RTL comparison covers 50,003
clocks and 788 stop/restart sequences. The distinct PM-data case still requires
the documented forced external instruction fetch even on a cache hit. A
standalone controller now schedules that path: PM-data recognition completes
the data cycle, admits one forced fetch at the following state-8 issue edge,
and stops only after that fetch completes. Eight directed tests and 50,033
model/RTL clocks cover 335 such recognitions and issue events. A bounded
Type 13/native-PM composition now attaches the handoff: late recognition
overrides a captured cache hit, data actions commit exactly once, one external
fetch fills the monitor, and the stop follows that fetch's state-7 completion.
Five directed tests and 50,124 clocks cover 210 such attached handoffs.
The parallel Type 5/native-PM composition verifies another five directed tests
and 50,126 clocks: 197 late hits are suppressed, ALU/MAC/PM/PX/DAG2 effects
commit once, one native external fetch follows, and 387 stop/resume handshakes
complete without replay. Shared-PM/event arbitration remains open
[ADI-UM-1989, printed pp. 4-26–4-30 and 5-13–5-14].

PM data use conflicts with external instruction fetch. The 16×24 cache can
supply a valid next instruction; otherwise an additional external fetch cycle
occurs [ADI-UM-1989, printed pp. 1-7, 4-26–4-28]. Cache fills transparently with
executed external instructions.

Interrupt entry aborts an already fetched instruction and later refetches it
[ADI-UM-1989, printed pp. 4-9–4-10, Figure 5.11 p. 5-16]. HALT during PM data
also forces an instruction fetch before stopping [ADI-UM-1989, printed
pp. 5-13–5-14].

The standalone functional monitor implements the documented 16-by-24 array,
PMA[3:0] indexing, one contiguous valid region, out-of-region invalidation,
and oldest-word circular replacement. It passes 50,028 deterministic model/
RTL clocks. The manual describes hidden ahead/behind registers but does not
expose their exact encoding, so this is the externally visible region contract,
not a gate-level reconstruction [ADI-UM-1989, printed pp. 4-26–4-28].
Self-modifying PM behavior and unified branch/loop/interrupt/HALT/BR arbitration
remain OQ-008.

The bounded Type 13 model/RTL makes the sourced two outcomes explicit. Its
composed cache boundary looks up the next fetch address in the pre-cycle
monitor. A valid entry supplies the actual 24-bit next instruction and the PM
data instruction completes in its single data cycle. Without one, that cycle
commits the shifter, PM/PX, and DAG2 effects and records one recovery fetch
address; the next cycle performs only the external instruction fetch, fills
the monitor, supplies that instruction, and exposes the event-recognition
boundary. A forced-fetch input models the documented HALT handoff and refreshes
the cache even on a prior hit. The base Type 13 and integrated boundaries pass
50,070 and 50,086 model/RTL clocks respectively [ADI-UM-1989, printed
pp. 4-26–4-30, 5-13–5-16]. Ordinary external fetch completion is an explicit
fill input when Type 13 does not own PM. Unified PC/branch/loop/interrupt/HALT/
BR ownership and self-modifying PM effects remain OQ-008.

The bounded native attachment maps each of those logical cycles onto the
source-backed eight states. Type 13 issue and old-value capture occur at the
enabled state-8-to-state-1 boundary; architectural data-cycle commit and hit
instruction release occur at state 7-to-8. On a miss, the recovery descriptor
is accepted at the immediately following state 8-to-1 and completes at its
state 7-to-8 edge. Five directed tests and 50,081 model/RTL clocks verify this
mapping without claiming ordinary-PC fetch arbitration, branch/loop flushes,
interrupt recognition or BR/BG ownership
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8].

The Type 13/HALT wrapper adds the late-recognition path without changing the
ordinary hit/miss contract. It withholds the issue-time cached word when HALT
arrives at state 3, records recovery in the already-pending descriptor, and
hands the native PM bus to exactly one recovery fetch after data completion.
The recovery fills the monitor and provides the stopped instruction word; no
shifter, PM transfer, PX, or DAG write is replayed. Halted state 8 retains the
driven PM levels, and release requires HALT inactive with DMACK high. The
Type 5/HALT wrapper applies the same late-hit conversion and one-time commit
rule to ALU/MAC-plus-PM. Idle ordinary-fetch HALT, BG/DM waits, TRAP,
interrupts, reset release, and multi-owner priority remain outside these
PM-data owners.
