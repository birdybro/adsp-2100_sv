# ADR-0002: Default scope is the original external-memory ADSP-2100

- **Status:** Accepted
- **Date:** 2026-07-30
- **Tasks:** DEV-001, DEV-002

## Context

The original ADSP-2100 uses external program and data memories with separate
14-bit address buses and 24-bit/16-bit data buses
[ADI-UM-1989, printed pp. 1-1, 1-5–1-7; ADI-DATABOOK-1987, printed
pp. 2-15–2-17]. It includes a 16-word instruction cache to cover instruction
fetches during PM data accesses [ADI-UM-1989, printed pp. 1-7, 4-26].

Later ADSP-2101-class devices integrate program/data RAM, a timer, and serial
ports, and expose a multiplexed external memory interface
[ADI-UM-FAMILY-1995, printed Table 1.1 pp. 1-2–1-3]. Those are not harmless
packaging variants.

## Decision

The generic core models the original ADSP-2100 interface and architecture.
ADSP-2100A differences remain a research item and are not silently assumed
identical. The default has:

- no on-chip program/data RAM;
- no SPORT, timer, HIP, DMA, boot memory, overlay, or later programmable-flag
  facility;
- original PM and DM interfaces, instruction cache, four external interrupt
  inputs, HALT, TRAP, BR/BG, and DMACK.

No parameter for a later member is accepted until the original device is
release-qualified. Board memories belong in wrappers.

## Consequences

MAME family classes and later assembler syntax must be filtered against the
original 1989 opcode appendix. Hard Drivin' logic stays in a separate wrapper.
The exact ADSP-2100-versus-2100A mask and package distinctions remain open.
