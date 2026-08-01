# Program-memory cycles

**Status: logical ordering baseline**

For a PM read, the processor drives PMA and PMDA, asserts PMS, then asserts
active-low PMRD; memory supplies PMD; the processor samples data and releases
PMRD [ADI-UM-1989, printed p. 5-7, Figure 5.5 p. 5-8].

For a PM write, the processor drives PMA/PMDA, asserts PMS, drives PMD, asserts
PMWR, then releases PMWR after its fixed interval
[ADI-UM-1989, printed pp. 5-7–5-8]. PMS normally remains asserted across
successive program accesses and is inactive only during halt/trap/bus grant
[ADI-UM-1989, printed p. 5-6].

Original PM has no DMACK-equivalent documented in this interface. The bounded
Type 13 slice therefore completes a PM-data transfer in one fixed logical
processor cycle. It exposes PM select, data-versus-instruction classification,
read/write direction, 14-bit address, and 24-bit write data. The composed cache
boundary derives the next-instruction decision from its pre-cycle 16-word
monitor: a valid hit supplies the actual cached word with no external fetch;
a miss schedules one fixed instruction-read recovery cycle and uses that
cycle's returned word to fill the monitor. Ordinary external instruction
completions populate the same monitor when Type 13 does not own PM
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8]. Exact state-by-state PMS/PMDA/
PMRD/PMWR pin assertions still require the Figure 5.5 phase transcriptions and
data-sheet AC table; this bounded logical-cycle RTL does not claim those
electrical substates.
