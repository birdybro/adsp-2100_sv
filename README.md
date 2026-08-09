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

The hash-pinned 1989 joint ADI data sheet now establishes that the ADSP-2100
and ADSP-2100A are pin/code compatible and share the documented architecture
and instruction set, while their speed and electrical/timing grades differ.
Undocumented mask fixes and errata remain open, so the default is still the
original ADSP-2100 [ADI-DATABOOK-1989, printed p. 2-19].

## Quick start

Requirements for the foundation tests are Python 3.11 or newer and GNU Make.
Optional HDL and formal tools are detected rather than silently assumed.

```sh
make test
make lint
make synth-yosys
make formal
make differential
make fuzz
```

The bounded differential tooling now includes a versioned NDJSON retirement
schema with bitwise known masks, a complete independent-model state adapter,
an exact state/transaction comparator, and a deterministic one-minimal failure
reducer. A deterministic model-side program generator covers thirteen source-
closed straight-line classes from known replayable state; `make fuzz` executes
4,096 seeded retirements and qualifies the reducer. The replay CLI at
`tools/trace/run_legal_program.py` emits canonical corpora and byte-stable
common traces. RTL and pinned-MAME program adapters remain unavailable, and no
unpinned system MAME executable is used as an oracle. See
[docs/architecture/differential_trace.md](docs/architecture/differential_trace.md).

`make test` currently validates repository policy, the reference manifest,
machine-readable architecture tables, exhaustive 24-bit instruction-class
decode, independent block models, and the
implemented compute, DAG, sequencer-flow, CNTR, PC/count/loop/status-stack,
computational-register, and status/control RTL slices, including bounded
sequencer, MSTAT-consumer, Type 25 MR-saturation, and Type 26 stack-control
integration, plus exact Type 18 mode-control and Type 21 address-modify
execution, exact Type 6 immediate-to-DREG execution across both computational
banks, the 14,336 source-closed Type 15 immediate LSHIFT/ASHIFT words with
selected-bank SR writeback, all 507,904 supported Type 7 immediate-to-non-data
register words with exact-width state, selected-bank SB, and CNTR/count-stack
effects, and bounded independent-model/native-RTL integration in which NOP,
legal Type 6/7, all 476,672 source-closed Type 8 ALU/MAC-plus-DREG words, all
Type 9 conditional ALU/MAC words, all 2,256 legal Type 17
internal MOVE source/destination pairs, all 25,648 canonical Type 14 shifter-
plus-DREG packets, all eight Type 23 DIVQ words, all sixteen source-closed
Type 24 DIVS words, the exact Type 25 conditional
MR-saturation word, all 32 Type 21 address-modify words, all 32 Type 26
manual stack-control words, all 507,904 source-closed Type 10 direct JUMP/CALL
words, all 262,144 Type 11 DO UNTIL words, all 124 source-closed Type 19
indirect JUMP/CALL words, all 32 Type 20 conditional RTS/RTI words, all 16
Type 22 conditional TRAP words, all
14,336 supported Type 15 immediate
shift words, all 1,792 supported Type 16 conditional shift words, and all Type
18 MODE CONTROL words
execute at the current PC while the selected sequential, direct, indirect,
return, or automatic-loop target word is fetched across the sourced state-8
issue/state-7 retire phases, with 444,003 model/RTL phase clocks and an
explicit OQ-016
provisional-source retirement pulse. The private owner also samples the four
original active-low IRQ pins at state 7, retains edge requests, applies
ICNTL/IMASK and fixed priority, discards the concurrent following fetch on
recognition, performs a vectoring NOP with PC/status entry pushes, fetches
vectors 0–3, and returns through fetched RTI; the standalone recognizer passes
50,027 clocks, while OQ-025 keeps its first post-reset edge baseline
provisional. A bounded normal-BR/BG attachment adds
50,054 clocks and 87 complete current-fetch/inhibit/grant/restart handshakes,
and a separate bounded active-low HALT attachment adds 50,048 clocks, 789
ordinary-fetch stop/restart sequences, and one complete fetched Type 22 TRAP
assertion/HALT-clear/handoff/restart sequence with state-8 PM stability and
DMACK-qualified release. Both now retain a state-7-sampled IRQ through the
no-service interval and enter on the qualified resume edge; the retained-fetch/
shared-PM BR/BG composition covers the same rule across 50,054 clocks. The
ordinary-fetch/native-DM composition now owns real fetched Type 2, every legal
Type 3 transfer, every source-closed Type 4 ALU/MAC-plus-DM action, and every
source-closed Type 12 shifter-plus-DM action. It now also composes normal
BR/BG and ordinary-fetch HALT. State-3 recognition remains live during a
DMACK extension; grant or HALT stop service is deferred until the current
PM/DM instruction completes, while future issue is inhibited. Native grant
masks every PM and DM output enable. HALT instead holds the driven buses in
stable state 8, blocks release while DMACK is low, and resumes the retained
next word at state 8-to-1 after a qualified release. Same-boundary and
cross-owner BR/HALT requests fail closed and report a conflict without
assigning an unsourced priority; an already active owner is preserved. Its
twenty-two directed checks and 50,000-clock comparison cover 73 generated Type 2 accepts,
149 generated Type 3,
2,057 generated Type 4, and 119 generated Type 12 descriptors; every Type 2
G/I/M selection; every legal Type 3 register source/destination; all 2,048 Type
4 `(Z, AMF, YOP, XOP)` tuples; all 112 sourced Type 12 `(SF, XOP)` pairs; every
Type 4/Type 12 DAG/I/M and DREG selector; both directions; address/immediate
boundaries; DAG1 bit reversal; circular wrap; and full-cycle waits. Each
physical state-7 pass can sample IRQ while the DM transfer, PM fetch,
architectural owner, vector issue, and context push remain held until aligned
completion. Thirteen BR recognitions include one first sampled during an active
wait; three aligned completions precede pending grant service, twelve grants
mask both buses, and ten release/reacquire/resume handshakes complete. The Type
2 selected-I postmodify, Type 3 load destination, Type 4
compute/status/read/I effects, or Type 12 shifter/status/read/I effects retire
with PC and the returned instruction exactly once. Fetched Type 3/4/12 stores
and compute/shift operands are initialized and loads use valid DMD; their
standalone slices retain the reset-unknown/invalid-data evidence. A raw
descriptor port remains structural scaffolding. The fail-closed shared-DM
owner is now attached behind an atomic preflight: a generated/raw collision
accepts neither PM nor DM request and retains the fetched instruction for
retry. One real Type 2 wait covers HALT recognition, deferred stop,
completion-aligned retirement, state-8 hold, DMACK-blocked release, and
resume. Additional architectural DM requesters remain unintegrated. Unsourced
BR/HALT overlap or BR overlap with TRAP or interrupt service is conflict-
reported instead of receiving an invented priority. The real Type 5 and
Type 13 native/cache owners now
also sample an edge at uncached PM-data completion without servicing it, then
release recognition only when the immediately following recovery fetch
completes; their independent comparisons pass 50,100 and 50,098 clocks. A
bounded composition places the real retained ordinary-fetch, Type 5, and
Type 13 clients behind one 16-word cache, one native PM controller, and normal
BR/BG. Both PM-data clients are state-external action clients of the retained
fetch client's sole architectural-state owner. Forty-five directed checks and
51,587 independent-model/RTL clocks retain the cross-client state/cache/BR-BG
coverage and now drive a current fetched Type 5 or Type 13 directly from the
retained opcode and PC. A cache hit installs PC+1 in the same logical
instruction cycle; a miss commits the PM-data action once, performs one pure
external recovery fetch, then installs the returned word and advances the
14-bit PC, including `0x3fff` wrap. A directed edge-sensitive IRQ2 remains
pending through that miss interval, recognizes only at whole-instruction
retirement, discards the returned sequential word, pushes PC/status context,
and fetches vector 2 through the ordinary client. A second IRQ2 sequence enters
after reset-unknown AX1 has
invalidated ASTAT/MSTAT, fetches RTI from vector 2, and restores those pre-entry
validity classifications before dependent PM work. Fetched Type 3 DM reads
propagate returned-data validity to every selected destination, and Type 4
compute plus Type 12 shifter results track their parallel DMD-read validity
independently. Following PM stores exercise both known-result/unknown-read and
unknown-result/known-read cases. Fetched Type 17 also reads
the live SSTAT low byte through status-stack empty, nonempty, overflow, and
empty-with-sticky-overflow transitions; upper extension remains OQ-016. HALT
is also attached at the
combined owner: ordinary fetch completes before stopping; a Type 5/Type 13
PM-data recognition invalidates a cache hit, commits once, performs one forced
external recovery, and then stops. Release is DMACK-qualified. Simultaneous
BR/HALT requests fail closed because the sources do not establish priority.
Active-loop PM issue likewise fails closed. Validity sidecars now cover every
implemented fetched result in this combined owner and the status-stack entry/
return paths exercised here. TRAP/interrupt/HALT/BR cross-event priority,
additional DM requesters, Type 1 simultaneous PM/DM timing under OQ-023, and
whole-core event ownership remain open. The
standalone HALT sequencer adds 50,033 clocks
covering both cycle
classes, including 335 PM-data recognitions that each emit exactly one forced
external-fetch issue before stop; a Type 13 attachment adds 50,124 clocks in
which every late HALT overrides an issue-time cache hit, completes the data
action once, performs one native external fetch, and stops only after that
fetch; a Type 5 attachment adds 50,126 clocks covering the corresponding
ALU/MAC-plus-PM path, including 197 late hit overrides/forced fetches and 387
stop/resume handshakes without replay,
25,648 canonical
Type 14 shifter-plus-DREG
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
attachments for Type 2, Type 3, Type 4, and Type 12 issue, read/write pin phases, wait
extension, and completion, 54,320 source-closed Type 13
shifter-plus-PM words with the original 16-word cache monitor now connected
for pre-cycle hits, one-cycle recovery fetches, recovery fills, and ordinary
external instruction fills, plus a source-backed eight-state native PM
pin-phase attachment that captures the Type 13 descriptor at state 8-to-1,
commits its architectural effects at state 7-to-8, performs back-to-back miss
recovery, preserves select continuity, and masks relinquished bus outputs,
an exhaustive original Type 5 boundary with 1,017,344 ALU/MAC-plus-PM or
PM-only words and 31,232 explicit read collisions, selected-bank compute/DAG2/
PX execution, cache-hit or one-cycle recovery selection, and native state-8
issue/state-7 completion,
all 4,194,304 Type 1 words decoded as source-closed fixed-DAG1-DM plus
DAG2-PM dual-read actions with cycle-start computation operands, cycle-end
DD/PD loads, implicit AR/MR result selection, and AMF-zero dual fetch, plus a
bounded logical state slice whose 12 directed/model checks and 51,069
model/RTL clocks hold and atomically commit both reads, PX, both DAG-I
postmodifications, and optional compute/status across both banks,
all 2,097,152 Type 3 direct-DM words partitioned into 1,556,480 supported
general-register transfers and 540,672 explicit reserved/read-only-destination
words, with selected-bank/general-register execution, waited logical
transactions, and native state-8 issue/state-7 completion,
476,672 Type 8
ALU/MAC-plus-DREG multifunction words with atomic result/status/move
writeback in both the exhaustive standalone slice and the bounded fetched
owner, all 32,768 Type 9 conditional ALU/MAC words including documented
AMF-zero no-operation aliases, 507,904 source-closed Type 10 direct JUMP/CALL
words with a decoder-connected PC register, native target fetch, shared CALL
return stacking, JUMP NOT CE counter transitions, and a fetched Type 26 POP PC
consumer, all 262,144 Type 11 DO UNTIL setup words with simultaneous
PC/loop-stack state plus fetched non-counter/ASTAT/CE automatic loopback/exit
and explicit-flow precedence, including one nonterminal fetched Type 26 word
that atomically pops valid status, count, PC, and loop contexts, 124
source-closed Type 19 DAG2-indirect
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
General HALT owner composition beyond the ordinary-fetch and bounded Type 5
and Type 13 attachments, simultaneous ordinary-HALT/TRAP priority,
active-interrupt arbitration with those events, reset-first-fetch, and unified
PM-client PC/opcode flow
remain outside the fetched Type 22 attachment. Pinned MAME's
conflicting reserved classification is recorded as SC-013.
The Type 24 AY0/zero YOP field words remain fail-closed, and the later-device
division-flag conflict is recorded as SC-014. Both division primitives now
execute in the bounded ordinary-fetch owner alongside Types 10/11/19/20,
automatic loop flow, and bounded private-owner interrupt entry, but other
control transfers and active-IRQ composition with PM-data,
reset-first-fetch, and unified register/event ownership remain open.
Type 2, Type 3, Type 4, and Type 12 supply logical DM transaction boundaries, and a separate
native controller reproduces the original active-low DM phases and full-cycle
DMACK extension. All four clients attach at state 8-to-1 and defer every
architectural destination, including read data and selected-I postmodify, to
the qualified state 7-to-8 completion. A further bounded ordinary-fetch/native-
DM composition now derives Type 2, legal Type 3, source-closed Type 4, and
source-closed Type 12 descriptors from the retained fetched opcode and live
architectural state, pairs them with the overlapped PM fetch through waits,
and retires their register/DAG/compute/shifter/status effects with PC and the
next word only at aligned completion.
Types 5 and
13 supply cache-integrated
logical PM data/recovery
boundary attached to the original active-low logical pin phases. These remain
bounded clients, not a unified fetch/decode/execute core. The three real
clients now share one bounded cache/native-PM/BR-BG composition, and Type 5
and Type 13 use the retained fetch client's sole architectural-state owner.
Sequential Type 5/Type 13 issue, cache-hit or recovery next-instruction
installation, retirement-aligned IRQ entry, and the documented ordinary/PM-
data HALT schedules now use that retained PC/opcode flow. Active loops and
unsourced simultaneous-event priorities fail closed.
Type 1 now executes bounded logical dual-bus state behind an explicit
implementation/test completion input. It is not attached to native PM/DM
phases, cache/fetch ownership, or the integrated core: OQ-023 records the
unresolved native PM behavior when DMACK extends the simultaneous DM cycle.
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
