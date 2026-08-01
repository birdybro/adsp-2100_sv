# Pipeline and cache

**Status: one-stage pipeline and bounded PM-data hit/miss timing implemented;
full cache monitor and hazards pending**

An instruction fetched in one processor cycle executes in the next while the
following instruction is fetched [ADI-UM-1989, printed p. 1-5]. Computation
inputs are read at cycle start and writes/status latch at cycle end
[ADI-UM-1989, printed pp. 2-6, 4-21].

PM data use conflicts with external instruction fetch. The 16×24 cache can
supply a valid next instruction; otherwise an additional external fetch cycle
occurs [ADI-UM-1989, printed pp. 1-7, 4-26–4-28]. Cache fills transparently with
executed external instructions.

Interrupt entry aborts an already fetched instruction and later refetches it
[ADI-UM-1989, printed pp. 4-9–4-10, Figure 5.11 p. 5-16]. HALT during PM data
also forces an instruction fetch before stopping [ADI-UM-1989, printed
pp. 5-13–5-14].

Cache tag/monitor algorithm, self-modifying PM behavior, branches at cache
boundaries, and precise miss traces are highest-priority timing tests.

The bounded Type 13 model/RTL makes the sourced two outcomes explicit. With a
caller-validated next cache entry, the PM-data instruction completes in its
single data cycle. Without one, that cycle commits the shifter, PM/PX, and
DAG2 effects and records one recovery fetch address; the next cycle performs
only the external instruction fetch and then exposes the event-recognition
boundary. A forced-fetch input models the documented HALT handoff. Fifty
thousand seventy model/RTL clocks confirm that no architectural data action
repeats in recovery [ADI-UM-1989, printed pp. 4-26–4-30, 5-13–5-16]. This is
not yet the 16-entry tag/monitor/fill implementation, which remains OQ-008.
