# Data address generator 2

**Status: source-backed arithmetic model and RTL function block**

DAG2 owns I4–I7, M4–M7, and L4–L7. It can generate either PM or DM addresses,
but has no bit-reverse output [ADI-UM-1989, printed pp. 3-1–3-2].

Its post-modify and circular arithmetic use the same documented rules as DAG1:
the memory access observes old I, any M in the same DAG can modify it, the
matching L follows the I selection, and L=0 disables modulus
[ADI-UM-1989, printed pp. 3-2–3-4].

The shared function block applies the original ADSP-2100 power-of-two base rule
documented in `dag1.md`, not the later-family/MAME placement rule. Its
`BIT_REVERSE_CAPABLE=0` configuration proves that MSTAT bit-reverse requests
cannot affect DAG2 output. Model/RTL vectors compare DAG1 and DAG2 arithmetic
while keeping their address-output capability distinct.

DAG2 also supplies the target for register-indirect control flow via PMA
[ADI-UM-1989, printed pp. 4-2, 4-20]. Tests must keep PM data, DM data, and
indirect control paths distinct and cover concurrent DAG1/DAG2 updates.
The bounded Type 21 integration slice now implements standalone MODIFY
selection and stored-I writeback. With `G=1`, it maps the two-bit I and M
fields to I4–I7 and M4–M7, selects the L corresponding to I, and writes only
that I at cycle end. PM/DM bus attachment, control-flow use, multifunction
updates, and wait-state timing remain unimplemented
[ADI-UM-1989, printed pp. 3-1–3-5, 6-14–6-15, A-4, A-7–A-8].
