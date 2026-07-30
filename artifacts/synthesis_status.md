# Synthesis status

**Updated:** 2026-07-30

- Verilator 5.048 parses and lints the three packages and source-backed
  condition, ALU, MAC, shifter, DAG, sequencer-flow, stateful register-file,
  and stateful status/control RTL with `-Wall` and no warnings.
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
- Quartus full compilation of the separately constrained shifter smoke project
  passes. Its virtual-pin fit uses 374 ALMs, 580 combinational ALUTs, 0
  registers, 0 RAM blocks, and 0 DSP blocks. Across the four fitted timing
  models, worst setup slack is 8.795 ns and worst hold slack is 0.434 ns
  against the 20 ns virtual I/O constraint; setup and hold are fully
  constrained.
- Quartus full compilation of the separately constrained DAG smoke project
  passes. Its virtual-pin fit uses 172 ALMs, 305 combinational ALUTs, 0
  registers, 0 RAM blocks, and 0 DSP blocks. Across the four fitted timing
  models, worst setup slack is 7.201 ns and worst hold slack is 0.527 ns
  against the 20 ns virtual I/O constraint; setup and hold are fully
  constrained.
- Quartus full compilation of the separately constrained sequencer-flow smoke
  project passes. Its virtual-pin fit uses 74 ALMs, 44 combinational ALUTs, 0
  registers, 0 RAM blocks, and 0 DSP blocks. Across the four fitted timing
  models, worst setup slack is 14.139 ns and worst hold slack is 0.386 ns
  against the 20 ns virtual I/O constraint; setup and hold are fully
  constrained.
- Quartus full compilation of the register-file smoke project passes with the
  DE10-Nano 50 MHz input constrained on `PIN_V11` and 356 virtual data/control
  pins. Analysis identifies exactly 554 design registers; deterministic
  Standard Fit seed 2 adds 55 secondary routing-optimization duplicates. The
  fit uses 1,084 ALMs, 1,353 combinational ALUTs, no RAM, and no DSPs. Across
  the four timing models, worst setup slack is 9.985 ns and worst hold slack is
  0.109 ns against the 20 ns constraint, with zero unconstrained clocks, ports,
  or paths.
- The only full-flow warning is Quartus Lite's unavailable LogicLock feature;
  the project does not use LogicLock.
- Quartus full compilation of the status/control smoke project passes. It uses
  84 ALMs, 41 combinational ALUTs, exactly 21 architectural registers with no
  fitter-created register duplicates, no RAM, and no DSPs. Its virtual internal
  controls have an explicit 5 ns same-clock registered-source input-arrival
  assumption. Across four timing models, worst setup is +11.811 ns and worst
  hold is +0.169 ns against 20 ns, with zero unconstrained paths.
- SymbiYosys is not installed. `make formal` strictly lints the eight available
  assertion harnesses before reporting that proof execution is skipped.

There is no whole-core utilization, latch-count, Fmax, critical-path, or
timing-closure claim. `make synth-yosys` reports an explicit tool-availability
skip; `make synth-quartus` runs the bounded condition, ALU, MAC, shifter, DAG,
sequencer-flow, register-file, and status-register block smoke projects.
