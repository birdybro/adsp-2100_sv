`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_linear_core_slice;
    logic clk;
    logic [80:0] stimulus;
    logic [130:0] expected_pre;
    logic [122:0] expected_post;

    logic reset;
    logic [2:0] phase;
    logic phase_advance;
    logic instruction_issue_inhibit;
    logic bus_relinquished;
    logic instruction_setup;
    logic [13:0] setup_pc;
    logic [23:0] setup_opcode;
    logic [23:0] pmd_read_data;
    logic pmd_read_data_valid;
    logic [3:0] irq_n;
    logic [5:0] probe_code;

    logic issue_boundary;
    logic setup_accepted;
    logic instruction_issue;
    logic retire_event;
    logic trap_event;
    logic interrupt_recognition_event;
    logic interrupt_entry_event;
    logic interrupt_vector_issue_event;
    logic interrupt_vector_fetch_event;
    logic [1:0] interrupt_level;
    logic [13:0] interrupt_vector;
    logic [3:0] interrupt_pending;
    logic interrupt_vectoring;
    logic interrupt_configuration_invalid;
    logic interrupt_reset_baseline_provisional;
    logic interrupt_adjacent_control_conflict;
    logic instruction_valid;
    logic transaction_pending;
    logic unsupported_instruction;
    logic reserved_subencoding;
    logic phase_conflict;
    logic integration_conflict;
    logic internal_conflict;
    logic provisional_source_extension;
    logic [13:0] pc;
    logic [23:0] opcode;
    logic [15:0] probe_data;
    logic [7:0] astat;
    logic [3:0] mstat;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic [13:0] cntr;
    logic cntr_valid;
    logic [7:0] px;
    logic [7:0] sstat;
    logic alternate_bank;
    logic [2:0] count_stack_depth;
    logic count_stack_overflow;
    logic pm_request_accepted;
    logic pm_completion_event;
    logic pm_read_sample_event;
    logic pm_bus_active;
    logic pm_address_oe;
    logic pm_control_oe;
    logic pm_data_oe;
    logic [13:0] pma;
    logic pma_valid;
    logic pmda;
    logic pmda_valid;
    logic pms_n;
    logic pmrd_n;
    logic pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;

    logic exp_issue_boundary;
    logic exp_setup_accepted;
    logic exp_instruction_issue;
    logic exp_retire_event;
    logic exp_trap_event;
    logic exp_interrupt_recognition_event;
    logic exp_interrupt_entry_event;
    logic exp_interrupt_vector_issue_event;
    logic exp_interrupt_vector_fetch_event;
    logic [1:0] exp_interrupt_level;
    logic [13:0] exp_interrupt_vector;
    logic [3:0] exp_pre_interrupt_pending;
    logic exp_pre_interrupt_vectoring;
    logic exp_interrupt_configuration_invalid;
    logic exp_interrupt_reset_baseline_provisional;
    logic exp_interrupt_adjacent_control_conflict;
    logic exp_pre_instruction_valid;
    logic exp_pre_pending;
    logic exp_unsupported_instruction;
    logic exp_reserved_subencoding;
    logic exp_phase_conflict;
    logic exp_integration_conflict;
    logic exp_internal_conflict;
    logic exp_provisional_source_extension;
    logic [13:0] exp_pre_pc;
    logic [23:0] exp_pre_opcode;
    logic exp_pm_request_accepted;
    logic exp_pm_completion_event;
    logic exp_pm_read_sample_event;
    logic exp_pre_pm_active;
    logic exp_pm_address_oe;
    logic exp_pm_control_oe;
    logic exp_pm_data_oe;
    logic exp_pma_valid;
    logic [13:0] exp_pma;
    logic exp_pmda;
    logic exp_pmda_valid;
    logic exp_pms_n;
    logic exp_pmrd_n;
    logic exp_pmwr_n;
    logic exp_pmd_write_data_valid;
    logic [23:0] exp_pmd_write_data;

    logic exp_post_instruction_valid;
    logic exp_post_pending;
    logic [13:0] exp_post_pc;
    logic [23:0] exp_post_opcode;
    logic exp_probe_valid;
    logic [15:0] exp_probe_data;
    logic exp_astat_valid;
    logic [7:0] exp_astat;
    logic [3:0] exp_mstat;
    logic exp_icntl_valid;
    logic [4:0] exp_icntl;
    logic [3:0] exp_imask;
    logic exp_cntr_valid;
    logic [13:0] exp_cntr;
    logic exp_px_valid;
    logic [7:0] exp_px;
    logic [7:0] exp_sstat;
    logic exp_alternate_bank;
    logic [2:0] exp_count_stack_depth;
    logic exp_count_stack_overflow;
    logic exp_post_pm_active;
    logic exp_post_interrupt_vectoring;
    logic [3:0] exp_post_interrupt_pending;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, phase, phase_advance, instruction_issue_inhibit,
        bus_relinquished,
        instruction_setup, setup_pc, setup_opcode,
        pmd_read_data, pmd_read_data_valid, irq_n, probe_code
    } = stimulus;

    assign {
        exp_issue_boundary, exp_setup_accepted, exp_instruction_issue,
        exp_retire_event, exp_trap_event,
        exp_interrupt_recognition_event, exp_interrupt_entry_event,
        exp_interrupt_vector_issue_event,
        exp_interrupt_vector_fetch_event,
        exp_interrupt_level, exp_interrupt_vector,
        exp_pre_interrupt_pending, exp_pre_interrupt_vectoring,
        exp_interrupt_configuration_invalid,
        exp_interrupt_reset_baseline_provisional,
        exp_interrupt_adjacent_control_conflict,
        exp_pre_instruction_valid, exp_pre_pending,
        exp_unsupported_instruction, exp_reserved_subencoding,
        exp_phase_conflict, exp_integration_conflict,
        exp_internal_conflict, exp_provisional_source_extension,
        exp_pre_pc, exp_pre_opcode,
        exp_pm_request_accepted, exp_pm_completion_event,
        exp_pm_read_sample_event, exp_pre_pm_active,
        exp_pm_address_oe, exp_pm_control_oe, exp_pm_data_oe,
        exp_pma_valid, exp_pma, exp_pmda, exp_pmda_valid,
        exp_pms_n, exp_pmrd_n, exp_pmwr_n,
        exp_pmd_write_data_valid, exp_pmd_write_data
    } = expected_pre;

    assign {
        exp_post_instruction_valid, exp_post_pending,
        exp_post_pc, exp_post_opcode,
        exp_probe_valid, exp_probe_data,
        exp_astat_valid, exp_astat, exp_mstat,
        exp_icntl_valid, exp_icntl, exp_imask,
        exp_cntr_valid, exp_cntr, exp_px_valid, exp_px,
        exp_sstat, exp_alternate_bank, exp_count_stack_depth,
        exp_count_stack_overflow, exp_post_pm_active,
        exp_post_interrupt_vectoring, exp_post_interrupt_pending
    } = expected_post;

    /* verilator lint_off PINCONNECTEMPTY */
    adsp2100_linear_core_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .interrupt_sample_advance_i(1'b0),
        .instruction_issue_inhibit_i(instruction_issue_inhibit),
        .bus_relinquished_i(bus_relinquished),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(setup_pc),
        .instruction_setup_opcode_i(setup_opcode),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .dmd_read_data_i(16'h0000),
        .dmd_read_data_valid_i(1'b0),
        .irq_n_i(irq_n),
        .probe_code_i(probe_code),
        .issue_boundary_o(issue_boundary),
        .instruction_setup_accepted_o(setup_accepted),
        .instruction_issue_o(instruction_issue),
        .retire_event_o(retire_event),
        .trap_event_o(trap_event),
        .interrupt_recognition_event_o(interrupt_recognition_event),
        .interrupt_entry_event_o(interrupt_entry_event),
        .interrupt_vector_issue_event_o(interrupt_vector_issue_event),
        .interrupt_vector_fetch_event_o(interrupt_vector_fetch_event),
        .interrupt_level_o(interrupt_level),
        .interrupt_vector_o(interrupt_vector),
        .interrupt_pending_o(interrupt_pending),
        .interrupt_vectoring_o(interrupt_vectoring),
        .interrupt_configuration_invalid_o(
            interrupt_configuration_invalid
        ),
        .interrupt_reset_baseline_provisional_o(
            interrupt_reset_baseline_provisional
        ),
        .interrupt_adjacent_control_conflict_o(
            interrupt_adjacent_control_conflict
        ),
        .instruction_valid_o(instruction_valid),
        .transaction_pending_o(transaction_pending),
        .unsupported_instruction_o(unsupported_instruction),
        .reserved_subencoding_o(reserved_subencoding),
        .phase_conflict_o(phase_conflict),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .provisional_source_extension_o(provisional_source_extension),
        .pc_o(pc),
        .opcode_o(opcode),
        .fetched_dm_request_candidate_o(),
        .fetched_dm_request_presented_o(),
        .fetched_dm_request_address_o(),
        .fetched_dm_request_address_valid_o(),
        .fetched_dm_request_write_o(),
        .fetched_dm_request_write_data_o(),
        .fetched_dm_request_write_data_valid_o(),
        .probe_data_o(probe_data),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .px_o(px),
        .sstat_o(sstat),
        .alternate_bank_o(alternate_bank),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .pm_request_accepted_o(pm_request_accepted),
        .pm_completion_event_o(pm_completion_event),
        .pm_read_sample_event_o(pm_read_sample_event),
        .pm_bus_active_o(pm_bus_active),
        .pm_address_output_enable_o(pm_address_oe),
        .pm_control_output_enable_o(pm_control_oe),
        .pm_data_output_enable_o(pm_data_oe),
        .pma_o(pma),
        .pma_valid_o(pma_valid),
        .pmda_o(pmda),
        .pmda_valid_o(pmda_valid),
        .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n),
        .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );
    /* verilator lint_on PINCONNECTEMPTY */

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_pre = '0;
        expected_post = '0;
        vector_file = $fopen("build/linear_core_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open linear-core vectors");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_pre,
                expected_post
            );
            if (scan_count == 3) begin
                #2;
                if ({
                    issue_boundary, setup_accepted, instruction_issue,
                    retire_event, trap_event,
                    interrupt_recognition_event, interrupt_entry_event,
                    interrupt_vector_issue_event,
                    interrupt_vector_fetch_event,
                    interrupt_configuration_invalid,
                    interrupt_reset_baseline_provisional,
                    interrupt_adjacent_control_conflict,
                    instruction_valid, transaction_pending,
                    unsupported_instruction, reserved_subencoding,
                    phase_conflict, integration_conflict, internal_conflict,
                    provisional_source_extension,
                    pm_request_accepted, pm_completion_event,
                    pm_read_sample_event, pm_bus_active,
                    pm_address_oe, pm_control_oe, pm_data_oe,
                    pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n,
                    pmd_write_data_valid
                } !== {
                    exp_issue_boundary, exp_setup_accepted,
                    exp_instruction_issue, exp_retire_event,
                    exp_trap_event,
                    exp_interrupt_recognition_event,
                    exp_interrupt_entry_event,
                    exp_interrupt_vector_issue_event,
                    exp_interrupt_vector_fetch_event,
                    exp_interrupt_configuration_invalid,
                    exp_interrupt_reset_baseline_provisional,
                    exp_interrupt_adjacent_control_conflict,
                    exp_pre_instruction_valid, exp_pre_pending,
                    exp_unsupported_instruction, exp_reserved_subencoding,
                    exp_phase_conflict, exp_integration_conflict,
                    exp_internal_conflict, exp_provisional_source_extension,
                    exp_pm_request_accepted, exp_pm_completion_event,
                    exp_pm_read_sample_event, exp_pre_pm_active,
                    exp_pm_address_oe, exp_pm_control_oe, exp_pm_data_oe,
                    exp_pma_valid, exp_pmda, exp_pmda_valid,
                    exp_pms_n, exp_pmrd_n, exp_pmwr_n,
                    exp_pmd_write_data_valid
                }) begin
                    $fatal(
                        1,
                        "linear-core pre mismatch vector=%0d actual=%h expected=%h stimulus=%h",
                        vector_count,
                        {
                            issue_boundary, setup_accepted,
                            instruction_issue, retire_event, trap_event,
                            interrupt_recognition_event,
                            interrupt_entry_event,
                            interrupt_vector_issue_event,
                            interrupt_vector_fetch_event,
                            interrupt_configuration_invalid,
                            interrupt_reset_baseline_provisional,
                            interrupt_adjacent_control_conflict,
                            instruction_valid, transaction_pending,
                            unsupported_instruction, reserved_subencoding,
                            phase_conflict, integration_conflict,
                            internal_conflict,
                            provisional_source_extension,
                            pm_request_accepted,
                            pm_completion_event, pm_read_sample_event,
                            pm_bus_active, pm_address_oe, pm_control_oe,
                            pm_data_oe, pma_valid, pmda, pmda_valid,
                            pms_n, pmrd_n, pmwr_n,
                            pmd_write_data_valid
                        },
                        {
                            exp_issue_boundary, exp_setup_accepted,
                            exp_instruction_issue, exp_retire_event,
                            exp_trap_event,
                            exp_interrupt_recognition_event,
                            exp_interrupt_entry_event,
                            exp_interrupt_vector_issue_event,
                            exp_interrupt_vector_fetch_event,
                            exp_interrupt_configuration_invalid,
                            exp_interrupt_reset_baseline_provisional,
                            exp_interrupt_adjacent_control_conflict,
                            exp_pre_instruction_valid, exp_pre_pending,
                            exp_unsupported_instruction,
                            exp_reserved_subencoding, exp_phase_conflict,
                            exp_integration_conflict,
                            exp_internal_conflict,
                            exp_provisional_source_extension,
                            exp_pm_request_accepted,
                            exp_pm_completion_event,
                            exp_pm_read_sample_event, exp_pre_pm_active,
                            exp_pm_address_oe, exp_pm_control_oe,
                            exp_pm_data_oe, exp_pma_valid, exp_pmda,
                            exp_pmda_valid, exp_pms_n, exp_pmrd_n,
                            exp_pmwr_n, exp_pmd_write_data_valid
                        },
                        stimulus
                    );
                end
                if (!reset && pc !== exp_pre_pc)
                    $fatal(1, "pre PC mismatch vector=%0d", vector_count);
                if (exp_pre_instruction_valid && opcode !== exp_pre_opcode)
                    $fatal(1, "opcode mismatch vector=%0d", vector_count);
                if (exp_pma_valid && pma !== exp_pma)
                    $fatal(1, "PMA mismatch vector=%0d", vector_count);
                if (interrupt_level !== exp_interrupt_level) begin
                    $display(
                        "IRQ level actual=%h expected=%h vector=%0d stimulus=%h",
                        interrupt_level, exp_interrupt_level,
                        vector_count, stimulus
                    );
                    $fatal(1, "IRQ level mismatch vector=%0d", vector_count);
                end
                if (interrupt_vector !== exp_interrupt_vector)
                    $fatal(1, "IRQ vector mismatch vector=%0d", vector_count);
                if (interrupt_pending !== exp_pre_interrupt_pending)
                    $fatal(1, "IRQ pending mismatch vector=%0d", vector_count);
                if (interrupt_vectoring !== exp_pre_interrupt_vectoring)
                    $fatal(1, "IRQ vectoring mismatch vector=%0d", vector_count);
                if (
                    exp_pmd_write_data_valid
                    && pmd_write_data !== exp_pmd_write_data
                ) $fatal(1, "PMD write mismatch vector=%0d", vector_count);

                #2 clk = 1'b1;
                #1;
                if ({
                    instruction_valid, transaction_pending, pc,
                    mstat, imask, cntr_valid, sstat, alternate_bank,
                    count_stack_depth, count_stack_overflow, pm_bus_active,
                    interrupt_vectoring, interrupt_pending
                } !== {
                    exp_post_instruction_valid, exp_post_pending,
                    exp_post_pc, exp_mstat, exp_imask, exp_cntr_valid,
                    exp_sstat, exp_alternate_bank, exp_count_stack_depth,
                    exp_count_stack_overflow, exp_post_pm_active,
                    exp_post_interrupt_vectoring,
                    exp_post_interrupt_pending
                }) begin
                    $fatal(1, "linear-core post mismatch vector=%0d", vector_count);
                end
                if (exp_post_instruction_valid && opcode !== exp_post_opcode)
                    $fatal(1, "post opcode mismatch vector=%0d", vector_count);
                if (exp_probe_valid && probe_data !== exp_probe_data)
                    $fatal(1, "probe mismatch vector=%0d", vector_count);
                if (exp_astat_valid && astat !== exp_astat)
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
                if (exp_icntl_valid && icntl !== exp_icntl)
                    $fatal(1, "ICNTL mismatch vector=%0d", vector_count);
                if (exp_cntr_valid && cntr !== exp_cntr)
                    $fatal(1, "CNTR mismatch vector=%0d", vector_count);
                if (exp_px_valid && px !== exp_px)
                    $fatal(1, "PX mismatch vector=%0d", vector_count);
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50_000) begin
            $fatal(1, "insufficient linear-core vectors: %0d", vector_count);
        end
        $display(
            "PASS bounded NOP/Type 6/Type 7/Type 8/Type 9/Type 10/Type 11/Type 14/Type 15/Type 16/Type 17/Type 18/Type 19/Type 20/Type 21/Type 22/Type 23/Type 24/Type 25/Type 26 plus automatic-loop linear core: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
