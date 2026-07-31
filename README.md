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
integration. Commands return nonzero on a real
failure.
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
