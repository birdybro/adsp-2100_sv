# Computational register banks

**Status: bank membership verified**

MSTAT bit 0 selects primary (`0`) or secondary (`1`) computational registers.
The banked set is AX0/1, AY0/1, AF, AR, MX0/1, MY0/1, MF, MR2/1/0, SI, SE, SB,
SR1, and SR0 [ADI-UM-1989, printed p. 4-22].

I/M/L, PX, sequencer stacks, ASTAT, SSTAT, MSTAT, ICNTL, and IMASK are not
listed in that banked set. An interrupt does not automatically switch banks;
software must execute mode control when it wants fast context switching
[ADI-UM-1989, printed p. 4-8].

Tests must cover switch visibility, inactive-bank preservation, same-cycle mode
change ordering, computation/move overlap, and interrupt entry/return without
an implicit switch.
