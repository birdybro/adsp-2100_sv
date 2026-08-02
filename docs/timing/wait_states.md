# Wait states

**Status: original logical DMACK substate extension implemented**

The original device documents asynchronous wait extension only on the DM
interface through DMACK [ADI-UM-1989, printed pp. 5-9–5-11, Figure 5.7].
This differs from later devices' programmed wait-state controls and must not be
replaced by a generic per-space counter.

The native DM controller samples DMACK only on the enabled 6-to-7 edge. A low
sample retains the descriptor and all active strobes while the eight physical
substates repeat under architectural state seven; a later high 6-to-7 sample
permits completion and read sampling on the following 7-to-8 edge. Nine
directed tests and 50,039 model/RTL clocks cover zero, one, and repeated
extensions, late ACK rejection, phase holds, stable output values, and reset.

A bounded structural composition now pairs an ordinary PM fetch with one raw
native-DM descriptor. During every DMACK-low extension it freezes the
architectural fetch/execute boundary but continues physical state-7 interrupt
sampling. A request first sampled there is retained without vector issue,
context push, retirement, or PM completion and is serviced only after the PM
and DM transactions complete together. Four directed/model tests and 50,000
model/RTL clocks cover 1,356 admitted companion transactions, 446 extensions,
446 wait-time interrupt samples, and one edge-mode IRQ2 retained through the
wait. This establishes the cycle-control rule, not fetched DM instruction
semantics or whole-core PM/DM arbitration [ADI-UM-1989, printed pp. 5-9–5-11
and 5-15–5-16].

The bounded Type 2, Type 3, Type 4, and Type 12 execution slices separately
automate the architectural rule:
each DMACK-low sample retains select, direction, valid address/write data, and
architectural state, while the first high sample completes the transaction and
permits selected-I post-modification. Their 50,035-, 50,151-, 50,072-, and
50,069-clock model/RTL differentials establish the architectural hold/commit rule but do
not alone claim asynchronous setup/hold or native pin substate accuracy.

Type 2, Type 3, Type 4, and Type 12 are now connected to the native controller
through separate bounded wrappers. Their 50,027-, 50,077-, 50,082-, and
50,064-clock attachment comparisons ensure
that a DMACK-low sample causes a complete physical-substate repeat while the
instruction remains pending. The selected I register, Type 3 general-register
destination, Type 12 shifter result, Type 4 compute/status result, and optional
read destinations cannot change until the later qualified 7-to-8 completion.

The original AC table specifies DMACK setup to CLKIN high at 6-to-7 and hold
after that edge; those nanosecond requirements are documented but not modeled
as synthesizable delays [ADI-DATABOOK-1987, printed pp. 2-40 and 2-42,
parameters 72–75]. Pending questions are the FPGA pin-wrapper synchronizer,
reset/HALT release interactions, and Hard Drivin' PAL connectivity. The Atari
schematic
shows the CPU DMACK net and a 10 kΩ pull-up
[ATARI-ADSP-SCHEM, drawing A044421, sheet 3 left, PDF p. 6], but every load and
PAL driver has not yet been traced.
