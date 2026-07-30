# ADSP-2100 versus ADSP-21xx feature matrix

**Status: partial source-backed audit. `UNKNOWN` is not “absent.”**

The 1995 family manual's Table 1.1 begins with ADSP-2101 and does not include
the original ADSP-2100. Its integrated-memory and peripheral rows must not be
back-projected onto the original [ADI-UM-FAMILY-1995, printed Table 1.1,
pp. 1-1–1-3].

## Device resources

| Feature | ADSP-2100 | 2101 | 2103 | 2104 | 2105 | 2115 | 2111 | 2171/2173 | 2181/2183 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PM word / DM word | 24 / 16 | 24 / 16 core | same core | same core | same core | same core | same core | same core | same core |
| On-chip PM | none | 2K | 2K | 512 | 1K | 1K | 2K | 2K | 16K |
| On-chip DM | none | 1K | 1K | 256 | 512 | 512 | 1K | 2K | 16K |
| Timer | none | yes | yes | yes | yes | yes | yes | yes | yes |
| SPORT0 / SPORT1 | none | yes / yes | yes / yes | yes / yes | no / yes | yes / yes | yes / yes | yes / yes | yes / yes |
| HIP | none | no | no | no | no | no | yes | yes | no |
| DMA ports | none | no | no | no | no | no | no | no | yes |
| Nominal supply in table | 5 V | 5 V | 3.3 V | 5 V | 5 V | 5 V | 5 V | 5/3.3 V variants | 5/3.3 V variants |

Original-device cells are from the complete original architecture/pin overview
[ADI-UM-1989, printed pp. 1-1–1-7, 5-17–5-20]. 2101/2103/2105/2115/2111
and 217x/218x resource cells are from Table 1.1
[ADI-UM-FAMILY-1995, printed p. 1-2]. ADSP-2104 cells are from its official
device-specific data sheet [ADI-2104-DS-REV0, printed p. 1].

## Architectural and system differences

| Topic | Original ADSP-2100 | 2101/2103/2104/2105/2115 | 2111 | 217x | 218x |
|---|---|---|---|---|---|
| External memory | Separate PMA/PMD and DMA/DMD interfaces | Later multiplexed external address/data interface plus internal memories | Same later class plus HIP | Later system interface; device audit incomplete | Large internal memory, overlays and DMA; device audit incomplete |
| Instruction cache | 16 × 24, required for PM-data/fetch conflict | Applicability and organization to audit per device | audit | audit | audit |
| Boot | none documented | byte-wide boot for integrated PM | boot plus HIP options to audit | audit | BDMA/IDMA boot paths |
| External IRQ pins | four, IRQ0–IRQ3 | three claimed by later data sheets; exact vectors/internal sources per device to audit | audit | audit | audit |
| HALT/TRAP | dedicated input/output behavior | later IDLE/flag facilities are not equivalent; exact pins per device to audit | audit | audit | audit |
| Bus arbitration | BR/BG halts after current instruction and tristates both full interfaces | later parts may continue from internal memory; exact GO-mode behavior to audit | audit | audit | audit |
| DM wait | asynchronous DMACK extends state 7 | programmed per-space waits on later integrated parts | audit | audit | audit |
| Circular buffer, exact power-of-two L | base clears one more low bit; L=8 requires base multiple 16 | base uses ordinary power-of-two alignment; L=8 may start at a multiple of 8 | same later rule | same later rule | same later rule |
| Package | 100-pin PGA; contemporary ordering also lists 100-lead PLCC | smaller PLCC/PQFP variants by device | audit | audit | audit |

Original bus, cache, interrupt, reset, and wait behavior:
[ADI-UM-1989, printed pp. 4-26, 5-3–5-20]. The later-family manual says its
off-chip buses are multiplexed and that processors can continue while buses are
granted if no external access is required [ADI-UM-FAMILY-1995, printed p. 1-3],
which directly differs from original BR/BG behavior
[ADI-UM-1989, printed pp. 5-3–5-5].

The exact-power-of-two circular-buffer row is an explicitly documented
original-device difference [ADI-ASM-1994, section 3.7.2.2, printed
pp. 3-29–3-32]. It also agrees with the original manual's L=8 example
[ADI-UM-1989, printed pp. 3-3–3-4]. See SC-010.

## Instruction, register, and arithmetic evolution

- The original opcode appendix defines 30 top-level types, including an output
  TRAP instruction and three reserved classes [ADI-UM-1989, printed
  pp. A-1–A-4].
- The 1995 unified reference includes later facilities such as IDLE, I/O-space
  access, programmable flags, timer and multiplier modes, and additional bit
  operations [ADI-UM-FAMILY-1995, printed pp. 15-1, 15-16–15-17]. None is
  admitted to the original database without an original opcode entry.
- The original MSTAT is four bits: register bank, DAG1 bit reverse, AV latch,
  and AR saturation [ADI-UM-1989, printed pp. 4-22–4-23]. Later mode names in
  the unified table are not original-register fields.
- The later family manual explicitly notes original-only multiplier behavior:
  the ADSP-2100 always applies the fractional left shift, whereas later parts
  have integer/fractional mode selection [ADI-UM-FAMILY-1995, Appendix A
  “Multiplication Modes,” printed section near pp. A-8–A-9; page extraction
  needs final indexing].

## Items still required for DEV-002 acceptance

Exact per-device opcode deltas, vector maps, stack depths, loop edge cases,
status fields, package/pin tables, overlays, boot choices, and bus controls need
device-specific pages. Until then the later-device cells above are comparative
guardrails, not a completed parameterization specification.
