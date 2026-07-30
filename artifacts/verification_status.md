# Verification status

**Updated:** 2026-07-30

| Area | Status | Objective evidence |
|---|---|---|
| Text/source hygiene | PASS | `python3 scripts/lint_text.py` |
| Reference manifest schema | PASS | 5 tests in `tests/test_reference_manifest.py` |
| Cached reference hashes | PASS | 13/13 acquired files verified |
| Repository policy/layout | PASS | 6 tests in `tests/test_repository.py` |
| ISA class/schema | PASS, PARTIAL | 8 tests; 30 non-overlapping masks and reserved fallback |
| IF/DO condition logic | PASS | all 32 field meanings; 2,048 exhaustive RTL truth-table vectors |
| Appendix A ISA subfields | PASS, PARTIAL | 19 finite tables exhaustive; cross-field legality incomplete |
| Standard ALU compute | PASS, PARTIAL | 8 directed/model tests plus 51,472 RTL differential vectors |
| Standard MAC compute | PASS, PARTIAL | 8 directed/model tests plus 21,760 RTL differential vectors |
| Shifter compute | PASS, PARTIAL | 10 directed/model tests plus 644,368 RTL differential vectors |
| DAG arithmetic | PASS, PARTIAL | 10 directed/random model tests plus 204,864 RTL differential vectors |
| Sequencer flow arbitration | PASS, PARTIAL | 9 directed/random model tests plus 636,512 RTL differential vectors |
| Computational register banks | PASS, PARTIAL | 14 directed/model tests plus 58,307 DREG and 50,120 full-bank/writeback RTL cycles |
| Formal harnesses | SYNTAX PASS, PROOFS NOT RUN | condition/ALU/MAC/shifter/DAG/sequencer/register recipes lint; SymbiYosys unavailable |
| Register encoding metadata | PASS, PARTIAL | 4 tests; all 64 RGP/REG positions accounted |
| Assembler/disassembler | PASS, PARTIAL | 5 tests; NOP only, reserved words fail closed |
| Model foundation | PASS, PARTIAL | 11 exact-width/reset/image/NOP/trace tests |
| SystemVerilog lint | PASS, PARTIAL | Verilator 5.048, type and generated decode packages |
| Semantic decode completeness | NOT STARTED | class decode exists; only NOP has full semantics |
| Instruction execution RTL | NOT STARTED | no execution core exists |
| Differential testing | NOT STARTED | no comparable RTL implementation |
| Hard Drivin' synthetic tests | NOT STARTED | no board wrapper exists |

The implemented foundation regression is `make test`: 114 distinct Python
checks plus the 2,048-vector condition and 51,472-vector ALU Verilator
regressions, 21,760-vector MAC regression, and 644,368-vector shifter
regression, plus the 204,864-vector DAG and 636,512-vector sequencer-flow
regressions, 58,307 stateful DREG cycles, and 50,120 complete-bank/writeback
cycles. Targets for
unavailable or unimplemented areas print `SKIP` and do not create false pass
evidence.
