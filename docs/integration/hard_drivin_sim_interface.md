# Hard Drivin' sequential input memory (SIM)

**Status: interface behavior corroborated by MAME; net timing unverified**

The Atari schematic package contains two “sequential input memory” sheets
[ATARI-ADSP-SCHEM, PDF pp. 13–14]. A net-level table of RAM/ROM types, shift
clocks, counters, reset/load controls, and word ordering has not yet been
completed.

MAME models DSP data-space special accesses as follows:

- special subaddress 0 reads one SIM word and post-increments the SIM address;
- special subaddress 1 writes the SIM address;
- special subaddress 7 selects a `0x10000`-word EPROM bank.

Source: [MAME-HARDDRIV-MACHINE, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 776–831].

MAME's comments alternate between signal labels (`/SIMBUF`, `/SIMLD`) and
functional labels (`/SIMCLK`). These comments are not authoritative pin names.
Until schematic nets are traced, increment order, wrap width, out-of-range
data, bank granularity, and access-cycle wait behavior remain provisional.
