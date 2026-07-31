# Data-memory cycles

**Status: logical ordering and wait sample verified**

DM read/write drives DMA and DMS, selects DMRD or DMWR, and transfers DMD.
DMS can remain asserted without a glitch across consecutive DM cycles
[ADI-UM-1989, printed pp. 5-9–5-12].

DMACK is checked at the end of state 6. If absent, state 7 extends by one full
processor cycle repeatedly. HALT, BR, and interrupts may latch but are not
serviced during this extension [ADI-UM-1989, printed p. 5-9].

Automated bus traces must check address/control/write-data stability throughout
every extension and completion at the first accepted DMACK sample.

The Type 12 execution boundary now automates that logical check. A request can
complete on its issue clock when DMACK is asserted or enter a pending state.
Pending state freezes the transaction descriptor and does not repeat shifter
or DAG execution. DM read data is sampled only on the completing clock; DM
write data is the old selected-bank DREG value. Reset cancels a pending
transaction and invalidates reset-unknown computational and DAG state. The
50,069-cycle differential includes arbitrary multi-clock extension and checks
atomic completion. PM concurrency, event latching during waits, and active-low
pin-level state timing are still unimplemented.
