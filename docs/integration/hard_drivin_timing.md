# Hard Drivin' board timing

**Status: clock established; memory and arbitration timing open**

The board oscillator is 32 MHz at ADSP `CLKIN` [ATARI-ADSP-SCHEM, PDF p. 6].
The original ADSP-2100 instruction cycle is four `CLKIN` periods
[ADI-UM-1989, printed pp. 10-3–10-4], yielding an 8 MHz nominal instruction
cycle. MAME independently configures the part at `32 MHz / 4`
[MAME-HARDDRIV, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 1594–1600].

No board-level timing claim is complete yet for:

- PM/DM SRAM access and write pulse width;
- host-to-ADSP bus turnaround;
- `/BR` assertion to `BG`;
- host access while the DSP is halted;
- SIM/SOM address-load and stream clocks;
- output-bank handoff;
- interrupt latch and acknowledge latency.

The wrapper must express these as clock enables and explicit states. MAME's
scheduler synchronization and CPU halt calls are behavioral conveniences and
must not determine hardware phase timing.
