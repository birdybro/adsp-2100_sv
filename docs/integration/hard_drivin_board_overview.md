# Hard Drivin' ADSP board overview

**Status: first-pass board identification; implementation is not authorized by
this document alone**

## Confirmed identity

Hard Drivin' uses the original ADSP-2100 for graphics mathematics. The ADSP
board uses the PGA package; ADSP II uses the PQFP package. Jed Margolin, an
original Atari engineer, describes the two as electrically and mechanically
equivalent [ATARI-MARGOLIN, “ADSP Board” section]. The Atari schematic scan
contains both the PGA processor sheet and a separate PQFP pin-location sheet
[ATARI-ADSP-SCHEM, PDF pp. 6 and 19].

The processor sheet shows a 32 MHz oscillator driving `CLKIN`
[ATARI-ADSP-SCHEM, PDF p. 6, “ADSP” processor sheet]. The original processor
uses four input-clock periods per instruction cycle, so this is consistent with
an 8 MHz instruction rate [ADI-UM-1989, printed pp. 10-3–10-4]. MAME models the
board as an ADSP-2100 at `32 MHz / 4`; that is corroboration, not proof
[MAME-HARDDRIV, commit `030fefcbd14e47c01ec9d67655be90f64a1dc8ab`,
lines 1594–1600].

## Board resources

The schematic package separately identifies:

- processor and control logic [ATARI-ADSP-SCHEM, PDF pp. 6–7];
- data memory [ATARI-ADSP-SCHEM, PDF pp. 8–10];
- program memory and buffers [ATARI-ADSP-SCHEM, PDF pp. 11–12];
- sequential input memory [ATARI-ADSP-SCHEM, PDF pp. 13–14];
- two banks of sequential output memory [ATARI-ADSP-SCHEM, PDF pp. 15–18].

Exact device counts, address-decode equations, and board-revision deltas remain
under net-by-net transcription. They must not be inferred from MAME's compact
memory maps.

## Variant boundary

MAME identifies early ADSP board A044420 and ADSP II A047046 and describes both
as 8 MHz ADSP-2100 boards; it separately identifies later DS III/IV boards as
ADSP-2101 systems [MAME-HARDDRIV, same commit, lines 42–70]. The DS III/IV
behavior is outside the Hard Drivin' ADSP-2100 wrapper and must not leak into
the generic core.
