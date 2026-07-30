# Interrupt architecture

**Status: original-device behavior baseline**

Four active-low inputs IRQ0–IRQ3 are individually masked and configured
edge/level by ICNTL; IRQ3 has highest priority and vectors are PM addresses
0x0000–0x0003 [ADI-UM-1989, printed pp. 4-8–4-9, 5-15–5-16].

Requests are sampled at state 7. Edge mode detects a high-to-low difference
between successive cycle samples and latches it; level mode must remain active
until serviced [ADI-UM-1989, printed pp. 4-8–4-9, 5-15].

Interrupt entry aborts the previously fetched instruction without updating data
registers, pushes current PC rather than PC+1, and pushes ASTAT/MSTAT/IMASK.
The manual describes two cycles of vectoring overhead, including the usual jump
stored at the vector [ADI-UM-1989, printed pp. 4-9–4-10]. RTI pops PC and status
together.

Requests latch but are not serviced during HALT, TRAP, bus grant, DMACK waits,
or between the two cycles of an uncached PM-data access
[ADI-UM-1989, printed p. 5-16].
