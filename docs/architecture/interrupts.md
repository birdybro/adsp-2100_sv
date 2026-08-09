# Interrupt architecture

**Status: original-device recognition implemented; entry/vector/RTI bounded
in the private ordinary-fetch owner; retained requests composed with ordinary
HALT, normal BR/BG, native DMACK waits, and both real uncached PM-data owners**

Four active-low inputs IRQ0–IRQ3 are individually masked and configured
edge/level by ICNTL; IRQ3 has highest priority and vectors are PM addresses
0x0000–0x0003 [ADI-UM-1989, printed pp. 4-8–4-9, 5-15–5-16].

Requests are sampled at state 7. Edge mode detects a high-to-low difference
between successive cycle samples and latches it; level mode must remain active
until serviced [ADI-UM-1989, printed pp. 4-8–4-9, 5-15].

Recognition at the end of state 7 does not cancel the instruction executing in
that cycle. That instruction completes, while the word fetched concurrently is
ignored. The following cycle executes a NOP, pushes the current PC (the address
of the ignored word) and ASTAT/MSTAT/IMASK, and fetches the selected vector.
The vector word executes in the next cycle. The manual describes two cycles of
overhead when the vector contains the usual jump [ADI-UM-1989, printed
pp. 4-9–4-10; Figure 5.11, printed p. 5-16]. RTI pops PC and status together,
then refetches the ignored word.

The independent model and status/control RTL implement the exact-width
ASTAT/MSTAT/IMASK pre-entry snapshot, suppression of the aborted instruction's
ordinary status writes, and RTI-style status restoration. With nesting
disabled, entry clears IMASK. With nesting enabled, entry at IRQ0, IRQ1, IRQ2,
or IRQ3 masks that level and every lower-priority level, producing IMASK
`0xE`, `0xC`, `0x8`, or `0x0` [ADI-UM-1989, printed pp. 4-9–4-10, 4-23–4-24].
The standalone model/RTL recognizer implements all four original pins,
state-7 sampling, edge retention, level sensitivity, IMASK gating, IRQ3-to-IRQ0
priority, and vectors `0x0000`–`0x0003`. Nine directed/model checks and 50,027
model/RTL clocks pass. The first state-7 sample after reset establishes a
comparison baseline and cannot manufacture an edge; the exact physical-device
reset-release comparison sample is not stated by the source and remains
PROVISIONAL under OQ-025.

The private ordinary-fetch owner connects that recognizer to the shared PC,
PC stack, status stack, and status/control state. A recognized request retires
the current instruction, discards its completed next-word fetch, performs one
vectoring-NOP cycle, pushes the post-instruction PC/status context when the
vector request is accepted, applies the documented nesting mask, fetches the
vector, and permits a fetched RTI to restore and refetch the ignored word. Two
directed owner tests and the superseding 48-test, 444,003-clock model/RTL run
exercise IRQ2 level entry/RTI and OQ-015 fail-closed adjacency. Interrupts
adjacent to an effective MODE CONTROL or MSTAT/ICNTL/IMASK write are retained
but not serviced because the manual does not close that ordering.

The original status stack is four entries by 16 bits and can therefore retain
all four possible nested interrupt contexts [ADI-DATABOOK-1987, printed
pp. 2-21–2-22, Figure 6]. Its independent model and portable RTL now implement
the storage and fault-status boundary. Each accepted entry also carries an
implementation-only ASTAT/MSTAT/IMASK validity snapshot beside the documented
16-bit word, and the accepted POP STS/RTI output restores that snapshot with
the data. Direct stack comparison covers the metadata across 50,037 clocks,
and a combined-owner manual-push/pop sequence proves invalid context survives
intervening known writes. The bounded Type 20 return slice now
wires a condition-true RTI to simultaneous valid PC/status pops and cycle-end
ASTAT/MSTAT/IMASK restoration. It verifies the return half of the context
path, including condition-false preservation and OQ-013 fail-closed missing
context, across 50,254 model/RTL cycles. It does not yet connect the entry
recognizer, priority logic, vectors, or active-loop arbitration. The same RTI
return half now executes in the ordinary fetched owner with return-target
state-8 issue and atomic PC/status state-7 retirement; this does not establish
interrupt-entry latency or cross-event priority
[ADI-UM-1989, printed pp. 4-3–4-4, 4-9–4-10, 6-14 Table 6.8].

Requests latch but are not serviced during HALT, TRAP, bus grant, DMACK waits,
or between the two cycles of an uncached PM-data access
[ADI-UM-1989, printed p. 5-16]. The private owner suppresses service for a
taken fetched TRAP. The ordinary-fetch HALT, private BR/BG, and retained-
fetch/shared-PM BR/BG compositions now connect the recognizer. Directed IRQ2
sequences sample a request at state 7 while stop or grant is pending, retain it
without issuing a vector request or pushing context throughout state 8 or BG,
and enter through the vectoring-NOP path on the qualified state-8-to-state-1
resume edge. Those comparisons pass 11 tests/50,048 clocks, 6 tests/50,054
clocks, and 7 tests/50,054 clocks respectively.

A bounded native-DM composition couples each accepted ordinary fetch to a real
fetched Type 2, legal Type 3, source-closed Type 4, or source-closed Type 12
descriptor; a raw descriptor remains separate structural scaffolding. A low
DMACK sample repeats the complete physical state-seven interval while the
architectural fetch/execute boundary remains held. The interrupt recognizer
still receives each physical state-7 sample, so an IRQ2 edge first observed
during the wait becomes pending, but vector issue, context push, instruction
retirement, and PM completion remain suppressed until paired PM/DM completion.
The same owner recognizes BR at physical state 3 during a wait while deferring
grant service until completion. It also recognizes ordinary HALT during a
real Type 2 wait and defers stop until that same completion/retirement.
Twenty-two directed/model tests and 50,000 model/RTL clocks cover 111 wait
extensions/IRQ samples, one retained edge-mode
request, 12 BR recognitions, three completions before pending grant, and service
only after the aligned completion. BR overlap with interrupt/TRAP service and
simultaneous BR/HALT are
conflict-reported rather than assigned an unsourced priority
[ADI-UM-1989, printed pp. 5-3–5-16].

The real Type 5 ALU/MAC-plus-PM and Type 13 shifter-plus-PM native/cache
owners now compose the same recognizer with the documented two-cycle uncached
PM-data interval. Physical state 7 still samples the pins at data-cycle
completion, but recognition is gated by the owner's instruction-complete
event. Thus an edge first observed at an uncached data completion becomes
pending without service; the immediately following pure recovery fetch
completes the instruction and releases recognition. Directed IRQ2 cases plus
50,100 Type 5 and 50,098 Type 13 model/RTL clocks verify that ordering
[ADI-UM-1989, printed pp. 4-26–4-30 and 5-15–5-16]. The combined automatic
program-client owner now consumes that handoff at whole-instruction recovery
retirement: a directed Type 5 miss discards the returned sequential opcode,
pushes PC/status, applies the nesting mask, and issues vector 2 through the
ordinary client across the 51,587-clock comparison. A second directed sequence
invalidates ASTAT/MSTAT from reset-unknown AX1 before recognizing IRQ2, accepts
the shared vector request, executes a fetched RTI at vector 2, and proves that
the pre-entry invalid classifications are restored before dependent PM work.
IMASK is necessarily known for recognition and restores to its known pre-entry
value. This is bounded evidence for the documented entry/return data path, not
a priority claim for an unresolved simultaneous event.

This is evidence for a request actually sampled at state 7; it is not a claim
that a shorter asynchronous pulse wholly contained in a stopped/granted
interval is captured. The native-DM composition establishes state-7 sampling
during full-cycle DMACK extensions and now derives held descriptors from real
fetched Type 2, legal Type 3, source-closed Type 4, or source-closed Type 12
words. Their memory, compute/shifter/status, DAG, PC, and returned-word effects remain paired until aligned
completion, and only then may the retained request enter. Type 3 covers every
legal register selector; Type 4 covers all 2,048 compute tuples, all DAG/I/M and
DREG selectors, and both directions. Fetched vectors use initialized store/
compute operands and valid DMD; broader unknown propagation remains standalone
evidence. Its raw descriptor port remains separate structural scaffolding. The
real Type 5/Type
13 owners establish
recognition deferral across an uncached PM-data pair, and the automatic
combined owner establishes PC/status entry for one sequential PM miss.
Simultaneous IRQ with Type 22 TRAP, HALT, BR/BG, an active loop, or shared-PM
contention still lacks sourced priority. The fetched-DM owner reports the
BR/IRQ/TRAP subset as an integration conflict; it does not choose a winner.
