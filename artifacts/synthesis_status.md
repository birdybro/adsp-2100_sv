# Synthesis status

**Updated:** 2026-07-30

- Verilator 5.048 parses and lints the two packages and source-backed
  combinational condition and ALU RTL with `-Wall` and no warnings.
- Yosys is not installed in this environment.
- Quartus 17.0.2 full compilation of the condition-logic smoke project passes
  for Cyclone V `5CSEBA6U23I7`. The constrained virtual-pin fit uses 10 ALMs,
  6 combinational ALUTs, 0 registers, 0 RAM blocks, and 0 DSP blocks.
- TimeQuest reports zero unconstrained clocks, ports, or paths against a
  20 ns virtual I/O constraint. Across the four fitted timing models, the
  worst setup slack is 17.927 ns and worst hold slack is 0.283 ns. These are
  unit-level virtual-pin estimates, not whole-core Fmax or MiSTer closure.
- Quartus full compilation of the separately constrained ALU smoke project
  also passes. Its virtual-pin fit uses 161 ALMs, 196 combinational ALUTs,
  0 registers, 0 RAM blocks, and 0 DSP blocks. Across the four fitted timing
  models, worst setup slack is 9.686 ns and worst hold slack is 0.212 ns
  against the 20 ns virtual I/O constraint; setup and hold are fully
  constrained.
- Quartus full compilation of the separately constrained MAC smoke project
  passes. Its virtual-pin fit uses 229 ALMs, 229 combinational ALUTs, one DSP
  block, 0 registers, and 0 RAM blocks. Across the four fitted timing models,
  worst setup slack is 2.857 ns and worst hold slack is 0.321 ns against the
  20 ns virtual I/O constraint; setup and hold are fully constrained.
- The only full-flow warning is Quartus Lite's unavailable LogicLock feature;
  the project does not use LogicLock.
- SymbiYosys is not installed. `make formal` strictly lints the three available
  assertion harnesses before reporting that proof execution is skipped.

There is no whole-core utilization, latch-count, Fmax, critical-path, or
timing-closure claim. `make synth-yosys` reports an explicit tool-availability
skip; `make synth-quartus` runs the bounded condition, ALU, and MAC block smoke
projects.
