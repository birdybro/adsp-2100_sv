# Register definitions

**Status: original-device map; computational-bank and status/control storage
slices implemented**

## Computational registers

The ALU's AX0/1 and AY0/1 inputs, AR result, and AF feedback are 16 bits.
The complete set is duplicated by the active register bank
[ADI-UM-1989, printed pp. 2-5–2-8].

The MAC has 16-bit MX0/1 and MY0/1 inputs, MF feedback, and a 40-bit MR
accumulator exposed as MR0, MR1, and MR2 segments. The register group is
duplicated by the active bank [ADI-UM-1989, printed pp. 2-13–2-20].

The shifter has SI input, SE exponent, SB block exponent, and a 32-bit SR
exposed as SR0/SR1; these registers are included in the duplicate bank. SE is
signed 8-bit, SB is signed 5-bit, and both reads sign-extend on DMD
[ADI-UM-1989, printed pp. 2-20–2-30, 4-22]. EXP HI/HIX/LO produces SE values
from +1 through -31 according to Table 2.5; EXPADJ produces SB values from
-15 through zero after software initializes SB to -16. Reset values remain
unverified.

The implemented computational storage boundary contains 277 bits per bank:
240 bits for the sixteen DREG-coded stores plus AF, MF, and five-bit SB.
Unit-specific ALU, MAC, and shifter writeback preserves the documented
cycle-start read and cycle-end write boundary [ADI-UM-1989, printed
pp. 2-5–2-7, 2-13–2-18, 2-21–2-23]. A bounded integration slice now connects
MSTAT bit 0 to this storage boundary. Instruction decode and complete
computational-unit connectivity are not yet integrated.

## DAG and exchange registers

Each DAG has four 14-bit I, M, and L registers. I/L read as unsigned with upper
DMD bits zero; M reads sign-extended [ADI-UM-1989, printed pp. 3-1–3-3]. PX is
8 bits and supplies/receives the low eight PMD bits during 24-bit transfers
[ADI-UM-1989, printed pp. 3-6–3-8].

## Status registers

- ASTAT[7:0] = SS, MV, AQ, AS, AC, AV, AN, AZ
  [ADI-UM-1989, printed p. 4-21].
- SSTAT[7:0] reports empty/overflow for loop, status, count, and PC stacks and
  is read-only [ADI-UM-1989, printed p. 4-22]. Reset clears all stack pointers
  and sticky overflow indications; the four empty bits are positive-sense, so
  the resulting reset status is `0x55` [ADI-UM-1989, printed pp. 4-22,
  5-13–5-14].
- MSTAT[3:0] controls AR saturation, AV latching, DAG1 bit reverse, and
  secondary bank [ADI-UM-1989, printed pp. 4-22–4-23].
- ICNTL[4:0] controls nesting and edge/level sensitivity for IRQ3–IRQ0; every
  bit is undefined after reset [ADI-UM-1989, printed p. 4-23].
- IMASK[3:0] enables IRQ3–IRQ0 and resets to zero
  [ADI-UM-1989, printed p. 4-24].

### Implemented status/control boundary

`docs/generated/adsp2100_status_registers.yaml` records the exact fields,
reset classifications, update sources, interrupt-entry masks, and MODE CONTROL
codes. ASTAT's bits are numbered AZ=0, AN=1, AV=2, AC=3, AS=4, AQ=5, MV=6,
and SS=7. Standard non-division ALU operations update AZ/AN/AV/AC; ABS
additionally updates AS; DIVS/DIVQ update AQ; every MAC operation except SAT
MR updates MV; and shifter EXP updates SS. Generated status is latched at the
end of its instruction cycle and is therefore first usable in the next cycle
[ADI-UM-1989, printed p. 4-21].

MSTAT bit 0 selects the computational register bank, bit 1 enables DAG1 bit
reversal, bit 2 enables sticky AV, and bit 3 enables AR saturation. A direct
MOVE replaces all four stored bits. MODE CONTROL has one two-bit field per
MSTAT bit in that order: `00` and `01` preserve the bit, `10` clears it, and
`11` sets it [ADI-UM-1989, printed pp. 4-22–4-23, A-8].

ICNTL bits 0 through 3 independently select level (`0`) or edge (`1`)
sensitivity for IRQ0 through IRQ3, and bit 4 enables interrupt nesting. IMASK
bits 0 through 3 independently enable those four interrupt levels. On
recognized interrupt entry, the pre-entry ASTAT, MSTAT, and IMASK values are
presented as one atomic status-stack snapshot. With nesting disabled, live
IMASK becomes `0`; with nesting enabled, IRQ0/IRQ1/IRQ2/IRQ3 entry produces
`0xE`/`0xC`/`0x8`/`0x0`, respectively. An RTI-style restore atomically replaces
ASTAT, MSTAT, and IMASK while preserving ICNTL [ADI-UM-1989, printed
pp. 4-9–4-10, 4-23–4-24].

The original reset list explicitly clears MSTAT and IMASK but does not
initialize ASTAT or ICNTL. The model consequently returns every ASTAT bit and
the ICNTL value to `UNKNOWN` on reset, and synthesizable RTL deliberately has
no reset assignments for those registers. MSTAT and IMASK use a synchronous
architectural reset input at this block boundary; exact asynchronous pin
sampling and eight-phase reset release remain a future sequencer/bus-control
responsibility [ADI-UM-1989, printed p. 5-13].

`sim/reference_models/adsp2100_model/status.py` and
`rtl/core/adsp2100_status_registers.sv` implement this state transition. The
four MSTAT outputs are connected in
`sim/reference_models/adsp2100_model/mode_slice.py` and
`rtl/core/adsp2100_mode_slice.sv`: bit 0 selects the computational bank, bit 1
controls DAG1 bit reversal, bit 2 controls sticky AV, and bit 3 controls AR
saturation. Computation/register operands are read at cycle start and results
are written at cycle end, so the integration boundary uses the current stored
MSTAT value throughout a cycle and exposes a direct MOVE or MODE CONTROL
change to consumers on the following cycle [ADI-UM-1989, printed pp. 2-6–2-7,
2-9, 3-5, 4-22–4-23]. This closes ordinary cycle-to-cycle visibility only;
interrupt-adjacent selection remains OQ-015 and whole-instruction decode does
not exist.

Interrupt entry has priority over ordinary cycle-end writes because the
interrupted instruction is aborted. The status block exposes the status-stack
payload but intentionally does not own stack storage or instruction
sequencing. A same-cycle direct and automatic ASTAT write, multiple
computational status writers, a direct MSTAT write with an active MODE CONTROL
field, or a restore colliding with another state-changing action raises
`write_conflict_o` and suppresses all writes. That is a fail-closed
implementation safeguard, not a claim about an illegal real-device encoding;
OQ-017 tracks the evidence gap.

This boundary exposes exact eight-bit ASTAT, four-bit MSTAT, five-bit ICNTL,
and four-bit IMASK storage. A separate four-by-sixteen status stack now
provides the SSTAT status-empty and status-overflow sources with documented
pointer saturation and sticky overflow behavior [ADI-DATABOOK-1987, printed
pp. 2-21–2-22; ADI-UM-1989, printed p. 4-22]. How unused upper DMD bits read
for the narrow general-MOVE sources remains open as OQ-016. PC/count/loop
stack-derived SSTAT dynamics, interrupt recognition timing, DIVS/DIVQ
execution, and instruction decode are not part of this increment.

## Accessibility

AF, MF, and PC are not in the general MOVE register set in the original
instruction overview [ADI-UM-1989, printed p. 6-12 and Appendix A register
coding]. Exact source/destination field values will be generated only after
hand review of Appendix A scan images.
