# Interrupt architecture

**Status: original-device behavior baseline; status-entry transition and
bounded RTI execution implemented**

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

The independent model and status/control RTL implement the exact-width
ASTAT/MSTAT/IMASK pre-entry snapshot, suppression of the aborted instruction's
ordinary status writes, and RTI-style status restoration. With nesting
disabled, entry clears IMASK. With nesting enabled, entry at IRQ0, IRQ1, IRQ2,
or IRQ3 masks that level and every lower-priority level, producing IMASK
`0xE`, `0xC`, `0x8`, or `0x0` [ADI-UM-1989, printed pp. 4-9–4-10, 4-23–4-24].
The block accepts an already-recognized interrupt level; request sampling,
priority arbitration, PC-stack entry connectivity, and vector timing remain
sequencer work.

The original status stack is four entries by 16 bits and can therefore retain
all four possible nested interrupt contexts [ADI-DATABOOK-1987, printed
pp. 2-21–2-22, Figure 6]. Its independent model and portable RTL now implement
the storage and fault-status boundary. The bounded Type 20 return slice now
wires a condition-true RTI to simultaneous valid PC/status pops and cycle-end
ASTAT/MSTAT/IMASK restoration. It verifies the return half of the context
path, including condition-false preservation and OQ-013 fail-closed missing
context, across 50,254 model/RTL cycles. It does not yet connect the entry
recognizer, priority logic, vectors, active-loop arbitration, or fetch phases
[ADI-UM-1989, printed pp. 4-3–4-4, 4-9–4-10, 6-14 Table 6.8].

Requests latch but are not serviced during HALT, TRAP, bus grant, DMACK waits,
or between the two cycles of an uncached PM-data access
[ADI-UM-1989, printed p. 5-16].
