# Hard Drivin' host interface

**Status: behavioral discovery; schematic timing incomplete**

MAME exposes host access to ADSP program RAM, data RAM, and the selected
sequential-output bank [MAME-HARDDRIV, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 4817–4835]. Its board
handlers model byte-mask-aware program/data writes and two-bank SOM access
[MAME-HARDDRIV-MACHINE, same commit, lines 549–624].

MAME decodes each control operation from address bits rather than write data:
address-derived value bit 3 selects set/clear and low bits select LED, output
bank, `/BR`, `/HALT`, or reset functions [MAME-HARDDRIV-MACHINE, same commit,
lines 685–747]. This is a strong clue for set/clear latch hardware but remains
`CORROBORATED`, not schematic-verified.

The portable processor must retain its native `BR`, `BG`, `HALT`, and `RESET`
timing. The board wrapper may decode the 68000 controls only after:

1. corresponding schematic latch and PAL nets are traced;
2. active levels are confirmed;
3. host ownership of PM/DM buses is related to physical `BR/BG`;
4. asynchronous host writes are synchronized in the eventual FPGA clock
   domain.

MAME treats either asserted board `/BR` or `/HALT` as an emulator halt request
[MAME-HARDDRIV-MACHINE, same commit, lines 704–735]. That abstraction is not
evidence that the physical signals have identical bus effects.
