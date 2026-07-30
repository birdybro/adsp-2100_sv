# Wait states

**Status: original DMACK behavior identified**

The original device documents asynchronous wait extension only on the DM
interface through DMACK [ADI-UM-1989, printed pp. 5-9–5-11, Figure 5.7].
This differs from later devices' programmed wait-state controls and must not be
replaced by a generic per-space counter.

Pending questions are DMACK setup/hold from the original AC table, reset/HALT
release requirements, and Hard Drivin' PAL connectivity. The Atari schematic
shows the CPU DMACK net and a 10 kΩ pull-up
[ATARI-ADSP-SCHEM, drawing A044421, sheet 3 left, PDF p. 6], but every load and
PAL driver has not yet been traced.
