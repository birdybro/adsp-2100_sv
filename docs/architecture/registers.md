# Register definitions

**Status: initial original-device map**

## Computational registers

The ALU's AX0/1 and AY0/1 inputs, AR result, and AF feedback are 16 bits.
The complete set is duplicated by the active register bank
[ADI-UM-1989, printed pp. 2-5–2-8].

The MAC has 16-bit MX0/1 and MY0/1 inputs, MF feedback, and a 40-bit MR
accumulator exposed as MR0, MR1, and MR2 segments. The register group is
duplicated by the active bank [ADI-UM-1989, printed pp. 2-13–2-20].

The shifter has SI input, SE exponent, SB block exponent, and a 32-bit SR exposed
as SR0/SR1; these registers are included in the duplicate bank
[ADI-UM-1989, printed pp. 2-20–2-30, 4-22]. Exact SE and SB implemented widths
and sign-extension rules remain to be transcribed from the shifter diagrams.

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

## Accessibility

AF, MF, and PC are not in the general MOVE register set in the original
instruction overview [ADI-UM-1989, printed p. 6-12 and Appendix A register
coding]. Exact source/destination field values will be generated only after
hand review of Appendix A scan images.
