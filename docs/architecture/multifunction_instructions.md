# Multifunction execution semantics

**Status: key ordering rule verified; full legality matrix pending**

All computational register reads take their values at the beginning of a cycle
and all writes become visible at the end. Therefore a simultaneous memory load
may overwrite an input only after that input has participated in the
computation [ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 2-28].

For a compute-plus-write using the computation's destination as the store
source, memory receives the old register value and the computation result
becomes the new register value [ADI-UM-FAMILY-1995, printed p. 15-6]. This
later explanation is corroborated by the original generic read/write rule above
and remains `CORROBORATED` until an original instruction-reference example is
located.

The original explicitly supports:

- ALU/MAC plus DM and PM reads;
- DM plus PM reads without computation;
- compute plus one PM or DM read;
- compute plus one PM or DM write;
- compute plus an internal data-register move.

[ADI-UM-1989, printed pp. 6-3–6-7 and Appendix A types 1, 4, 5, 8, 12–14.]

PM data access can add an instruction-fetch cycle when the cache cannot source
the next instruction [ADI-UM-1989, printed pp. 1-7, 4-26, 6-21]. This external
timing effect is part of the instruction, even though the computation itself is
single-cycle.

## Tests required before implementation

- source/destination overlap for every computational register group;
- old store value versus new computation result;
- dual PM/DM loads and independent DAG post-modifies;
- status from the computation visible only to the next cycle;
- condition-false preservation and cycle/bus activity;
- PM cache hit/miss, branch, loop-end, interrupt, wait, HALT, and BR boundaries;
- illegal destination collisions and reserved field combinations.
