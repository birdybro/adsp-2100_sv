# Loops and stacks

**Status: original depths verified; status-stack storage implemented; other
stack storage incomplete**

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
original four-entry LIFO, both no-change Spp codes, manual/automatic
push-compatible storage, RTI/manual-pop-compatible output, saturating depth,
sticky overflow, and the status-stack empty/overflow sources for SSTAT bits 4
and 5. Reset clears the pointer and overflow bit without initializing stored
data [ADI-UM-1989, printed pp. 4-10, 4-22, 5-13, A-10]. An empty pop produces
`pop_valid_o=0`; its zero data output is an explicitly non-architectural
interface sentinel.

Nested loops cannot terminate on the same instruction because the comparator
checks one termination at a time [ADI-UM-1989, printed p. 4-8]. Premature loop
exit may require explicit stack pops [ADI-UM-1989, printed p. 4-7].

The instruction-boundary flow block implements the sourced precedence rule:
a taken jump, call, or return on the loop's final instruction performs only its
explicit flow/PC-stack action and suppresses implicit loop, count-stack, and
counter-test actions. A false explicit condition allows the normal loop back
or exit path. PC/count/loop stack arrays, DO UNTIL pushes, nested state, their
SSTAT sources, and every empty-pop architectural side effect remain outside
this block.
