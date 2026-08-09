# Pipeline and cache

**Status: one-stage pipeline, bounded ordinary linear fetch/IRQ/BR/HALT control,
bounded Type 5/Type 13 PM-data/HALT forced-fetch attachments, and cache-
integrated PM-data hit/miss timing implemented; unified hazards pending**

An instruction fetched in one processor cycle executes in the next while the
following instruction is fetched [ADI-UM-1989, printed p. 1-5]. Computation
inputs are read at cycle start and writes/status latch at cycle end
[ADI-UM-1989, printed pp. 2-6, 4-21].

Type 1 now has a separate bounded logical execution slice, but it is not a
member of the ordinary-fetch owner below. That slice captures simultaneous
DAG1 DM, DAG2 PM, and optional ALU/MAC actions, holds them together, and
atomically commits both loads, PX, both postmodifications, and computation/
status at one implementation/test completion boundary across 51,069 clocks.
It does not select or install the next instruction. OQ-023 still withholds the
native PM behavior during DMACK extension, so composing Type 1 with this
pipeline, the cache, and system events would exceed the sourced timing
evidence [ADI-UM-1989, printed pp. 2-6–2-7, 3-6–3-7, 4-26–4-30,
5-5–5-12, 6-3–6-5, A-1].

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
forms, the exact Type 25 conditional MR-saturation word, all 32 Type 21
MODIFY words, all 32 Type 26 stack-control words, and all 507,904
source-closed Type 10 direct-transfer words. Address `N` executes while the
selected next fetch occupies the native PM phases. Ordinary and false Type 10
flow select `N+1`; a taken Type 10 selects its 14-bit target. The state-7-to-8
edge commits the current action, PC=selected fetch address, and the fetched
word. Type 18 therefore transforms cycle-start MSTAT atomically at
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
7-to-8, without a PM-data, DM, or status action. Type 26 reads status and stack
tops at cycle start and commits its independent manual actions only at
retirement. Valid fetched status and count pops are covered. A fetched Type
10 CALL creates valid PC-stack context that a following Type 26 POP PC or Type
20 RTS consumes; fetched Type 11 creates valid PC- and loop-stack context that
automatic termination or Type 26 POP LOOP consumes. One nonterminal Type 26
word also consumes valid status, count, PC, and loop tops together at the same
retirement edge. Type 11 retirement pushes
wrapped PC+1 and its descriptor atomically, while a later terminal issue
selects loopback or exit from the cycle-start top, condition, CNTR, and
count-stack state. Type 19 selects PC+1
or the known cycle-start I4-I7 target at the same issue boundary, leaves I
unchanged, commits CALL/JUMP-NOT-CE actions only at retirement, and fails
closed for an unknown taken target; fetched Type 20 RTS consumes one such CALL
context. Type 20 selects PC+1
for false flow or the valid PC-stack top for a taken return at state-8 issue;
state-7 completion pops PC and, for RTI, atomically pops/restores status.
Type 22 evaluates its cycle-start condition at the same issue boundary. A
false form participates in the ordinary automatic-loop decision; a true form
selects PC+1 as an explicit action, suppresses a simultaneous loop-terminal
action, and emits the retirement-aligned TRAP event after that PC+1 word has
been fetched.
The request is admitted at the
enabled state-8-to-1 edge, and
neither model invents an ordinary-PM wait extension because the original
interface exposes no PM acknowledge input. Forty-eight directed tests and
444,003 phase clocks compare the independent model with RTL. They traverse
every Type 8 compute-field tuple and every move source/destination pair in both
banks, every legal Type 17 pair, every Type 9 AMF/condition combination, every canonical Type 14
packet, every supported Type 15 and Type 16 word, every Type 18 encoding,
all Type 23 divisors in both banks and both old-AQ paths, every legal Type 24
divisor/upper-source form in both banks, dependent DIVS-to-DIVQ, the Type 25
true/false paths in both banks, every Type 21 DAG/I/M selection with positive
and negative linear/circular modification, every Type 26 payload with valid
status/count context plus one fully valid combined status/count/PC/loop pop,
representative Type 10 targets and every condition plus
directed false, CALL/POP-PC, counter-restore, and counter-decrement sequences,
Type 19 I4-I7 taken/false flow, unknown-target rejection, CALL/RTS context, and
JUMP NOT CE, every Type 11 setup field, non-counter/ASTAT/CE loopback and exit,
nested CE restoration, explicit-flow precedence, valid Type 26 loop
consumption, phase holds, every Type 20 condition through RTS, valid RTI
restore, missing-context rejection, every Type 22 condition under low/high
ASTAT and both NOT CE outcomes, true/false loop-terminal precedence, bus-output
relinquishment, PC wrap, selected-bank state,
CNTR-stack effects, invalid fetched data, and fail-closed unsupported words. A
Type 17 move sourced from ASTAT, MSTAT,
SSTAT, IMASK, or ICNTL raises a dedicated retirement pulse so the OQ-016
zero-extension hypothesis cannot become invisible. The deterministic
instruction preload and complete state initialization are verification hooks,
not architectural interfaces. The same private owner now recognizes original
IRQ0–IRQ3 at state 7, retires the executing instruction, discards the fetched
following word, issues one vectoring-NOP fetch, pushes PC/status context, and
loads the vector word; fetched RTI refetches the discarded address. Reset
release/first fetch, other transfer classes, PM-data/cache ownership,
PC/status entry ownership after PM-data
recognition,
simultaneous ordinary-HALT/TRAP/IRQ
priority, unresolved OQ-018 automatic/manual combinations, and whole-core
BR/BG arbitration remain outside this bounded result. Separate bounded
compositions now prove a retained state-7-sampled IRQ through ordinary HALT and
normal BR/BG. A third composition proves that physical state-7 IRQ sampling
continues through native DMACK extensions while the architectural pipeline
remains held, and that service waits for aligned PM/DM completion. That
composition now enables real fetched Type 2, legal Type 3, source-closed Type 4,
and source-closed Type 12 semantics. State-8 issue captures the Type 2
old-I/immediate descriptor, Type 3 direct descriptor, Type 4 cycle-start
compute/store/DAG descriptor, or Type 12 cycle-start shifter/store/DAG descriptor.
All wait cycles hold it beside the PM fetch, and aligned state-7 completion
commits the applicable selected-I, load, compute/shifter, and status effects
with PC and the returned instruction once. Twenty-two checks and 50,000 clocks
cover 2,612 DM accepts, 2,611 completions, 111 wait/IRQ samples, 1,169 reads,
1,443 writes, and 889 holds. Generated ownership contributes 73 Type 2
accepts/72 completions, 149 Type 3, 2,057 Type 4, and 119 Type 12 transfers;
every Type 2 G/I/M; every legal Type 3 register selector; all 2,048 Type 4
compute tuples; all 112 sourced Type 12 shifter tuples; all applicable DAG/I/M
and DREG selectors; both directions; boundary cases; and full waits. BR remains
recognizable at physical state 3 during a wait, grant service waits for paired
completion, and native grant masks every PM/DM output enable.
Ordinary HALT recognition also remains live during a real Type 2 wait, but its
stop is deferred until the aligned completion/retirement. The owner then holds
driven state 8, blocks low-DMACK release, and resumes the retained next word at
state 8-to-1. Same-boundary and cross-owner BR/HALT requests fail closed while
preserving an already active owner.
Loads sample DMD only at completion. The raw descriptor port remains separate
scaffolding for lower-level timing tests. Fetched Type 3/4/12 store and compute/shift
sources are initialized and load data is valid in this composition; standalone
slices retain the broader unknown-validity evidence. The private BR/BG
run covers 50,054 clocks and 87 complete
handshakes, including current-fetch retirement, next-issue inhibition,
grant-time PM masking, post-release vector entry, and state-8-to-state-1
restart; it does not
attach any other PM/DM owner [ADI-UM-1989, printed pp. 1-5,
2-6–2-7, 2-15, 2-18–2-19, 2-20–2-30, 3-2–3-3, 3-7, 4-3–4-4, 4-10, 4-20–4-25,
5-5–5-8, 6-1–6-2, 6-11–6-12, 6-14–6-15, A-3, A-7, and A-9].

Another bounded composition now verifies the ordinary-fetch HALT pipeline
case, including the fetched Type 22 handoff. Active-low HALT recognition at
state 3 does not squash the word already
executing or its overlapped fetch. That fetch retires at state 7-to-8, the
pipeline then remains stopped with the fetched PC/opcode and external PM
levels stable in state 8, and a DMACK-qualified HALT release issues the next
fetch at state 8-to-1. A taken fetched Type 22 instead retires its PC+1 fetch,
asserts TRAP, and holds state 8. HALT assertion clears TRAP but retains the
hold; HALT release with DMACK high issues the already-fetched PC+1 word. Eleven
directed tests and 50,048 independent-model/RTL clocks cover 789 ordinary
recognitions/stops, one Type 22 assertion/acknowledgment/handoff/restart, one
retained IRQ2 entry after resume, 150 blocked releases, and 819 held clocks.
The distinct PM-data case still requires
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
state 7-to-8 edge. Six directed tests and 50,098 model/RTL clocks verify this
mapping and the no-service interval for an IRQ edge first sampled at uncached
data completion: it remains pending until recovery completion. The Type 5
native/cache owner verifies the same rule across six tests and 50,100 clocks.
Both expose recognition/vector handoff without claiming ordinary-PC fetch
arbitration, context entry, branch/loop flushes, or BR/BG ownership
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8, 5-15–5-16].

The bounded three-client owner composes the retained ordinary-fetch pipeline
and both real PM-data pipelines behind one cache/native-PM/BR-BG boundary.
Fetched Type 2/3/4/12 additionally use one native DM controller driven by that
same retained owner. Their ordinary fetch and DM descriptor accept together;
DMACK-low repeats a physical cycle while architectural and PM progress hold,
then both transactions and all parallel state retire at the qualified state-7
boundary.
The ordinary client retains its selected next-PC descriptor, and each PM-data
client retains either its data descriptor or subsequent recovery descriptor
until routed acceptance/completion. State-external Type 5 and Type 13 clients
commit into the retained fetch client's sole architectural-state owner.
Sequential automatic mode derives Type 5/Type 13 issue from the retained
opcode and PC+1. A hit makes its cached word available at PM-data completion;
a miss commits the data action there but delays instruction retirement until
the external recovery word returns. That retirement atomically advances PC and
installs the next opcode. The original HALT schedule is attached at this
combined boundary: ordinary fetch retires before stop, while PM-data
recognition suppresses a hit, commits once, forces one recovery for the
captured client, and stops at recovery completion. Forty-five directed checks
and 51,587 independent-model/RTL clocks cover one-time completion, shared
fills/hits, recovery, PC
wrap, following fetched execution, fail-closed requests, grant masking, and
cross-client state visibility. One IRQ case proves recognition is withheld
until recovery retirement, where the returned sequential word is discarded
and shared PC/status vector entry begins. Three HALT cases cover ordinary
stop, Type 5 forced recovery, Type 13 forced recovery, DMACK-qualified release,
and fail-closed BR/HALT overlap. Type 8/Type 9/Type 14/Type 15/Type 16/Type 17/Type 21/
Type 23/Type 24/Type 25 validity is now retained from issue through retirement,
including unknown conditional predicates and operands, the Type 16 EXP LO
write-possibility exception, a Type 21 result's validity in the following PM
address, and Type 25 MV-false preservation. Type 17 unknown source validity
propagates through DREG, DAG, status/control, SB, and PX; unknown MSTAT blocks
bank-dependent issue. Accepted status entries also carry ASTAT/MSTAT/IMASK
validity through intervening writes to the later POP STS retirement boundary.
Active-loop PM issue, OQ-016, additional DM requester priority, OQ-023 Type 1
timing, and sourced event priority remain prerequisites to broader integration
[ADI-UM-1989, printed pp. 4-26–4-30 and 5-3–5-14;
ADI-DATABOOK-1987, printed pp. 2-33–2-43].

For FPGA timing, the owner captures decoded Type 8/Type 9 and Type 5 compute
actions at the already established state-8 issue edge and retires those
captured actions only at the same state-7 completion edge. Dedicated
selected-bank DREG read ports provide the parallel PM-data operands without a
generic register-group mux. The combined integration also proves that vector
entry excludes both ordinary retirement and PM-data state action before
eliding the otherwise redundant generic conflict cone; the reusable
architectural-state block retains its fail-closed default. These choices are
**implementation convenience**, not evidence for hidden original-device
pipeline registers. They do not add an instruction cycle or change the
source-backed cycle-start-read/cycle-end-write rule [ADI-UM-1989, printed pp.
1-5–1-7, 2-6–2-7, and 5-5–5-8].

The same implementation-only validity boundary captures canonical Type 14,
Type 15, and Type 16 decode plus exact shifter input dependencies. It commits
SR0/SR1, SE, SB, SS, and the independent Type 14 DREG move sidecars with the
already established state-7 architectural retirement. A condition-false Type
16 preserves all validity; an unknown predicate invalidates only destinations
that the instruction could write. EXP LO therefore preserves a destination
when known old SE is not `0xf1`, and treats the destination as a possible write
when old SE is `0xf1` or unknown. This is reset-unknown accounting derived from
the source-backed action, not a new device timing claim
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18–2-35, 4-25, 6-1–6-11, A-3, and
A-6–A-7].

The same boundary captures the canonical Type 23 DIVQ, source-closed Type 24
DIVS, and exact Type 25 saturation dependencies at issue. Type 23 and Type 24
atomically mark AF, AY0, and AQ valid only when every selected cycle-start
operand is valid. Type 25 known-false preserves MR validity, known-true derives
all three MR segments from the MR2 sign validity, and unknown MV conservatively
invalidates all three possible write destinations. These sidecars retire with
the documented state updates and do not alter instruction timing
[ADI-UM-1989, printed pp. 2-9–2-19, 4-21, 6-9 Table 6.3, A-4, and B-1–B-8].

The Type 13/HALT wrapper adds the late-recognition path without changing the
ordinary hit/miss contract. It withholds the issue-time cached word when HALT
arrives at state 3, records recovery in the already-pending descriptor, and
hands the native PM bus to exactly one recovery fetch after data completion.
The recovery fills the monitor and provides the stopped instruction word; no
shifter, PM transfer, PX, or DAG write is replayed. Halted state 8 retains the
driven PM levels, and release requires HALT inactive with DMACK high. The
Type 5/HALT wrapper applies the same late-hit conversion and one-time commit
rule to ALU/MAC-plus-PM. Idle ordinary-fetch HALT, BG/DM waits, TRAP,
interrupt-entry handoff, reset release, and multi-owner priority remain outside these
PM-data owners.
