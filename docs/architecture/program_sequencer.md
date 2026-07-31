# Program sequencer

**Status: source-backed next-PC, CNTR, stack storage, and bounded Type
10/11/19/20 and phase-aware Type 22 PC-state integration; whole-core timing
incomplete**

PC is a 14-bit register containing the currently executing address. Its
incrementer normally provides the next address [ADI-UM-1989, printed p. 4-3].
The 16-word PC stack receives PC+1 for CALL but current PC for interrupt entry
because the fetched instruction is aborted and must be retried
[ADI-UM-1989, printed pp. 4-3–4-4, 4-9].

CNTR is a 14-bit unsigned down counter. The count stack is four words. Loading a
valid new count pushes the old count, while a reset-invalid count does not waste
a stack entry [ADI-UM-1989, printed pp. 4-4–4-5].

CE observes the cycle-start count and is true at `CNTR=1`; the count update
occurs at cycle end. A false CE test post-decrements the 14-bit counter. A true
test pops and restores the dormant outer count, or invalidates CNTR when the
count stack is empty. The decrementing contexts explicitly identified by the
manual are a `DO UNTIL CE` loop end and a conditional jump. Conditional return,
trap, and arithmetic tests do not decrement; conditional CALL remains OQ-012
[ADI-UM-1989, printed pp. 4-4–4-5].

The loop stack is four entries of 14-bit end address plus 4-bit termination
condition. DO UNTIL simultaneously pushes the loop information and first-loop
address on the PC stack [ADI-UM-1989, printed pp. 4-5–4-6]. A true explicit
jump/call/return at loop end takes precedence and suppresses implicit loop
sequencing/pops [ADI-UM-1989, printed p. 4-7].

The independent instruction-boundary model and portable combinational flow
block now select among sequential PC+1, taken jump/call/return, loop back, and
loop exit. A taken CALL requests a PC-stack push of 14-bit PC+1; a taken return
requests its explicit PC pop. At a loop end, a taken explicit control transfer
suppresses loop-stack/count-stack actions and counter testing. If its condition
is false, ordinary loop termination processing remains eligible
[ADI-UM-1989, printed pp. 4-3–4-7, 4-12–4-19].

The flow regression checks 636,512 model-versus-RTL vectors, including every
PC value for sequential wrap, CALL return-address generation, loop back/exit,
and all taken explicit-transfer kinds at loop end. A separate independent
model and `rtl/core/adsp2100_sequencer_stacks.sv` implement the 16-by-14 PC,
four-by-14 count, and four-by-18 loop stack storage. Their pointers saturate,
the newest overflowing push is discarded, overflow is sticky until reset, and
their empty/overflow sources occupy SSTAT bits 0–3 and 6–7
[ADI-UM-1989, printed pp. 4-3–4-7, 4-22]. A deterministic 50,062-cycle
model-versus-RTL regression covers exact depths, LIFO order, overflow,
independent simultaneous actions, reset, and empty-pop invalidation.

The independent CNTR model and `rtl/core/adsp2100_counter.sv` implement the
separate valid bit, cycle-start CE/NOT CE outputs, cycle-end post-decrement,
load-time push requests, true-CE pop/restore or empty invalidation, and valid
manual-pop restore. Twelve directed/model tests and a deterministic
50,022-cycle model-versus-RTL regression pass. The condition output has an
explicit valid qualifier so reset-invalid or post-empty CNTR state is not
silently interpreted as a predicate. An empty manual pop is flagged and
preserves state only as a fail-closed OQ-013 boundary, not as a device claim.

The bounded independent integration model and
`rtl/core/adsp2100_sequencer_slice.sv` now connect the condition evaluators,
flow selector, CNTR, and all three sequencer stacks. It pushes PC+1 and the
loop descriptor for DO UNTIL, evaluates the stored DO condition at loop end,
couples CE decrement/restore to count-stack storage, derives RETURN targets
from the PC-stack top, and preserves the documented taken explicit-transfer
precedence. Fifteen directed/random integration tests and 50,014
model-versus-RTL stateful cycles pass, including exact-N and nested CE loops,
conditional JUMP CE updates, and non-decrementing RETURN CE checks.

The slice is not an instruction decoder or complete program sequencer. It
fails closed for conditional CALL CE (OQ-012), missing required stack/CNTR
context, DO UNTIL setup on an active outer loop's end instruction, and
competing automatic/manual actions (OQ-018). Empty manual pop remains OQ-013.
The internal loop descriptor packs condition in bits 17:14 and end address in
bits 13:0 solely as an implementation interface; no externally readable
register layout is claimed. That generic integration slice has no PC register
or opcode input. Interrupt and status-stack connectivity, cache/fetch overlap,
phase enables, complete reset integration, and bus-cycle timing remain
unimplemented. The discovered MAME ordering difference is recorded as SC-012.

A separate bounded Type 26 execution slice now connects all original manual
stack-control fields to the status/count/loop/PC stacks, live CNTR, and
ASTAT/MSTAT/IMASK. It reads every source from cycle-start state, commits the
selected actions together at cycle end, composes all eight SSTAT stack bits,
and agrees with the independent model for 50,015 stateful cycles. Non-Type-26
words and simultaneous setup/automatic requests are action-free, the latter
flagged as OQ-018 integration conflicts. This slice is not yet arbitrated with
the automatic flow slice, interrupts, or RTI, and preserves the explicit
OQ-013 empty-pop boundary.

The bounded Type 10 direct-transfer slice is the first decoder-connected PC
register boundary. Its authentic reset path sets PC to `0x0004`, then every
accepted instruction commits exactly one of wrapped PC+1 or the 14-bit direct
target. Taken CALL also pushes cycle-start PC+1; false CALL does not push.
JUMP NOT CE connects to live CNTR/count-stack state and applies the sourced
test-before-post-decrement rule, including outer-count restoration. Exhaustive
decode classifies 507,904 supported words and 16,384 OQ-012 CALL NOT CE words;
554,412 deterministic model/RTL cycles cover every supported word plus reset,
stack overflow, counter restore, unknown predicates, and integration conflicts
[ADI-UM-1989, printed pp. 4-3–4-5, 4-12–4-13, 5-13, 6-13–6-14, A-2,
A-6]. The slice intentionally has no active-loop descriptor, fetch/cache,
interrupt, wait-state, bus, or eight-state phase input, so it is not a complete
program sequencer.

The bounded Type 11 slice connects exact DO decode to PC, PC-stack,
loop-stack, and CNTR-valid state. Every accepted word samples cycle-start PC,
then simultaneously commits PC+1 to PC and the PC stack and `{TERM,ADDR}` to
the loop stack. It accepts distinct-end nesting, rejects the original
same-terminal prohibition atomically, validates active outer CE context, and
holds DO-on-outer-terminal under OQ-018. Exhaustive RTL classification covers
the full 24-bit opcode space, and 554,309 model/RTL cycles execute every one
of the 262,144 Type 11 words plus directed invalid, nesting, and overflow
boundaries [ADI-UM-1989, printed pp. 4-5–4-8, 4-16–4-19, 6-13–6-14,
A-2, A-10]. Loop-end evaluation remains in the separate generic sequencer
slice; fetch, interrupt, wait, and bus phases are not yet unified.

The bounded Type 19 slice adds the original register-indirect path. Exact
decode selects I4 through I7 and preserves Type 19 bit 5 as fixed zero. A
taken transfer reads the selected cycle-start DAG2 I value, exposes a PMA
indirect-drive event, and loads PC from that value without post-modifying I;
a false transfer advances to PC+1 and does not require valid I state. Taken
CALL and JUMP NOT CE use the same independently verified PC-stack and CNTR/
count-stack boundaries as Type 10. The 128-word class partitions into 124
bounded actions and four OQ-012 CALL NOT CE words. Exhaustive 24-bit decode,
two hand-derived fixtures, twelve directed model tests, and 50,259 model/RTL
cycles pass [ADI-UM-1989, printed pp. 3-1–3-2, 4-3–4-4, 4-20, 6-13–6-14,
A-3, A-6]. The PMA observation proves next-address intent only; fetch strobes,
cache behavior, wait extension, active-loop arbitration, interrupts, and
eight-state pin timing remain unconnected.

The bounded Type 20 slice closes the original conditional-return format. It
samples COND, the PC-stack top, and, for RTI, the status-stack top at cycle
start. A false condition commits PC+1 and no stack action. A true RTS pops PC;
a true RTI atomically pops PC and status and restores ASTAT/MSTAT/IMASK. Return
`NOT CE` reads CNTR only as a predicate and requests no test, decrement, count
pop, or restore. Missing condition state or required taken-return context is
action-free and explicitly reported; this applies the OQ-013 fail-closed
boundary without claiming real empty-pop behavior. Exhaustive 24-bit decode,
two hand-derived fixtures, twelve model tests, and 50,254 model/RTL cycles pass
[ADI-UM-1989, printed pp. 4-3–4-4, 4-7, 4-9–4-10, 6-14 Table 6.8,
A-4, A-6]. Active-loop precedence is already proved in the generic sequencer
flow block but is not yet physically unified with this decoder-connected
slice. Interrupt entry/vectoring, fetch, waits, and bus phases remain open.

The bounded Type 22 slice closes all sixteen conditional TRAP words and, unlike
the instruction-boundary-only slices, retains an accepted condition decision
through explicit logical phases. False and true forms both commit PC+1 at the
enabled state-7/state-8 boundary. A true form simultaneously asserts TRAP and
requests a state-8 phase hold; an already-recognized HALT clears TRAP but keeps
the processor stopped, and releasing HALT produces a resume event without
changing PC. Conditional TRAP `NOT CE` observes CNTR without decrementing it.
Twelve model tests, exhaustive 24-bit decode, two hand-derived fixtures, and
50,168 model/RTL clocks pass [ADI-UM-1989, printed pp. 4-3–4-4, 4-25,
5-14–5-15, Figure 5.10, 6-14, A-4, and A-6]. General HALT recognition,
active-loop and interrupt arbitration, BR/BG, complete fetch strobes, and bus
ownership remain separate incomplete boundaries. SC-013 records MAME's
incorrect reserved classification for these original-device words.
