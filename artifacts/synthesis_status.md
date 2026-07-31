# Synthesis status

**Updated:** 2026-07-31

- Verilator 5.048 parses and lints the generated packages, class decoder,
  Type 6, Type 8, Type 9, Type 10, Type 11, Type 14, Type 15, Type 16, Type 17, Type 19, and Type 20 decoders/integration slices, stack-control
  decoder/integration slice, Type 21
  decoder/integration slice, and source-backed
  condition, ALU, MAC, shifter, DAG, sequencer-flow, stateful register-file,
  stateful CNTR, stateful status/control, stateful status-stack, and stateful
  PC/count/loop stack plus bounded sequencer-integration RTL with `-Wall` and
  no warnings.
- Yosys is not installed in this environment.
- Quartus 17.0.2 full compilation of the bounded Type 20 conditional-return
  slice passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone
  constraint. It uses 318 ALMs and 417 fitted registers with no RAM or DSP
  blocks. Across four timing models, worst setup slack is +7.725 ns, worst
  hold slack is +0.136 ns, and worst slow-corner Fmax is 81.47 MHz, with zero
  unconstrained clocks, ports, or paths. This is bounded-slice evidence, not
  whole-core or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 19 indirect-transfer
  slice passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone
  constraint. It uses 353 ALMs and 400 fitted registers with no RAM or DSP
  blocks. Across four timing models, worst setup slack is +7.520 ns, worst
  hold slack is +0.045 ns, and worst slow-corner Fmax is 80.93 MHz, with zero
  unconstrained clocks, ports, or paths. This is bounded-slice evidence, not
  whole-core or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 11 DO UNTIL setup slice
  passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone constraint. It
  uses 308 ALMs and 402 fitted registers with no RAM or DSP blocks. Across
  four timing models, worst setup slack is +7.263 ns, worst hold slack is
  +0.074 ns, and worst slow-corner Fmax is 78.51 MHz, with zero unconstrained
  clocks, ports, or paths. This is bounded setup evidence, not whole-core or
  MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 10 direct-transfer slice
  passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone constraint. It
  uses 284 ALMs and 334 fitted registers with no RAM or DSP blocks. Across
  four timing models, worst setup slack is +8.138 ns, worst hold slack is
  +0.167 ns, and worst slow-corner Fmax is 84.3 MHz, with zero unconstrained
  clocks, ports, or paths. This is bounded-slice evidence, not whole-core or
  MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 8 ALU/MAC-plus-MOVE
  slice passes for Cyclone V `5CSEBA6U23I7` at its documented 22 ns
  standalone constraint. It uses 983 ALMs, 693 fitted registers, one DSP
  block, and no RAM. Across four timing models, worst setup slack is +1.131
  ns, worst hold slack is +0.177 ns, and worst slow-corner Fmax is 47.92 MHz,
  with zero unconstrained clocks, ports, or paths. A 20 ns run missed setup by
  1.721 ns; the relaxed unit constraint is explicit evidence that this
  monolithic execution slice needs phase scheduling before any 50 MHz or
  MiSTer timing claim.
- Quartus 17.0.2 full compilation of the bounded Type 9 conditional-compute
  slice passes for Cyclone V `5CSEBA6U23I7` at its documented 22 ns
  standalone constraint. It uses 970 ALMs, 697 fitted registers, one DSP
  block, and no RAM. Across four timing models, worst setup slack is +1.140
  ns, worst hold slack is +0.165 ns, and worst slow-corner Fmax is 47.94 MHz,
  with zero unconstrained clocks, ports, or paths. The initial 20 ns fit
  missed setup by 1.735 ns and measured 46.01 MHz at the worst slow corner;
  this is bounded-slice evidence, not whole-core or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 14 shifter-plus-MOVE
  slice passes for Cyclone V `5CSEBA6U23I7`. It uses 1,032 ALMs and 565
  fitted registers (502 design registers plus 63 fitter-created routing
  duplicates), with no RAM or DSP blocks. Across four timing models, worst
  setup slack is +3.041 ns and worst hold slack is +0.171 ns against 20 ns,
  with zero unconstrained clocks, ports, or paths. Constant no-PM/no-DM
  outputs, fail-closed unsupported encodings, and same-destination conflict
  suppression are asserted properties of the bounded slice.
- Quartus 17.0.2 full compilation of the bounded Type 16 conditional-shift
  slice passes for Cyclone V `5CSEBA6U23I7`. It uses 840 ALMs and 520 fitted
  registers with no RAM or DSP blocks. Across four timing models, worst setup
  slack is +2.304 ns and worst hold slack is +0.173 ns against 20 ns, with
  zero unconstrained clocks, ports, or paths. Constant no-PM/no-DM outputs and
  condition-false write suppression are asserted properties of the slice.
- Quartus 17.0.2 full compilation of the bounded Type 15 immediate-shift slice
  passes for Cyclone V `5CSEBA6U23I7`. It uses 774 ALMs and 501 fitted
  registers with no RAM or DSP blocks. Across four timing models, worst setup
  slack is +3.728 ns and worst hold slack is +0.057 ns against 20 ns, with
  zero unconstrained clocks, ports, or paths. Constant no-PM/no-DM and
  conflict outputs are asserted properties of this bounded instruction slice.
- Quartus 17.0.2 full compilation of the bounded Type 6 immediate-load slice
  passes for Cyclone V `5CSEBA6U23I7`. It uses 302 ALMs and 484 registers with
  no RAM or DSP blocks. Across four timing models, worst setup slack is +8.167
  ns and worst hold slack is +0.133 ns against 20 ns, with zero unconstrained
  clocks, ports, or paths. Constant no-PM/no-DM and conflict outputs are
  asserted properties of this bounded instruction slice.
- Quartus 17.0.2 full compilation of the generated class-decoder smoke project
  passes for Cyclone V `5CSEBA6U23I7`. The constrained virtual-pin fit uses 55
  ALMs, 63 combinational ALUTs, 0 registers, 0 RAM blocks, and 0 DSP blocks.
  Across four timing models, worst setup slack is 14.723 ns and worst hold
  slack is 0.407 ns against the 20 ns virtual I/O constraint, with zero
  unconstrained clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the Type 17 internal-MOVE action decoder
  passes for Cyclone V `5CSEBA6U23I7`. It uses 42 ALMs, 24 combinational
  ALUTs, no registers, no RAM, and no DSPs. Across four timing models, worst
  setup slack is +15.704 ns and worst hold slack is +0.462 ns against 20 ns,
  with zero unconstrained clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the bounded Type 17 state slice passes
  for Cyclone V `5CSEBA6U23I7`. It uses 816 ALMs and 906 registers with no
  M10K or DSP blocks. Across four timing models, worst setup slack is +6.401
  ns and worst hold slack is +0.151 ns against 20 ns, with zero unconstrained
  clocks, ports, or paths. Constant no-PM/no-DM outputs and untouched stack
  status fragments are expected properties of this bounded instruction slice.
- Quartus 17.0.2 full compilation of the Type 26 stack-control decoder passes
  for Cyclone V `5CSEBA6U23I7`. The constrained virtual-pin fit uses 25 ALMs,
  12 combinational ALUTs, 0 registers, 0 RAM blocks, and 0 DSP blocks. Across
  four timing models, worst setup slack is +17.244 ns and worst hold slack is
  +0.287 ns against the 20 ns virtual I/O constraint, with zero unconstrained
  clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the stateful Type 26 integration slice
  passes. It uses 351 ALMs, 260 combinational logic ALUTs, exactly 465 design
  registers plus twelve fitter-created routing duplicates, no RAM, and no
  DSPs. The 465 design registers comprise the bounded PC/count/loop/status
  stack, CNTR, and live ASTAT/MSTAT/IMASK state. Across four timing models,
  worst setup is +10.550 ns and worst hold is +0.165 ns against 20 ns, with
  zero unconstrained clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the bounded Type 25 MR-saturation slice
  passes. It uses 144 ALMs, exactly 92 design registers, no RAM, and no DSPs.
  Across four timing models, worst setup slack is +11.443 ns and worst hold
  slack is +0.246 ns against the 20 ns virtual I/O constraint, with zero
  unconstrained clocks, ports, or paths. Quartus reports
  `internal_conflict_o` as constant low; the bounded exclusive execution mux
  makes that signal an asserted invariant rather than an untested output.
- Quartus 17.0.2 full compilation of the bounded Type 18 mode-control slice
  passes. It uses 46 ALMs, 30 combinational ALUTs, exactly four MSTAT
  registers, no RAM, and no DSPs. Across four timing models, worst setup slack
  is +12.168 ns and worst hold slack is +0.173 ns against the 20 ns virtual
  I/O constraint, with zero unconstrained clocks, ports, or paths. Quartus
  reports `internal_conflict_o` constant low, matching its asserted invariant.
- Quartus 17.0.2 full compilation of the bounded Type 21 address-modify slice
  passes. It uses 526 ALMs, 543 design combinational ALUTs, exactly 360
  architectural data/valid registers plus fourteen fitter-created routing
  duplicates, no RAM, and no DSPs. Across four timing models, worst setup
  slack is +2.361 ns and worst hold slack is +0.185 ns against the 20 ns
  constraint, with zero unconstrained clocks, ports, or paths. Constant-low
  conflict and PM/DM data-access outputs are asserted properties of this
  bounded instruction.
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
  passes. Its virtual-pin fit uses 228 ALMs, 228 combinational ALUTs, one DSP
  block, 0 registers, and 0 RAM blocks. Across the four fitted timing models,
  worst setup slack is 3.209 ns and worst hold slack is 0.418 ns against the
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
- Quartus full compilation of the separately constrained stateful CNTR smoke
  project passes. Its virtual-pin fit uses 72 ALMs, 49 combinational ALUTs,
  exactly 15 architectural registers plus seven fitter-created routing
  duplicates, no RAM, and no DSPs. Its virtual internal controls use the
  documented 5 ns registered-source assumption. Across four timing models,
  worst setup is +11.818 ns and worst hold is +0.171 ns against 20 ns, with
  zero unconstrained paths.
- Quartus full compilation of the bounded sequencer-integration project
  passes. It uses 388 ALMs, 383 fitted combinational ALUTs, exactly 381 design
  registers plus fourteen fitter-created routing duplicates, no RAM, and no
  DSPs. The 381 design registers are exactly the 366 PC/count/loop-stack bits
  plus the 15 CNTR data/valid bits. Across four timing models, worst setup is
  +6.776 ns and worst hold is +0.166 ns against 20 ns, with zero unconstrained
  clocks, ports, or paths.
- Quartus full compilation of the register-file smoke project passes with the
  DE10-Nano 50 MHz input constrained on `PIN_V11` and 356 virtual data/control
  pins. Analysis identifies exactly 554 design registers; deterministic
  Standard Fit seed 2 adds 55 secondary routing-optimization duplicates. The
  fit uses 1,084 ALMs, 1,353 combinational ALUTs, no RAM, and no DSPs. Across
  the four timing models, worst setup slack is 9.985 ns and worst hold slack is
  0.109 ns against the 20 ns constraint, with zero unconstrained clocks, ports,
  or paths.
- Quartus Lite emits its recurring unavailable-LogicLock warning; none of the
  projects uses LogicLock.
- Quartus full compilation of the status/control smoke project passes. It uses
  84 ALMs, 41 combinational ALUTs, exactly 21 architectural registers with no
  fitter-created register duplicates, no RAM, and no DSPs. Its virtual internal
  controls have an explicit 5 ns same-clock registered-source input-arrival
  assumption. Across four timing models, worst setup is +11.811 ns and worst
  hold is +0.169 ns against 20 ns, with zero unconstrained paths.
- Quartus full compilation of the status-stack smoke project passes. It uses 53
  ALMs, 30 combinational logic ALUTs, exactly 68 design registers plus one
  fitter-created routing duplicate, no RAM, and no DSPs. Its virtual internal
  controls use the same documented 5 ns registered-source assumption. Across
  four timing models, worst setup is +13.077 ns and worst hold is +0.172 ns
  against 20 ns, with zero unconstrained paths.
- Quartus full compilation of the PC/count/loop stack-storage smoke project
  passes. It uses 245 ALMs, 177 combinational logic ALUTs, exactly 366 design
  registers plus six fitter-created routing duplicates, no RAM, and no DSPs.
  Its virtual internal controls use the documented 5 ns registered-source
  assumption. Across four timing models, worst setup is +10.383 ns and worst
  hold is +0.162 ns against 20 ns, with zero unconstrained paths. Quartus
  reports the asynchronous-read arrays as intentionally uninferred RAM and
  flags constant SSTAT fragment bits 4/5; those bits belong to the separate
  status-stack slice.
- Quartus full compilation of the bounded MSTAT-consumer integration project
  passes. It uses 543 ALMs, 578 combinational ALUTs, 492 design implementation
  registers plus two fitter-created routing duplicates, no RAM, and no DSPs.
  The retained state comprises 480 observable DREG bits plus ASTAT/MSTAT; this
  top intentionally does not expose the other feedback/control registers.
  Across four timing models, worst setup is +5.529 ns and worst hold is
  +0.168 ns against 20 ns, with zero unconstrained paths.
- SymbiYosys and Yosys are not installed. `make formal` strictly lints the 34
  available assertion harnesses before reporting that proof execution is
  skipped.

There is no whole-core utilization, latch-count, Fmax, critical-path, or
timing-closure claim. `make synth-yosys` reports an explicit tool-availability
skip; `make synth-quartus` runs the bounded class-decode,
internal-move-decode, stack-control-decode, stack-control-integration,
Type-6 integration,
Type-8 integration,
Type-9 integration,
Type-14 integration,
Type-15 integration,
Type-16 integration,
Type-18 integration,
Type-19 integration,
Type-20 integration,
Type-21 integration, Type-25 integration,
condition, ALU, MAC, shifter, DAG, sequencer-flow, CNTR, sequencer-stack,
sequencer-integration, register-file, status-register, and status-stack block
smoke projects plus the bounded MSTAT integration project.
