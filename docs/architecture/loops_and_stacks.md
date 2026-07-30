# Loops and stacks

**Status: structural behavior verified; illegal-depth behavior incomplete**

The original has four stack classes reported by SSTAT: PC, count, status, and
loop [ADI-UM-1989, printed p. 4-22]. Known depths are 16 for the 14-bit PC
stack, four for the 14-bit count stack, and four for the 18-bit loop stack
[ADI-UM-1989, printed pp. 4-3–4-6]. Status-stack depth remains open.

On stack overflow, new items are lost while older data is retained; overflow
bits stick until reset. Empty and overflow can both be set
[ADI-UM-1989, printed p. 4-22]. Whether all stack classes share identical
physical overflow details and the exact status-stack depth require additional
evidence.

Nested loops cannot terminate on the same instruction because the comparator
checks one termination at a time [ADI-UM-1989, printed p. 4-8]. Premature loop
exit may require explicit stack pops [ADI-UM-1989, printed p. 4-7].

The instruction-boundary flow block implements the sourced precedence rule:
a taken jump, call, or return on the loop's final instruction performs only its
explicit flow/PC-stack action and suppresses implicit loop, count-stack, and
counter-test actions. A false explicit condition allows the normal loop back
or exit path. Stack arrays, DO UNTIL pushes, nested state, overflow, and empty
pop effects remain outside this block.
