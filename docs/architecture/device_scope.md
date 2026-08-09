# Original-device scope

**Status: research baseline, not implementation completion**

The scoped processor is the external-memory Analog Devices ADSP-2100 described
by the 1989 fourth-edition original-device manual. It is a 16-bit fixed-point
processor whose program statements occupy 24-bit words
[ADI-UM-1989, printed pp. 1-1–1-2, 2-1]. Its external architecture has:

- a 14-bit PM address bus and 24-bit PM data bus;
- a 14-bit DM address bus and 16-bit DM data bus;
- PM data-versus-instruction indication through PMDA;
- a 16-word instruction cache used when PM data access conflicts with the next
  instruction fetch;
- four external IRQ inputs, RESET, HALT, output TRAP, and BR/BG;
- a DMACK input that extends data-memory cycles.

[ADI-UM-1989, printed pp. 1-5–1-7, 4-26, 5-3–5-17; ADI-DATABOOK-1987,
printed pp. 2-15–2-17.]

The original core has no on-chip program/data memory or documented integrated
SPORT, timer, HIP, DMA, boot-memory, or overlay block in its complete system
overview and pin description [ADI-UM-1989, printed pp. 1-1–1-7, 5-17–5-20].
This is an original-device absence claim; it must not be replaced by later
family functional diagrams.

## ADSP-2100A boundary

The acquired joint data sheet explicitly calls the ADSP-2100 and ADSP-2100A
pin- and code-compatible, says that they have identical documented
architectures and instruction sets, and applies every unqualified ADSP-2100
description in that data sheet to both. It separately assigns the original
ADSP-2100 6.144/8.192 MHz grades and the ADSP-2100A 10.24/12.5 MHz grades and
states that timing and electrical specifications differ
[ADI-DATABOOK-1989, ADSP-2100/ADSP-2100A data sheet, printed p. 2-19,
scan PDF p. 27].

This closes the published architectural/instruction-set boundary, not the
mask-history boundary. No acquired original errata or mask records establish
whether undocumented behavior, reset signatures, or silicon fixes differ.
The current default therefore remains the original ADSP-2100, while an
ADSP-2100A statement may support architectural behavior only when it falls
within the joint data sheet's explicit compatibility scope. The later
assembler's `ADSP-2100A` alias is not independent electrical evidence
[ADI-ASM-1994, printed p. 1-11].

## Hard Drivin' identity

Original Atari engineer commentary identifies the first ADSP board as using a
PGA ADSP-2100 and ADSP II as using a PQFP ADSP-2100; it describes them as
electrically and mechanically equivalent [ATARI-MARGOLIN, “ADSP Board”
section]. The schematic CPU sheet shows a 100-pin ADSP2100 symbol and a 32 MHz
oscillator at CLKIN [ATARI-ADSP-SCHEM, drawing A044421, sheet 3 left, PDF p. 6].
The board therefore targets an 8 MHz instruction rate by the documented
divide-by-four clock relationship [ADI-UM-1989, printed p. 5-2].

## Excluded by default

All memory-integrated descendants and their peripherals are excluded. The
ADSP-2104, for example, is a 1996 low-cost device with 512 words PM RAM,
256 words DM RAM, timer, and two SPORTs; it is not an original-device variant
[ADI-2104-DS-REV0, printed p. 1].

## Unresolved

- exact 2100-to-2100A mask fixes, errata, and electrical limits by grade;
- mask revisions and errata;
- whether later packages used on ADSP II were marked 2100 or 2100A;
- authentic power-up state of every computational/DAG register;
- any undocumented response to reserved encodings or stack faults.
