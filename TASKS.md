# Engineering backlog

Task completion means that cited documentation and named objective tests pass;
the existence of RTL alone is never sufficient. Status values are `NOT
STARTED`, `RESEARCHING`, `BLOCKED`, `IMPLEMENTING`, `VERIFYING`, and
`COMPLETE`. Confidence values are `VERIFIED_PRIMARY`, `VERIFIED_HARDWARE`,
`CORROBORATED`, `INFERRED`, `PROVISIONAL`, and `UNKNOWN`.

Priorities are P0 (blocks trustworthy implementation), P1 (core architecture),
P2 (qualification), and P3 (release/integration follow-on). Reference IDs refer
to `docs/references/manifest.yaml`; `TBD-PRIMARY` means that a task cannot
advance beyond research until a page-level primary citation is added.

## M1 — Repository and automation foundation

### FND-001 — Repository and automation foundation

- **Status:** VERIFYING
- **Priority:** P0
- **Dependencies:** none
- **Acceptance criteria:** required layout and governance files exist; manifest,
  policy, model, lint, formal, and synthesis entry points return meaningful
  status; CI runs all license-compatible foundation checks.
- **Source references:** project requirements; ADR-0001, ADR-0002, ADR-0003
- **Relevant tests:** `tests/test_repository.py`,
  `tests/test_reference_manifest.py`, `make test`, `make lint`
- **Implementation notes:** required layout, governance, CI, `make test`,
  strict Verilator package lint, and explicit optional-tool skips exist;
  preserve existing `main` history and MIT license.
- **Unresolved questions:** CI tool-version pins and the minimum supported
  Quartus release need target qualification.
- **Confidence:** PROVISIONAL

## M2 — Documentation acquisition and provenance

### REF-001 — Documentation acquisition and provenance

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** FND-001
- **Acceptance criteria:** initial target list has complete provenance records;
  lawful configured downloads are idempotent, content-validated, hashed, and
  gitignored; missing and mismatched references are reported independently.
- **Source references:** ADI-MANUAL-INDEX, ADI-ASM-1994, ATARI-ADSP-SCHEM,
  MAME-ADSP2100-CORE, MAME-HARDDRIV, MAME-HARDDRIV-MACHINE
- **Relevant tests:** `tests/test_reference_manifest.py`,
  `tests/test_reference_scripts.py`
- **Implementation notes:** redistribution-unclear files remain only under
  `reference_cache/`; downloaded binaries are never executed.
- **Unresolved questions:** locate an ADI-hosted original ADSP-2100/2100A data
  sheet and earliest user-manual revision with stable URLs.
- **Confidence:** CORROBORATED

## M3 — Original ADSP-2100 device identification

### DEV-001 — Identify the original ADSP-2100/ADSP-2100A boundary

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** REF-001
- **Acceptance criteria:** package, address/data widths, pins, clocks, memory
  interfaces, revision naming, and documented 2100-versus-2100A differences are
  cited to original-device pages; Hard Drivin' fitted part evidence is cited.
- **Source references:** ADI-DATABOOK-1987 printed pp. 2-15 onward,
  ADI-UM-1989, ATARI-ADSP-SCHEM
- **Relevant tests:** `tests/test_architecture_claims.py::test_device_scope`
- **Implementation notes:** do not treat assembler convention that “ADSP-2100”
  includes 2100A as proof of electrical identity.
- **Unresolved questions:** exact mask/revision differences and authentic
  power-up state.
- **Confidence:** PROVISIONAL

## M4 — ADSP-2100 versus ADSP-21xx feature matrix

### DEV-002 — Source-backed family feature matrix

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** DEV-001
- **Acceptance criteria:** ADSP-2100, 2101, 2103, 2104, 2105, 2111/2115, and
  evolution-relevant 217x/218x rows cover all requested features with per-cell
  citations or `UNKNOWN`; default configuration excludes all later features.
- **Source references:** ADI-UM-FAMILY-1995, ADI-21XX-DS-REVC,
  ADI-DATABOOK-1987, ADI-2104-DS-REV0
- **Relevant tests:** `tests/test_architecture_claims.py::test_feature_matrix`
- **Implementation notes:** unknown cells are intentional research targets, not
  evidence of absence.
- **Unresolved questions:** 2104 primary documentation and original core
  arithmetic/revision differences.
- **Confidence:** PROVISIONAL

## M5 — Programmer's model

### ARCH-001 — Original-device programmer's model

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** DEV-001, DEV-002
- **Acceptance criteria:** every architectural register has width, signedness,
  read/write paths, reset/power-up state, bank behavior, visibility timing, and
  page-level original-device applicability evidence.
- **Source references:** ADI-UM-1989, ADI-DATABOOK-1987,
  ADI-UM-FAMILY-1995 for explicitly applicable comparisons only
- **Relevant tests:** `tests/test_model_state.py`,
  `tests/test_register_metadata.py`
- **Implementation notes:** initial register map and reset-state
  classifications exist; the original 2-bit RGP/4-bit REG table accounts for
  48 codes and every blank code, while direction-specific access paths and all
  hidden state still require complete metadata. Emulator variable names are
  discovery aids only.
- **Unresolved questions:** hidden sequencer state, undefined reset fields, and
  exact alternate-bank coverage.
- **Confidence:** UNKNOWN

## M6 — Instruction encoding database

### ISA-001 — Complete machine-readable 24-bit ISA database

- **Status:** IMPLEMENTING
- **Priority:** P0
- **Dependencies:** ARCH-001, REF-001
- **Acceptance criteria:** every legal and reserved 24-bit encoding class is
  represented with all required semantic/timing fields, citations, confidence,
  schema validation, uniqueness checks, and hand-reviewed opcode fixtures.
- **Source references:** ADI-ASM-1994 Appendix A,
  ADI-UM-1989 instruction chapters and Appendix A
- **Relevant tests:** `tests/test_isa_database.py`, `make decode-tests`
- **Implementation notes:** the database enumerates all 30 original top-level
  classes with primary-transcribed, non-overlapping masks, explicitly covers
  1,304,054 unshown words as reserved, and generates synthesizable class
  decode. The complete original 16-code IF and inverse-sense DO UNTIL
  condition fields and all 19 finite Appendix A abbreviation tables are
  separately machine-readable and exhaustively checked; only the all-zero NOP
  is a hand-verified full instruction fixture. Generated assembler/
  disassembler artifacts must derive from these databases as instruction
  entries are independently verified.
- **Unresolved questions:** earliest-tool opcode differences and undocumented
  encoding behavior.
- **Confidence:** UNKNOWN

## M7 — Multifunction-instruction semantics

### ISA-002 — Formalize parallel action and collision semantics

- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** ISA-001, ARCH-001
- **Acceptance criteria:** legal combinations, pre/new-value rules, DAG update,
  condition/status timing, move/compute collisions, PM/DM concurrency, and
  wait-state effects have source-backed action graphs and directed tests.
- **Source references:** ADI-UM-1989, ADI-UM-FAMILY-1995,
  ADI-ASM-1994
- **Relevant tests:** `make instruction-tests`,
  `tests/test_parallel_semantics.py`
- **Implementation notes:** do not serialize actions merely for coding
  convenience.
- **Unresolved questions:** result forwarding and illegal destination
  collisions are high-risk.
- **Confidence:** UNKNOWN

## M8 — Executable architectural model

### MODEL-001 — Independent cycle/transaction reference model

- **Status:** IMPLEMENTING
- **Priority:** P0
- **Dependencies:** ARCH-001; incremental groups depend on ISA-001/ISA-002
- **Acceptance criteria:** model covers all original instructions, exact-width
  state, simultaneous actions, sequencing, interrupts, reset/halt/BR, PM/DM
  transactions, waits, deterministic traces/replay, random initialization, and
  passes directed plus independent differential tests.
- **Source references:** source set required by each implemented group
- **Relevant tests:** `make model-tests`, `make differential`
- **Implementation notes:** the partial model has exact-width primitives,
  fail-closed unsupported opcodes, and a source-derived IF/DO condition
  evaluator; full instruction behavior remains unavailable.
- **Unresolved questions:** model cycle granularity awaits ADR-0003 evidence.
- **Confidence:** PROVISIONAL

## M9 — Assembler and disassembler workflow

### TOOL-001 — Original-syntax assembler/disassembler workflow

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ISA-001
- **Acceptance criteria:** all documented syntax and directives required by the
  project assemble deterministically; round trips preserve encodings; every
  class has hand-verified fixtures independent of the assembler.
- **Source references:** ADI-ASM-1994
- **Relevant tests:** `make assembler-tests`, `make decode-tests`
- **Implementation notes:** a fail-closed database-driven seed round-trips the
  independent NOP fixture and distinguishes legal-unimplemented, original
  reserved, and unshown-reserved words. First research surviving lawful
  assemblers; do not execute legacy tools on the host.
- **Unresolved questions:** scope of macros/object/linker compatibility needed
  for ROM qualification.
- **Confidence:** UNKNOWN

## M10 — Arithmetic logic unit

### RTL-ALU-001 — ALU model and synthesizable RTL

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-001
- **Acceptance criteria:** all ALU operations, feedback paths, flags, saturation,
  condition-false, and bank interactions match cited behavior in model and RTL;
  directed boundary/differential/formal tests pass; synthesis is warning-clean.
- **Source references:** ADI-UM-1989 computational-unit and instruction chapters
- **Relevant tests:** `make compute-tests`, `formal/alu.sby`
- **Implementation notes:** the source-backed standard AMF `0x10`–`0x1f`
  compute block, flags, sticky AV, and AR saturation exist in independent
  model and RTL. Instruction operand selection/writeback, condition-false,
  banking, and DIVS/DIVQ remain.
- **Unresolved questions:** DIVS/DIVQ iteration semantics and instruction-level
  old/new value visibility remain open.
- **Confidence:** CORROBORATED

## M11 — Multiplier/accumulator

### RTL-MAC-001 — MAC model and synthesizable RTL

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-001
- **Acceptance criteria:** sign modes, fractional/integer alignment, guard bits,
  rounding, accumulation, saturation, overflow, segmentation, and feedback are
  source-backed and pass boundary, randomized, differential, and formal tests.
- **Source references:** ADI-UM-1989 MAC and instruction chapters
- **Relevant tests:** `make compute-tests`, `formal/mac.sby`
- **Implementation notes:** the source-backed fixed-fractional AMF `0x01`–`0x0f`
  compute block, four signedness modes, unbiased rounding, MF extraction, MV,
  and SAT MR transform exist in independent model and RTL. Instruction
  operand selection/writeback, banking, and parallel timing remain.
- **Unresolved questions:** original-device multiplier visibility within
  multifunction instructions and the recorded MAME rounding conflict SC-008.
- **Confidence:** CORROBORATED

## M12 — Barrel shifter

### RTL-SHIFT-001 — Shifter model and synthesizable RTL

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-001
- **Acceptance criteria:** immediate/register shifts, logical/arithmetic modes,
  normalization, exponent/block exponent, off-scale fill, feedback, and status
  pass edge, differential, and formal tests.
- **Source references:** ADI-UM-1989 shifter and instruction chapters
- **Relevant tests:** `make compute-tests`, `formal/shifter.sby`
- **Implementation notes:** all sixteen source-backed SF functions now exist
  in the independent model and portable combinational RTL. Exact signed counts,
  HI/LO placement, PASS/OR, ASHIFT/LSHIFT, NORM AC extension, EXP HI/HIX/LO,
  EXPADJ, and explicit write enables pass directed and 644,368-vector
  model-versus-RTL tests. Operand decode, conditional execution, bank selection,
  architectural writeback, multifunction ordering, and cycles remain.
- **Unresolved questions:** reset values, same-cycle visibility during
  multifunction writeback, and OQ-011's manually loaded `SE=0x80` NORM
  negation; no undocumented shifter saturation operation is assumed.
- **Confidence:** CORROBORATED

## M13 — Data-address generator 1

### RTL-DAG1-001 — DAG1 addressing

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-002
- **Acceptance criteria:** all legal I/M/L combinations, linear/circular and
  applicable bit-reversed behavior, signed modifies, zero/non-power-of-two
  lengths, update order, waits, loops, and interrupts pass model/RTL tests.
- **Source references:** ADI-UM-1989 DAG and data-move chapters
- **Relevant tests:** `make dag-tests`, `formal/dag.sby`
- **Implementation notes:** an independent function model and portable
  combinational RTL implement old-I output, signed post-modify, L=0 linear
  wrap, circular wrap, original power-of-two alignment, and all-14-bit DAG1
  reversal. Ten directed/random model tests and 204,864 model-versus-RTL
  vectors pass, including all reversed addresses. Invalid circular
  configurations are exposed diagnostically, not assigned invented semantics.
- **Unresolved questions:** register-file integration, writeback and stall
  enables, same-cycle register writes, alternate banking, multifunction
  ordering, loops, interrupts, and externally visible timing.
- **Confidence:** CORROBORATED

## M14 — Data-address generator 2

### RTL-DAG2-001 — DAG2 addressing

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-002
- **Acceptance criteria:** DAG2's documented PM/DM roles and every legal
  I/M/L/update case pass independently and concurrently with DAG1.
- **Source references:** ADI-UM-1989 DAG and data-move chapters
- **Relevant tests:** `make dag-tests`, `formal/dag.sby`
- **Implementation notes:** the common source-backed post-modify/modulus block
  has a DAG2 configuration in which bit-reverse is structurally ineffective;
  all vectors compare DAG1/DAG2 arithmetic. PM/DM attachment and register
  selection do not yet exist.
- **Unresolved questions:** differing register group restrictions and
  simultaneous PM/DM semantics.
- **Confidence:** CORROBORATED

## M15 — Program sequencer

### RTL-SEQ-001 — Program sequencer

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-001, TIME-001
- **Acceptance criteria:** sequential PC, every condition, branch/call/return,
  loops, stacks, flushes, and control interactions match model, cycle, and
  formal properties.
- **Source references:** ADI-UM-1989 sequencer and instruction chapters
- **Relevant tests:** `make sequencer-tests`, `formal/sequencer_flow.sby`
- **Implementation notes:** an independent instruction-boundary model and
  portable combinational RTL select sequential, jump, call, return, loop-back,
  and loop-exit flow. All 636,512 model-versus-RTL vectors pass, including
  every 14-bit PC for return-address wrap and explicit-transfer precedence at
  loop end. This block emits stack/counter action requests; it does not
  implement their state or timing.
- **Unresolved questions:** opcode integration, DO setup, actual stacks,
  CNTR/CE semantics including OQ-012, interrupts, delayed transfers, cache
  interaction, stack faults, pipeline visibility, and logical bus phases.
- **Confidence:** CORROBORATED

## M16 — Register files and alternate register bank

### RTL-REG-001 — Computational register files and banking

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** ARCH-001, ISA-002
- **Acceptance criteria:** all primary/alternate registers, switching timing,
  interrupt/context interactions, simultaneous reads/writes, and reset
  classifications pass directed and formal tests.
- **Source references:** ADI-UM-1989 register and secondary-bank sections
- **Relevant tests:** `make register-tests`, `tests/test_register_banks.py`,
  `formal/registers.sby`
- **Implementation notes:** the exact banked set is primary-verified. The
  independent model and portable RTL implement both banks for all 16
  general-computational DREG codes, exact SE/MR2 widths, three cycle-start
  reads, three cycle-end writes, MR1-to-MR2 sign extension, and explicit
  collision reporting. The RTL has 480 source storage bits and deliberately
  no reset assignment; 58,306 model-versus-RTL stateful vectors pass.
- **Unresolved questions:** AF/MF/SB storage/write paths, compute result
  writeback, full multifunction legality, MSTAT storage, interrupt/context
  interactions, OQ-014 illegal collisions, and OQ-015 bank-switch visibility.
- **Confidence:** CORROBORATED

## M17 — Status and mode registers

### RTL-STATUS-001 — Status, mode, interrupt, and system registers

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** ARCH-001, RTL-REG-001
- **Acceptance criteria:** all fields, reserved bits, reset values, read/write
  effects, flag latency, masks, and context stacking pass tests tied to cited
  original applicability.
- **Source references:** ADI-UM-1989 status/control register sections
- **Relevant tests:** `tests/test_status_registers.py`,
  `formal/status_registers.sby`
- **Implementation notes:** later memory-mapped peripheral control registers
  are excluded from the ADSP-2100 default.
- **Unresolved questions:** original ICNTL/SSTAT field set and reserved reads.
- **Confidence:** UNKNOWN

## M18 — Program-memory interface

### RTL-PMBUS-001 — Native program-memory interface

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** DEV-001, TIME-001
- **Acceptance criteria:** sourced pins/polarities, logical phases, fetch
  transactions, wait extension, bus relinquishment, and data stability pass
  trace assertions and formal properties.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989 system-interface chapter
- **Relevant tests:** `make bus-tests`, `formal/pm_bus.sby`
- **Implementation notes:** keep PM physically/logically distinct from DM.
- **Unresolved questions:** exact original pin timing and wait input behavior.
- **Confidence:** UNKNOWN

## M19 — Data-memory interface

### RTL-DMBUS-001 — Native data-memory interface

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** DEV-001, TIME-001
- **Acceptance criteria:** sourced pins/polarities, read/write phases, waits,
  bus arbitration, concurrent PM operation, and stall stability pass traces and
  formal properties.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989 system-interface chapter
- **Relevant tests:** `make bus-tests`, `formal/dm_bus.sby`
- **Implementation notes:** shared physical pins, if documented, may be exposed
  through a native bus-control layer without erasing PM/DM transaction identity.
- **Unresolved questions:** shared data-bus turnaround and select ordering.
- **Confidence:** UNKNOWN

## M20 — Program-memory data transfers

### RTL-PMDATA-001 — PM data read/write semantics

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** ISA-002, RTL-PMBUS-001, RTL-DAG2-001
- **Acceptance criteria:** all PM data-move widths, packing, addressing,
  concurrency, waits, destination timing, and write data pass model/RTL bus
  traces and collision tests.
- **Source references:** ADI-UM-1989 PM transfer and data-move sections
- **Relevant tests:** `make instruction-tests`, `make bus-tests`
- **Implementation notes:** distinguish 24-bit program words from 16-bit data
  operands without assuming packing.
- **Unresolved questions:** original PM-write forms and same-cycle fetch
  arbitration.
- **Confidence:** UNKNOWN

## M21 — Loop and stack behavior

### RTL-STACK-001 — Hardware loops and architectural stacks

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** RTL-SEQ-001, ARCH-001
- **Acceptance criteria:** loop/PC/status stack depths, push/pop timing, nesting,
  terminal instruction behavior, interrupts, and documented overflow/underflow
  pass boundary and formal tests.
- **Source references:** ADI-UM-1989 sequencer and stack sections
- **Relevant tests:** `make sequencer-tests`, `formal/stacks.sby`
- **Implementation notes:** if fault behavior is undocumented, constrain tests
  to legal depth and record hardware-validation needs.
- **Unresolved questions:** exact original stack depths and illegal access
  behavior.
- **Confidence:** UNKNOWN

## M22 — Interrupt behavior

### RTL-IRQ-001 — Interrupt recognition, priority, entry, and return

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** RTL-SEQ-001, RTL-STATUS-001, TIME-001
- **Acceptance criteria:** original pins/vectors, recognition boundary,
  priority, mask/latch behavior, nesting, context/bank effects, latency, and
  return timing pass directed, randomized, bus, and formal tests.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989 interrupt sections
- **Relevant tests:** `make interrupt-tests`, `formal/interrupt.sby`
- **Implementation notes:** exclude later-device interrupt sources and vectors.
- **Unresolved questions:** edge/level sensitivity and reset-release boundary.
- **Confidence:** UNKNOWN

## M23 — Reset, halt, and bus arbitration

### RTL-SYS-001 — Reset, HALT, BR/BG, and restart

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** DEV-001, TIME-001, RTL-PMBUS-001, RTL-DMBUS-001
- **Acceptance criteria:** assertion/release, minimum reset, initial fetch,
  documented/unknown state, bus pins during reset, halt/restart, BR recognition,
  BG/reacquire, and interrupt interactions pass cycle and formal tests.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ATARI-ADSP-SCHEM
- **Relevant tests:** `make bus-tests`, `make interrupt-tests`,
  `formal/system_control.sby`
- **Implementation notes:** use clock enables and phase state, never gated
  clocks.
- **Unresolved questions:** whether “halt” is an instruction, pin, board
  mechanism, or a combination on the exact device.
- **Confidence:** UNKNOWN

## M24 — Pipeline and instruction timing

### TIME-001 — Source-backed pipeline and cycle model

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** DEV-001, REF-001
- **Acceptance criteria:** all documented instruction cases, overlap, false
  conditions, transfers, loops, stacks, interrupts, waits, halt, and BR have
  cycle definitions and automated assertions; unresolved timing is disclosed.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989, ADR-0003
- **Relevant tests:** `tests/test_cycle_tables.py`, all timing/bus regressions
- **Implementation notes:** the eight-state baseline, ordinary/PM-miss/wait/
  interrupt/HALT cases, and phase sampling points are documented; the full
  opcode timing table is not. Logical phase fidelity is separate from analog
  delay modeling.
- **Unresolved questions:** fetch/decode/execute visibility and PM-data conflict
  penalties.
- **Confidence:** UNKNOWN

## M25 — External wait-state behavior

### TIME-002 — PM/DM wait states and transaction extension

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** TIME-001, RTL-PMBUS-001, RTL-DMBUS-001
- **Acceptance criteria:** wait sampling, per-space configuration/input,
  address/control/data stability, phase extension, simultaneous transactions,
  interrupts, and BR during waits pass trace and liveness tests.
- **Source references:** ADI-DATABOOK-1987 ADSP-2100 data sheet,
  ADI-UM-1989 system-interface chapter
- **Relevant tests:** `make bus-tests`, `formal/wait_states.sby`
- **Implementation notes:** do not substitute a generic ready/valid protocol
  until original pin behavior is mapped.
- **Unresolved questions:** original ADSP-2100 wait pins versus programmed wait
  behavior.
- **Confidence:** UNKNOWN

## M26 — Differential testing

### VERIF-DIFF-001 — Model/RTL/MAME differential framework

- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** MODEL-001, ISA-001; MAME path depends on REF-001
- **Acceptance criteria:** deterministic trace schema compares all requested
  state and transactions; seeded legal programs run model/RTL; isolated
  commit-pinned MAME adapter runs where practical; reducer preserves failures.
- **Source references:** MAME-ADSP2100-CORE, MAME-ADSP2100-OPS,
  MAME-ADSP2100-DASM, and per-instruction primary sources
- **Relevant tests:** `make differential`, `make fuzz`
- **Implementation notes:** MAME is an implementation under test and cannot
  override primary evidence by itself.
- **Unresolved questions:** minimal licensed MAME build and cycle limitations.
- **Confidence:** UNKNOWN

## M27 — Formal verification

### FORMAL-001 — Bounded and invariant proof suite

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** applicable RTL blocks
- **Acceptance criteria:** requested control/bus/DAG/stack/interrupt/arithmetic
  properties run in CI with documented assumptions, engines, bounds, covers,
  and uncovered state.
- **Source references:** architecture specifications for each property
- **Relevant tests:** `make formal`
- **Implementation notes:** depth-one condition, ALU, MAC, shifter, DAG, and
  sequencer-flow combinational harnesses now exist; never call a bounded
  result complete proof. Proof execution awaits an installed
  SymbiYosys/Yosys/SMT toolchain.
- **Unresolved questions:** solver/tool version and tractable whole-core bounds.
- **Confidence:** UNKNOWN

## M28 — FPGA synthesis and timing

### SYNTH-001 — Portable and Cyclone V synthesis qualification

- **Status:** IMPLEMENTING
- **Priority:** P1
- **Dependencies:** first synthesizable RTL block
- **Acceptance criteria:** Yosys and Quartus builds have zero latches/accidental
  clocks, constrained interfaces, recorded warnings/utilization/Fmax/critical
  paths, optional no-DSP comparison, and passing behavioral equivalence tests.
- **Source references:** Intel Cyclone V/TimeQuest documentation; RTL specs
- **Relevant tests:** `make synth-yosys`, `make synth-quartus`
- **Implementation notes:** constrained Quartus Cyclone V smoke projects cover
  the condition, ALU, MAC, shifter, DAG, and sequencer-flow combinational
  blocks. Whole-core clocks, utilization, and timing remain unavailable;
  Yosys is not installed.
- **Unresolved questions:** exact DE10-Nano device support in installed edition.
- **Confidence:** UNKNOWN

## M29 — MiSTer-compatible wrapper

### INTEG-MISTER-001 — MiSTer clock-enable/memory wrapper

- **Status:** NOT STARTED
- **Priority:** P2
- **Dependencies:** generic core timing and interfaces, SYNTH-001
- **Acceptance criteria:** single system clock, sourced cycle enables, separate
  synchronous PM/DM, reset/halt/BR/BG/IRQs, trace/debug hooks, and SDRAM
  adaptation as needed pass wrapper tests and Quartus timing.
- **Source references:** MiSTer framework documentation; generic interface spec
- **Relevant tests:** `make synth-quartus`, wrapper regressions
- **Implementation notes:** keep Atari memory map outside the generic core.
- **Unresolved questions:** host-core clock and SDRAM schedule.
- **Confidence:** UNKNOWN

## M30 — Hard Drivin' ADSP-board research

### HD-RESEARCH-001 — Reconstruct ADSP and ADSP II boards

- **Status:** RESEARCHING
- **Priority:** P0
- **Dependencies:** REF-001, DEV-001
- **Acceptance criteria:** requested board variants, fitted part/package/clock,
  memory organization, host arbitration, reset/halt/IRQs, SIM/SOM, banking,
  PAL logic, and discrepancies are cited per schematic sheet/source line.
- **Source references:** ATARI-ADSP-SCHEM, ATARI-MARGOLIN,
  ATARI-HD-SERVICE, MAME-HARDDRIV, MAME-HARDDRIV-MACHINE
- **Relevant tests:** `tests/test_harddriv_metadata.py`
- **Implementation notes:** board schematics take precedence over MAME handler
  abstractions; engineer commentary establishes provenance/context.
- **Unresolved questions:** missing PAL/GAL equations and physical captures.
- **Confidence:** INFERRED

## M31 — Hard Drivin' synthetic integration tests

### HD-SYNTH-001 — Noncopyrighted board-level programs

- **Status:** NOT STARTED
- **Priority:** P2
- **Dependencies:** HD-RESEARCH-001, TOOL-001, generic core and board wrapper
- **Acceptance criteria:** synthetic tests cover host PM/DM loading, reset/halt,
  BR/BG, execution, SIM/SOM, banking, both signaling directions, X flag, and
  geometry command/result behavior with bus traces.
- **Source references:** HD-RESEARCH-001 outputs
- **Relevant tests:** `make harddriv-tests`
- **Implementation notes:** programs and fixtures must be project-authored and
  redistributable.
- **Unresolved questions:** authoritative X flag and bank-switch timing.
- **Confidence:** UNKNOWN

## M32 — Hard Drivin' ROM-based qualification

### HD-ROM-001 — Authorized local-ROM qualification

- **Status:** BLOCKED
- **Priority:** P2
- **Dependencies:** HD-SYNTH-001, VERIF-DIFF-001, local authorized ROMs
- **Acceptance criteria:** hash-verified user-supplied ROMs load; reset/initial
  trace, self-test, command wait loop, trigger, known geometry result, IRQ, and
  frame-level processing compare against MAME and available hardware captures.
- **Source references:** MAME-HARDDRIV, MAME-HARDDRIV-MACHINE,
  ATARI-ADSP-SCHEM, ATARI-HD-SERVICE, user-local ROM hash metadata
- **Relevant tests:** `make harddriv-tests` with local ROM configuration
- **Implementation notes:** never distribute ROM contents or derived large
  extracts.
- **Unresolved questions:** authorized ROM availability and physical golden
  captures.
- **Confidence:** UNKNOWN

## M33 — Release qualification

### RELEASE-001 — Architecture, verification, synthesis, and license audit

- **Status:** NOT STARTED
- **Priority:** P3
- **Dependencies:** FND-001 through HD-SYNTH-001; HD-ROM-001 where lawful
  inputs are available
- **Acceptance criteria:** every instruction-complete, cycle-accurate,
  Hard-Drivin'-ready, and release-ready criterion in the project requirements
  has linked objective evidence; all regressions/proofs/syntheses pass; no
  hidden discrepancies, license issues, or unconstrained paths remain.
- **Source references:** complete manifest and architecture corpus
- **Relevant tests:** `make test`, `make formal`, `make synth-yosys`,
  `make synth-quartus`, `make harddriv-tests`
- **Implementation notes:** release audit is independent of implementation
  existence and includes provenance plus copyright checks.
- **Unresolved questions:** remain explicit until all preceding task questions
  are resolved or bounded by documented hardware evidence.
- **Confidence:** UNKNOWN

## Next task selection

The highest-priority unblocked work is `REF-001`, especially the original
Cross-Software/opcode references, followed by `DEV-001`, per-field work in
`ISA-001`, and full register semantics in `ARCH-001`. `TIME-001` must be
completed before architectural execution RTL is permitted to claim cycle
accuracy.
