# Wait states

**Status: original logical DMACK substate extension implemented**

The original device documents asynchronous wait extension only on the DM
interface through DMACK [ADI-UM-1989, printed pp. 5-9–5-11, Figure 5.7].
This differs from later devices' programmed wait-state controls and must not be
replaced by a generic per-space counter.

The native DM controller samples DMACK only on the enabled 6-to-7 edge. A low
sample retains the descriptor and all active strobes while the eight physical
substates repeat under architectural state seven; a later high 6-to-7 sample
permits completion and read sampling on the following 7-to-8 edge. Nine
directed tests and 50,039 model/RTL clocks cover zero, one, and repeated
extensions, late ACK rejection, phase holds, stable output values, and reset.

The standalone shared-DM owner retains the accepted requester as well as the
native descriptor across these complete-cycle extensions. A repeated physical
state-8 boundary while waiting is not a new ready boundary and cannot clear or
replace that owner. DMACK sample/high/low and completion/read events route only
to the retained requester. Nine directed/model checks and 50,010 clocks cover
both requesters, 494 fail-closed collisions, 814 extensions, 3,302
completions, relinquishment, and owner changes. The fetched Type 2/3/4/12
composition now attaches through an atomic preflight. A simultaneous raw
companion request inhibits the overlapping PM fetch, causes both DM candidates
to fail closed, and leaves the fetched instruction available for a later
state-8 retry. This implementation invariant prevents partial issue without
inventing an architectural requester priority [ADI-UM-1989, printed pp.
1-5–1-7, 5-9–5-12].

A bounded composition pairs an ordinary PM fetch with one native-DM descriptor
and derives architectural ownership from fetched Type 2, legal Type 3,
source-closed Type 4, or source-closed Type 12 words. A lower-level raw descriptor remains structural
scaffolding. During every DMACK-low extension the composition freezes the
architectural fetch/execute boundary while continuing physical state-7
interrupt sampling. A request first sampled there is retained without vector
issue, context push, retirement, or PM completion and is serviced only after
the PM and DM transactions complete together.

The same composition now samples BR at each physical state-3 boundary during
an extension. Recognition remains live, but follow-up grant/withdrawal service
is inhibited until paired PM/DM completion; native grant then masks every PM
and DM output enable. BR overlap with interrupt/TRAP service is reported as an
integration conflict because no original-device source establishes priority.

Ordinary HALT recognition is likewise sampled at each repeated physical
state-3 boundary. A composition-only service inhibit defers the pending stop
while the DM owner is waiting. The first qualified paired PM/DM state-7
completion retires the instruction exactly once and stops the owner in driven
state 8; release remains blocked until DMACK is high. This implements the
sourced finish-before-stop and DMACK-qualified release rules without claiming
an undocumented internal priority [ADI-UM-1989, printed pp. 5-13–5-14].

Twenty-two directed/contract tests and 50,000 independent-model/RTL clocks cover
2,612 DM accepts, 2,611 completions, 111 complete-cycle extensions and physical
state-7 IRQ samples, 1,169 reads, 1,443 writes, and 889 held architectural
clocks. Generated ownership contributes 73 Type 2 accepts/72 completions, 149
Type 3, 2,057 Type 4, and 119 Type 12 transfers. Type 3 covers every legal
source/destination. Type 4 covers all 2,048
compute tuples; Type 12 covers all 112 sourced shifter tuples; both cover all
applicable DAG/I/M and DREG selectors, both directions, old-value overlap,
alternate-bank operation, bit reversal, circular wrap, and complete waits.
Twelve BR recognitions include one first sampled during a wait; three paired
completions precede pending grant service, 12 grants mask both buses for 18,638
clocks, and 10 release/reacquire/resume handshakes complete. One generated/raw
preflight collision accepts neither bus and the retained instruction later
retries successfully. One real Type 2 sequence covers HALT recognition during
a low-DMACK extension, deferred stop, aligned completion/retirement, driven
state-8 hold, low-DMACK blocked release, and state-8-to-state-1 resume. A
same-boundary pair fails closed; two cross-owner cases prove that a competing
request cannot release or replace the already active HALT or bus owner.
Fetched vectors initialize Type 3/4/12 sources and supply valid DMD; the
standalone slices remain the unknown-validity evidence for this 50,000-clock
owner. The larger 45-test/51,587-clock combined owner also covers an invalid
Type 3 returned-DMD destination and both complementary validity directions for
the Type 4 compute/read and Type 12 shift/read result pairs at aligned
completion. Additional
architectural DM requesters, HALT during BG, and whole-core event priority remain open
[ADI-UM-1989, printed
pp. 2-6–2-7, 2-18, 4-22, 5-9–5-16, 6-3–6-7, 6-12–6-13, A-5, A-7,
and A-9].

The bounded Type 2, Type 3, Type 4, and Type 12 execution slices separately
automate the architectural rule:
each DMACK-low sample retains select, direction, valid address/write data, and
architectural state, while the first high sample completes the transaction and
permits selected-I post-modification. Their 50,035-, 50,151-, 50,072-, and
50,069-clock model/RTL differentials establish the architectural hold/commit rule but do
not alone claim asynchronous setup/hold or native pin substate accuracy.

The separate Type 1 logical slice applies an even narrower verification
boundary: a single completion input holds and releases its DM and PM reads,
optional computation, PX write, and both DAG postmodifications atomically.
Its 51,069-clock comparison includes 27,309 held clocks, but the input is not
called DMACK and is not a native phase model. OQ-023 still withholds whether
the simultaneous PM cycle holds, repeats, or completes internally during a
real DMACK-low extension. The later-family external bus is multiplexed and
serializes PM before DM; SC-015 records why that different topology cannot
close the original-device pin question.

Type 2, Type 3, Type 4, and Type 12 are now connected to the native controller
through separate bounded wrappers. Their 50,027-, 50,077-, 50,082-, and
50,064-clock attachment comparisons ensure
that a DMACK-low sample causes a complete physical-substate repeat while the
instruction remains pending. The selected I register, Type 3 general-register
destination, Type 12 shifter result, Type 4 compute/status result, and optional
read destinations cannot change until the later qualified 7-to-8 completion.

The original AC table specifies DMACK setup to CLKIN high at 6-to-7 and hold
after that edge; those nanosecond requirements are documented but not modeled
as synthesizable delays [ADI-DATABOOK-1987, printed pp. 2-40 and 2-42,
parameters 72–75]. Pending questions are the FPGA pin-wrapper synchronizer,
reset/HALT release interactions, attachment of additional architectural DM requesters,
simultaneous-event
priority, and Hard Drivin' PAL connectivity. The Atari
schematic
shows the CPU DMACK net and a 10 kΩ pull-up
[ATARI-ADSP-SCHEM, drawing A044421, sheet 3 left, PDF p. 6], but every load and
PAL driver has not yet been traced.
