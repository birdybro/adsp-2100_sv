# Program sequencer

**Status: source-backed next-PC arbitration block; state/timing incomplete**

PC is a 14-bit register containing the currently executing address. Its
incrementer normally provides the next address [ADI-UM-1989, printed p. 4-3].
The 16-word PC stack receives PC+1 for CALL but current PC for interrupt entry
because the fetched instruction is aborted and must be retried
[ADI-UM-1989, printed pp. 4-3–4-4, 4-9].

CNTR is a 14-bit unsigned down counter. The count stack is four words. Loading a
valid new count pushes the old count, while a reset-invalid count does not waste
a stack entry [ADI-UM-1989, printed pp. 4-4–4-5].

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

The regression checks 636,512 model-versus-RTL vectors, including every PC
value for sequential wrap, CALL return-address generation, loop back/exit, and
all taken explicit-transfer kinds at loop end. This closes a combinational
arbitration rule only. A separate four-entry status-stack block now covers
status context LIFO storage and its fault flags. Opcode decode, actual
PC/loop/count stack storage, status-stack connectivity, DO UNTIL setup, counter
decrement, interrupts, cache/fetch overlap, phase enables, reset integration,
remaining stack faults, and bus-cycle timing remain unimplemented. The
discovered MAME ordering difference is recorded as SC-012.
