# Program sequencer

**Status: source-backed next-PC, CNTR, and stack-storage blocks;
connectivity/timing incomplete**

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

This storage block accepts already-resolved push/pop requests; it does not
claim that arbitrary same-stack push/pop collisions are architectural. Such a
collision suppresses all storage changes and raises `write_conflict_o` as a
fail-closed integration safeguard. Opcode decode, connection of flow,
DO UNTIL, counter-load, interrupt, return, and manual-pop requests to the
stacks, CNTR-to-count-stack/condition connectivity, status-stack connectivity,
cache/fetch overlap, phase enables, reset integration, empty-pop
architectural effects, and bus-cycle timing remain unimplemented. The
discovered MAME ordering difference is recorded as SC-012.
