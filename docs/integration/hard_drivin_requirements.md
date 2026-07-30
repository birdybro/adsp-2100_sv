# Hard Drivin' integration requirements

The Atari board is a qualification target around—not a configuration of—the
generic original ADSP-2100 core.

## Generic-core requirements

- original 24-bit program and 16-bit data semantics;
- distinct concurrent PM and DM transactions;
- authentic eight-state logical cycle representation;
- documented `RESET`, `HALT`, `BR/BG`, IRQ, wait, and restart timing;
- optional trace of phase, PC, PM/DM activity, and architectural retirement.

These requirements follow the original processor sources, not MAME or the
board memory map [ADI-UM-1989, printed chapters 4, 5, and 10].

## Board-wrapper requirements

- host-loadable program and data RAM;
- verified 68000 program-word packing;
- physical `BR/BG`, halt, and reset control behavior;
- SIM address load, stream read, bank selection, and wrapping;
- SOM address load, stream write, dual-bank handoff, and wrapping;
- host/DSP interrupt latches and X flag;
- board-derived memory decoding and wait states;
- no copyrighted ROM content in source or CI.

The schematic sheet inventory is [ATARI-ADSP-SCHEM, PDF pp. 6–18]. MAME's
pinned board maps and handlers are useful comparison points
[MAME-HARDDRIV; MAME-HARDDRIV-MACHINE, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`] but are never the sole
implementation specification.

## Evidence gates

“Hard Drivin'-ready” remains prohibited until synthetic host-loading,
arbitration, SIM/SOM, signaling, and geometry tests pass; authorized local ROMs
reach the command loop and reproduce a known result; MAME traces are compared;
and the MiSTer Quartus build closes timing. Current status satisfies none of
those completion gates.
