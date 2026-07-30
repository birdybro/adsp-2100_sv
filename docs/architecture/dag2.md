# Data address generator 2

**Status: source-backed specification baseline**

DAG2 owns I4–I7, M4–M7, and L4–L7. It can generate either PM or DM addresses,
but has no bit-reverse output [ADI-UM-1989, printed pp. 3-1–3-2].

Its post-modify and circular arithmetic use the same documented rules as DAG1:
the memory access observes old I, any M in the same DAG can modify it, the
matching L follows the I selection, and L=0 disables modulus
[ADI-UM-1989, printed pp. 3-2–3-4].

DAG2 also supplies the target for register-indirect control flow via PMA
[ADI-UM-1989, printed pp. 4-2, 4-20]. Tests must keep PM data, DM data, and
indirect control paths distinct and cover concurrent DAG1/DAG2 updates.
