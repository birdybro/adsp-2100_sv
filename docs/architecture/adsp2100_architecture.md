# ADSP-2100 architecture baseline

**Status: source-backed research baseline**

The original processor combines three independent 16-bit computational units,
two DAGs, a program sequencer, five internal buses, a PMD-DMD exchange, and a
16-word instruction cache [ADI-UM-1989, printed pp. 1-1, 1-4–1-7].

One instruction can compute, update the next PC, perform one or two data moves,
and post-modify one or two address pointers
[ADI-UM-1989, printed p. 1-7]. This parallelism defines architectural
same-cycle semantics; it is not a license to execute sequential micro-operations.

The instruction register creates one level of program-flow pipelining: a fetched
instruction executes during the next processor cycle while the subsequent
instruction is fetched [ADI-UM-1989, printed p. 1-5]. Computational registers
are read at cycle start and written at cycle end
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 2-28]. Status generated in a cycle is
latched at its end and conditions see the previous cycle's status
[ADI-UM-1989, printed pp. 4-21, 4-25].

Externally, PM is 24 bits wide and DM is 16 bits wide with independent address
and data buses [ADI-UM-1989, printed pp. 5-6, 5-9]. Details are split among the
component documents; unresolved behavior remains in
`docs/research/open_questions.md`.
