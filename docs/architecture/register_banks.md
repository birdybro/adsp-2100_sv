# Computational register banks

**Status: bank membership verified; DREG storage slice implemented**

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
codes, with three combinational reads and three cycle-end write inputs. Its
14 full-width registers plus two exact eight-bit registers per bank total 480
architectural storage bits. It has deliberately no reset port or initialization
construct. The independent model retains unknowns separately for MR0/MR1/MR2
and SR0/SR1, so one segment can become known without silently initializing its
neighbors.

Three write inputs are an integration interface, not a claim that every
three-write combination is a legal instruction. `write_conflict_o` detects
same-destination writes and the implicit MR1/MR2 collision. Behavior after
clocking a reported conflict is outside the verified contract; the independent
model rejects it rather than assigning undocumented architectural priority
(OQ-014).

AF, MF, and SB are banked but are not DREG-encoded. Their compute/exponent
write paths, complete multifunction legality, MSTAT storage and update timing,
interrupt/context interaction, and exact same-cycle bank-switch visibility
remain unimplemented. M16 therefore remains `IMPLEMENTING`.

## Objective evidence

- `tests/test_register_banks.py` covers unknown preservation, every DREG in
  both banks, inactive-bank preservation, old-read/new-write visibility,
  narrow sign extension, MR1's MR2 side effect, legal triple writes, and
  fail-closed collisions.
- `make register-tests` compares 58,306 deterministic stateful sequences
  against independent Python results. It exhausts all 4,096 three-read address
  combinations in each bank and adds directed and seeded-random legal writes.
- `formal/registers.sby` states conflict, narrow-extension, and MR1 side-effect
  properties. The harness passes assertion lint; proof execution remains
  unavailable until SymbiYosys is installed.
