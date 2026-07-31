# Computational register banks

**Status: bank membership, storage/writeback, and ordinary MSTAT selection
implemented**

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

`rtl/core/adsp2100_mode_slice.sv` now wires stored MSTAT bit 0 directly to the
register-file bank selector. The corresponding independent model samples the
selected bank at cycle start and commits MSTAT and register writes at cycle
end. Consequently, a MOVE/MODE CONTROL change selects the other bank on the
following cycle. The structural boundary would keep any co-present DREG
access in the old bank, but this is not a claim that such an instruction
encoding is legal. This follows the compute chapter's general
start-read/end-write rule
[ADI-UM-1989, printed pp. 2-6–2-7] but does not settle the exact
interrupt-recognition boundary tracked by OQ-015.

The separate bounded `adsp2100_mode_control_slice` now supplies that MSTAT
write from exact original Type 18 decode. It verifies that SR changes bank
selection only after the cycle-end commit, including instructions that also
change BR, OL, or AS. It does not yet connect a same-instruction
computational-register access or interrupt recognition, so OQ-015 and full
multifunction legality remain unchanged.

`adsp2100_internal_move_slice` also composes general Type 17 access with this
bank boundary. Source and bank selection come from cycle-start MSTAT; a MOVE
to MSTAT changes the selected bank only after its source has been read. The
slice covers all legal computational-register source/destination pairs and
retains the MR1-to-MR2 side effect. Its 59,430-cycle comparison initializes
both banks independently and checks the complete register cross-product.

`adsp2100_load_dreg_immediate_slice` composes exact Type 6 decode with the
same bank and storage boundary. The decoded word is `DATA[19:4]` and the DREG
destination is `[3:0]`; all sixteen destinations execute in both banks. SE and
MR2 retain only their documented low eight bits and read back sign-extended,
while MR1 writes sign-fill MR2. The instruction performs no PM-data or DM
transaction. Six directed/model tests exhaustively decode all 1,048,576 class
words, and 50,204 deterministic model-versus-RTL cycles check reset unknowns,
both banks, boundary values, invalid words, and atomic setup-conflict
suppression [ADI-UM-1989, printed pp. 1-2, 2-6–2-7, 2-15, 2-18,
6-12–6-13, A-2, and A-9].

`adsp2100_immediate_shift_slice` connects the Type 15 immediate LSHIFT/ASHIFT
subset to the same bank boundary. It reads SI, AR, MR0, MR1, MR2, SR0, or SR1
from the bank selected by cycle-start MSTAT and atomically writes the 32-bit SR
result at cycle end. OR forms use the pre-instruction SR value, the immediate
exponent does not modify SE, and the inactive bank remains untouched. The
58,709-cycle comparison covers every supported opcode in both banks plus
deterministic invalid/conflict sequences
[ADI-UM-1989, printed pp. 2-23–2-30, 6-11 Table 6.5, A-3, and A-7].

`adsp2100_conditional_shift_slice` extends the same boundary through every
source-backed Type 16 shifter function. Cycle-start MSTAT selects the X, SE,
SR, and SB operands; condition-false preserves both banks; and condition-true
commits exactly the SF-selected SR, SE, or SB destination. EXP HI/HIX also
updates the unbanked ASTAT.SS on the same cycle-end edge. The inactive bank is
unchanged across all 54,403 model/RTL cycles
[ADI-UM-1989, printed pp. 2-20–2-35, 4-21, 4-25, 6-11, A-3, A-6–A-7].

`adsp2100_shift_move_slice` is the first bounded instruction slice to exercise
two ordinary writes to the selected computational bank in parallel. The
shifter and move source each read cycle-start state. Source overlap is legal;
the DREG move may replace the X operand after it has been consumed or read the
old SR/SE value before shifter writeback. The decoder excludes every
same-destination request, and the register file atomically commits the
remaining DREG plus SR/SE/SB writeback. The inactive bank is preserved across
all 82,597 comparison cycles
[ADI-UM-1989, printed pp. 2-6–2-7, 2-18, 6-4–6-7, A-3, and A-7].

`adsp2100_compute_move_slice` extends that parallel boundary through all
source-backed Type 8 ALU and MAC functions. X, Y, optional MR feedback, and
the DREG move source all come from cycle-start selected-bank state. The
noncolliding AR/AF or MR/MF computation result, status, and DREG move commit
together at cycle end while the inactive bank remains unchanged. The decoder
rejects move writes to AR alongside a Z=0 ALU result and MR0/MR1/MR2 alongside
a Z=0 MAC result. Every one of the 476,672 supported words executes in both
banks in the 983,386-cycle comparison
[ADI-UM-1989, printed pp. 2-6–2-20, 6-4–6-10, A-2, A-5–A-7, A-11].

Complete instruction and multifunction legality, operand/result decode
connectivity, and interrupt/context interaction remain unimplemented. M16
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
- `make mode-tests` adds five directed integration checks and 50,112
  deterministic model-versus-RTL cycles. It initializes every DREG in both
  banks, traverses all 16 MSTAT values, and checks that selection changes only
  after the writing cycle. The exact Type 18 slice adds 58,248 cycles,
  including every one of the 4,096 opcode/initial-MSTAT transforms.
- `make register-tests` adds seven directed Type 17 state tests, executes all
  2,256 legal pairs with each bank selected, and compares 59,430 deterministic
  stateful cycles with RTL. Narrow status reads remain labeled provisional
  under OQ-016.
- `make register-tests` also adds six Type 6 model tests and 50,204 stateful
  model-versus-RTL cycles, including every destination in both banks and exact
  SE/MR2/MR1 storage side effects.
- `make compute-tests` adds eight directed Type 15 tests and 58,709 stateful
  model-versus-RTL cycles, including all 14,336 supported words in each bank.
- `make compute-tests` adds ten directed Type 16 tests and 54,403 stateful
  model-versus-RTL cycles, including all 1,792 supported words in both banks
  under true and false condition patterns.
- `make compute-tests` adds ten directed Type 14 tests and 82,597 stateful
  model-versus-RTL cycles, including all 25,648 supported words in both banks
  and directed old-value hazards in both parallel clauses.
- `make compute-tests` adds ten directed Type 8 tests and 983,386 stateful
  model-versus-RTL cycles, executing all 476,672 supported words in both banks
  plus invalid, collision, reset-unknown, and setup-conflict boundaries.
- Quartus 17.0.2 fits exactly 554 design registers in the Cyclone V smoke
  project. Seed 2 closes the fully constrained 20 ns multicorner check at
  +9.985 ns worst setup and +0.109 ns worst hold slack.
