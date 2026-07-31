# AGENTS.md

## Mission and exact-device scope

This repository implements the **original Analog Devices ADSP-2100**, including
its complete documented instruction set and externally visible logical timing,
as portable synthesizable SystemVerilog. Atari Hard Drivin' is an integration
qualification target, not the definition of the supported instruction subset.

The default and currently only architectural configuration is the external
memory original ADSP-2100 identified by original-device sources. ADSP-2100A is
not assumed identical until its differences are closed. Do not silently add
ADSP-2101, ADSP-2103, ADSP-2104, ADSP-2105, ADSP-2111,
ADSP-2115, ADSP-217x, ADSP-218x, or ADSP-219x features. Later-device material
is comparative evidence only unless it explicitly says that a behavior applies
to the original ADSP-2100.

## Required reading before work

Before modifying RTL, the executable model, ISA data, or an architectural
expectation:

1. read this file;
2. read `TASKS.md` and `CHANGELOG.md`;
3. read the relevant documents under `docs/architecture/` and `docs/timing/`;
4. read every applicable ADR under `docs/decisions/`;
5. inspect `docs/research/open_questions.md` and
   `docs/research/source_conflicts.md`;
6. inspect current verification and confidence reports under `artifacts/`.

Every meaningful development cycle must update `TASKS.md` and `CHANGELOG.md`.
Update the progress artifacts after each major milestone.

## Source precedence and claim taxonomy

Use this authority order:

1. original ADI ADSP-2100-specific manuals, data sheets, errata, and timing
   documents;
2. ADI family manuals with an explicit applicability statement for ADSP-2100;
3. original Atari schematics, engineering records, PAL equations, and service
   manuals;
4. contemporary ADI toolchain and application documentation;
5. physical-chip measurements or die evidence;
6. original Atari engineering commentary;
7. maintained emulators;
8. academic or prior FPGA implementations;
9. community summaries.

Label claims as one of: original-device documented, explicit family-wide,
later-family only, reference-software observed, Atari schematic inferred, Hard
Drivin' software observed, MAME observed, physical-hardware confirmed,
implementation convenience, or unverified. Confidence is one of
`VERIFIED_PRIMARY`, `VERIFIED_HARDWARE`, `CORROBORATED`, `INFERRED`,
`PROVISIONAL`, or `UNKNOWN`.

Every architectural statement needs a citation precise enough to recover the
publication, revision, page, chapter/section/table/figure, schematic sheet, or
MAME commit and line. Never turn `PROVISIONAL` into `VERIFIED_*` without new
evidence.

## Clean-room and copyright policy

- Implement from specifications and independently derived tests.
- Do not copy MAME or other emulator source into RTL, the model, or tools.
- External implementations may be isolated differential oracles, subject to
  their licenses.
- Do not commit manuals, game ROMs, PAL dumps, or legacy tool binaries unless
  redistribution permission is explicit and recorded.
- Put redistribution-unclear downloads only in gitignored `reference_cache/`.
- Record URL, retrieval date, checksum, applicability, authority, license, and
  redistribution status in `docs/references/manifest.yaml`.
- Never evade authentication, paywalls, robots restrictions, or access
  controls.
- Never execute downloaded legacy binaries on the host. Use an isolated
  emulator/VM/container without credentials or sensitive mounts when a task
  explicitly requires execution.
- Prefer paraphrase and precise citation over copied manual text.

## Ambiguities and conflicts

Never invent or silently infer architectural behavior. Record incomplete or
contradictory evidence in `docs/research/open_questions.md` or
`docs/research/source_conflicts.md`, including competing hypotheses, affected
tests, and whether Hard Drivin' depends on the distinction. A provisional
implementation is permitted only when clearly labeled in code, documentation,
task status, and tests. Reserved encodings are not no-ops without authoritative
evidence.

## SystemVerilog conventions

The generic core targets the common synthesizable subset supported by current
Verilator, Icarus Verilog where practical, Yosys, and Intel Quartus:

- use `logic`, `always_ff`, `always_comb`, packages, explicit-width types, and
  enumerated state machines;
- use explicit signedness at declarations and arithmetic boundaries;
- size every literal; do not rely on unsized arithmetic constants;
- extend operands explicitly before arithmetic and slice results explicitly;
- document every intentional truncation, rounding point, guard bit, and
  signed/unsigned conversion;
- give combinational outputs defaults and avoid inferred latches;
- declare every net; implicit nets are prohibited;
- avoid multiple procedural drivers and combinational loops;
- avoid `initial` state in architectural RTL;
- no `#` delays, real-number constructs, `force/release`, DPI dependencies, or
  testbench-only constructs in synthesizable RTL;
- no vendor primitives in `rtl/core/` or `rtl/packages/`;
- assertions may be guarded for synthesis, but normal simulation must keep
  them enabled.

Use lower_snake_case signals and module names. Module filenames match module
names. Active-low external signals use an `_n` suffix only after original pin
polarity is sourced. Constants and enum members use upper snake case.

## Clocking and reset

The portable core has one primary FPGA clock. Represent historical instruction
cycles, bus phases, stalls, and arbitration with explicit state and synchronous
clock enables. **Gated clocks and logic-generated internal clocks are
prohibited.** CDC logic belongs only in a wrapper with a real clock-domain
crossing.

Reset behavior must distinguish asynchronous pin behavior, synchronous
architectural updates, documented reset values, unknown power-up state, and
wrapper-only deterministic initialization. Do not turn undocumented or
power-up-unknown state into zero. Any deterministic FPGA convenience belongs
behind an explicit wrapper parameter and must not change the default authentic
model.

## Synthesis requirements

Architectural RTL must be portable and synthesizable without vendor libraries.
Inference of RAMs, adders, and multipliers is allowed if their behavior is
fully specified independently of the mapping. Keep latch count and accidental
clock count at zero. Treat unconstrained paths, width warnings, and
synthesis/simulation mismatches as defects. RTL commits require a Verilator
lint/build and an available Yosys smoke synthesis; target work additionally
requires the applicable Quartus project and SDC checks.

## Verification requirements

- Every encoding claim needs automated decode coverage based on independently
  reviewed fixtures.
- Every arithmetic claim needs boundary tests.
- Every cycle-count claim needs an automated timing assertion.
- Every external memory transaction must be trace-testable.
- Every multifunction ordering rule needs documentation and directed tests.
- Model, assembler, RTL, and MAME must not validate each other circularly.
- Random tests use deterministic seeds and preserve reduced failures.
- Never bypass a failing test, weaken an assertion to pass, or change expected
  output without documenting why the old expectation was wrong.
- RTL existence never makes a task complete. Completion requires source-backed
  documentation and objective passing tests named in `TASKS.md`.

The default verification ladder is:

1. manifest/schema and generated-data consistency;
2. independent model unit tests;
3. hand-fixture assembler/disassembler/decode tests;
4. computational-unit, DAG, sequencer, bus, and interrupt unit tests;
5. instruction and program regressions;
6. randomized RTL/model differential tests;
7. independent MAME comparison where applicable;
8. formal properties;
9. synthesis and timing qualification.

## Formal verification

Use SVA plus SymbiYosys-compatible harnesses when available. At minimum, cover
decode uniqueness, legal state transitions, stalled-bus stability, legal PM/DM
controls, bus grant/relinquishment, stack bounds, PC/loop rules, interrupt
priority/masking, bank selection, DAG wrapping, condition-false preservation,
write-conflict exclusion, and arithmetic identities. Every proof report must
state assumptions, engine, depth, bounded state, and uncovered state. A bounded
proof is not a complete proof.

## Documentation discipline

Architecture documents are specifications, not marketing. Attach each claim to
evidence and list unresolved cases near the claim. Machine-readable ISA data is
the intended source for generated opcode tables, decode constants,
assembler/disassembler tables, and coverage reports. Do not maintain
contradictory handwritten opcode definitions.

Timing documentation distinguishes logical bus phase accuracy from analog
setup/hold/access/pulse-width limits. Hard Drivin'-specific maps and behavior
remain in integration documents and wrappers, never in the generic core.

## Commit discipline

Use small coherent commits with prefixes such as `chore`, `docs`, `research`,
`model`, `tools`, `rtl`, `test`, `formal`, `synth`, `integration`, or `fix`.
Do not rewrite published history.

Before every commit:

1. inspect the full diff and staged file list;
2. run the focused tests;
3. run `make test` and `make lint`;
4. run `make synth-yosys` for RTL changes when Yosys is available;
5. run applicable formal checks;
6. ensure no manual, ROM, dump, or downloaded binary is staged;
7. update `TASKS.md`, `CHANGELOG.md`, citations, and assumptions;
8. ensure the repository remains buildable and testable.

A commit message must state the engineering change and its verification.

## Repository layout

- `docs/{architecture,timing,research,references,decisions,integration}`:
  specifications, provenance, and decisions
- `docs/generated/`: reviewed generated architecture artifacts
- `rtl/{packages,core,wrappers}`: synthesizable implementation
- `sim/reference_models/`: structurally independent executable model
- `sim/`: HDL testbenches and differential adapters
- `tools/`: assembler, disassembler, trace, generators, converters
- `tests/`: fixtures, vectors, programs, traces, regressions, fuzz cases
- `formal/`: properties and harnesses
- `synthesis/`: Yosys, Quartus, and MiSTer projects
- `third_party/`: permitted source dependencies and notices
- `reference_cache/`, `build/`: gitignored local products
- `artifacts/`: tracked concise status reports, not large generated outputs

## Current architectural status and risk

No integrated fetch/decode/execute instruction core exists. Bounded
source-backed RTL execution slices now implement all original Type 18 mode
controls, all 32 original Type 21 MODIFY selections, exact Type 25 conditional
MR saturation, all Type 6 immediate-to-DREG loads, the 14,336 source-closed
Type 15 immediate LSHIFT/ASHIFT words, 25,648 canonical Type 14
shifter-plus-DREG words, all 1,792 source-backed Type 16 conditional shifter
words, 476,672 source-closed Type 8 ALU/MAC-plus-DREG words, and all Type 26
stack-control actions,
but they do not establish
whole-core PC, pipeline, bus, interrupt, or wait-state behavior. Type 18
excludes later timer, GO, and multiplier-placement fields and exhaustively
covers all 256 original words. Type 21 uses an exact-width I/M/L register file
with authentic reset-invalid state and cycle-start-read/cycle-end-write
ordering; ordinary data transfers and multifunction DAG updates are not yet
attached.
Type 15 exhaustively partitions its 32,768-word class: XOP `001` and SF 8–15
remain explicit unsupported subencodings rather than receiving invented
behavior. Its bounded state slice samples the selected bank and OR feedback at
cycle start, commits SR at cycle end, and leaves SE/status unchanged; other
shifter instruction classes remain unintegrated. Type 16 exhaustively
partitions its 2,048-word class into 1,792 supported actions and 256 XOP `001`
subencodings held under OQ-020. Its bounded slice evaluates cycle-start
conditions, samples selected-bank SE/SR/SB and ASTAT feedback, preserves all
destinations when false, and commits the SF-selected SR/SE/SB/SS writes at
cycle end. Memory-access shifter multifunction classes remain unintegrated.
The bounded Type 14 slice is the first integrated multifunction instruction:
both shifter and DREG-move sources read cycle-start selected-bank state, and
noncolliding move plus SR/SE/SB/SS writes commit together at cycle end. Its
canonical bit-15-zero subset contains 25,648 supported words. The remaining
32,768 bit-15-one, 4,096 unavailable-XOP, and 3,024 same-destination words fail
closed; OQ-021 tracks the original diagram's unnamed bit 15. Type 12–13 memory
multifunction classes remain unintegrated.
The bounded Type 8 slice executes documented ALU and fractional-MAC
computations in parallel with one internal DREG move. Both clauses sample the
cycle-start selected bank; noncolliding DREG/AR/AF/MR/MF and ASTAT writes
commit atomically at cycle end. The exact 524,288-word class partitions into
476,672 supported words, 16,384 AMF-zero words held under OQ-022, and 31,232
same-destination collision words held under OQ-014. It does not establish
conditional-computation, PM/DM-data, fetch, interrupt, or bus timing.
A generated
synthesizable class decoder recognizes all 30 original Appendix A format
classes and fails closed for unshown words; it has exhaustive 24-bit membership
comparison. A separate exact Type 17 decoder partitions its 4,096 words into
2,256 legal moves and 1,840 reserved/read-only-destination subencodings. A
bounded Type 17 state slice now connects both computational banks, both DAG
register files, status/control, PX, CNTR/count-stack, and SSTAT with
cycle-start read/cycle-end write ordering. Its narrow status-source
zero-extension is visibly PROVISIONAL under OQ-016; fetch, interrupts, PC, and
bus phases remain unintegrated. Source-backed condition,
standard ALU, fractional MAC, all-function shifter, DAG arithmetic, and
sequencer-flow combinational blocks exist with independent model comparison,
and a stateful two-bank storage slice exists for the complete computational
bank, including AF/MF/SB and unit-specific ALU/MAC/shifter writeback. A
stateful status/control slice also implements original ASTAT/MSTAT/ICNTL/IMASK
fields, reset classifications, exact Type 18 MODE CONTROL, computational flag writes,
interrupt-entry snapshot/masking, and status restore. MSTAT consumer
integration now covers its four original outputs at an ordinary
cycle-start/cycle-end boundary; ICNTL consumer wiring, interrupt recognition,
and complete operand/decode connectivity do not exist. A separate original
four-by-sixteen status stack and exact PC/count/loop stack-storage slice
implement LIFO state, saturating depth, sticky overflow, and all eight SSTAT
sources. A separate stateful CNTR slice implements reset validity,
pre-decrement CE/NOT CE evaluation, post-decrement, and count-stack request
generation. A bounded sequencer integration slice connects IF/DO condition
evaluation, explicit flow, DO setup, CNTR, and PC/count/loop stack storage for
source-backed cases. It rejects conditional-CALL CE (OQ-012), empty-pop
effects remain OQ-013, and competing automatic/manual actions are held and
flagged under OQ-018. Type 26 now connects manual status-stack push/restore to
live ASTAT/MSTAT/IMASK in its bounded slice; interrupt/RTI arbitration remains
absent. No PC register, integrated semantic instruction decode, interrupt
recognition, or phase-level sequencer timing exists.
Multifunction legality, ordering, and whole-core cycle integration remain
incomplete. The executable
instruction model establishes
exact-width state, reset unknowns, deterministic traces, PM fetch
transactions, and only the hand-verified all-zero NOP in its top-level step
method. Independent bounded models cover Type 17 action/state selection and
Type 6, Type 8, Type 14, Type 15, Type 16, Type 18, Type 21, Type 25, and
Type 26 state/action behavior outside that
top-level step path; all other opcodes still fail closed. Architectural
documents marked partial or provisional remain research inputs until their
named evidence gates pass.

Highest risks are:

1. separating original ADSP-2100 behavior from later ADSP-21xx behavior;
2. semantic completion and legal multifunction combinations after the
   source-closed 24-bit class/field-placement inventory;
3. pre-instruction versus same-cycle value ordering;
4. pipeline, wait-state, interrupt, halt, and bus-arbitration timing;
5. arithmetic edge behavior, especially MAC alignment/rounding/guard bits;
6. lack of physical ADSP-2100 measurements for undocumented cases;
7. reconstructing Atari PAL/host/SIM/SOM behavior without treating MAME as
   primary proof.

## Completion

Do not call the core instruction-complete, cycle-accurate, Hard Drivin'-ready,
or release-ready until the corresponding criteria in `TASKS.md` and README
status artifacts have objective evidence. At a minimum release requires full
legal/reserved encoding accounting, directed and differential coverage,
documented cycle/bus behavior, passing lint/formal/regressions, successful
Yosys and Quartus synthesis, timing constraints and closure evidence,
provenance/license audits, synthetic board tests, and authorized local-ROM
qualification where ROMs are available.
