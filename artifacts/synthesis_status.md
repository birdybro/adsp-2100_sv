# Synthesis status

**Updated:** 2026-07-30

- Verilator 5.048 parses and lints `rtl/packages/adsp2100_pkg.sv` and generated
  `rtl/packages/adsp2100_decode_pkg.sv` with `-Wall` and no warnings.
- Yosys is not installed in this environment.
- Quartus 17.0.2 is installed, but there is no architectural RTL top, project,
  target-device selection, or SDC yet.
- SymbiYosys is not installed.

There is no utilization, latch count, Fmax, critical-path, or timing-closure
claim. `make synth-yosys`, `make synth-quartus`, and `make formal` report
explicit skips until meaningful tops/harnesses exist.
