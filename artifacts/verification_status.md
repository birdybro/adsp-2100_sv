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
| Type 26 stack-control action decode | PASS, PARTIAL | 6 model/schema tests; all 32 field-defined words checked and all other 24-bit words proven action-free by exhaustive RTL simulation; stateful execution and OQ-013 remain |
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
| Status/control storage | PASS, PARTIAL | 17 directed/model tests plus 50,287 stateful RTL cycles; all SSTAT storage sources exist, but fragment composition, interrupt recognition/connectivity, and decode remain |
| Status stack | PASS, PARTIAL | 8 directed/model tests plus 50,037 stateful RTL cycles; interrupt/RTI connectivity and empty-pop effects remain |
| MSTAT consumer integration | PASS, PARTIAL | 5 directed/model tests plus 50,112 stateful RTL cycles across bank, DAG1, sticky AV, and saturation consumers; decode and interrupt-adjacent timing remain |
| Formal harnesses | SYNTAX PASS, PROOFS NOT RUN | 15 class-decode/stack-control-decode/condition/ALU/MAC/shifter/DAG/sequencer-flow/CNTR/sequencer-stack/sequencer-integration/register/status/status-stack/MSTAT-integration recipes lint; SymbiYosys unavailable |
| Register encoding metadata | PASS, PARTIAL | 4 tests; all 64 RGP/REG positions accounted |
| Assembler/disassembler | PASS, PARTIAL | 5 tests; NOP only, reserved words fail closed |
| Model foundation | PASS, PARTIAL | 11 exact-width/reset/image/NOP/trace tests |
| SystemVerilog lint | PASS, PARTIAL | Verilator 5.048, generated packages and class-decoder RTL plus implemented architectural slices |
| Semantic decode completeness | IMPLEMENTING | NOP has full semantics; Type 26 action selection is complete but not statefully executed; all other classes remain incomplete |
| Instruction execution RTL | NOT STARTED | no execution core exists |
| Differential testing | NOT STARTED | no comparable RTL implementation |
| Hard Drivin' synthetic tests | NOT STARTED | no board wrapper exists |

The implemented foundation regression is `make test`: 193 distinct Python
checks plus exhaustive 16,777,216-word class decode, the 2,048-vector
Type 26 action-decode pass, the 2,048-vector condition and 51,472-vector ALU
Verilator
regressions, 21,760-vector MAC regression, and 644,368-vector shifter
regression, plus the 204,864-vector DAG and 636,512-vector sequencer-flow
regressions, 50,022 CNTR cycles, 50,011 bounded sequencer-integration cycles,
58,307 stateful DREG cycles, and 50,120 complete-bank/writeback cycles, plus
50,287 status/control and 50,037 status-stack state-transition cycles, plus
50,062 PC/count/loop stack-storage cycles and 50,112 MSTAT-consumer
integration cycles. Targets for unavailable or unimplemented areas print
`SKIP` and do not create false pass evidence.
