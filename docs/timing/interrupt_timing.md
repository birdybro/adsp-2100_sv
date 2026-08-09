# Interrupt timing

**Status: recognition verified; private-owner entry sequence bounded; retained
requests composed with ordinary HALT, normal BR/BG, native DMACK waits, and
both real uncached PM-data owners**

IRQ inputs are recognized at state 7. Edge mode compares consecutive state-7
samples; an asynchronous request must be active longer than one processor cycle
to guarantee recognition [ADI-UM-1989, printed pp. 5-15–5-16].

The fetched instruction following the executing instruction is ignored during
entry; a NOP occupies the vectoring cycle while the vector instruction is
fetched [ADI-UM-1989, Figure 5.11 printed p. 5-16]. The program-control chapter
describes two cycles of overhead when the vector contains the usual jump
[ADI-UM-1989, printed pp. 4-9–4-10].

The bounded private owner exposes distinct recognition, vector request/entry,
and vector-fetch-completion events:

1. At the enabled state-7-to-state-8 boundary, the executing instruction and
   its concurrent next-word fetch complete. Recognition retires the executing
   instruction but marks the fetched word invalid.
2. At the following state-8-to-state-1 boundary, the vector request is issued,
   current PC/status context is pushed, and IMASK is transformed for nesting.
3. At that request's state-7-to-state-8 completion, the vector word becomes the
   current instruction. This completion is not an ordinary retirement event.
4. The vector instruction executes in the following cycle. A fetched RTI uses
   the saved PC as its fetch target and restores ASTAT/MSTAT/IMASK atomically.

These boundaries pass the 444,003-clock private-owner comparison. An IRQ2
sampled at state 7 while ordinary HALT or normal BR/BG is pending is now held
without entry through the stopped/granted interval and enters at the qualified
state-8-to-state-1 resume boundary. The ordinary-HALT, private-BR/BG, and
retained-fetch/shared-PM BR/BG comparisons pass 50,048, 50,054, and 50,054
clocks respectively. A separate fetched Type 2/3/4/12 native-DM composition
passes 21 checks and 50,000 clocks: physical state 7 continues to sample IRQ
during each full-cycle DMACK extension, while the architectural phase, fetch
retirement, and interrupt service remain held until paired PM/DM completion.
It also recognizes BR at physical state 3 during the wait, defers grant service
through completion, and conflict-reports unsourced BR/IRQ/TRAP service overlap.
Ordinary HALT is also recognized during one real Type 2 wait and defers its
stop until the same paired completion/retirement; simultaneous BR/HALT fails
closed rather than assigning priority.
The real Type 5 and Type 13
native/cache owners add 50,100 and 50,098 clocks: an edge sampled at uncached
PM-data completion is retained without recognition, and the immediately
following recovery-fetch completion releases recognition. This closes the
documented two-cycle no-service interval at those bounded owners, but not
PC/status entry handoff or simultaneous-event priority. Additional
architectural DM ownership, HALT during BG, and sourced cross-event priority
remain open. Input
synchronization, metastability, pulses with no state-7 sample, and analog
setup/hold are outside the logical model.
