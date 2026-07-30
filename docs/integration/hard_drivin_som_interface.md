# Hard Drivin' sequential output memory (SOM)

**Status: dual-bank behavior corroborated; switching timing unresolved**

The Atari package has four sequential-output sheets covering two banks
[ATARI-ADSP-SCHEM, PDF pp. 15–18]. MAME represents two banks of `0x2000`
16-bit words:

- DSP special subaddress 2 writes the bank opposite the host-selected bank and
  post-increments a 13-bit-wrapped SOM address;
- DSP special subaddress 3 loads the SOM address;
- the host reads or writes its selected bank;
- the host bank change is deferred to a scheduler synchronization point.

Source: [MAME-HARDDRIV-MACHINE, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 614–624, 634–681, and
803–817].

The opposite-bank rule is a useful implementation hypothesis. Physical
switching edge, address-counter width, counter load semantics, collision
behavior, and whether the host can safely write the displayed bank require
schematic and software-trace confirmation.
