PYTHON ?= python3
VERILATOR ?= verilator

.DEFAULT_GOAL := test

.PHONY: test lint model-tests cache-tests pm-bus-tests dm-bus-tests dm-write-native-tests dm-shifter-native-tests dm-compute-native-tests pm-native-tests assembler-tests decode-tests compute-tests \
	dag-tests sequencer-tests register-tests status-tests mode-tests instruction-tests bus-tests interrupt-tests \
	differential fuzz formal synth-yosys synth-quartus harddriv-tests docs clean \
	reference-check repository-check

test: lint reference-check repository-check decode-tests assembler-tests model-tests \
	cache-tests compute-tests dag-tests sequencer-tests register-tests status-tests mode-tests \
	bus-tests
	@echo "PASS implemented foundation regression"

lint:
	$(PYTHON) -m compileall -q scripts tools sim tests
	$(PYTHON) scripts/lint_text.py
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_instruction_cache \
			rtl/core/adsp2100_instruction_cache.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_program_bus \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_program_bus.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_data_bus \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_data_bus.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_dm_write_immediate_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_dm_write_immediate_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_dm_write_immediate_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_dm_write_immediate_native_slice.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_dm_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_dm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_dm_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_shifter_dm_native_slice.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_dm_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_compute_dm_native_slice.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_pm_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv \
			rtl/core/adsp2100_shifter_pm_cache_slice.sv \
			rtl/core/adsp2100_program_bus.sv \
			rtl/core/adsp2100_shifter_pm_native_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			-Wno-UNUSEDPARAM \
			--top-module adsp2100_class_decode \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_decode_pkg.sv \
			rtl/packages/adsp2100_format_pkg.sv \
			rtl/core/adsp2100_class_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_load_dreg_immediate_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_load_dreg_immediate_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_load_dreg_immediate_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_immediate_shift_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_immediate_shift_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_immediate_shift_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_conditional_shift_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_conditional_shift_decode.sv \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_shift_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shift_move_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shift_move_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shift_move_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_dm_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_dm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_dm_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_pm_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_pm_cache_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv \
			rtl/core/adsp2100_shifter_pm_cache_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_move_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_move_decode.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_move_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_compute_dm_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_compute_pm_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_compute_dual_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_dm_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_pm_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_pm_decode.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_compute_pm_slice.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_pm_cache_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_pm_decode.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_compute_pm_slice.sv \
			rtl/core/adsp2100_compute_pm_cache_slice.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_pm_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_pm_decode.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_compute_pm_slice.sv \
			rtl/core/adsp2100_compute_pm_cache_slice.sv \
			rtl/core/adsp2100_program_bus.sv \
			rtl/core/adsp2100_compute_pm_native_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_conditional_compute_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_compute_decode.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_compute_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_direct_jump_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_direct_jump_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_direct_jump_slice.sv; \
			"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
				--top-module adsp2100_do_until_slice \
			rtl/core/adsp2100_do_until_decode.sv \
			rtl/core/adsp2100_counter.sv \
				rtl/core/adsp2100_sequencer_stacks.sv \
				rtl/core/adsp2100_do_until_slice.sv; \
			"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
				--top-module adsp2100_indirect_jump_slice \
				rtl/core/adsp2100_condition_logic.sv \
				rtl/core/adsp2100_indirect_jump_decode.sv \
				rtl/core/adsp2100_counter.sv \
				rtl/core/adsp2100_sequencer_stacks.sv \
				rtl/core/adsp2100_dag_register_file.sv \
				rtl/core/adsp2100_indirect_jump_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_conditional_return_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_return_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_return_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_conditional_trap_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_trap_decode.sv \
			rtl/core/adsp2100_conditional_trap_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_divide_quotient_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_divide_quotient_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_divide_quotient_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_divide_sign_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_divide_sign_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_divide_sign_slice.sv; \
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
			rtl/core/adsp2100_internal_move_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_internal_move_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_internal_move_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_internal_move_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_modify_address_decode.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			rtl/core/adsp2100_dm_write_immediate_decode.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_dm_write_immediate_slice \
			rtl/core/adsp2100_dm_write_immediate_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_dm_write_immediate_slice.sv; \
		"$(VERILATOR)" --lint-only -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_modify_address_slice \
			rtl/core/adsp2100_modify_address_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_modify_address_slice.sv; \
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

cache-tests:
	$(PYTHON) -m unittest -v tests.test_instruction_cache \
		tests.test_shifter_pm_cache
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_instruction_cache_vectors.py \
			--output build/instruction_cache_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_instruction_cache \
			--top-module tb_adsp2100_instruction_cache \
			rtl/core/adsp2100_instruction_cache.sv \
			sim/unit/tb_adsp2100_instruction_cache.sv; \
		build/obj_instruction_cache/Vtb_adsp2100_instruction_cache; \
		$(PYTHON) tools/generators/generate_shifter_pm_cache_vectors.py \
			--output build/shifter_pm_cache_vectors.txt; \
		"$(VERILATOR)" --binary --timing --assert -Wall \
			-Wno-DECLFILENAME -Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter_pm_cache_slice \
			--top-module tb_adsp2100_shifter_pm_cache_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv \
			rtl/core/adsp2100_shifter_pm_cache_slice.sv \
			sim/unit/tb_adsp2100_shifter_pm_cache_slice.sv; \
		build/obj_shifter_pm_cache_slice/Vtb_adsp2100_shifter_pm_cache_slice; \
	else \
		echo "SKIP instruction-cache RTL test: Verilator is not installed"; \
	fi

pm-bus-tests:
	$(PYTHON) -m unittest -v tests.test_program_bus
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_program_bus_vectors.py \
			--output build/program_bus_vectors.txt; \
		"$(VERILATOR)" --binary --timing --assert -Wall \
			-Wno-DECLFILENAME -Wno-TIMESCALEMOD \
			--Mdir build/obj_program_bus \
			--top-module tb_adsp2100_program_bus \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_program_bus.sv \
			sim/unit/tb_adsp2100_program_bus.sv; \
		build/obj_program_bus/Vtb_adsp2100_program_bus; \
	else \
		echo "SKIP PM-bus RTL test: Verilator is not installed"; \
	fi

dm-bus-tests:
	$(PYTHON) -m unittest -v tests.test_data_bus
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_data_bus_vectors.py \
			--output build/data_bus_vectors.txt; \
		"$(VERILATOR)" --binary --timing --assert -Wall \
			-Wno-DECLFILENAME -Wno-TIMESCALEMOD \
			--Mdir build/obj_data_bus \
			--top-module tb_adsp2100_data_bus \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_data_bus.sv \
			sim/unit/tb_adsp2100_data_bus.sv; \
		build/obj_data_bus/Vtb_adsp2100_data_bus; \
	else \
		echo "SKIP DM-bus RTL test: Verilator is not installed"; \
	fi

dm-write-native-tests:
	$(PYTHON) -m unittest -v tests.test_dm_write_immediate_native
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_dm_write_immediate_native_vectors.py \
			--output build/dm_write_immediate_native_vectors.txt; \
		"$(VERILATOR)" --binary --timing --assert -Wall \
			-Wno-DECLFILENAME -Wno-TIMESCALEMOD \
			--Mdir build/obj_dm_write_immediate_native_slice \
			--top-module tb_adsp2100_dm_write_immediate_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_dm_write_immediate_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_dm_write_immediate_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_dm_write_immediate_native_slice.sv \
			sim/unit/tb_adsp2100_dm_write_immediate_native_slice.sv; \
		build/obj_dm_write_immediate_native_slice/Vtb_adsp2100_dm_write_immediate_native_slice; \
	else \
		echo "SKIP Type 2/native-DM RTL test: Verilator is not installed"; \
	fi

dm-shifter-native-tests:
	$(PYTHON) -m unittest -v tests.test_shifter_dm_native
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_shifter_dm_native_vectors.py \
			--output build/shifter_dm_native_vectors.txt; \
		"$(VERILATOR)" --binary --timing --assert -Wall \
			-Wno-DECLFILENAME -Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter_dm_native_slice \
			--top-module tb_adsp2100_shifter_dm_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_dm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_dm_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_shifter_dm_native_slice.sv \
			sim/unit/tb_adsp2100_shifter_dm_native_slice.sv; \
		build/obj_shifter_dm_native_slice/Vtb_adsp2100_shifter_dm_native_slice; \
	else \
		echo "SKIP Type 12/native-DM RTL test: Verilator is not installed"; \
	fi

dm-compute-native-tests:
	$(PYTHON) -m unittest -v tests.test_compute_dm_native
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_compute_dm_native_vectors.py \
			--output build/compute_dm_native_vectors.txt; \
		"$(VERILATOR)" --binary --timing --assert -Wall \
			-Wno-DECLFILENAME -Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_dm_native_slice \
			--top-module tb_adsp2100_compute_dm_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_compute_dm_native_slice.sv \
			sim/unit/tb_adsp2100_compute_dm_native_slice.sv; \
		build/obj_compute_dm_native_slice/Vtb_adsp2100_compute_dm_native_slice; \
	else \
		echo "SKIP Type 4/native-DM RTL test: Verilator is not installed"; \
	fi

pm-native-tests:
	$(PYTHON) -m unittest -v tests.test_shifter_pm_native
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_shifter_pm_native_vectors.py \
			--output build/shifter_pm_native_vectors.txt; \
		"$(VERILATOR)" --binary --timing --assert -Wall \
			-Wno-DECLFILENAME -Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter_pm_native_slice \
			--top-module tb_adsp2100_shifter_pm_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv \
			rtl/core/adsp2100_shifter_pm_cache_slice.sv \
			rtl/core/adsp2100_program_bus.sv \
			rtl/core/adsp2100_shifter_pm_native_slice.sv \
			sim/unit/tb_adsp2100_shifter_pm_native_slice.sv; \
		build/obj_shifter_pm_native_slice/Vtb_adsp2100_shifter_pm_native_slice; \
	else \
		echo "SKIP Type 13/native-PM RTL test: Verilator is not installed"; \
	fi

decode-tests:
	$(PYTHON) tools/generators/validate_isa.py
	$(PYTHON) tools/generators/validate_register_codes.py
	$(PYTHON) tools/generators/validate_condition_codes.py
	$(PYTHON) tools/generators/validate_isa_fields.py
	$(PYTHON) tools/generators/validate_instruction_formats.py
	$(PYTHON) tools/generators/validate_stack_control.py
	$(PYTHON) tools/generators/validate_mr_saturation.py
	$(PYTHON) tools/generators/validate_mode_control.py
	$(PYTHON) tools/generators/validate_modify_address.py
	$(PYTHON) tools/generators/validate_internal_move.py
	$(PYTHON) tools/generators/generate_opcode_table.py --check
	$(PYTHON) tools/generators/generate_decode_package.py --check
	$(PYTHON) tools/generators/generate_instruction_formats.py --check
	$(PYTHON) tools/generators/generate_register_package.py --check
	$(PYTHON) -m unittest -v tests.test_isa_database tests.test_register_metadata \
		tests.test_isa_fields tests.test_instruction_formats \
		tests.test_stack_control tests.test_mr_saturation \
		tests.test_dm_write_immediate \
		tests.test_internal_move tests.test_load_dreg_immediate \
		tests.test_immediate_shift tests.test_conditional_shift \
		tests.test_shift_move tests.test_shifter_dm tests.test_shifter_pm \
		tests.test_compute_move tests.test_compute_dual \
		tests.test_compute_dm tests.test_compute_pm \
		tests.test_compute_pm_cache tests.test_compute_pm_native \
		tests.test_conditional_compute tests.test_direct_jump \
		tests.test_do_until tests.test_indirect_jump \
		tests.test_conditional_return tests.test_conditional_trap \
		tests.test_divide_quotient tests.test_divide_sign
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
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_load_dreg_immediate_decode \
			--top-module tb_adsp2100_load_dreg_immediate_decode \
			rtl/core/adsp2100_load_dreg_immediate_decode.sv \
			sim/unit/tb_adsp2100_load_dreg_immediate_decode.sv; \
		build/obj_load_dreg_immediate_decode/Vtb_adsp2100_load_dreg_immediate_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_immediate_shift_decode \
			--top-module tb_adsp2100_immediate_shift_decode \
			rtl/core/adsp2100_immediate_shift_decode.sv \
			sim/unit/tb_adsp2100_immediate_shift_decode.sv; \
		build/obj_immediate_shift_decode/Vtb_adsp2100_immediate_shift_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_conditional_shift_decode \
			--top-module tb_adsp2100_conditional_shift_decode \
			rtl/core/adsp2100_conditional_shift_decode.sv \
			sim/unit/tb_adsp2100_conditional_shift_decode.sv; \
		build/obj_conditional_shift_decode/Vtb_adsp2100_conditional_shift_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_shift_move_decode \
			--top-module tb_adsp2100_shift_move_decode \
			rtl/core/adsp2100_shift_move_decode.sv \
			sim/unit/tb_adsp2100_shift_move_decode.sv; \
		build/obj_shift_move_decode/Vtb_adsp2100_shift_move_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter_dm_decode \
			--top-module tb_adsp2100_shifter_dm_decode \
			rtl/core/adsp2100_shifter_dm_decode.sv \
			sim/unit/tb_adsp2100_shifter_dm_decode.sv; \
		build/obj_shifter_dm_decode/Vtb_adsp2100_shifter_dm_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter_pm_decode \
			--top-module tb_adsp2100_shifter_pm_decode \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			sim/unit/tb_adsp2100_shifter_pm_decode.sv; \
		build/obj_shifter_pm_decode/Vtb_adsp2100_shifter_pm_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_move_decode \
			--top-module tb_adsp2100_compute_move_decode \
			rtl/core/adsp2100_compute_move_decode.sv \
			sim/unit/tb_adsp2100_compute_move_decode.sv; \
		build/obj_compute_move_decode/Vtb_adsp2100_compute_move_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_dual_decode \
			--top-module tb_adsp2100_compute_dual_decode \
			rtl/core/adsp2100_compute_dual_decode.sv \
			sim/unit/tb_adsp2100_compute_dual_decode.sv; \
		build/obj_compute_dual_decode/Vtb_adsp2100_compute_dual_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_dm_decode \
			--top-module tb_adsp2100_compute_dm_decode \
			rtl/core/adsp2100_compute_dm_decode.sv \
			sim/unit/tb_adsp2100_compute_dm_decode.sv; \
		build/obj_compute_dm_decode/Vtb_adsp2100_compute_dm_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_pm_decode \
			--top-module tb_adsp2100_compute_pm_decode \
			rtl/core/adsp2100_compute_pm_decode.sv \
			sim/unit/tb_adsp2100_compute_pm_decode.sv; \
		build/obj_compute_pm_decode/Vtb_adsp2100_compute_pm_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_conditional_compute_decode \
			--top-module tb_adsp2100_conditional_compute_decode \
			rtl/core/adsp2100_conditional_compute_decode.sv \
			sim/unit/tb_adsp2100_conditional_compute_decode.sv; \
		build/obj_conditional_compute_decode/Vtb_adsp2100_conditional_compute_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_direct_jump_decode \
			--top-module tb_adsp2100_direct_jump_decode \
			rtl/core/adsp2100_direct_jump_decode.sv \
			sim/unit/tb_adsp2100_direct_jump_decode.sv; \
		build/obj_direct_jump_decode/Vtb_adsp2100_direct_jump_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_do_until_decode \
			--top-module tb_adsp2100_do_until_decode \
			rtl/core/adsp2100_do_until_decode.sv \
			sim/unit/tb_adsp2100_do_until_decode.sv; \
		build/obj_do_until_decode/Vtb_adsp2100_do_until_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_indirect_jump_decode \
			--top-module tb_adsp2100_indirect_jump_decode \
			rtl/core/adsp2100_indirect_jump_decode.sv \
			sim/unit/tb_adsp2100_indirect_jump_decode.sv; \
		build/obj_indirect_jump_decode/Vtb_adsp2100_indirect_jump_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_conditional_return_decode \
			--top-module tb_adsp2100_conditional_return_decode \
			rtl/core/adsp2100_conditional_return_decode.sv \
			sim/unit/tb_adsp2100_conditional_return_decode.sv; \
		build/obj_conditional_return_decode/Vtb_adsp2100_conditional_return_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_conditional_trap_decode \
			--top-module tb_adsp2100_conditional_trap_decode \
			rtl/core/adsp2100_conditional_trap_decode.sv \
			sim/unit/tb_adsp2100_conditional_trap_decode.sv; \
		build/obj_conditional_trap_decode/Vtb_adsp2100_conditional_trap_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_divide_quotient_decode \
			--top-module tb_adsp2100_divide_quotient_decode \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_divide_quotient_decode.sv \
			sim/unit/tb_adsp2100_divide_quotient_decode.sv; \
		build/obj_divide_quotient_decode/Vtb_adsp2100_divide_quotient_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_divide_sign_decode \
			--top-module tb_adsp2100_divide_sign_decode \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_divide_sign_decode.sv \
			sim/unit/tb_adsp2100_divide_sign_decode.sv; \
		build/obj_divide_sign_decode/Vtb_adsp2100_divide_sign_decode; \
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
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_internal_move_decode \
			--top-module tb_adsp2100_internal_move_decode \
			rtl/core/adsp2100_internal_move_decode.sv \
			sim/unit/tb_adsp2100_internal_move_decode.sv; \
		build/obj_internal_move_decode/Vtb_adsp2100_internal_move_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_modify_address_decode \
			--top-module tb_adsp2100_modify_address_decode \
			rtl/core/adsp2100_modify_address_decode.sv \
			sim/unit/tb_adsp2100_modify_address_decode.sv; \
		build/obj_modify_address_decode/Vtb_adsp2100_modify_address_decode; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_dm_write_immediate_decode \
			--top-module tb_adsp2100_dm_write_immediate_decode \
			rtl/core/adsp2100_dm_write_immediate_decode.sv \
			sim/unit/tb_adsp2100_dm_write_immediate_decode.sv; \
		build/obj_dm_write_immediate_decode/Vtb_adsp2100_dm_write_immediate_decode; \
	else \
		echo "SKIP exhaustive RTL decode: Verilator is not installed"; \
	fi

assembler-tests:
	$(PYTHON) -m unittest -v tests.test_assembler_disassembler

compute-tests:
	$(PYTHON) -m unittest -v tests.test_condition_logic tests.test_alu_model \
		tests.test_mac_model tests.test_shifter_model tests.test_mr_saturation \
		tests.test_immediate_shift tests.test_conditional_shift \
		tests.test_shift_move tests.test_shifter_dm tests.test_shifter_pm \
		tests.test_compute_move tests.test_compute_dual \
		tests.test_compute_dm tests.test_compute_pm \
		tests.test_compute_pm_cache tests.test_compute_pm_native \
		tests.test_conditional_compute tests.test_divide_quotient \
		tests.test_divide_sign
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
		$(PYTHON) tools/generators/generate_divide_quotient_vectors.py \
			--output build/divide_quotient_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_divide_quotient_slice \
			--top-module tb_adsp2100_divide_quotient_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_divide_quotient_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_divide_quotient_slice.sv \
			sim/unit/tb_adsp2100_divide_quotient_slice.sv; \
		build/obj_divide_quotient_slice/Vtb_adsp2100_divide_quotient_slice; \
		$(PYTHON) tools/generators/generate_divide_sign_vectors.py \
			--output build/divide_sign_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_divide_sign_slice \
			--top-module tb_adsp2100_divide_sign_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_divide_sign_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_divide_sign_slice.sv \
			sim/unit/tb_adsp2100_divide_sign_slice.sv; \
		build/obj_divide_sign_slice/Vtb_adsp2100_divide_sign_slice; \
		$(PYTHON) tools/generators/generate_shifter_vectors.py \
			--output build/shifter_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter \
			--top-module tb_adsp2100_shifter \
			rtl/core/adsp2100_shifter.sv \
			sim/unit/tb_adsp2100_shifter.sv; \
		build/obj_shifter/Vtb_adsp2100_shifter; \
		$(PYTHON) tools/generators/generate_immediate_shift_vectors.py \
			--output build/immediate_shift_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_immediate_shift_slice \
			--top-module tb_adsp2100_immediate_shift_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_immediate_shift_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_immediate_shift_slice.sv \
			sim/unit/tb_adsp2100_immediate_shift_slice.sv; \
		build/obj_immediate_shift_slice/Vtb_adsp2100_immediate_shift_slice; \
		$(PYTHON) tools/generators/generate_conditional_shift_vectors.py \
			--output build/conditional_shift_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_conditional_shift_slice \
			--top-module tb_adsp2100_conditional_shift_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_conditional_shift_decode.sv \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_shift_slice.sv \
			sim/unit/tb_adsp2100_conditional_shift_slice.sv; \
		build/obj_conditional_shift_slice/Vtb_adsp2100_conditional_shift_slice; \
		$(PYTHON) tools/generators/generate_shift_move_vectors.py \
			--output build/shift_move_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_shift_move_slice \
			--top-module tb_adsp2100_shift_move_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shift_move_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shift_move_slice.sv \
			sim/unit/tb_adsp2100_shift_move_slice.sv; \
		build/obj_shift_move_slice/Vtb_adsp2100_shift_move_slice; \
		$(PYTHON) tools/generators/generate_shifter_dm_vectors.py \
			--output build/shifter_dm_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter_dm_slice \
			--top-module tb_adsp2100_shifter_dm_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_dm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_dm_slice.sv \
			sim/unit/tb_adsp2100_shifter_dm_slice.sv; \
		build/obj_shifter_dm_slice/Vtb_adsp2100_shifter_dm_slice; \
		$(PYTHON) tools/generators/generate_shifter_pm_vectors.py \
			--output build/shifter_pm_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_shifter_pm_slice \
			--top-module tb_adsp2100_shifter_pm_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv \
			sim/unit/tb_adsp2100_shifter_pm_slice.sv; \
		build/obj_shifter_pm_slice/Vtb_adsp2100_shifter_pm_slice; \
		$(PYTHON) tools/generators/generate_compute_move_vectors.py \
			--output build/compute_move_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_move_slice \
			--top-module tb_adsp2100_compute_move_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_move_decode.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_move_slice.sv \
			sim/unit/tb_adsp2100_compute_move_slice.sv; \
		build/obj_compute_move_slice/Vtb_adsp2100_compute_move_slice; \
		$(PYTHON) tools/generators/generate_compute_dm_vectors.py \
			--output build/compute_dm_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_dm_slice \
			--top-module tb_adsp2100_compute_dm_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			sim/unit/tb_adsp2100_compute_dm_slice.sv; \
		build/obj_compute_dm_slice/Vtb_adsp2100_compute_dm_slice; \
		$(PYTHON) tools/generators/generate_compute_pm_vectors.py \
			--output build/compute_pm_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_pm_slice \
			--top-module tb_adsp2100_compute_pm_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_pm_decode.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_compute_pm_slice.sv \
			sim/unit/tb_adsp2100_compute_pm_slice.sv; \
		build/obj_compute_pm_slice/Vtb_adsp2100_compute_pm_slice; \
		$(PYTHON) tools/generators/generate_compute_pm_native_vectors.py \
			--output build/compute_pm_native_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_compute_pm_native_slice \
			--top-module tb_adsp2100_compute_pm_native_slice \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_pm_decode.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_compute_pm_slice.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_compute_pm_cache_slice.sv \
			rtl/core/adsp2100_program_bus.sv \
			rtl/core/adsp2100_compute_pm_native_slice.sv \
			sim/unit/tb_adsp2100_compute_pm_native_slice.sv; \
		build/obj_compute_pm_native_slice/Vtb_adsp2100_compute_pm_native_slice; \
		$(PYTHON) tools/generators/generate_conditional_compute_vectors.py \
			--output build/conditional_compute_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_conditional_compute_slice \
			--top-module tb_adsp2100_conditional_compute_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_compute_decode.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_compute_slice.sv \
			sim/unit/tb_adsp2100_conditional_compute_slice.sv; \
		build/obj_conditional_compute_slice/Vtb_adsp2100_conditional_compute_slice; \
	else \
		echo "SKIP condition RTL test: Verilator executable not available"; \
	fi

dag-tests:
	$(PYTHON) -m unittest -v tests.test_dag_model \
		tests.test_modify_address
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
		$(PYTHON) tools/generators/generate_modify_address_vectors.py \
			--output build/modify_address_slice_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_modify_address_slice \
			--top-module tb_adsp2100_modify_address_slice \
			rtl/core/adsp2100_modify_address_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_modify_address_slice.sv \
			sim/unit/tb_adsp2100_modify_address_slice.sv; \
		build/obj_modify_address_slice/Vtb_adsp2100_modify_address_slice; \
	else \
		echo "SKIP DAG RTL test: Verilator executable not available"; \
	fi

sequencer-tests:
		$(PYTHON) -m unittest -v tests.test_sequencer_flow \
		tests.test_counter tests.test_sequencer_stacks \
		tests.test_sequencer_slice tests.test_stack_control_slice \
		tests.test_direct_jump tests.test_do_until tests.test_indirect_jump \
		tests.test_conditional_return tests.test_conditional_trap
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
		$(PYTHON) tools/generators/generate_direct_jump_vectors.py \
			--output build/direct_jump_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_direct_jump_slice \
			--top-module tb_adsp2100_direct_jump_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_direct_jump_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_direct_jump_slice.sv \
			sim/unit/tb_adsp2100_direct_jump_slice.sv; \
		build/obj_direct_jump_slice/Vtb_adsp2100_direct_jump_slice; \
		$(PYTHON) tools/generators/generate_do_until_vectors.py \
			--output build/do_until_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_do_until_slice \
			--top-module tb_adsp2100_do_until_slice \
			rtl/core/adsp2100_do_until_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_do_until_slice.sv \
			sim/unit/tb_adsp2100_do_until_slice.sv; \
		build/obj_do_until_slice/Vtb_adsp2100_do_until_slice; \
		$(PYTHON) tools/generators/generate_indirect_jump_vectors.py \
			--output build/indirect_jump_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_indirect_jump_slice \
			--top-module tb_adsp2100_indirect_jump_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_indirect_jump_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_indirect_jump_slice.sv \
			sim/unit/tb_adsp2100_indirect_jump_slice.sv; \
		build/obj_indirect_jump_slice/Vtb_adsp2100_indirect_jump_slice; \
		$(PYTHON) tools/generators/generate_conditional_return_vectors.py \
			--output build/conditional_return_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD -Wno-PINCONNECTEMPTY \
			--Mdir build/obj_conditional_return_slice \
			--top-module tb_adsp2100_conditional_return_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_return_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_return_slice.sv \
			sim/unit/tb_adsp2100_conditional_return_slice.sv; \
		build/obj_conditional_return_slice/Vtb_adsp2100_conditional_return_slice; \
		$(PYTHON) tools/generators/generate_conditional_trap_vectors.py \
			--output build/conditional_trap_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_conditional_trap_slice \
			--top-module tb_adsp2100_conditional_trap_slice \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_trap_decode.sv \
			rtl/core/adsp2100_conditional_trap_slice.sv \
			sim/unit/tb_adsp2100_conditional_trap_slice.sv; \
		build/obj_conditional_trap_slice/Vtb_adsp2100_conditional_trap_slice; \
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
	$(PYTHON) -m unittest -v tests.test_register_banks \
		tests.test_internal_move_slice tests.test_load_dreg_immediate
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
		$(PYTHON) tools/reference/generate_internal_move_slice_vectors.py \
			--output build/internal_move_slice_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_internal_move_slice \
			--top-module tb_adsp2100_internal_move_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_internal_move_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_internal_move_slice.sv \
			sim/unit/tb_adsp2100_internal_move_slice.sv; \
		build/obj_internal_move_slice/Vtb_adsp2100_internal_move_slice; \
		$(PYTHON) tools/generators/generate_load_dreg_immediate_vectors.py \
			--output build/load_dreg_immediate_vectors.txt; \
		"$(VERILATOR)" --binary --timing -Wall -Wno-DECLFILENAME \
			-Wno-TIMESCALEMOD \
			--Mdir build/obj_load_dreg_immediate_slice \
			--top-module tb_adsp2100_load_dreg_immediate_slice \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_load_dreg_immediate_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_load_dreg_immediate_slice.sv \
			sim/unit/tb_adsp2100_load_dreg_immediate_slice.sv; \
		build/obj_load_dreg_immediate_slice/Vtb_adsp2100_load_dreg_immediate_slice; \
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

instruction-tests: decode-tests assembler-tests compute-tests sequencer-tests mode-tests bus-tests
	@echo "PASS bounded semantic instruction-slice regression"

bus-tests: cache-tests pm-bus-tests dm-bus-tests dm-write-native-tests dm-shifter-native-tests dm-compute-native-tests pm-native-tests compute-tests
	$(PYTHON) -m unittest -v tests.test_dm_write_immediate_slice
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		$(PYTHON) tools/generators/generate_dm_write_immediate_vectors.py \
			--output build/dm_write_immediate_vectors.txt; \
		"$(VERILATOR)" --binary --timing --assert -Wall \
			-Wno-DECLFILENAME -Wno-TIMESCALEMOD \
			--Mdir build/obj_dm_write_immediate_slice \
			--top-module tb_adsp2100_dm_write_immediate_slice \
			rtl/core/adsp2100_dm_write_immediate_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_dm_write_immediate_slice.sv \
			sim/unit/tb_adsp2100_dm_write_immediate_slice.sv; \
		build/obj_dm_write_immediate_slice/Vtb_adsp2100_dm_write_immediate_slice; \
	else \
		echo "SKIP Type 2 transaction RTL test: Verilator is not installed"; \
	fi
	@echo "PASS bounded cache, Type 2/4/12 DM, and Type 5/13 PM transaction regressions"

interrupt-tests:
	@echo "SKIP interrupt tests: interrupt RTL does not exist"

differential: bus-tests dag-tests sequencer-tests register-tests status-tests mode-tests
	@echo "PASS available bounded model/RTL differential regressions"

fuzz:
	@echo "SKIP fuzz tests: complete legal-instruction generator does not exist"

formal:
	@if command -v "$(VERILATOR)" >/dev/null 2>&1; then \
		set -e; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_instruction_cache_formal \
			rtl/core/adsp2100_instruction_cache.sv \
			formal/harnesses/adsp2100_instruction_cache_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_program_bus_formal \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_program_bus.sv \
			formal/harnesses/adsp2100_program_bus_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_data_bus_formal \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_data_bus.sv \
			formal/harnesses/adsp2100_data_bus_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_dm_write_immediate_native_formal \
			rtl/packages/adsp2100_pkg.sv \
			rtl/core/adsp2100_dm_write_immediate_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_dm_write_immediate_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_dm_write_immediate_native_slice.sv \
			formal/harnesses/adsp2100_dm_write_immediate_native_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_dm_native_formal \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_dm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_dm_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_shifter_dm_native_slice.sv \
			formal/harnesses/adsp2100_shifter_dm_native_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_dm_native_formal \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_data_bus.sv \
			rtl/core/adsp2100_compute_dm_native_slice.sv \
			formal/harnesses/adsp2100_compute_dm_native_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_pm_native_formal \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv \
			rtl/core/adsp2100_shifter_pm_cache_slice.sv \
			rtl/core/adsp2100_program_bus.sv \
			rtl/core/adsp2100_shifter_pm_native_slice.sv \
			formal/harnesses/adsp2100_shifter_pm_native_formal.sv; \
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
			--top-module adsp2100_load_dreg_immediate_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_load_dreg_immediate_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_load_dreg_immediate_slice.sv \
			formal/harnesses/adsp2100_load_dreg_immediate_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_immediate_shift_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_immediate_shift_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_immediate_shift_slice.sv \
			formal/harnesses/adsp2100_immediate_shift_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_conditional_shift_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_conditional_shift_decode.sv \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_shift_slice.sv \
			formal/harnesses/adsp2100_conditional_shift_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shift_move_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shift_move_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shift_move_slice.sv \
			formal/harnesses/adsp2100_shift_move_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_dm_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_dm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_dm_slice.sv \
			formal/harnesses/adsp2100_shifter_dm_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			-Wno-PINCONNECTEMPTY \
			--top-module adsp2100_shifter_pm_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv \
			formal/harnesses/adsp2100_shifter_pm_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_shifter_pm_cache_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_shifter_pm_decode.sv \
			rtl/core/adsp2100_shifter.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_shifter_pm_slice.sv \
			rtl/core/adsp2100_shifter_pm_cache_slice.sv \
			formal/harnesses/adsp2100_shifter_pm_cache_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_move_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_move_decode.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_move_slice.sv \
			formal/harnesses/adsp2100_compute_move_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_dual_decode_formal \
			rtl/core/adsp2100_compute_dual_decode.sv \
			formal/harnesses/adsp2100_compute_dual_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_dm_decode_formal \
			rtl/core/adsp2100_compute_dm_decode.sv \
			formal/harnesses/adsp2100_compute_dm_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_pm_decode_formal \
			rtl/core/adsp2100_compute_pm_decode.sv \
			formal/harnesses/adsp2100_compute_pm_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_dm_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			formal/harnesses/adsp2100_compute_dm_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_pm_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_pm_decode.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_compute_pm_slice.sv \
			formal/harnesses/adsp2100_compute_pm_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_pm_cache_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_pm_decode.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_compute_pm_slice.sv \
			rtl/core/adsp2100_compute_pm_cache_slice.sv \
			formal/harnesses/adsp2100_compute_pm_cache_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_compute_pm_native_formal \
			rtl/packages/adsp2100_pkg.sv \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_compute_pm_decode.sv \
			rtl/core/adsp2100_compute_dm_decode.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_instruction_cache.sv \
			rtl/core/adsp2100_compute_dm_slice.sv \
			rtl/core/adsp2100_compute_pm_slice.sv \
			rtl/core/adsp2100_compute_pm_cache_slice.sv \
			rtl/core/adsp2100_program_bus.sv \
			rtl/core/adsp2100_compute_pm_native_slice.sv \
			formal/harnesses/adsp2100_compute_pm_native_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_conditional_compute_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_compute_decode.sv \
			rtl/core/adsp2100_alu.sv \
			rtl/core/adsp2100_mr_saturate.sv \
			rtl/core/adsp2100_mac.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_compute_slice.sv \
			formal/harnesses/adsp2100_conditional_compute_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mr_saturation_decode_formal \
			rtl/core/adsp2100_mr_saturation_decode.sv \
			formal/harnesses/adsp2100_mr_saturation_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_mode_control_decode_formal \
			rtl/core/adsp2100_mode_control_decode.sv \
			formal/harnesses/adsp2100_mode_control_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_internal_move_decode_formal \
			rtl/core/adsp2100_internal_move_decode.sv \
			formal/harnesses/adsp2100_internal_move_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_internal_move_slice_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_internal_move_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_internal_move_slice.sv \
			formal/harnesses/adsp2100_internal_move_slice_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_modify_address_decode_formal \
			rtl/core/adsp2100_modify_address_decode.sv \
			formal/harnesses/adsp2100_modify_address_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_dm_write_immediate_decode_formal \
			rtl/core/adsp2100_dm_write_immediate_decode.sv \
			formal/harnesses/adsp2100_dm_write_immediate_decode_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_dm_write_immediate_slice_formal \
			rtl/core/adsp2100_dm_write_immediate_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_dm_write_immediate_slice.sv \
			formal/harnesses/adsp2100_dm_write_immediate_slice_formal.sv; \
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
			--top-module adsp2100_modify_address_slice_formal \
			rtl/core/adsp2100_modify_address_decode.sv \
			rtl/core/adsp2100_dag.sv \
			rtl/core/adsp2100_dag_register_file.sv \
			rtl/core/adsp2100_modify_address_slice.sv \
			formal/harnesses/adsp2100_modify_address_slice_formal.sv; \
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
			--top-module adsp2100_direct_jump_formal \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_direct_jump_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_direct_jump_slice.sv \
			formal/harnesses/adsp2100_direct_jump_formal.sv; \
			"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
				--top-module adsp2100_do_until_formal \
			rtl/core/adsp2100_do_until_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
				rtl/core/adsp2100_do_until_slice.sv \
				formal/harnesses/adsp2100_do_until_formal.sv; \
			"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
				--top-module adsp2100_indirect_jump_formal \
				rtl/core/adsp2100_condition_logic.sv \
				rtl/core/adsp2100_indirect_jump_decode.sv \
				rtl/core/adsp2100_counter.sv \
				rtl/core/adsp2100_sequencer_stacks.sv \
				rtl/core/adsp2100_dag_register_file.sv \
				rtl/core/adsp2100_indirect_jump_slice.sv \
				formal/harnesses/adsp2100_indirect_jump_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_conditional_return_formal \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_return_decode.sv \
			rtl/core/adsp2100_counter.sv \
			rtl/core/adsp2100_sequencer_stacks.sv \
			rtl/core/adsp2100_status_stack.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_conditional_return_slice.sv \
			formal/harnesses/adsp2100_conditional_return_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_conditional_trap_formal \
			rtl/core/adsp2100_condition_logic.sv \
			rtl/core/adsp2100_conditional_trap_decode.sv \
			rtl/core/adsp2100_conditional_trap_slice.sv \
			formal/harnesses/adsp2100_conditional_trap_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_divide_quotient_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_divide_quotient_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_divide_quotient_slice.sv \
			formal/harnesses/adsp2100_divide_quotient_formal.sv; \
		"$(VERILATOR)" --lint-only --assert -Wall -Wno-DECLFILENAME \
			--top-module adsp2100_divide_sign_formal \
			rtl/packages/adsp2100_register_pkg.sv \
			rtl/core/adsp2100_divide_sign_decode.sv \
			rtl/core/adsp2100_register_file.sv \
			rtl/core/adsp2100_status_registers.sv \
			rtl/core/adsp2100_divide_sign_slice.sv \
			formal/harnesses/adsp2100_divide_sign_formal.sv; \
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
		sby -f -d build/formal_load_dreg_immediate \
			formal/load_dreg_immediate.sby; \
		sby -f -d build/formal_immediate_shift \
			formal/immediate_shift.sby; \
		sby -f -d build/formal_conditional_shift \
			formal/conditional_shift.sby; \
		sby -f -d build/formal_shift_move formal/shift_move.sby; \
		sby -f -d build/formal_shifter_dm formal/shifter_dm.sby; \
		sby -f -d build/formal_shifter_pm formal/shifter_pm.sby; \
		sby -f -d build/formal_shifter_pm_cache \
			formal/shifter_pm_cache.sby; \
		sby -f -d build/formal_instruction_cache formal/instruction_cache.sby; \
		sby -f -d build/formal_pm_bus formal/pm_bus.sby; \
		sby -f -d build/formal_dm_bus formal/dm_bus.sby; \
		sby -f -d build/formal_dm_write_immediate_native \
			formal/dm_write_immediate_native.sby; \
		sby -f -d build/formal_shifter_dm_native \
			formal/shifter_dm_native.sby; \
		sby -f -d build/formal_shifter_pm_native \
			formal/shifter_pm_native.sby; \
		sby -f -d build/formal_compute_move formal/compute_move.sby; \
		sby -f -d build/formal_compute_dual_decode \
			formal/compute_dual_decode.sby; \
		sby -f -d build/formal_compute_dm_decode \
			formal/compute_dm_decode.sby; \
		sby -f -d build/formal_compute_pm_decode \
			formal/compute_pm_decode.sby; \
		sby -f -d build/formal_compute_dm formal/compute_dm.sby; \
		sby -f -d build/formal_compute_dm_native \
			formal/compute_dm_native.sby; \
		sby -f -d build/formal_compute_pm formal/compute_pm.sby; \
		sby -f -d build/formal_compute_pm_cache \
			formal/compute_pm_cache.sby; \
		sby -f -d build/formal_compute_pm_native \
			formal/compute_pm_native.sby; \
		sby -f -d build/formal_conditional_compute \
			formal/conditional_compute.sby; \
		sby -f -d build/formal_stack_control_decode \
			formal/stack_control_decode.sby; \
		sby -f -d build/formal_mr_saturation_decode \
			formal/mr_saturation_decode.sby; \
		sby -f -d build/formal_mode_control_decode \
			formal/mode_control_decode.sby; \
		sby -f -d build/formal_internal_move_decode \
			formal/internal_move_decode.sby; \
		sby -f -d build/formal_internal_move_slice \
			formal/internal_move_slice.sby; \
		sby -f -d build/formal_modify_address_decode \
			formal/modify_address_decode.sby; \
		sby -f -d build/formal_dm_write_immediate_decode \
			formal/dm_write_immediate_decode.sby; \
		sby -f -d build/formal_dm_write_immediate_slice \
			formal/dm_write_immediate_slice.sby; \
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
		sby -f -d build/formal_modify_address_slice \
			formal/modify_address_slice.sby; \
		sby -f -d build/formal_sequencer formal/sequencer_flow.sby; \
		sby -f -d build/formal_counter formal/counter.sby; \
		sby -f -d build/formal_sequencer_stacks formal/sequencer_stacks.sby; \
		sby -f -d build/formal_sequencer_slice formal/sequencer_slice.sby; \
		sby -f -d build/formal_direct_jump formal/direct_jump.sby; \
		sby -f -d build/formal_do_until formal/do_until.sby; \
		sby -f -d build/formal_indirect_jump formal/indirect_jump.sby; \
		sby -f -d build/formal_conditional_return \
			formal/conditional_return.sby; \
		sby -f -d build/formal_conditional_trap \
			formal/conditional_trap.sby; \
		sby -f -d build/formal_divide_quotient formal/divide_quotient.sby; \
		sby -f -d build/formal_divide_sign formal/divide_sign.sby; \
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
			synthesis/quartus/load_dreg_immediate_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/immediate_shift_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/conditional_shift_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/shift_move_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/shifter_dm_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/dm_write_immediate_slice_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/shifter_pm_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/shifter_pm_cache_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/instruction_cache_smoke; \
		quartus_sh --flow compile synthesis/quartus/program_bus_smoke; \
		quartus_sh --flow compile synthesis/quartus/data_bus_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/dm_write_immediate_native_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/shifter_dm_native_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/shifter_pm_native_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_move_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_dual_decode_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_dm_decode_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_pm_decode_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_dm_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_dm_native_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_pm_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_pm_cache_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/compute_pm_native_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/conditional_compute_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/direct_jump_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/do_until_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/indirect_jump_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/conditional_return_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/conditional_trap_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/divide_quotient_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/divide_sign_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/stack_control_decode_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/stack_control_slice_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/mr_saturation_slice_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/mode_control_slice_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/internal_move_decode_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/internal_move_slice_smoke; \
		quartus_sh --flow compile \
			synthesis/quartus/modify_address_slice_smoke; \
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
	@find build -maxdepth 1 -type f -name instruction_cache_vectors.txt -delete
	@find build -maxdepth 1 -type f -name shifter_pm_cache_vectors.txt -delete
	@find build -maxdepth 1 -type f -name program_bus_vectors.txt -delete
	@find build -maxdepth 1 -type f -name data_bus_vectors.txt -delete
	@find build -maxdepth 1 -type f -name dm_write_immediate_native_vectors.txt -delete
	@find build -maxdepth 1 -type f -name shifter_dm_native_vectors.txt -delete
	@find build -maxdepth 1 -type f -name compute_dm_native_vectors.txt -delete
	@find build -maxdepth 1 -type f -name shifter_pm_native_vectors.txt -delete
	@find build -maxdepth 1 -type f -name dm_write_immediate_vectors.txt -delete
	@find scripts tools sim tests -type d -name __pycache__ -prune -exec rm -r {} +
	@find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	@find build -maxdepth 1 -type f -name condition_expected.mem -delete
	@find build -maxdepth 1 -type f -name alu_vectors.txt -delete
	@find build -maxdepth 1 -type f -name mac_vectors.txt -delete
	@find build -maxdepth 1 -type f -name mr_saturation_slice_vectors.txt -delete
	@find build -maxdepth 1 -type f -name mode_control_slice_vectors.txt -delete
	@find build -maxdepth 1 -type f -name modify_address_slice_vectors.txt -delete
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
	@find build -maxdepth 1 -type f -name internal_move_slice_vectors.txt -delete
	@find build -maxdepth 1 -type f -name load_dreg_immediate_vectors.txt -delete
	@find build -maxdepth 1 -type f -name immediate_shift_vectors.txt -delete
	@find build -maxdepth 1 -type f -name conditional_shift_vectors.txt -delete
	@find build -maxdepth 1 -type f -name shift_move_vectors.txt -delete
	@find build -maxdepth 1 -type f -name shifter_dm_vectors.txt -delete
	@find build -maxdepth 1 -type f -name shifter_pm_vectors.txt -delete
	@find build -maxdepth 1 -type f -name compute_move_vectors.txt -delete
	@find build -maxdepth 1 -type f -name compute_dm_vectors.txt -delete
	@find build -maxdepth 1 -type f -name compute_pm_vectors.txt -delete
	@find build -maxdepth 1 -type f -name compute_pm_native_vectors.txt -delete
	@find build -maxdepth 1 -type f -name conditional_compute_vectors.txt -delete
	@find build -maxdepth 1 -type f -name direct_jump_vectors.txt -delete
	@find build -maxdepth 1 -type f -name do_until_vectors.txt -delete
	@find build -maxdepth 1 -type f -name indirect_jump_vectors.txt -delete
	@find build -maxdepth 1 -type f -name conditional_return_vectors.txt -delete
	@find build -maxdepth 1 -type f -name conditional_trap_vectors.txt -delete
	@find build -maxdepth 1 -type f -name divide_quotient_vectors.txt -delete
	@find build -maxdepth 1 -type f -name divide_sign_vectors.txt -delete
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
	@if [ -d build/obj_internal_move_decode ]; then \
		find build/obj_internal_move_decode -depth -delete; \
	fi
	@if [ -d build/obj_internal_move_slice ]; then \
		find build/obj_internal_move_slice -depth -delete; \
	fi
	@if [ -d build/obj_load_dreg_immediate_decode ]; then \
		find build/obj_load_dreg_immediate_decode -depth -delete; \
	fi
	@if [ -d build/obj_load_dreg_immediate_slice ]; then \
		find build/obj_load_dreg_immediate_slice -depth -delete; \
	fi
	@if [ -d build/obj_immediate_shift_decode ]; then \
		find build/obj_immediate_shift_decode -depth -delete; \
	fi
	@if [ -d build/obj_immediate_shift_slice ]; then \
		find build/obj_immediate_shift_slice -depth -delete; \
	fi
	@if [ -d build/obj_conditional_shift_decode ]; then \
		find build/obj_conditional_shift_decode -depth -delete; \
	fi
	@if [ -d build/obj_conditional_shift_slice ]; then \
		find build/obj_conditional_shift_slice -depth -delete; \
	fi
	@if [ -d build/obj_shift_move_decode ]; then \
		find build/obj_shift_move_decode -depth -delete; \
	fi
	@if [ -d build/obj_shift_move_slice ]; then \
		find build/obj_shift_move_slice -depth -delete; \
	fi
	@if [ -d build/obj_shifter_dm_decode ]; then \
		find build/obj_shifter_dm_decode -depth -delete; \
	fi
	@if [ -d build/obj_shifter_dm_slice ]; then \
		find build/obj_shifter_dm_slice -depth -delete; \
	fi
	@if [ -d build/obj_shifter_pm_decode ]; then \
		find build/obj_shifter_pm_decode -depth -delete; \
	fi
	@if [ -d build/obj_shifter_pm_slice ]; then \
		find build/obj_shifter_pm_slice -depth -delete; \
	fi
	@if [ -d build/obj_shifter_pm_cache_slice ]; then \
		find build/obj_shifter_pm_cache_slice -depth -delete; \
	fi
	@if [ -d build/obj_instruction_cache ]; then \
		find build/obj_instruction_cache -depth -delete; \
	fi
	@if [ -d build/obj_program_bus ]; then \
		find build/obj_program_bus -depth -delete; \
	fi
	@if [ -d build/obj_data_bus ]; then \
		find build/obj_data_bus -depth -delete; \
	fi
	@if [ -d build/obj_dm_write_immediate_native_slice ]; then \
		find build/obj_dm_write_immediate_native_slice -depth -delete; \
	fi
	@if [ -d build/obj_shifter_dm_native_slice ]; then \
		find build/obj_shifter_dm_native_slice -depth -delete; \
	fi
	@if [ -d build/obj_compute_dm_native_slice ]; then \
		find build/obj_compute_dm_native_slice -depth -delete; \
	fi
	@if [ -d build/obj_shifter_pm_native_slice ]; then \
		find build/obj_shifter_pm_native_slice -depth -delete; \
	fi
	@if [ -d build/obj_shifter_pm_native_debug ]; then \
		find build/obj_shifter_pm_native_debug -depth -delete; \
	fi
	@if [ -d build/obj_compute_move_decode ]; then \
		find build/obj_compute_move_decode -depth -delete; \
	fi
	@if [ -d build/obj_compute_move_slice ]; then \
		find build/obj_compute_move_slice -depth -delete; \
	fi
	@if [ -d build/obj_compute_dual_decode ]; then \
		find build/obj_compute_dual_decode -depth -delete; \
	fi
	@if [ -d build/obj_compute_dm_decode ]; then \
		find build/obj_compute_dm_decode -depth -delete; \
	fi
	@if [ -d build/obj_compute_pm_decode ]; then \
		find build/obj_compute_pm_decode -depth -delete; \
	fi
	@if [ -d build/obj_compute_dm_slice ]; then \
		find build/obj_compute_dm_slice -depth -delete; \
	fi
	@if [ -d build/obj_compute_pm_slice ]; then \
		find build/obj_compute_pm_slice -depth -delete; \
	fi
	@if [ -d build/obj_compute_pm_native_slice ]; then \
		find build/obj_compute_pm_native_slice -depth -delete; \
	fi
	@if [ -d build/obj_conditional_compute_decode ]; then \
		find build/obj_conditional_compute_decode -depth -delete; \
	fi
	@if [ -d build/obj_conditional_compute_slice ]; then \
		find build/obj_conditional_compute_slice -depth -delete; \
	fi
	@if [ -d build/obj_direct_jump_decode ]; then \
		find build/obj_direct_jump_decode -depth -delete; \
	fi
	@if [ -d build/obj_direct_jump_slice ]; then \
		find build/obj_direct_jump_slice -depth -delete; \
	fi
	@if [ -d build/obj_do_until_decode ]; then \
		find build/obj_do_until_decode -depth -delete; \
	fi
	@if [ -d build/obj_do_until_slice ]; then \
		find build/obj_do_until_slice -depth -delete; \
	fi
	@if [ -d build/obj_indirect_jump_decode ]; then \
		find build/obj_indirect_jump_decode -depth -delete; \
	fi
	@if [ -d build/obj_indirect_jump_slice ]; then \
		find build/obj_indirect_jump_slice -depth -delete; \
	fi
	@if [ -d build/obj_conditional_return_decode ]; then \
		find build/obj_conditional_return_decode -depth -delete; \
	fi
	@if [ -d build/obj_conditional_return_slice ]; then \
		find build/obj_conditional_return_slice -depth -delete; \
	fi
	@if [ -d build/obj_conditional_trap_decode ]; then \
		find build/obj_conditional_trap_decode -depth -delete; \
	fi
	@if [ -d build/obj_conditional_trap_slice ]; then \
		find build/obj_conditional_trap_slice -depth -delete; \
	fi
	@if [ -d build/obj_divide_quotient_decode ]; then \
		find build/obj_divide_quotient_decode -depth -delete; \
	fi
	@if [ -d build/obj_divide_quotient_slice ]; then \
		find build/obj_divide_quotient_slice -depth -delete; \
	fi
	@if [ -d build/obj_divide_sign_decode ]; then \
		find build/obj_divide_sign_decode -depth -delete; \
	fi
	@if [ -d build/obj_divide_sign_slice ]; then \
		find build/obj_divide_sign_slice -depth -delete; \
	fi
	@if [ -d build/obj_modify_address_decode ]; then \
		find build/obj_modify_address_decode -depth -delete; \
	fi
	@if [ -d build/obj_dm_write_immediate_decode ]; then \
		find build/obj_dm_write_immediate_decode -depth -delete; \
	fi
	@if [ -d build/obj_dm_write_immediate_slice ]; then \
		find build/obj_dm_write_immediate_slice -depth -delete; \
	fi
	@if [ -d build/obj_modify_address_slice ]; then \
		find build/obj_modify_address_slice -depth -delete; \
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
	@if [ -d build/quartus_internal_move_decode ]; then \
		find build/quartus_internal_move_decode -depth -delete; \
	fi
	@if [ -d build/quartus_internal_move_slice ]; then \
		find build/quartus_internal_move_slice -depth -delete; \
	fi
	@if [ -d build/quartus_load_dreg_immediate ]; then \
		find build/quartus_load_dreg_immediate -depth -delete; \
	fi
	@if [ -d build/quartus_immediate_shift ]; then \
		find build/quartus_immediate_shift -depth -delete; \
	fi
	@if [ -d build/quartus_conditional_shift ]; then \
		find build/quartus_conditional_shift -depth -delete; \
	fi
	@if [ -d build/quartus_shift_move ]; then \
		find build/quartus_shift_move -depth -delete; \
	fi
	@if [ -d build/quartus_shifter_dm ]; then \
		find build/quartus_shifter_dm -depth -delete; \
	fi
	@if [ -d build/quartus_dm_write_immediate_slice ]; then \
		find build/quartus_dm_write_immediate_slice -depth -delete; \
	fi
	@if [ -d build/quartus_shifter_pm ]; then \
		find build/quartus_shifter_pm -depth -delete; \
	fi
	@if [ -d build/quartus_shifter_pm_cache ]; then \
		find build/quartus_shifter_pm_cache -depth -delete; \
	fi
	@if [ -d build/quartus_instruction_cache ]; then \
		find build/quartus_instruction_cache -depth -delete; \
	fi
	@if [ -d build/quartus_program_bus ]; then \
		find build/quartus_program_bus -depth -delete; \
	fi
	@if [ -d build/quartus_data_bus ]; then \
		find build/quartus_data_bus -depth -delete; \
	fi
	@if [ -d build/quartus_dm_write_immediate_native ]; then \
		find build/quartus_dm_write_immediate_native -depth -delete; \
	fi
	@if [ -d build/quartus_shifter_dm_native ]; then \
		find build/quartus_shifter_dm_native -depth -delete; \
	fi
	@if [ -d build/quartus_shifter_pm_native ]; then \
		find build/quartus_shifter_pm_native -depth -delete; \
	fi
	@if [ -d build/quartus_compute_move ]; then \
		find build/quartus_compute_move -depth -delete; \
	fi
	@if [ -d build/quartus_compute_dual_decode ]; then \
		find build/quartus_compute_dual_decode -depth -delete; \
	fi
	@if [ -d build/quartus_compute_dm_decode ]; then \
		find build/quartus_compute_dm_decode -depth -delete; \
	fi
	@if [ -d build/quartus_compute_pm_decode ]; then \
		find build/quartus_compute_pm_decode -depth -delete; \
	fi
	@if [ -d build/quartus_compute_dm ]; then \
		find build/quartus_compute_dm -depth -delete; \
	fi
	@if [ -d build/quartus_compute_dm_native ]; then \
		find build/quartus_compute_dm_native -depth -delete; \
	fi
	@if [ -d build/quartus_compute_pm ]; then \
		find build/quartus_compute_pm -depth -delete; \
	fi
	@if [ -d build/quartus_compute_pm_cache ]; then \
		find build/quartus_compute_pm_cache -depth -delete; \
	fi
	@if [ -d build/quartus_compute_pm_native ]; then \
		find build/quartus_compute_pm_native -depth -delete; \
	fi
	@if [ -d build/quartus_conditional_compute ]; then \
		find build/quartus_conditional_compute -depth -delete; \
	fi
	@if [ -d build/quartus_direct_jump ]; then \
		find build/quartus_direct_jump -depth -delete; \
	fi
	@if [ -d build/quartus_do_until ]; then \
		find build/quartus_do_until -depth -delete; \
	fi
	@if [ -d build/quartus_indirect_jump ]; then \
		find build/quartus_indirect_jump -depth -delete; \
	fi
	@if [ -d build/quartus_conditional_return ]; then \
		find build/quartus_conditional_return -depth -delete; \
	fi
	@if [ -d build/quartus_conditional_trap ]; then \
		find build/quartus_conditional_trap -depth -delete; \
	fi
	@if [ -d build/quartus_divide_quotient ]; then \
		find build/quartus_divide_quotient -depth -delete; \
	fi
	@if [ -d build/quartus_divide_sign ]; then \
		find build/quartus_divide_sign -depth -delete; \
	fi
	@if [ -d build/quartus_modify_address_slice ]; then \
		find build/quartus_modify_address_slice -depth -delete; \
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
		build/formal_internal_move_decode \
		build/formal_internal_move_slice \
		build/formal_load_dreg_immediate \
		build/formal_immediate_shift \
		build/formal_conditional_shift \
		build/formal_shift_move \
		build/formal_shifter_dm \
		build/formal_shifter_pm \
		build/formal_shifter_pm_cache \
		build/formal_instruction_cache \
		build/formal_pm_bus \
		build/formal_dm_bus \
		build/formal_dm_write_immediate_native \
		build/formal_shifter_dm_native \
		build/formal_shifter_pm_native \
		build/formal_compute_move \
		build/formal_compute_dual_decode \
		build/formal_compute_dm_decode \
		build/formal_compute_pm_decode \
		build/formal_compute_dm \
		build/formal_compute_dm_native \
		build/formal_compute_pm \
		build/formal_compute_pm_cache \
		build/formal_compute_pm_native \
		build/formal_conditional_compute \
		build/formal_direct_jump \
		build/formal_do_until \
		build/formal_indirect_jump \
		build/formal_conditional_return \
		build/formal_conditional_trap \
		build/formal_divide_quotient \
		build/formal_divide_sign \
		build/formal_modify_address_decode \
		build/formal_dm_write_immediate_decode \
		build/formal_dm_write_immediate_slice \
		build/formal_modify_address_slice \
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
