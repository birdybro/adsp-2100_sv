# Architectural memory model

**Status: original-device baseline**

Program words are 24 bits; data words are 16 bits. PMA and DMA are each 14 bits
[ADI-UM-1989, printed pp. 1-5–1-6]. PM can contain instructions or data.
PMDA distinguishes data access and can act as a fifteenth address bit, creating
separate 16K code and 16K data regions when used that way
[ADI-UM-1989, printed pp. 5-6–5-7].

PM data read/write bridges through the PMD-DMD exchange. The upper 16 PM bits
transfer directly and PX carries the low eight bits; PM data reads automatically
load PX and PM writes append PX [ADI-UM-1989, printed pp. 3-6–3-8].

The architectural model exposes separate PM instruction fetch, PM data read,
PM data write, DM read, and DM write transactions. It does not embed RAM into
the CPU. Uninitialized memory is a model input, not silently zero.

The bounded Type 2 immediate-write path drives the old selected I (or DAG1
bit reversal), raw 16-bit immediate, and write direction. It holds those
signals over every DMACK-low extension and commits only the selected-I
post-modification at the first acknowledged boundary. The 50,035-clock
model/RTL differential covers every I/M selection, both DAGs, immediate and
multi-clock completion, reset cancellation, and invalid/unknown DAG state
[ADI-UM-1989, printed pp. 3-1–3-5, 5-9–5-12, 6-1, 6-12, A-1, and A-6].

The bounded Type 12 boundary adds the multifunction DM transaction path. It
drives the old selected I (or the DAG1 bit-reversal of that value), direction,
select, and old write-source data. A missing DMACK holds all valid bus outputs
and all architectural destinations. The first acknowledged boundary samples
read data and atomically commits the optional DREG load, shifter action, and
selected-I post-modification [ADI-UM-1989, printed pp. 5-9–5-12,
6-3–6-7]. It does not yet include PM fetch concurrency, BR/BG ownership,
interrupt/HALT latching, or a physical state-1-through-state-8 pin wrapper.

The bounded Type 13 boundary implements the corresponding PM-data path with
fixed original-device timing. It exposes the old DAG2 I address, PM data
direction, and the old `{DREG,PX}` 24-bit write word. A read atomically loads
the upper 16 bits into the selected DREG and the low eight bits into PX while
the shifter and selected-I post-modify commit. There is no invented PM
acknowledge input [ADI-UM-1989, printed pp. 3-6–3-7, 5-5–5-8,
6-3–6-7]. A cache hit completes in that cycle; a miss adds one instruction
fetch cycle without repeating the data action [ADI-UM-1989, printed
pp. 4-26–4-30]. The bounded slice receives cache validity and the next fetch
address from its caller. A separate source-bounded cache monitor now supplies
the documented contiguous-region hit/data decision and external-fetch fill
behavior, but it is not yet connected to Type 13 or whole-core PM ownership;
that integration remains OQ-008.
