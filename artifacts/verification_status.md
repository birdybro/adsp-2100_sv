# Verification status

**Updated:** 2026-07-30

| Area | Status | Objective evidence |
|---|---|---|
| Text/source hygiene | PASS | `python3 scripts/lint_text.py` |
| Reference manifest schema | PASS | 5 tests in `tests/test_reference_manifest.py` |
| Cached reference hashes | PASS | 13/13 acquired files verified |
| Repository policy/layout | PASS | 5 tests in `tests/test_repository.py` |
| ISA class/schema | PASS, PARTIAL | 8 tests; 30 non-overlapping masks and reserved fallback |
| IF/DO condition logic | PASS | all 32 field meanings; 2,048 exhaustive RTL truth-table vectors |
| Appendix A ISA subfields | PASS, PARTIAL | 19 finite tables exhaustive; cross-field legality incomplete |
| Register encoding metadata | PASS, PARTIAL | 4 tests; all 64 RGP/REG positions accounted |
| Assembler/disassembler | PASS, PARTIAL | 5 tests; NOP only, reserved words fail closed |
| Model foundation | PASS, PARTIAL | 11 exact-width/reset/image/NOP/trace tests |
| SystemVerilog lint | PASS, PARTIAL | Verilator 5.048, type and generated decode packages |
| Semantic decode completeness | NOT STARTED | class decode exists; only NOP has full semantics |
| Instruction execution RTL | NOT STARTED | no execution core exists |
| Differential testing | NOT STARTED | no comparable RTL implementation |
| Hard Drivin' synthetic tests | NOT STARTED | no board wrapper exists |

The implemented foundation regression is `make test`: 54 distinct Python
checks plus the 2,048-vector Verilator condition regression. Targets for
unavailable or unimplemented areas print `SKIP` and do not create false pass
evidence.
