# Data-memory cycles

**Status: source-backed eight-substate logical pin phases implemented;
Type 2, Type 3, Type 4, and Type 12 attached as bounded clients**

DM read/write drives DMA and DMS, selects DMRD or DMWR, and transfers DMD.
DMS can remain asserted without a glitch across consecutive DM cycles
[ADI-UM-1989, printed pp. 5-9–5-12].

DMACK is checked at the end of state 6. If absent, state 7 extends by one full
processor cycle repeatedly. HALT, BR, and interrupts may latch but are not
serviced during this extension [ADI-UM-1989, printed p. 5-9].

Type 1 now has a bounded logical execution slice that holds its simultaneous
DAG1 DM and DAG2 PM read descriptors, computation, and all architectural
destinations until one implementation/test completion signal. Its 51,069-
clock comparison establishes atomic logical completion, including 27,309 held
clocks, but deliberately does not interpret that signal as DMACK. The source
does not state whether Type 1 PM address/strobe/data holds, repeats, or
completes internally while DMACK extends state seven; native attachment
therefore remains OQ-023 [ADI-UM-1989, printed pp. 5-5–5-12, 6-3–6-5, A-1].

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

The bounded shared-DM owner composes two descriptor sources with exactly one
instance of that native controller. It rejects simultaneous state-8 requests
without claiming a priority, retains the accepted owner across every repeated
eight-substate wait cycle, and one-hot routes the state-6 DMACK sample/result
and state-7 completion/read sample. Nine directed/model checks and 50,010
model/RTL clocks include 494 rejected collisions, 814 low-DMACK extensions,
3,302 acknowledged completions, both owners, back-to-back changes,
relinquishment, reset, and unknown fields. The retained fetched client now
uses this owner with one atomic state-8 preflight: a simultaneous generated and
structural descriptor inhibits the PM fetch, is rejected by the DM owner, and
leaves the instruction retained for a later retry. This closes partial issue
for this bounded composition without assigning either requester a priority
[ADI-UM-1989, printed pp. 1-5–1-7, 5-9–5-12;
ADI-DATABOOK-1987, printed pp. 2-36–2-43].

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
commit, reset, late-ACK and off-boundary rejection, and relinquishment. The
separate normal BR/BG controller now supplies sourced recognition, grant,
release, and restart timing. The ordinary-fetch/native-DM owner below composes
it with all four fetched clients: BR remains recognizable at physical state 3
during a wait, protocol service is deferred through incomplete DM, and native
grant masks every PM/DM output enable. Separate one-client wrappers remain
independent evidence. The larger real-client owner also composes these four
fetched DM classes with ordinary fetch and real Type 5/Type 13 PM-data clients
behind one controller per bus; nine paired completions and one full wait pass
in its 45-test/51,587-clock comparison. Those nine completions include directed
Type 3 returned-DMD validity and independent Type 4 compute/DM-read and Type 12
shift/DM-read validity cases. Additional architectural DM admission,
Type 1 concurrency under OQ-023, HALT during BG, and sourced cross-event
priority remain unimplemented. Ordinary HALT during a fetched DM wait is
attached below.

The bounded Type 3 native wrapper accepts an absolute-address descriptor and
cycle-start general-register write source at state 8-to-1. Its five directed
tests and 50,077 connected clocks verify both directions, stable address/data
through complete-cycle extension, state-7 read sampling and register commit,
late-ACK/off-boundary rejection, reset, and relinquishment. OQ-016 remains
visible for narrow status/control write sources rather than silently defining
their upper DMD bits.

The ordinary-fetch/native-DM wait composition now derives descriptors from
every legal fetched Type 3 word and every source-closed Type 4 or Type 12 word.
Twenty-two tests and 50,000 model/RTL clocks cover 2,612 DM accepts, 2,611
completions, 111 wait extensions/state-7 samples, 1,169 reads, 1,443 writes,
and 889 architectural holds. Generated ownership contributes 73 Type 2
accepts/72 completions, 149 Type 3, 2,057 Type 4, and 119 Type 12 transfers;
all legal Type 3 register
selectors; all 2,048 Type 4 compute tuples; all 112 sourced Type 12 shifter
tuples; all applicable DAG/I/M and DREG selectors; both directions; old-value
store overlap/readback; alternate-bank operation; memory-only Type 4; DAG1 bit
reversal; circular wrap; and complete-cycle waits. Qualified state-7 completion
commits the applicable load, compute/shifter/status, selected-I, PC, and
returned-word effects together; stores use state-8 captured data. The fetched
vectors initialize Type 3/4/12 sources and supply valid DMD, so reset-unknown
and invalid-DMD propagation remain qualified by the standalone slices for that
50,000-clock owner. The larger combined owner adds the invalid Type 3 DMD and
independent Type 4 compute/read and Type 12 shift/read validity cases described
above.
Twelve BR recognitions include one first sampled during a wait; three paired
completions precede pending grant service, 12 grants mask every PM/DM output
enable for 18,638 clocks, and 10 release/reacquire/resume handshakes complete.
One generated/raw collision is rejected before PM or DM acceptance and the
retained instruction later retries successfully. Additional architectural DM
requesters, HALT during BG, and sourced event priority remain open. Ordinary
HALT is recognized during one real Type 2 wait, defers stop until the paired
completion and retirement, holds driven state 8, blocks release while DMACK is
low, and resumes at state 8-to-1. Same-boundary and cross-owner BR/HALT
requests fail closed while preserving an already active owner.
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 4-22, 5-9–5-16, 6-3–6-7,
6-12–6-13, A-5, A-7, and A-9].
