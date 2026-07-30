# Changelog

All notable engineering changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
semantic versioning after its first release.

## [Unreleased]

### Added

- Repository governance, contribution policy, required directory layout, and
  explicit evidence-based completion rules.
- Initial reference provenance schema and safe local-cache workflow.
- Initial architecture, timing, integration, decision, and research framework.
- Foundation automation for manifest validation, repository checks, model
  tests, lint entry points, and optional-tool reporting.
- Eighteen-record reference manifest with thirteen hash-verified local sources,
  including original ADI manuals/data book, Atari schematics, and a pinned
  MAME ADSP/Hard Drivin' source set.
- Isolated sparse MAME checkout workflow pinned to commit
  `030fefcbd14e47c01ec9d67655be90f64a1dc8ab`.
- Machine-readable 30-class original opcode inventory with a complete-field,
  hand-verified all-zero NOP fixture and fail-closed schema validator.
- Primary-transcribed masks for all 30 original encoding classes, explicit
  accounting for 1,304,054 unshown-reserved words, generated synthesizable
  class decode, and a generated opcode table.
- Original RGP/REG general-MOVE table accounting for 48 register encodings,
  reserved holes, storage widths, and verified narrow-register extension
  behavior.
- Independent Python exact-width state, authentic reset-unknown
  classification, deterministic random-state/replay foundation, PM fetch
  transactions, program/data image loading, reserved-code rejection, and the
  verified NOP execution slice.
- Partial database-driven assembler/disassembler that round-trips the
  independent NOP fixture and fails closed for unimplemented/reserved words.
- Shared SystemVerilog width/phase/type package and GitHub Actions foundation
  regression.

### Changed

- Expanded the initial README to state the exact ADSP-2100 scope and current
  non-complete status.
- Identified the contemporary original ADSP-2100 data sheet within the 1987
  ADI data book at printed pages 2-15 onward.

### Fixed

- Made clean-checkout CI independent of the intentionally untracked reference
  cache while retaining strict local hash checks whenever the cache is present.

### Verified

- Existing repository state and installed-tool baseline recorded on
  2026-07-30: Git/Python/Make/Verilator/Quartus available; pytest, Icarus,
  Yosys, SymbiYosys, and svlint unavailable.
- `make test` passes 40 Python checks, ISA/register validators, thirteen cached
  reference hash checks, generated-file checks, and strict Verilator 5.048
  package lint.

### Documentation

- Established primary-source precedence, clean-room rules, clock/reset policy,
  signedness policy, verification expectations, and provenance requirements.
- Added first-pass original-device programmer, compute, DAG, sequencer,
  bus/timing, scope/matrix, and Hard Drivin' host/SIM/SOM/interrupt/PAL notes
  with explicit confidence boundaries.
- Recorded original-reserved versus later-family reuse and the Type 19 bit-5
  disagreement with MAME as explicit source conflicts.

### Known Issues

- Cross-Software, evaluation-board, independent data-sheet revisions, errata,
  and page-level opcode-field and semantic extraction remain incomplete.
- No instruction, cycle, bus, interrupt, or Hard Drivin' compatibility claim is
  complete.
- Open-source synthesis and formal tools are not installed in this environment.

[Unreleased]: https://github.com/birdybro/adsp-2100_sv/compare/HEAD...HEAD
