# Interrupt timing

**Status: recognition boundary and entry outline verified**

IRQ inputs are recognized at state 7. Edge mode compares consecutive state-7
samples; an asynchronous request must be active longer than one processor cycle
to guarantee recognition [ADI-UM-1989, printed pp. 5-15–5-16].

The fetched instruction following the executing instruction is ignored during
entry; a NOP occupies the vectoring cycle while the vector instruction is
fetched [ADI-UM-1989, Figure 5.11 printed p. 5-16]. The program-control chapter
describes two cycles of overhead when the vector contains the usual jump
[ADI-UM-1989, printed pp. 4-9–4-10].

Tests must distinguish recognition, abort, vector fetch, vector instruction,
optional jump, first ISR instruction, and RTI refetch boundaries.
