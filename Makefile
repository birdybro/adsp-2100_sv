PYTHON ?= python3
VERILATOR ?= verilator

.DEFAULT_GOAL := test

.PHONY: test lint model-tests assembler-tests decode-tests compute-tests \
	dag-tests sequencer-tests register-tests status-tests mode-tests instruction-tests bus-tests interrupt-tests \
	differential fuzz formal synth-yosys synth-quartus harddriv-tests docs clean \
	reference-check repository-check

test: lint reference-check repository-check decode-tests assembler-tests model-tests \
	compute-tests dag-tests sequencer-tests register-tests status-tests mode-tests
	@echo "PASS implemented foundation regression"

lint:
	$(PYTHON) -m compileall -q scripts tools sim tests
	$(PYTHON) scripts/lint_text.py
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			-Wno-UNUSEDPARAM \
			--top-module adsp2100_class_decode \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_decode_pkg.sv \
			rtl/packages/adsp2100_format_pkg.sv \
			rtl/core/adsp2100_class_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_stack_control_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_mr_saturation_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_mode_control_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mode_control_slice \
			rtl/core/adsp2100_mode_control_decode.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_mode_control_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_stack_control_slice \
			rtl/core/adsp2100_stack_control_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_stack_control_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_condition_logic.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_alu.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mr_saturation_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mr_saturation_decode.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_mr_saturation_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_shifter.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_dag.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_sequencer_flow.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_counter.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_sequencer_stacks.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_sequencer_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_sequencer_flow.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_sequencer_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_register_file.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_status_registers.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_status_stack.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_mode_slice.sv; \
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
	$(PYTHON) tools/generators/validate_instruction_formats.py
	$(PYTHON) tools/generators/validate_stack_control.py
	$(PYTHON) tools/generators/validate_mr_saturation.py
	$(PYTHON) tools/generators/validate_mode_control.py
	$(PYTHON) tools/generators/generate_opcode_table.py --check
	$(PYTHON) tools/generators/generate_decode_package.py --check
	$(PYTHON) tools/generators/generate_instruction_formats.py --check
	$(PYTHON) tools/generators/generate_register_package.py --check
	$(PYTHON) -m unittest -v tests.test_isa_database tests.test_register_metadata \
		tests.test_isa_fields tests.test_instruction_formats \
		tests.test_stack_control tests.test_mr_saturation
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			--Mdir build/obj_decode \
			--top-module tb_adsp2100_decode \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_decode_pkg.sv \
			rtl/core/adsp2100_class_decode.sv \
			sim/unit/tb_adsp2100_decode.sv; \
		build/obj_decode/Vtb_adsp2100_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			--Mdir build/obj_stack_control_decode \
			--top-module tb_adsp2100_stack_control_decode \
			rtl/core/adsp2100_stack_control_decode.sv \
			sim/unit/tb_adsp2100_stack_control_decode.sv; \
		build/obj_stack_control_decode/Vtb_adsp2100_stack_control_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_mr_saturation_decode \
			--top-module tb_adsp2100_mr_saturation_decode \
			rtl/core/adsp2100_mr_saturation_decode.sv \
			sim/unit/tb_adsp2100_mr_saturation_decode.sv; \
		build/obj_mr_saturation_decode/Vtb_adsp2100_mr_saturation_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_mode_control_decode \
			--top-module tb_adsp2100_mode_control_decode \
			rtl/core/adsp2100_mode_control_decode.sv \
			sim/unit/tb_adsp2100_mode_control_decode.sv; \
		build/obj_mode_control_decode/Vtb_adsp2100_mode_control_decode; \
	else \
		echo "SKIP exhaustive RTL decode: Verilator is not installed"; \
	fi

assembler-tests:
	$(PYTHON) -m unittest -v tests.test_assembler_disassembler

compute-tests:
	$(PYTHON) -m unittest -v tests.test_condition_logic tests.test_alu_model \
		tests.test_mac_model tests.test_shifter_model tests.test_mr_saturation
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
		$(PYTHON) tools/generators/generate_mac_vectors.py \
			--output build/mac_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_mac \
			--top-module tb_adsp2100_mac \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv \
			sim/unit/tb_adsp2100_mac.sv; \
		build/obj_mac/Vtb_adsp2100_mac; \
		$(PYTHON) tools/generators/generate_mr_saturation_vectors.py \
			--output build/mr_saturation_slice_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_mr_saturation_slice \
			--top-module tb_adsp2100_mr_saturation_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mr_saturation_decode.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_mr_saturation_slice.sv \
			sim/unit/tb_adsp2100_mr_saturation_slice.sv; \
		build/obj_mr_saturation_slice/Vtb_adsp2100_mr_saturation_slice; \
		$(PYTHON) tools/generators/generate_shifter_vectors.py \
			--output build/shifter_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter \
			--top-module tb_adsp2100_shifter \
			rtl/core/adsp2100_shifter.sv \
			sim/unit/tb_adsp2100_shifter.sv; \
		build/obj_shifter/Vtb_adsp2100_shifter; \
	else \
		echo "SKIP condition RTL test: Verilator executable not available"; \
	fi

dag-tests:
	$(PYTHON) -m unittest -v tests.test_dag_model
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_dag_vectors.py \
			--output build/dag_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_dag \
			--top-module tb_adsp2100_dag \
			rtl/core/adsp2100_dag.sv \
			sim/unit/tb_adsp2100_dag.sv; \
		build/obj_dag/Vtb_adsp2100_dag; \
	else \
		echo "SKIP DAG RTL test: Verilator executable not available"; \
	fi

sequencer-tests:
	$(PYTHON) -m unittest -v tests.test_sequencer_flow \
		tests.test_counter tests.test_sequencer_stacks \
		tests.test_sequencer_slice tests.test_stack_control_slice
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_sequencer_vectors.py \
			--output build/sequencer_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_sequencer \
			--top-module tb_adsp2100_sequencer_flow \
			rtl/core/adsp2100_sequencer_flow.sv \
			sim/unit/tb_adsp2100_sequencer_flow.sv; \
		build/obj_sequencer/Vtb_adsp2100_sequencer_flow; \
		$(PYTHON) tools/generators/generate_counter_vectors.py \
			--output build/counter_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_counter \
			--top-module tb_adsp2100_counter \
			rtl/core/adsp2100_counter.sv \
			sim/unit/tb_adsp2100_counter.sv; \
		build/obj_counter/Vtb_adsp2100_counter; \
		$(PYTHON) tools/generators/generate_sequencer_stack_vectors.py \
			--output build/sequencer_stack_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_sequencer_stacks \
			--top-module tb_adsp2100_sequencer_stacks \
			rtl/core/adsp2100_sequencer_stacks.sv \
			sim/unit/tb_adsp2100_sequencer_stacks.sv; \
		build/obj_sequencer_stacks/Vtb_adsp2100_sequencer_stacks; \
		$(PYTHON) tools/generators/generate_sequencer_slice_vectors.py \
			--output build/sequencer_slice_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_sequencer_slice \
			--top-module tb_adsp2100_sequencer_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_sequencer_flow.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_sequencer_slice.sv \
			sim/unit/tb_adsp2100_sequencer_slice.sv; \
		build/obj_sequencer_slice/Vtb_adsp2100_sequencer_slice; \
		$(PYTHON) tools/generators/generate_stack_control_slice_vectors.py \
			--output build/stack_control_slice_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_stack_control_slice \
			--top-module tb_adsp2100_stack_control_slice \
			rtl/core/adsp2100_stack_control_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_stack_control_slice.sv \
			sim/unit/tb_adsp2100_stack_control_slice.sv; \
		build/obj_stack_control_slice/Vtb_adsp2100_stack_control_slice; \
	else \
		echo "SKIP sequencer RTL tests: Verilator is not installed"; \
	fi

register-tests:
	$(PYTHON) -m unittest -v tests.test_register_banks
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_register_vectors.py \
			--output build/register_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_register \
			--top-module tb_adsp2100_register_file \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_register_file.sv \
			sim/unit/tb_adsp2100_register_file.sv; \
		build/obj_register/Vtb_adsp2100_register_file; \
		$(PYTHON) tools/generators/generate_writeback_vectors.py \
			--output build/register_writeback_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_register_writeback \
			--top-module tb_adsp2100_register_writeback \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_register_file.sv \
			sim/unit/tb_adsp2100_register_writeback.sv; \
		build/obj_register_writeback/Vtb_adsp2100_register_writeback; \
	else \
		echo "SKIP register-file RTL test: Verilator is not installed"; \
	fi

status-tests:
	$(PYTHON) -m unittest -v tests.test_status_registers tests.test_status_stack
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_status_vectors.py \
			--output build/status_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_status \
			--top-module tb_adsp2100_status_registers \
			rtl/core/adsp2100_status_registers.sv \
			sim/unit/tb_adsp2100_status_registers.sv; \
		build/obj_status/Vtb_adsp2100_status_registers; \
		$(PYTHON) tools/generators/generate_status_stack_vectors.py \
			--output build/status_stack_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_status_stack \
			--top-module tb_adsp2100_status_stack \
			rtl/core/adsp2100_status_stack.sv \
			sim/unit/tb_adsp2100_status_stack.sv; \
		build/obj_status_stack/Vtb_adsp2100_status_stack; \
	else \
		echo "SKIP status-register RTL test: Verilator is not installed"; \
	fi

mode-tests:
	$(PYTHON) -m unittest -v tests.test_mode_integration \
		tests.test_mode_control
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_mode_slice_vectors.py \
			--output build/mode_slice_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_mode_slice \
			--top-module tb_adsp2100_mode_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_mode_slice.sv \
			sim/unit/tb_adsp2100_mode_slice.sv; \
		build/obj_mode_slice/Vtb_adsp2100_mode_slice; \
		$(PYTHON) tools/generators/generate_mode_control_vectors.py \
			--output build/mode_control_slice_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_mode_control_slice \
			--top-module tb_adsp2100_mode_control_slice \
			rtl/core/adsp2100_mode_control_decode.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_mode_control_slice.sv \
			sim/unit/tb_adsp2100_mode_control_slice.sv; \
		build/obj_mode_control_slice/Vtb_adsp2100_mode_control_slice; \
	else \
		echo "SKIP MSTAT-consumer RTL test: Verilator is not installed"; \
	fi

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
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_class_decode_formal \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_decode_pkg.sv \
			rtl/core/adsp2100_class_decode.sv \
			formal/harnesses/adsp2100_class_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_stack_control_decode_formal \
			rtl/core/adsp2100_stack_control_decode.sv \
			formal/harnesses/adsp2100_stack_control_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mr_saturation_decode_formal \
			rtl/core/adsp2100_mr_saturation_decode.sv \
			formal/harnesses/adsp2100_mr_saturation_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mode_control_decode_formal \
			rtl/core/adsp2100_mode_control_decode.sv \
			formal/harnesses/adsp2100_mode_control_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_stack_control_slice_formal \
			rtl/core/adsp2100_stack_control_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_stack_control_slice.sv \
			formal/harnesses/adsp2100_stack_control_slice_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_condition_formal \
			rtl/core/adsp2100_condition_logic.sv \
			formal/harnesses/adsp2100_condition_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_alu_formal \
			rtl/core/adsp2100_alu.sv \
			formal/harnesses/adsp2100_alu_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mac_formal \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv \
			formal/harnesses/adsp2100_mac_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mr_saturation_slice_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mr_saturation_decode.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_mr_saturation_slice.sv \
			formal/harnesses/adsp2100_mr_saturation_slice_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mode_control_slice_formal \
			rtl/core/adsp2100_mode_control_decode.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_mode_control_slice.sv \
			formal/harnesses/adsp2100_mode_control_slice_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_formal \
			rtl/core/adsp2100_shifter.sv \
			formal/harnesses/adsp2100_shifter_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_dag_formal \
			rtl/core/adsp2100_dag.sv \
			formal/harnesses/adsp2100_dag_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_sequencer_flow_formal \
			rtl/core/adsp2100_sequencer_flow.sv \
			formal/harnesses/adsp2100_sequencer_flow_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_counter_formal \
			rtl/core/adsp2100_counter.sv \
			formal/harnesses/adsp2100_counter_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_sequencer_stacks_formal \
			rtl/core/adsp2100_sequencer_stacks.sv \
			formal/harnesses/adsp2100_sequencer_stacks_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_sequencer_slice_formal \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_sequencer_flow.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_sequencer_slice.sv \
			formal/harnesses/adsp2100_sequencer_slice_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_register_file_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_register_file.sv \
			formal/harnesses/adsp2100_register_file_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_status_registers_formal \
			rtl/core/adsp2100_status_registers.sv \
			formal/harnesses/adsp2100_status_registers_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_status_stack_formal \
			rtl/core/adsp2100_status_stack.sv \
			formal/harnesses/adsp2100_status_stack_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mode_slice_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_mode_slice.sv \
			formal/harnesses/adsp2100_mode_slice_formal.sv; \
	else \
		echo "SKIP formal harness lint: Verilator is not installed"; \
	fi
	@if command -v sby >/dev/null 2>&1; then \
		set -e; \
		sby -f -d build/formal_decode formal/class_decode.sby; \
		sby -f -d build/formal_stack_control_decode \
			formal/stack_control_decode.sby; \
		sby -f -d build/formal_mr_saturation_decode \
			formal/mr_saturation_decode.sby; \
		sby -f -d build/formal_mode_control_decode \
			formal/mode_control_decode.sby; \
		sby -f -d build/formal_stack_control_slice \
			formal/stack_control_slice.sby; \
		sby -f -d build/formal_condition formal/condition.sby; \
		sby -f -d build/formal_alu formal/alu.sby; \
		sby -f -d build/formal_mac formal/mac.sby; \
		sby -f -d build/formal_mr_saturation_slice \
			formal/mr_saturation_slice.sby; \
		sby -f -d build/formal_mode_control_slice \
			formal/mode_control_slice.sby; \
		sby -f -d build/formal_shifter formal/shifter.sby; \
		sby -f -d build/formal_dag formal/dag.sby; \
		sby -f -d build/formal_sequencer formal/sequencer_flow.sby; \
		sby -f -d build/formal_counter formal/counter.sby; \
		sby -f -d build/formal_sequencer_stacks formal/sequencer_stacks.sby; \
		sby -f -d build/formal_sequencer_slice formal/sequencer_slice.sby; \
		sby -f -d build/formal_registers formal/registers.sby; \
		sby -f -d build/formal_status formal/status_registers.sby; \
		sby -f -d build/formal_status_stack formal/status_stack.sby; \
		sby -f -d build/formal_mode_slice formal/mode_slice.sby; \
	else \
		echo "SKIP formal proofs: SymbiYosys is not installed"; \
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
		quartus_sh --flow compile synthesis/quartus/decode_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/stack_control_decode_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/stack_control_slice_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/mr_saturation_slice_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/mode_control_slice_smoke; \
		quartus_sh --flow compile synthesis/quartus/condition_smoke; \
		quartus_sh --flow compile synthesis/quartus/alu_smoke; \
		quartus_sh --flow compile synthesis/quartus/mac_smoke; \
		quartus_sh --flow compile synthesis/quartus/shifter_smoke; \
		quartus_sh --flow compile synthesis/quartus/dag_smoke; \
		quartus_sh --flow compile synthesis/quartus/sequencer_flow_smoke; \
		quartus_sh --flow compile synthesis/quartus/counter_smoke; \
		quartus_sh --flow compile synthesis/quartus/sequencer_slice_smoke; \
		quartus_sh --flow compile synthesis/quartus/register_file_smoke; \
		quartus_sh --flow compile synthesis/quartus/status_registers_smoke; \
		quartus_sh --flow compile synthesis/quartus/status_stack_smoke; \
		quartus_sh --flow compile synthesis/quartus/sequencer_stacks_smoke; \
		quartus_sh --flow compile synthesis/quartus/mode_slice_smoke; \
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
	@find build -maxdepth 1 -type f -name mac_vectors.txt -delete
	@find build -maxdepth 1 -type f -name mr_saturation_slice_vectors.txt -delete
	@find build -maxdepth 1 -type f -name mode_control_slice_vectors.txt -delete
	@find build -maxdepth 1 -type f -name shifter_vectors.txt -delete
	@find build -maxdepth 1 -type f -name dag_vectors.txt -delete
	@find build -maxdepth 1 -type f -name sequencer_vectors.txt -delete
	@find build -maxdepth 1 -type f -name counter_vectors.txt -delete
	@find build -maxdepth 1 -type f -name sequencer_stack_vectors.txt -delete
	@find build -maxdepth 1 -type f -name sequencer_slice_vectors.txt -delete
	@find build -maxdepth 1 -type f -name stack_control_slice_vectors.txt -delete
	@find build -maxdepth 1 -type f -name register_vectors.txt -delete
	@find build -maxdepth 1 -type f -name register_writeback_vectors.txt -delete
	@find build -maxdepth 1 -type f -name status_vectors.txt -delete
	@find build -maxdepth 1 -type f -name status_stack_vectors.txt -delete
	@find build -maxdepth 1 -type f -name mode_slice_vectors.txt -delete
	@if [ -d build/obj_decode ]; then find build/obj_decode -depth -delete; fi
	@if [ -d build/obj_stack_control_decode ]; then \
		find build/obj_stack_control_decode -depth -delete; \
	fi
	@if [ -d build/obj_condition ]; then find build/obj_condition -depth -delete; fi
	@if [ -d build/obj_alu ]; then find build/obj_alu -depth -delete; fi
	@if [ -d build/obj_mac ]; then find build/obj_mac -depth -delete; fi
	@if [ -d build/obj_shifter ]; then find build/obj_shifter -depth -delete; fi
	@if [ -d build/obj_dag ]; then find build/obj_dag -depth -delete; fi
	@if [ -d build/obj_sequencer ]; then find build/obj_sequencer -depth -delete; fi
	@if [ -d build/obj_counter ]; then find build/obj_counter -depth -delete; fi
	@if [ -d build/obj_sequencer_stacks ]; then \
		find build/obj_sequencer_stacks -depth -delete; \
	fi
	@if [ -d build/obj_sequencer_slice ]; then \
		find build/obj_sequencer_slice -depth -delete; \
	fi
	@if [ -d build/obj_stack_control_slice ]; then \
		find build/obj_stack_control_slice -depth -delete; \
	fi
	@if [ -d build/obj_mr_saturation_decode ]; then \
		find build/obj_mr_saturation_decode -depth -delete; \
	fi
	@if [ -d build/obj_mr_saturation_slice ]; then \
		find build/obj_mr_saturation_slice -depth -delete; \
	fi
	@if [ -d build/obj_mode_control_decode ]; then \
		find build/obj_mode_control_decode -depth -delete; \
	fi
	@if [ -d build/obj_mode_control_slice ]; then \
		find build/obj_mode_control_slice -depth -delete; \
	fi
	@if [ -d build/obj_register ]; then find build/obj_register -depth -delete; fi
	@if [ -d build/obj_register_writeback ]; then \
		find build/obj_register_writeback -depth -delete; \
	fi
	@if [ -d build/obj_status ]; then find build/obj_status -depth -delete; fi
	@if [ -d build/obj_status_stack ]; then find build/obj_status_stack -depth -delete; fi
	@if [ -d build/obj_mode_slice ]; then find build/obj_mode_slice -depth -delete; fi
	@if [ -d build/quartus_condition ]; then find build/quartus_condition -depth -delete; fi
	@if [ -d build/quartus_decode ]; then find build/quartus_decode -depth -delete; fi
	@if [ -d build/quartus_stack_control_decode ]; then \
		find build/quartus_stack_control_decode -depth -delete; \
	fi
	@if [ -d build/quartus_stack_control_slice ]; then \
		find build/quartus_stack_control_slice -depth -delete; \
	fi
	@if [ -d build/quartus_alu ]; then find build/quartus_alu -depth -delete; fi
	@if [ -d build/quartus_mac ]; then find build/quartus_mac -depth -delete; fi
	@if [ -d build/quartus_mr_saturation_slice ]; then \
		find build/quartus_mr_saturation_slice -depth -delete; \
	fi
	@if [ -d build/quartus_mode_control_slice ]; then \
		find build/quartus_mode_control_slice -depth -delete; \
	fi
	@if [ -d build/quartus_shifter ]; then find build/quartus_shifter -depth -delete; fi
	@if [ -d build/quartus_dag ]; then find build/quartus_dag -depth -delete; fi
	@if [ -d build/quartus_sequencer ]; then find build/quartus_sequencer -depth -delete; fi
	@if [ -d build/quartus_counter ]; then find build/quartus_counter -depth -delete; fi
	@if [ -d build/quartus_sequencer_slice ]; then \
		find build/quartus_sequencer_slice -depth -delete; \
	fi
	@if [ -d build/quartus_register ]; then find build/quartus_register -depth -delete; fi
	@if [ -d build/quartus_status ]; then find build/quartus_status -depth -delete; fi
	@if [ -d build/quartus_status_stack ]; then \
		find build/quartus_status_stack -depth -delete; \
	fi
	@if [ -d build/quartus_sequencer_stacks ]; then \
		find build/quartus_sequencer_stacks -depth -delete; \
	fi
	@if [ -d build/quartus_mode_slice ]; then \
		find build/quartus_mode_slice -depth -delete; \
	fi
	@for directory in build/formal_decode build/formal_stack_control_decode \
		build/formal_stack_control_slice \
		build/formal_mr_saturation_decode \
		build/formal_mr_saturation_slice \
		build/formal_mode_control_decode \
		build/formal_mode_control_slice \
		build/formal_condition build/formal_alu build/formal_mac \
		build/formal_shifter build/formal_dag build/formal_sequencer \
		build/formal_counter build/formal_sequencer_stacks \
		build/formal_sequencer_slice \
		build/formal_registers build/formal_status build/formal_status_stack \
		build/formal_mode_slice; do \
		if [ -d "$$directory" ]; then find "$$directory" -depth -delete; fi; \
	done
	@if [ -d synthesis/quartus/db ]; then find synthesis/quartus/db -depth -delete; fi
	@if [ -d synthesis/quartus/incremental_db ]; then \
		find synthesis/quartus/incremental_db -depth -delete; \
	fi
	@find synthesis/quartus -maxdepth 1 -type f -name '*_pin_model_dump.txt' -delete
	@echo "PASS removed local generated test products"
