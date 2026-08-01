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
The bounded Type 19 slice now connects this control path to exact I4-I7
storage. A taken JUMP/CALL exposes the selected old I value as the PMA target
and leaves that I unchanged; a false conditional transfer neither drives the
indirect PMA observation nor requires the selected I to be initialized. The
50,259-cycle model/RTL comparison checks all four selections and rotating I
probes. It does not attach PMS/PMRD, cache, fetch, or wait-state phases
[ADI-UM-1989, printed pp. 4-3, 4-20, 6-13–6-14, A-3].
The bounded Type 21 integration slice implements standalone MODIFY
selection and stored-I writeback. With `G=1`, it maps the two-bit I and M
fields to I4–I7 and M4–M7, selects the L corresponding to I, and writes only
that I at cycle end. Type 2 now attaches all DAG2 I/M selections to immediate
DM writes with stable waited transactions and completion-only
post-modification; Type 12 separately attaches shifter-plus-DM. Type 4 action
execution selects every DAG2 I/M pair and matching L-by-I relationship, holds
the logical DM transaction across waits, and commits selected-I postmodify only
at acknowledgment. Its native attachment preserves that completion rule.
Other PM/DM multifunction updates remain unimplemented
[ADI-UM-1989, printed pp. 3-1–3-5, 6-14–6-15, A-4, A-7–A-8].

Original Type 5 fixes every I/M selection to DAG2: the two-bit fields map to
I4-I7 and M4-M7, with L selected by I. All sixteen I/M pairs are covered
exhaustively. Its bounded execution captures old I/M/L at issue, uses old I as
the PM-data address, and commits the selected-I postmodify only at the fixed PM
data completion; a cache-miss recovery fetch does not modify I again. The
native attachment verifies state-8 issue and state-7-only I commit. Whole-core
PM ownership and event arbitration remain open
[ADI-UM-1989, printed pp. 3-1–3-7, 6-3–6-7, A-1, A-7–A-8].

The bounded Type 13 path now attaches all I4–I7/M4–M7 selections to PM data.
The access observes old I, chooses L by I, never applies DAG1 bit reversal,
and commits the post-modified I with the fixed PM data cycle. A following
cache-miss recovery fetch does not modify I again. Directed and randomized
model/RTL checks include positive/negative M, invalid configurations, all
four I/M selections, and both computational banks [ADI-UM-1989, printed
pp. 3-1–3-4, 4-26–4-30, 6-3–6-7, A-3].
