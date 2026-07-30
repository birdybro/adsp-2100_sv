# Hard Drivin' board interrupts and flags

**Status: MAME behavior documented; physical nets not yet closed**

MAME models DSP special write subaddress 5 as the one-bit `X` output and
subaddress 6 as an ADSP-to-68000 interrupt latch set operation
[MAME-HARDDRIV-MACHINE, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 819–827]. The 68000 clears
the interrupt through a separate write window and reads a status word in which
the X and IRQ latches affect bits 1 and 0 [MAME-HARDDRIV-MACHINE, same commit,
lines 751–765].

A 68000 write to ADSP data RAM address `0x1fff` causes MAME to synchronize CPUs
and issue an emulator-specific interrupt trigger [MAME-HARDDRIV-MACHINE, same
commit, lines 585–603]. This is not yet proven to be a physical ADSP IRQ edge;
it may stand in for board signaling or a scheduler speedup.

Required closure work:

- trace `/GINT`, `/XOUT`, host interrupt, and host-to-DSP nets on the Atari
  processor/control and main-board sheets;
- determine latch polarity and reset state;
- identify the exact ADSP IRQ input and recognition timing;
- distinguish physical signaling from MAME's `signal_interrupt_trigger()`
  scheduling mechanism.
