# Loops and stacks

**Status: original depths and storage implemented; bounded automatic,
Type 20 return, and manual Type 26 connectivity verified**

The original has four stack classes reported by SSTAT: PC, count, status, and
loop [ADI-UM-1989, printed p. 4-22]. Depths are 16 for the 14-bit PC stack,
four for the 14-bit count stack, four for the 16-bit status stack, and four for
the 18-bit loop stack [ADI-UM-1989, printed pp. 4-3–4-6;
ADI-DATABOOK-1987, printed pp. 2-21–2-22, Figure 6]. The status word packs
ASTAT[7:0], MSTAT[3:0], then IMASK[3:0], yielding exactly 16 bits
[ADI-UM-1989, printed p. 4-10].

On stack overflow, the pointer saturates, new items are lost while older data
is retained, and the overflow bit sticks until reset. Exactly four subsequent
valid pops empty a full status stack even after any number of overflowing
pushes, so empty and overflow can both be set [ADI-UM-1989, printed p. 4-22].
The value and register side effects of a pop attempted while already empty are
not documented and remain OQ-013.

The independent model and `rtl/core/adsp2100_status_stack.sv` implement the
original four-entry status LIFO, both no-change Spp codes,
manual/automatic-push-compatible storage, RTI/manual-pop-compatible output,
saturating depth, sticky overflow, and SSTAT bits 4/5. The independent
sequencer-stack model and `rtl/core/adsp2100_sequencer_stacks.sv` implement
the exact PC, count, and loop dimensions and SSTAT bits 0–3 and 6–7. Reset
clears all pointers and overflow bits without initializing stored data
[ADI-UM-1989, printed pp. 4-3–4-7, 4-10, 4-22, 5-13, A-10].

The implementation additionally stores a 13-bit validity sidecar with each
accepted status entry: eight ASTAT known-state bits, four MSTAT known-state
bits, and one whole-IMASK known-state bit. This metadata is not part of the
documented 16-bit architectural stack word. It prevents a reset-unknown or
otherwise invalid status value from becoming spuriously known after an
intervening write and later POP STS or RTI. The sidecar follows the same
accepted-push, saturating-depth, and valid-pop selection as its word. Direct
model/RTL comparison covers independent data and sidecar patterns, overflow,
LIFO ordering, and reset across 50,037 clocks; an end-to-end combined-owner
sequence invalidates ASTAT/MSTAT/IMASK, pushes that context, overwrites each
register with known data, and proves that the subsequent valid pop restores
all three validity classifications. A second combined-owner sequence enters
IRQ2 with invalid ASTAT/MSTAT, installs the known interrupt nesting mask, and
proves that fetched RTI restores the pre-entry classifications before
dependent PM work. IMASK is known in this path because interrupt recognition
requires it. Fetched Type 17 then reads the live composed SSTAT low byte across
status-stack empty (`0x55`), nonempty (`0x45`), overflow (`0x65`), and emptied
with sticky overflow (`0x75`) states. Its upper-byte extension remains OQ-016.

The original Type 26 action selection is now independently machine-readable
and executable. `SPP[1:0]` preserves both no-change encodings and selects
status push/pop; `CP`, `LP`, and `PP` independently select count-, loop-, and
PC-stack pops. The original grammar permits these clauses to be combined, and
the instruction remains one processor cycle [ADI-UM-1989, printed pp. 1-2,
6-14–6-15, A-4, A-8–A-10]. The Python action model and
`rtl/core/adsp2100_stack_control_decode.sv` cover all 32 encodings while
failing closed for every non-Type-26 word.

The independent composed model and
`rtl/core/adsp2100_stack_control_slice.sv` now execute those requests against
all four stack classes at one cycle boundary. PUSH STS captures cycle-start
ASTAT/MSTAT/IMASK; POP STS restores all three from the cycle-start status top;
POP CNTR restores the cycle-start count top; and POP PC/POP LOOP discard their
selected entries. All selected actions commit together at cycle end. Nine
directed/schema/random model checks and 50,015 model-versus-RTL cycles cover
combined actions, both no-effect aliases, valid/empty/full stacks, reset,
invalid opcodes, SSTAT composition, and fail-closed integration conflicts
[ADI-UM-1989, printed pp. 4-3–4-7, 4-9–4-10, 6-14–6-15,
A-4, A-8–A-10].

The same action decoder is now attached to the shared architectural state in
the bounded ordinary-fetch owner. Status PUSH captures live cycle-start
ASTAT/MSTAT/IMASK and their validity sidecars, status POP restores both the
tuple and its captured validity, and a count POP restores a valid prior CNTR
only on the fetched instruction's state-7 retirement. The
superseding 48-test, 444,003-clock owner comparison traverses all 32 payloads.
A fetched Type 10 CALL now creates valid PC-stack context and a following Type
26 POP PC consumes it. Fetched Type 19 CALL also supplies valid PC-stack
context consumed by Type 20 RTS. Fetched Type 20 RTS and RTI consume valid PC-stack
context, and RTI simultaneously consumes valid status-stack context. Fetched
Type 11 creates valid PC- and loop-stack context, automatic loop termination
consumes both, and a directed Type 26 POP LOOP consumes a valid loop top. A
further nonterminal fetched sequence creates valid status, count, PC, and loop
contexts before one `POP STS, POP CNTR, POP LOOP, POP PC` word restores both
value-bearing tops and empties all four stack depths atomically. This does not
assign behavior to the OQ-018 automatic/manual terminal case.

The sequencer storage exposes each current top with an explicit valid bit,
accepted pushes, valid pops, overflow events, and empty-pop indications. Its
SSTAT output is a fragment: bits 4/5 are zero and must be composed with the
status-stack fragment. The separate CNTR controller now generates a count-stack
push only when a load replaces a valid count, and generates a pop on true CE
or manual pop. A true CE test restores a valid stack top or invalidates CNTR
when the count stack is empty [ADI-UM-1989, printed pp. 4-4–4-5].
Same-stack simultaneous push/pop is suppressed globally with
`write_conflict_o`; this is a fail-closed integration safeguard, not a claimed
real-device illegal-encoding behavior.

An empty pop produces no valid data; zero on the RTL data output is an
explicitly non-architectural interface sentinel. The value and architectural
side effects remain OQ-013.

Nested loops cannot terminate on the same instruction because the comparator
checks one termination at a time [ADI-UM-1989, printed p. 4-8]. Premature loop
exit may require explicit stack pops [ADI-UM-1989, printed p. 4-7].

The instruction-boundary flow block implements the sourced precedence rule:
a taken jump, call, or return on the loop's final instruction performs only its
explicit flow/PC-stack action and suppresses implicit loop, count-stack, and
counter-test actions. A false explicit condition allows the normal loop back
or exit path.

The bounded sequencer slice connects that flow rule to PC/count/loop storage,
CNTR, and IF/DO condition evaluation. DO UNTIL setup pushes PC+1 and a loop
descriptor; loop back reads the current PC-stack top; loop exit atomically
pops the PC and loop stacks and, for true CE, restores or invalidates CNTR
while popping the count stack. Nested CE restoration and stack-depth
transitions match the independent model across 50,014 cycles. The boundary
also rejects nested DO requests whose end address equals the active loop end,
implementing the original restriction rather than allowing an unrepresentable
comparator state.

Complete arbitration between Type 26 and automatic sequencer/interrupt
actions remains outside these bounded integration results. Every
empty-pop architectural side effect remains OQ-013. Conditional-CALL CE
remains OQ-012. Competing automatic/manual actions and DO setup on an active
outer loop's final instruction are rejected under OQ-018 instead of receiving
an invented priority.

The bounded Type 10 direct-transfer slice and fetched owner connect CALL pushes and JUMP NOT CE
counter restoration to the same PC/count stack rules. A stack-full CALL still
takes its target while the newest return address is lost and overflow sticks,
matching the sourced global stack-overflow behavior. The fetched owner also
connects active loop descriptors and proves that a taken explicit transfer on
the terminal instruction suppresses the automatic loop action; a false
explicit condition leaves that automatic action eligible. All CALL NOT CE
encodings remain action-free under OQ-012 rather than assigning an unsupported
counter-stack interaction [ADI-UM-1989, printed pp. 4-3–4-7, 4-22].

The bounded Type 11 setup slice independently verifies the simultaneous
PC-stack and loop-stack pushes for all 262,144 encodings. Distinct-end nesting
through four loop-stack entries is accepted; a fifth push raises sticky loop
overflow and discards the newest loop descriptor under the existing sourced
stack contract. The associated PC-stack push remains an independent hardware
action. The exact full-chip recovery behavior after deliberately overflowing
only one of the two stacks is not claimed [ADI-UM-1989, printed pp. 4-5–4-8,
4-22, A-2, A-10]. The same action now retires in the ordinary fetched owner.
That owner evaluates the live top descriptor on its terminal instruction,
selects loopback or exit for non-counter and ASTAT conditions, couples CE
loopback/exit to CNTR/count-stack transitions, and restores nested CE context.
Six directed additions to the 48-test, 444,003-clock comparison cover these
paths, explicit-flow precedence, OQ-018 rejection, and the valid Type 26 loop
pop described above.

The bounded Type 20 slice connects RTS to the cycle-start PC-stack top and RTI
to both PC- and status-stack tops. A false condition pops neither stack. A
taken RTS pops only PC; a taken RTI pops both in the same instruction boundary
and restores ASTAT/MSTAT/IMASK from the status word. If a taken return lacks a
required top, the slice requests no pop and reports OQ-013 context failure.
This verifies valid-stack connectivity and prevents a sentinel value from
becoming architectural behavior; it does not resolve what physical hardware
does for an intentionally empty pop [ADI-UM-1989, printed pp. 4-3–4-4,
4-9–4-10, 4-22, 6-14 Table 6.8]. The same operations now retire in the
ordinary fetched owner after it issues PC+1 or the valid PC-stack top through
the native PM controller. Taken explicit-return precedence over an automatic
terminal action is connected there; interrupt-entry arbitration remains
outside that attachment.

Fetched Type 22 shares the explicit-flow precedence gate without modifying
any stack. A true predicate fetches PC+1 and suppresses the automatic terminal
pop/loopback action before its TRAP event; a false predicate leaves automatic
loop handling eligible. Directed true and false terminal cases pass in the
48-test, 444,003-clock owner comparison. Simultaneous interrupt, manual-stack,
ordinary-HALT, and cache-event priority remains outside this bounded claim
[ADI-UM-1989, printed pp. 4-3–4-8, 4-25, 5-14–5-15].
