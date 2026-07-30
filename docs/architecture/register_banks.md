# Computational register banks

**Status: bank membership and storage/writeback slice implemented**

MSTAT bit 0 selects primary (`0`) or secondary (`1`) computational registers.
The banked set is AX0/1, AY0/1, AF, AR, MX0/1, MY0/1, MF, MR2/1/0, SI, SE, SB,
SR1, and SR0 [ADI-UM-1989, printed p. 4-22].

I/M/L, PX, sequencer stacks, ASTAT, SSTAT, MSTAT, ICNTL, and IMASK are not
listed in that banked set. An interrupt does not automatically switch banks;
software must execute mode control when it wants fast context switching
[ADI-UM-1989, printed p. 4-8].

The sixteen Appendix A DREG codes cover AX0/1, MX0/1, AY0/1, MY0/1, SI, SE,
AR, MR0/1/2, and SR0/1 [ADI-UM-1989, printed p. A-9, scan PDF p. 148]. SE and
MR2 physically store eight bits and sign-extend when read on a 16-bit bus
[ADI-UM-1989, printed pp. 2-15, 2-21]. A DMD preload of MR1 also writes every
MR2 bit with MR1's sign; software must write MR2 after MR1 when another upper
byte is required [ADI-UM-1989, printed p. 2-18].

Computational registers are sampled at cycle start and committed at cycle end.
A simultaneous computation therefore consumes the old operand while a data
move supplies the following cycle's operand [ADI-UM-1989, printed p. 2-15 and
pp. 6-4–6-6]. Reset clears MSTAT and thereby selects the primary bank, but the
reset list does not initialize either computational bank
[ADI-UM-1989, printed p. 5-13].

## Implemented boundary

`rtl/core/adsp2100_register_file.sv` stores both banks for all sixteen DREG
codes plus AF, MF, and SB. Each bank contains fourteen 16-bit DREG stores, two
exact eight-bit DREG stores, two 16-bit feedback stores, and one exact five-bit
SB store: 277 bits per bank and 554 architectural bits total. It has
deliberately no reset port or initialization construct. The independent model
retains unknowns separately for MR0/MR1/MR2 and SR0/SR1, so one segment can
become known without silently initializing its neighbors.

Three write inputs are an integration interface, not a claim that every
three-write combination is a legal instruction. Unit-specific inputs write an
ALU result atomically to AR or AF, a full 40-bit MAC result to MR or its middle
word to MF, and one shifter result to SR, SE, or SB. A general MOVE to SB uses
an explicit exact five-bit storage input; upstream decode remains responsible
for narrowing the 16-bit bus value. These paths implement the manual's
start-of-cycle operand/end-of-cycle result rule
[ADI-UM-1989, printed pp. 2-5–2-7, 2-13–2-18, 2-21–2-23].

`write_conflict_o` detects same-storage writes, the implicit MR1/MR2
collision, multiple computational units, and multiple shifter destinations.
Any reported collision suppresses every write. This fail-closed behavior is
an implementation safeguard, not a claim about an illegal real-device
encoding; OQ-014 remains open.

Complete instruction and multifunction legality, operand/result decode
connectivity, MSTAT storage and update timing, interrupt/context interaction,
and exact same-cycle bank-switch visibility remain unimplemented. M16
therefore remains `IMPLEMENTING`.

## Objective evidence

- `tests/test_register_banks.py` has 14 directed tests covering unknown
  preservation, every DREG in both banks, inactive-bank preservation,
  old-read/new-write visibility, narrow sign extension, MR1's MR2 side
  effect, AF/MF/SB, atomic MR/SR writeback, legal parallel writes, and
  fail-closed collisions.
- `make register-tests` compares 58,307 deterministic DREG cycles and 50,120
  full-bank/writeback cycles against independent Python results. It exhausts
  all 4,096 three-read address combinations in each bank, adds boundary and
  seeded-random legal writes, clocks collision cases, and verifies that the
  next cycle sees unchanged state.
- `formal/registers.sby` states exact collision detection, conflict-state
  preservation, narrow-extension, MR consistency, and every unit-specific
  writeback property. The harness passes assertion lint; proof execution
  remains unavailable until SymbiYosys is installed.
- Quartus 17.0.2 fits exactly 554 design registers in the Cyclone V smoke
  project. Seed 2 closes the fully constrained 20 ns multicorner check at
  +9.985 ns worst setup and +0.109 ns worst hold slack.
