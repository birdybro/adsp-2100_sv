# Wait states

**Status: original DMACK behavior identified**

The original device documents asynchronous wait extension only on the DM
interface through DMACK [ADI-UM-1989, printed pp. 5-9–5-11, Figure 5.7].
This differs from later devices' programmed wait-state controls and must not be
replaced by a generic per-space counter.

The bounded Type 2 and Type 12 execution slices automate the logical rule:
each DMACK-low sample retains select, direction, valid address/write data, and
architectural state, while the first high sample completes the transaction and
permits selected-I post-modification. Their 50,035- and 50,069-clock
model/RTL differentials do not claim asynchronous setup/hold or native pin
substate accuracy.

Pending questions are DMACK setup/hold from the original AC table, reset/HALT
release requirements, and Hard Drivin' PAL connectivity. The Atari schematic
shows the CPU DMACK net and a 10 kΩ pull-up
[ATARI-ADSP-SCHEM, drawing A044421, sheet 3 left, PDF p. 6], but every load and
PAL driver has not yet been traced.
