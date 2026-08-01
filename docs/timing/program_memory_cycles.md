# Program-memory cycles

**Status: source-backed eight-state logical pin phases implemented in a
bounded controller; architectural request attachment pending**

For a PM read, the processor drives PMA and PMDA, asserts PMS, then asserts
active-low PMRD; memory supplies PMD; the processor samples data and releases
PMRD [ADI-UM-1989, printed p. 5-7, Figure 5.5 p. 5-8].

For a PM write, the processor drives PMA/PMDA, asserts PMS, drives PMD, asserts
PMWR, then releases PMWR after its fixed interval
[ADI-UM-1989, printed pp. 5-7–5-8]. PMS normally remains asserted across
successive program accesses and is inactive only during halt/trap/bus grant
[ADI-UM-1989, printed p. 5-6].

Original PM has no DMACK-equivalent documented in this interface. The bounded
Type 13 slice therefore completes a PM-data transfer in one fixed logical
processor cycle. It exposes PM select, data-versus-instruction classification,
read/write direction, 14-bit address, and 24-bit write data. The composed cache
boundary derives the next-instruction decision from its pre-cycle 16-word
monitor: a valid hit supplies the actual cached word with no external fetch;
a miss schedules one fixed instruction-read recovery cycle and uses that
cycle's returned word to fill the monitor. Ordinary external instruction
completions populate the same monitor when Type 13 does not own PM
[ADI-UM-1989, printed pp. 4-26–4-30, 5-5–5-8]. The Type 13 slice itself ends at
this logical request boundary; the separately verified pin-phase controller
below is not yet attached to it.

## Eight-state logical pin boundary

The independently modeled and portable `adsp2100_program_bus` controller now
implements the exact edge-to-state mapping below. Its implementation API
captures a request on an enabled state-8-to-state-1 edge, aligned with the
sourced output-change edge; this is not a claim about a hidden device latch.
PMA, PMDA, and active-low PMS then remain
valid throughout states 1–8; a back-to-back request replaces the descriptor at
the next 8-to-1 edge without deasserting PMS. With no following request, the
interface becomes inactive after that edge.

| Signal/action | Logical states or edge |
|---|---|
| PMA, PMDA, PMS valid | states 1–8 |
| PMRD low for fetch/read | states 4–7 |
| PMWR low for write | states 4–7 |
| PMD read sample | enabled state-7-to-state-8 edge |
| PMD write output enable | states 5–8 |

This transcription follows the original state-edge timing parameters: PMA,
PMDA, and PMS relative to CLKIN high (8–1); PMRD/PMWR relative to CLKIN low
(3–4 and 7–8); PMD input sampling at low (7–8); and PMD output enable/disable
relative to high (4–5 and 8–1) [ADI-DATABOOK-1987, ADSP-2100 data sheet,
printed pp. 2-36–2-39, parameters 23–60, Figures 14–15; ADI-UM-1989, printed
pp. 5-6–5-8, Figure 5.5]. Ten directed model tests and 50,032 deterministic
model/RTL clocks cover reads, writes, instruction/data selection, state-7
holds, back-to-back PMS continuity, unknown validity, reset, and bus-output
masking.

The controller exposes separate address, control, and PMD output enables so an
FPGA wrapper can implement bidirectional pins. A separate arbiter's
`bus_relinquished` input masks all three enables while preserving descriptor
state, matching the sourced external-bus release effect but not implementing
BR/BG recognition timing [ADI-UM-1989, printed p. 5-5]. Nanosecond delays,
electrical setup/hold requirements, Type 13/cache request attachment, fetch/PC
ownership, HALT/TRAP behavior, and BR/BG arbitration remain outside this
bounded controller.
