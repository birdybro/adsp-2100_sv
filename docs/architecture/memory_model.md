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

The bounded Type 12 boundary is the first executable DM transaction path. It
drives the old selected I (or the DAG1 bit-reversal of that value), direction,
select, and old write-source data. A missing DMACK holds all valid bus outputs
and all architectural destinations. The first acknowledged boundary samples
read data and atomically commits the optional DREG load, shifter action, and
selected-I post-modification [ADI-UM-1989, printed pp. 5-9–5-12,
6-3–6-7]. It does not yet include PM fetch concurrency, BR/BG ownership,
interrupt/HALT latching, or a physical state-1-through-state-8 pin wrapper.
