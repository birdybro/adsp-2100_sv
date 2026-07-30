PYTHON ?= python3
VERILATOR ?= verilator

.DEFAULT_GOAL := test

.PHONY: test lint model-tests assembler-tests decode-tests compute-tests \
	dag-tests sequencer-tests instruction-tests bus-tests interrupt-tests \
	differential fuzz formal synth-yosys synth-quartus harddriv-tests docs clean \
	reference-check repository-check

test: lint reference-check repository-check decode-tests assembler-tests model-tests compute-tests
	@echo "PASS implemented foundation regression"

lint:
	$(PYTHON) -m compileall -q scripts tools sim tests
	$(PYTHON) scripts/lint_text.py
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_decode_pkg.sv \
			rtl/core/adsp2100_condition_logic.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_alu.sv; \
	else \
		echo "SKIP Verilator lint: executable not available"; \
	fi

reference-check:
	$(PYTHON) -m unittest -v tests.test_reference_manifest tests.test_reference_scripts
	@if [ -n "$$(find reference_cache -type f ! -name .gitkeep -print -quit)" ]; then \
		$(PYTHON) scripts/verify_reference_hashes.py; \
	else \
		echo "SKIP reference hash verification: local cache is intentionally absent"; \
	fi

repository-check:
	$(PYTHON) -m unittest -v tests.test_repository

model-tests:
	$(PYTHON) -m unittest -v tests.test_model_foundation

decode-tests:
	$(PYTHON) tools/generators/validate_isa.py
	$(PYTHON) tools/generators/validate_register_codes.py
	$(PYTHON) tools/generators/validate_condition_codes.py
	$(PYTHON) tools/generators/validate_isa_fields.py
	$(PYTHON) tools/generators/generate_opcode_table.py --check
	$(PYTHON) tools/generators/generate_decode_package.py --check
	$(PYTHON) -m unittest -v tests.test_isa_database tests.test_register_metadata \
		tests.test_isa_fields

assembler-tests:
	$(PYTHON) -m unittest -v tests.test_assembler_disassembler

compute-tests:
	$(PYTHON) -m unittest -v tests.test_condition_logic tests.test_alu_model
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_condition_vectors.py \
			--output build/condition_expected.mem; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_condition \
			--top-module tb_adsp2100_condition_logic \
			rtl/core/adsp2100_condition_logic.sv \
			sim/unit/tb_adsp2100_condition_logic.sv; \
		build/obj_condition/Vtb_adsp2100_condition_logic; \
		$(PYTHON) tools/generators/generate_alu_vectors.py \
			--output build/alu_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_alu \
			--top-module tb_adsp2100_alu \
			rtl/core/adsp2100_alu.sv \
			sim/unit/tb_adsp2100_alu.sv; \
		build/obj_alu/Vtb_adsp2100_alu; \
	else \
		echo "SKIP condition RTL test: Verilator executable not available"; \
	fi

dag-tests:
	@echo "SKIP DAG tests: verified DAG implementations do not exist"

sequencer-tests:
	@echo "SKIP sequencer tests: verified sequencer implementation does not exist"

instruction-tests: decode-tests assembler-tests
	@echo "SKIP RTL instruction tests: no instruction execution RTL exists"

bus-tests:
	@echo "SKIP bus tests: native bus RTL does not exist"

interrupt-tests:
	@echo "SKIP interrupt tests: interrupt RTL does not exist"

differential:
	@echo "SKIP differential tests: only the independent model foundation exists"

fuzz:
	@echo "SKIP fuzz tests: complete legal-instruction generator does not exist"

formal:
	@if command -v sby >/dev/null 2>&1; then \
		echo "SKIP formal: no source-backed RTL property harness exists yet"; \
	else \
		echo "SKIP formal: SymbiYosys is not installed"; \
	fi

synth-yosys:
	@if command -v yosys >/dev/null 2>&1; then \
		echo "SKIP Yosys synthesis: no architectural RTL top exists yet"; \
	else \
		echo "SKIP Yosys synthesis: Yosys is not installed"; \
	fi

synth-quartus:
	@if command -v quartus_sh >/dev/null 2>&1; then \
		set -e; \
		quartus_sh --flow compile synthesis/quartus/condition_smoke; \
		quartus_sh --flow compile synthesis/quartus/alu_smoke; \
	else \
		echo "SKIP Quartus synthesis: Quartus is not installed"; \
	fi

harddriv-tests:
	@echo "SKIP Hard Drivin' tests: research notes exist but no board wrapper exists"

docs:
	$(PYTHON) -m unittest -v tests.test_repository.RepositoryTests.test_required_documentation

clean:
	@find scripts tools sim tests -type d -name __pycache__ -prune -exec rm -r {} +
	@find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	@find build -maxdepth 1 -type f -name condition_expected.mem -delete
	@find build -maxdepth 1 -type f -name alu_vectors.txt -delete
	@if [ -d build/obj_condition ]; then find build/obj_condition -depth -delete; fi
	@if [ -d build/obj_alu ]; then find build/obj_alu -depth -delete; fi
	@if [ -d build/quartus_condition ]; then find build/quartus_condition -depth -delete; fi
	@if [ -d build/quartus_alu ]; then find build/quartus_alu -depth -delete; fi
	@if [ -d synthesis/quartus/db ]; then find synthesis/quartus/db -depth -delete; fi
	@if [ -d synthesis/quartus/incremental_db ]; then \
		find synthesis/quartus/incremental_db -depth -delete; \
	fi
	@find synthesis/quartus -maxdepth 1 -type f -name '*_pin_model_dump.txt' -delete
	@echo "PASS removed local generated test products"
