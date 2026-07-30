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

Original PM has no DMACK-equivalent documented in this interface. Exact
state-by-state address/strobe/data assertions will be transcribed from Figure
5.5 and the data-sheet AC table before RTL.
