# Verification status

**Updated:** 2026-07-31

| Area | Status | Objective evidence |
|---|---|---|
| Text/source hygiene | PASS | `python3 scripts/lint_text.py` |
| Reference manifest schema | PASS | 5 tests in `tests/test_reference_manifest.py` |
| Cached reference hashes | PASS | 14/14 acquired files verified |
| Repository policy/layout | PASS | 6 tests in `tests/test_repository.py` |
| ISA class/schema | PASS, PARTIAL | 8 tests; 30 non-overlapping masks and reserved fallback |
| Instruction-format bit placement | PASS, PARTIAL | 7 tests; 30 formats, 106 fields, and 393 variable positions independently fixture-checked; semantic legality incomplete |
| Exhaustive RTL class decode | PASS | all 16,777,216 words match independent Appendix A classifier |
| Type 6 immediate DREG load | PASS, PARTIAL | all 1,048,576 class words decode exactly in Python and RTL; 6 directed/model tests, 2 hand fixtures, assembler/disassembler round trips, and 50,204 stateful RTL cycles cover both banks, every DREG, exact SE/MR2 and MR1 side effects, invalid words, and conflicts; fetch/PC, interrupt adjacency, and bus phases remain |
| Type 17 internal MOVE | PASS, PARTIAL | 6 action/schema tests plus 7 state tests; all 4,096 class words partition into 2,256 legal moves and 1,840 reserved/read-only-destination subencodings, all 2,256 legal pairs round trip, all 4,512 pair/bank state executions pass, and 59,430 RTL cycles compose computational, DAG, status, PX, CNTR/count-stack, and SSTAT state; OQ-016 narrow status extension and whole-core timing remain |
| Type 26 stack-control action decode | PASS, PARTIAL | 6 model/schema tests; all 32 field-defined words checked and all other 24-bit words proven action-free by exhaustive RTL simulation |
| Type 26 stateful execution | PASS, PARTIAL | 9 directed/schema/random model tests plus 50,015 stateful RTL cycles connect all four stacks, CNTR, live status, and SSTAT; fetch/PC, automatic-flow, interrupt/RTI arbitration, OQ-013, and bus phases remain |
| Type 25 MR saturation | PASS, PARTIAL | exact opcode fixture and exhaustive 24-bit RTL decode; 9 directed/schema/random model tests plus 50,112 stateful RTL cycles verify MV false/true, both signs/banks, status preservation, reset unknowns, invalid words, and conflict suppression; fetch/PC, interrupt adjacency, and bus phases remain |
| Type 18 mode control | PASS, PARTIAL | 8 directed/schema/random model tests; all 256 field-defined words, 81 action bundles, 16 actionless aliases, all 4,096 opcode/initial-MSTAT transforms, exhaustive 24-bit RTL decode, and 58,248 stateful RTL cycles pass; fetch/PC, interrupt adjacency, and bus phases remain |
| Type 21 address modify | PASS, PARTIAL | all 32 same-DAG selections and every other 24-bit word checked exhaustively; 10 directed/schema/random model tests plus 50,124 stateful RTL cycles verify exact I/M/L storage, both DAGs, signed linear/circular updates, selected-I-only writeback, reset unknowns, invalid configurations, and collision suppression; fetch and general data-transfer/multifunction/bus attachment remain |
| IF/DO condition logic | PASS | all 32 field meanings; 2,048 exhaustive RTL truth-table vectors |
| Appendix A ISA subfields | PASS, PARTIAL | 19 finite tables exhaustive; cross-field legality incomplete |
| Standard ALU compute | PASS, PARTIAL | 8 directed/model tests plus 51,472 RTL differential vectors |
| Standard MAC compute | PASS, PARTIAL | 8 directed/model tests plus 21,760 RTL differential vectors |
| Shifter compute | PASS, PARTIAL | 10 directed/model tests plus 644,368 RTL differential vectors |
| DAG arithmetic | PASS, PARTIAL | 10 directed/random model tests plus 204,864 RTL differential vectors |
| Sequencer flow arbitration | PASS, PARTIAL | 9 directed/random model tests plus 636,512 RTL differential vectors |
| CNTR state and CE transitions | PASS, PARTIAL | 12 directed/random model tests plus 50,022 stateful RTL cycles; conditional-CALL CE, decode, and empty-pop effects remain |
| PC/count/loop stack storage | PASS, PARTIAL | 10 directed/random model tests plus 50,062 stateful RTL cycles; decode/interrupt connectivity and empty-pop effects remain |
| Bounded sequencer integration | PASS, PARTIAL | 14 directed/random model tests plus 50,011 stateful RTL cycles connect IF/DO, flow, CNTR, and PC/count/loop stacks; PC state, decode, interrupts, OQ-012/OQ-013/OQ-018, and phase timing remain |
| Computational register banks | PASS, PARTIAL | 14 directed/model tests plus 58,307 DREG and 50,120 full-bank/writeback RTL cycles |
| Status/control storage | PASS, PARTIAL | 17 directed/model tests plus 50,287 stateful RTL cycles; all SSTAT storage sources exist and bounded Type 17/Type 26 slices compose them, but whole-core interrupt recognition/connectivity and decode remain |
| Status stack | PASS, PARTIAL | 8 directed/model tests plus 50,037 stateful RTL cycles; interrupt/RTI connectivity and empty-pop effects remain |
| MSTAT consumer integration | PASS, PARTIAL | 5 directed/model tests plus 50,112 stateful RTL cycles across bank, DAG1, sticky AV, and saturation consumers; decode and interrupt-adjacent timing remain |
| Formal harnesses | SYNTAX PASS, PROOFS NOT RUN | 25 recipes, including exact Type 6/Type 17/Type 21 action decode and bounded state execution, pass strict assertion syntax lint; SymbiYosys/Yosys unavailable |
| Register encoding metadata | PASS, PARTIAL | 4 tests; all 64 RGP/REG positions accounted |
| Assembler/disassembler | PASS, PARTIAL | 12 tests; NOP, all Type 6 immediate/DREG forms, parameterized Type 18, all 2,256 legal Type 17 pairs, all 32 Type 21 selections, exact Type 25, and raw alias words round trip; SSTAT destinations, illegal cross-DAG, and reserved words fail closed |
| Model foundation | PASS, PARTIAL | 11 exact-width/reset/image/NOP/trace tests |
| SystemVerilog lint | PASS, PARTIAL | Verilator 5.048, generated packages and class-decoder RTL plus implemented architectural slices |
| Semantic decode completeness | IMPLEMENTING | NOP, Type 6, Type 18, Type 21, and exact Type 25 have full semantic entries; Type 17 and Type 26 action selection and bounded state execution are exact except Type 17's flagged OQ-016 hypothesis; remaining classes and whole-core integration are incomplete |
| Instruction execution RTL | IMPLEMENTING, BOUNDED | Type 6, Type 17, Type 18, Type 21, Type 25, and Type 26 state slices execute sourced actions, but no integrated fetch/decode/PC/bus core exists |
| Differential testing | PASS, PARTIAL | independent-model comparison covers 50,204 Type 6, 59,430 Type 17, 58,248 Type 18, 50,124 Type 21, 50,112 Type 25, and 50,015 Type 26 stateful cycles; no whole-core or MAME execution harness exists |
| Hard Drivin' synthetic tests | NOT STARTED | no board wrapper exists |

The implemented foundation regression is `make test`: 255 distinct Python
checks plus exhaustive 16,777,216-word class decode, the 2,048-vector
Type 26 action-decode pass, the exhaustive Type 6, Type 17, Type 18, Type 21, and exact Type 25 decodes,
2,048-vector condition and 51,472-vector ALU
Verilator
regressions, 21,760-vector MAC regression, and 644,368-vector shifter
regression, plus the 204,864-vector DAG and 636,512-vector sequencer-flow
regressions, 50,022 CNTR cycles, 50,011 bounded sequencer-integration cycles,
58,307 stateful DREG cycles, and 50,120 complete-bank/writeback cycles, plus
50,287 status/control and 50,037 status-stack state-transition cycles, plus
50,062 PC/count/loop stack-storage cycles, 50,112 MSTAT-consumer integration
cycles, 50,015 stateful Type 26 execution cycles, and 50,112 Type 25
stateful cycles, plus 50,204 Type 6, 59,430 Type 17, 58,248 Type 18, and
50,124 Type 21 stateful cycles.
Targets for unavailable
or unimplemented areas print
`SKIP` and do not create false pass evidence.
