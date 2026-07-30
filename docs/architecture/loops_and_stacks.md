# Loops and stacks

**Status: original depths and all four storage slices implemented;
sequencer connectivity incomplete**

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

The sequencer storage exposes each current top with an explicit valid bit,
accepted pushes, valid pops, overflow events, and empty-pop indications. Its
SSTAT output is a fragment: bits 4/5 are zero and must be composed with the
status-stack fragment. A count-stack push is an upstream request; the future
CNTR controller remains responsible for the documented rule that loading a
new count pushes the old count only when the current count is valid
[ADI-UM-1989, printed pp. 4-4–4-5]. Same-stack simultaneous push/pop is
suppressed globally with `write_conflict_o`; this is a fail-closed integration
safeguard, not a claimed real-device illegal-encoding behavior.

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
or exit path. The storage arrays exist but are not yet connected to that flow
block. DO UNTIL setup, CNTR valid/decrement state, instruction/manual stack
controls, interrupt/RTI actions, and every empty-pop architectural side effect
remain outside the integrated sequencer.
