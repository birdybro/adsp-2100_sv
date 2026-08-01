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

The bounded Type 2 and Type 12 paths currently expose a logical active-high DM
select/read/write request, 14-bit address, 16-bit write data, validity, and
DMACK completion. Address/control/write data remain stable through arbitrary
wait extensions, and no architectural destination changes before completion.
This is traceable transaction-level behavior. A separate native controller now
maps captured descriptors to active-low DMS/DMRD/DMWR, shared-DMD output
enable, DMACK qualification, and full-cycle state-seven extension. The clients
are not yet attached to that controller [ADI-UM-1989, printed pp. 5-9–5-12;
ADI-DATABOOK-1987, printed pp. 2-40–2-43].

The bounded Type 13 path exposes distinct logical active-high PM data and
recovery-fetch cycles. Its connected 16-word cache supplies the actual next
instruction on a pre-cycle hit and captures each recovery word on a miss; an
explicit ordinary-fetch-completion input populates the same monitor outside
Type 13 ownership. A bounded wrapper now connects this owner to the sourced
active-low PMS/PMDA/PMRD/PMWR phases, but it is not a unified
PC/branch/interrupt bus owner
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8].

A separate native PM controller now converts a captured fetch/read/write
descriptor into the source-defined logical pin phases: PMA/PMDA/PMS through
states 1–8, active-low PMRD or PMWR through states 4–7, read sampling on the
7-to-8 edge, and write-data drive through states 5–8. It preserves active-low
PMS across back-to-back requests and exposes independent address, control, and
PMD output enables for bus relinquishment. Ten directed tests and 50,032
model/RTL clocks pass [ADI-DATABOOK-1987, ADSP-2100 data sheet, printed
pp. 2-36–2-39, parameters 23–60, Figures 14–15; ADI-UM-1989, printed
pp. 5-5–5-8, Figure 5.5]. Its bounded Type 13/cache client captures a data
descriptor at state 8-to-1, commits the architectural data action at state
7-to-8, and accepts a miss recovery back-to-back. Five directed tests and
50,081 model/RTL clocks cover the attachment. Ordinary fetch, other PM
instruction classes, and BR/BG recognition remain unattached.

Pin-compatible electrical timing belongs in a separate I/O wrapper. The generic
core exposes phase and transaction trace signals without a generic modern bus
that would erase original PM/DM concurrency.
