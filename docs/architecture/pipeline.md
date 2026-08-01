# Pipeline and cache

**Status: one-stage pipeline and bounded cache-integrated PM-data hit/miss
timing implemented; unified hazards pending**

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

The standalone functional monitor implements the documented 16-by-24 array,
PMA[3:0] indexing, one contiguous valid region, out-of-region invalidation,
and oldest-word circular replacement. It passes 50,028 deterministic model/
RTL clocks. The manual describes hidden ahead/behind registers but does not
expose their exact encoding, so this is the externally visible region contract,
not a gate-level reconstruction [ADI-UM-1989, printed pp. 4-26–4-28].
Self-modifying PM behavior and unified branch/loop/interrupt/HALT/BR arbitration
remain OQ-008.

The bounded Type 13 model/RTL makes the sourced two outcomes explicit. Its
composed cache boundary looks up the next fetch address in the pre-cycle
monitor. A valid entry supplies the actual 24-bit next instruction and the PM
data instruction completes in its single data cycle. Without one, that cycle
commits the shifter, PM/PX, and DAG2 effects and records one recovery fetch
address; the next cycle performs only the external instruction fetch, fills
the monitor, supplies that instruction, and exposes the event-recognition
boundary. A forced-fetch input models the documented HALT handoff and refreshes
the cache even on a prior hit. The base Type 13 and integrated boundaries pass
50,070 and 50,086 model/RTL clocks respectively [ADI-UM-1989, printed
pp. 4-26–4-30, 5-13–5-16]. Ordinary external fetch completion is an explicit
fill input when Type 13 does not own PM. Unified PC/branch/loop/interrupt/HALT/
BR ownership, self-modifying PM effects, and native pin phases remain OQ-008.
