# adsp-2100_sv

Clean-room, source-traceable SystemVerilog reimplementation of the original
Analog Devices ADSP-2100 fixed-point DSP.

The eventual integration target is the Atari Hard Drivin' ADSP geometry board
for MiSTer. The processor core itself is intended to remain portable,
vendor-neutral, and useful outside that system.

## Status

This repository is in the research and foundation phase. It is **not** yet an
instruction-complete, cycle-accurate CPU core. No compatibility, timing, or
synthesis-completeness claim should be inferred from the presence of a file or
module. See [TASKS.md](TASKS.md) and
[artifacts/verification_status.md](artifacts/verification_status.md) for the
evidence attached to each claim.

Current work deliberately separates:

- primary-source architectural facts;
- later ADSP-21xx family behavior;
- Atari schematic evidence;
- behavior observed in software and emulators;
- provisional implementation choices.

## Quick start

Requirements for the foundation tests are Python 3.11 or newer and GNU Make.
Optional HDL and formal tools are detected rather than silently assumed.

```sh
make test
make lint
make synth-yosys
make formal
```

`make test` currently validates repository policy, the reference manifest,
machine-readable architecture tables, exhaustive 24-bit instruction-class
decode, independent block models, and the
implemented compute, DAG, sequencer-flow, CNTR, PC/count/loop/status-stack,
computational-register, and status/control RTL slices, including bounded
sequencer, MSTAT-consumer, Type 25 MR-saturation, and Type 26 stack-control
integration, plus exact Type 18 mode-control and Type 21 address-modify
execution, exact Type 6 immediate-to-DREG execution across both computational
banks, the 14,336 source-closed Type 15 immediate LSHIFT/ASHIFT words with
selected-bank SR writeback, 25,648 canonical Type 14 shifter-plus-DREG
multifunction words with old-value parallel semantics, all 2,097,152 Type 4
words partitioned at the action boundary into 2,034,688 source-closed
compute/memory or memory-only actions and 62,464 fail-closed DM-read
destination collisions, with waited logical DM transactions and atomic
selected-bank compute/read/DAG completion across 50,072 clocks and a separate
50,082-clock native-DM attachment comparison, all 2,097,152 original Type 2
immediate-DM-write words with captured raw data, waited logical DMACK
transactions, and completion-only DAG post-modification, 108,640 source-closed
Type 12 shifter-plus-DM words with ACK-stretched logical bus transactions and
atomic shifter/DREG/DAG completion, plus bounded source-backed native DM
attachments for Type 2, Type 4, and Type 12 issue, read/write pin phases, wait
extension, and completion, 54,320 source-closed Type 13
shifter-plus-PM words with the original 16-word cache monitor now connected
for pre-cycle hits, one-cycle recovery fetches, recovery fills, and ordinary
external instruction fills, plus a source-backed eight-state native PM
pin-phase attachment that captures the Type 13 descriptor at state 8-to-1,
commits its architectural effects at state 7-to-8, performs back-to-back miss
recovery, preserves select continuity, and masks relinquished bus outputs,
an exhaustive original Type 5 action boundary with 1,017,344 ALU/MAC-plus-PM
or PM-only words and 31,232 explicit read collisions (state/cache/native-PM
execution pending),
476,672 Type 8
ALU/MAC-plus-DREG multifunction words with atomic result/status/move
writeback, all 32,768 Type 9 conditional ALU/MAC words including documented
AMF-zero no-operation aliases, 507,904 source-closed Type 10 direct JUMP/CALL
words with a decoder-connected PC register, CALL return stacking, and JUMP
NOT CE counter transitions, all 262,144 Type 11 DO UNTIL setup words with
simultaneous PC/loop-stack state, 124 source-closed Type 19 DAG2-indirect
JUMP/CALL words with PMA target observation, all 32 Type 20 conditional RTS/RTI
words with valid-stack PC/status restoration, all 16 Type 22 conditional TRAP
words with phase-aware state-7/state-8 assertion and HALT restart, all eight
source-closed Type 23 DIVQ forms with iterative AF/AY0/AQ update, all sixteen
source-closed Type 24 DIVS operand combinations with atomic AF/AY0/AQ
writeback and reset-unknown validity tracking, all 1,792 source-backed Type 16 conditional
LSHIFT/ASHIFT/NORM/EXP/EXPADJ words with selected-bank and status writeback,
and bounded Type 17 internal-MOVE execution across
computational, DAG, status/control, PX, CNTR/count-stack, and SSTAT state.
OQ-016 narrow status reads, OQ-021 Type 14 bit 15, OQ-022 Type 8 AMF zero,
47,616 fail-closed Type 8 words, 39,888 fail-closed Type 14
subencodings, 18,432 unverified Type 15 subencodings, and 256 unassigned-XOP
Type 16 subencodings remain explicitly unresolved or unsupported. Type 12's
16,384 unavailable-XOP words and 6,048 DM-read destination collisions fail
closed. The 16,384
Type 10 and four Type 19 CALL NOT CE words remain fail-closed under OQ-012.
General HALT synchronization, BR/BG, interrupt arbitration, and complete PM
strobes remain outside the bounded Type 22 controller. Pinned MAME's
conflicting reserved classification is recorded as SC-013.
The Type 24 AY0/zero YOP field words remain fail-closed, and the later-device
division-flag conflict is recorded as SC-014. Division exists as bounded
instruction slices, not yet in the top-level fetch/decode/execute model.
Type 2, Type 4, and Type 12 supply logical DM transaction boundaries, and a separate
native controller reproduces the original active-low DM phases and full-cycle
DMACK extension. All three clients attach at state 8-to-1 and defer every
architectural destination, including read data and selected-I postmodify, to
the qualified state 7-to-8 completion. Type 13 supplies a cache-integrated
logical PM data/recovery
boundary attached to the original active-low logical pin phases. These remain
bounded clients, not an integrated fetch/decode/execute bus owner; ordinary
fetch arbitration, other PM instruction classes, and BR/BG remain
unimplemented.
Commands return nonzero on a real failure.
Optional commands report `SKIP` when their named tool is unavailable.

## Reference handling

Copyrighted or redistribution-unclear source documents are not committed.
Their provenance and expected hashes live in
[docs/references/manifest.yaml](docs/references/manifest.yaml); authorized
users can fetch configured public sources with:

```sh
python3 scripts/fetch_references.py
python3 scripts/verify_reference_hashes.py
python3 scripts/report_missing_references.py
```

Downloads go to the gitignored `reference_cache/` directory and are never
executed. See [docs/references/README.md](docs/references/README.md).

## Repository guide

- `docs/architecture/`: source-backed architectural specifications
- `docs/research/`: open questions, conflicts, and research logs
- `docs/references/`: provenance metadata, never a manual dump
- `docs/timing/`: logical-cycle and electrical timing research
- `rtl/`: portable synthesizable SystemVerilog
- `sim/reference_models/`: independent executable architectural model
- `tests/`: hand-reviewed fixtures and deterministic regressions
- `formal/`: properties and proof harnesses
- `synthesis/`: portable and target-specific synthesis projects
- `rtl/wrappers/`: platform adapters kept outside the generic core

## Contributing

Read [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md), and the
relevant architecture decision records before changing architectural behavior.
Every meaningful engineering cycle updates both `TASKS.md` and `CHANGELOG.md`.

## License

Project-authored source and documentation are licensed under the existing MIT
License in [LICENSE](LICENSE). Third-party references retain their own
copyrights and licenses and are not relicensed by this project.
