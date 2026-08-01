# Data-memory cycles

**Status: source-backed eight-substate logical pin phases implemented;
Type 2, Type 3, Type 4, and Type 12 attached as bounded clients**

DM read/write drives DMA and DMS, selects DMRD or DMWR, and transfers DMD.
DMS can remain asserted without a glitch across consecutive DM cycles
[ADI-UM-1989, printed pp. 5-9–5-12].

DMACK is checked at the end of state 6. If absent, state 7 extends by one full
processor cycle repeatedly. HALT, BR, and interrupts may latch but are not
serviced during this extension [ADI-UM-1989, printed p. 5-9].

The portable `adsp2100_data_bus` controller now captures a request on the
enabled state-8-to-state-1 edge aligned with the sourced DMA/DMS transition.
It implements this logical pin map:

| Signal/action | Logical substates or edge |
|---|---|
| DMA and active-low DMS valid | states 1–8 and every wait substate |
| DMRD/DMWR low | states 4–7 and every wait substate |
| DMACK recognition | enabled state-6-to-state-7 edge |
| DMD read sample | completing state-7-to-state-8 edge |
| DMD write output enable | states 5–8 and every wait substate |

A low DMACK sample retains architectural state seven while the physical
substate counter traverses 8, 1, 2, 3, 4, 5, 6, and 7 again. Each low sample
therefore adds one complete eight-substate processor cycle; a high sample
qualifies completion only at the following 7-to-8 edge. This follows the
original timing figure's `7(8)` through `7(6)` notation rather than treating a
wait as one FPGA clock [ADI-UM-1989, printed pp. 5-9–5-11, Figures 5.6–5.7;
ADI-DATABOOK-1987, printed pp. 2-40–2-43, parameters 61–98, Figures 16–17].

Nine directed tests and 50,039 deterministic model/RTL clocks check address,
select, strobe, and write-data stability throughout every extension; rejection
of a late unsampled ACK; completion on the first qualified edge; consecutive
DMS continuity; phase holds; reset; unknown validity; and externally directed
bus relinquishment. The electrical DMACK setup/hold values remain wrapper
constraints rather than delay constructs in synthesizable RTL.

The Type 2 immediate-write, Type 3 direct-transfer, Type 4 ALU/MAC
multifunction, and Type 12 shifter multifunction execution boundaries now
automate that logical check. A request can
complete on its issue clock when DMACK is asserted or enter a pending state.
Pending state freezes the transaction descriptor and does not repeat shifter
or DAG execution. DM read data is sampled only on the completing clock; DM
write data is either Type 2's captured raw immediate or Type 4/Type 12's old
selected-bank DREG value. Reset cancels a pending transaction and invalidates
reset-unknown computational and DAG state. The Type 2, Type 3, Type 4, and Type
12 logical differentials cover 50,035, 50,151, 50,072, and 50,069 clocks
respectively,
including arbitrary multi-clock extension, stable address/data, and
completion-only architectural writes.
The bounded Type 2 native wrapper now accepts the captured old-I/raw-immediate
descriptor only at state 8-to-1, retains it across complete-cycle extensions,
and returns completion to the architectural slice only at the qualified
state-7-to-state-8 edge. Its five directed tests and 50,027 connected
model/RTL clocks verify that selected-I postmodify cannot occur on the state-6
ACK sample or on a late unsampled ACK. The bounded Type 12 native wrapper uses
the same issue/completion boundary for reads and writes. Six directed tests and
50,064 connected clocks verify old-DREG write data, state-7 DMD read sampling,
atomic shifter/DREG/I commit, full-cycle wait stability, invalid-data
propagation, reset, and bus relinquishment. The bounded Type 4 native wrapper
adds the same physical boundary for memory-only and
ALU/MAC reads/writes. Six directed tests and 50,082 clocks verify state-8
issue, old-value stores, full-cycle waits, state-7 atomic compute/read/I
commit, reset, late-ACK and off-boundary rejection, and relinquishment. PM
concurrency, multi-owner DM arbitration, event latching
during waits, and BR/BG recognition are still unimplemented.

The bounded Type 3 native wrapper accepts an absolute-address descriptor and
cycle-start general-register write source at state 8-to-1. Its five directed
tests and 50,077 connected clocks verify both directions, stable address/data
through complete-cycle extension, state-7 read sampling and register commit,
late-ACK/off-boundary rejection, reset, and relinquishment. OQ-016 remains
visible for narrow status/control write sources rather than silently defining
their upper DMD bits.
