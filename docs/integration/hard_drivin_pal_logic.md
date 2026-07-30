# Hard Drivin' PAL/GAL logic register

**Status: equations not acquired**

The schematic and service packages show board decoding context, but no
source-level PAL/GAL equations have been verified in the first acquisition
pass [ATARI-ADSP-SCHEM; ATARI-HD-SERVICE]. Jed Margolin's page mentions a
collection of GAL files, but applicability to a particular ADSP/ADSP II board
and redistribution status have not been established [ATARI-MARGOLIN, GAL-files
section].

No PAL behavior will be reconstructed solely by copying MAME address handlers.
For each programmable-logic device the research record must eventually include:

- board reference designator and marking;
- board and schematic revision;
- input/output net names and polarity;
- acquired equation or fuse-map provenance and checksum;
- legal redistribution status;
- truth-table comparison to schematic connectivity and observed software
  accesses.

Until then, host address mirrors, set/clear decoding, memory enables, bus
arbitration glue, and bank-select decode are `PROVISIONAL`.
