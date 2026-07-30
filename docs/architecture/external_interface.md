# Native external interface

**Status: pin names and logical roles verified**

| Group | Signals | Direction |
|---|---|---|
| Clock | CLKIN, CLKOUT | input, output |
| PM | PMA[13:0], PMD[23:0], PMS, PMRD, PMWR, PMDA | address/control out, data bidirectional |
| DM | DMA[13:0], DMD[15:0], DMS, DMRD, DMWR, DMACK | address/control out, data bidirectional, acknowledge in |
| Control | RESET, HALT, TRAP, BR, BG | inputs except TRAP/BG outputs |
| Interrupt | IRQ[3:0] | active-low inputs |

Source: [ADI-UM-1989, printed pp. 5-17–5-20].

The synthesizable core will express bidirectional buses as separate input,
output, and output-enable signals. That is an FPGA representation choice, not a
change in pin-level transaction semantics. Polarity follows the active-low
strobes and inputs shown in the original timing/pin tables
[ADI-UM-1989, printed pp. 5-6–5-20].

Pin-compatible electrical timing belongs in a separate I/O wrapper. The generic
core exposes phase and transaction trace signals without a generic modern bus
that would erase original PM/DM concurrency.
