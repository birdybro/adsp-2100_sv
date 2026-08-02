`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_linear_dm_wait_control_slice;
    logic clk;
    logic [130:0] stimulus;
    logic [171:0] expected_pre;
    logic [85:0] expected_post;

    logic reset;
    logic [2:0] phase;
    logic phase_advance;
    logic [3:0] irq_n;
    logic instruction_setup;
    logic [13:0] setup_pc;
    logic [23:0] setup_opcode;
    logic dm_request_valid;
    logic [13:0] dm_request_address;
    logic dm_request_address_valid;
    logic dm_request_write;
    logic [15:0] dm_request_write_data;
    logic dm_request_write_data_valid;
    logic dm_ack;
    logic [15:0] dmd_read_data;
    logic dmd_read_data_valid;
    logic [23:0] pmd_read_data;
    logic pmd_read_data_valid;
    logic [5:0] probe_code;

    logic architectural_phase_advance;
    logic interrupt_wait_sample;
    logic dm_companion_accepted;
    logic phase_conflict;
    logic attachment_conflict;
    logic integration_conflict;
    logic issue_boundary;
    logic setup_accepted;
    logic instruction_issue;
    logic retire_event;
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
    logic instruction_valid;
    logic transaction_pending;
    logic core_phase_conflict;
    logic core_integration_conflict;
    logic internal_conflict;
    logic [13:0] pc;
    logic [23:0] opcode;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic [7:0] sstat;

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

    logic dm_request_accepted;
    logic dmack_sample_event;
    logic dmack_accepted;
    logic dm_wait_extension_event;
    logic dm_completion_event;
    logic dm_read_sample_event;
    logic dm_transaction_active;
    logic dm_waiting;
    logic dm_response_valid;
    logic dm_response_write;
    logic [15:0] dm_response_read_data;
    logic dm_response_read_data_valid;
    logic dm_address_oe;
    logic dm_control_oe;
    logic dm_data_oe;
    logic [13:0] dma;
    logic dma_valid;
    logic dms_n;
    logic dmrd_n;
    logic dmwr_n;
    logic [15:0] dmd_write_data;
    logic dmd_write_data_valid;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, phase, phase_advance, irq_n,
        instruction_setup, setup_pc, setup_opcode,
        dm_request_valid, dm_request_address,
        dm_request_address_valid, dm_request_write,
        dm_request_write_data, dm_request_write_data_valid,
        dm_ack, dmd_read_data, dmd_read_data_valid,
        pmd_read_data, pmd_read_data_valid, probe_code
    } = stimulus;

    adsp2100_linear_dm_wait_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .irq_n_i(irq_n),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(setup_pc),
        .instruction_setup_opcode_i(setup_opcode),
        .dm_request_valid_i(dm_request_valid),
        .dm_request_address_i(dm_request_address),
        .dm_request_address_valid_i(dm_request_address_valid),
        .dm_request_write_i(dm_request_write),
        .dm_request_write_data_i(dm_request_write_data),
        .dm_request_write_data_valid_i(dm_request_write_data_valid),
        .dm_ack_i(dm_ack),
        .dmd_read_data_i(dmd_read_data),
        .dmd_read_data_valid_i(dmd_read_data_valid),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .probe_code_i(probe_code),
        .architectural_phase_advance_o(architectural_phase_advance),
        .interrupt_wait_sample_o(interrupt_wait_sample),
        .dm_companion_accepted_o(dm_companion_accepted),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .issue_boundary_o(issue_boundary),
        .instruction_setup_accepted_o(setup_accepted),
        .instruction_issue_o(instruction_issue),
        .retire_event_o(retire_event),
        .trap_event_o(),
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
        .interrupt_adjacent_control_conflict_o(),
        .instruction_valid_o(instruction_valid),
        .transaction_pending_o(transaction_pending),
        .unsupported_instruction_o(),
        .reserved_subencoding_o(),
        .core_phase_conflict_o(core_phase_conflict),
        .core_integration_conflict_o(core_integration_conflict),
        .internal_conflict_o(internal_conflict),
        .provisional_source_extension_o(),
        .pc_o(pc),
        .opcode_o(opcode),
        .probe_data_o(),
        .astat_o(),
        .mstat_o(),
        .icntl_o(icntl),
        .imask_o(imask),
        .cntr_o(),
        .cntr_valid_o(),
        .px_o(),
        .sstat_o(sstat),
        .alternate_bank_o(),
        .count_stack_depth_o(),
        .count_stack_overflow_o(),
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
        .pmd_write_data_o(),
        .pmd_write_data_valid_o(),
        .dm_request_accepted_o(dm_request_accepted),
        .dmack_sample_event_o(dmack_sample_event),
        .dmack_accepted_o(dmack_accepted),
        .dm_wait_extension_event_o(dm_wait_extension_event),
        .dm_completion_event_o(dm_completion_event),
        .dm_read_sample_event_o(dm_read_sample_event),
        .dm_transaction_active_o(dm_transaction_active),
        .dm_waiting_o(dm_waiting),
        .dm_response_valid_o(dm_response_valid),
        .dm_response_write_o(dm_response_write),
        .dm_response_read_data_o(dm_response_read_data),
        .dm_response_read_data_valid_o(dm_response_read_data_valid),
        .dm_address_output_enable_o(dm_address_oe),
        .dm_control_output_enable_o(dm_control_oe),
        .dm_data_output_enable_o(dm_data_oe),
        .dma_o(dma),
        .dma_valid_o(dma_valid),
        .dms_n_o(dms_n),
        .dmrd_n_o(dmrd_n),
        .dmwr_n_o(dmwr_n),
        .dmd_write_data_o(dmd_write_data),
        .dmd_write_data_valid_o(dmd_write_data_valid)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_pre = '0;
        expected_post = '0;
        vector_count = 0;
        vector_file = $fopen(
            "build/linear_dm_wait_control_vectors.txt", "r"
        );
        if (vector_file == 0) begin
            $fatal(1, "cannot open linear DM-wait vectors");
        end
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_pre,
                expected_post
            );
            if (scan_count == 3) begin
                #1;
                if ({
                    architectural_phase_advance,
                    interrupt_wait_sample,
                    dm_companion_accepted,
                    phase_conflict,
                    attachment_conflict,
                    integration_conflict,
                    issue_boundary,
                    setup_accepted,
                    instruction_issue,
                    retire_event,
                    interrupt_recognition_event,
                    interrupt_entry_event,
                    interrupt_vector_issue_event,
                    interrupt_vector_fetch_event,
                    interrupt_level,
                    interrupt_vector,
                    interrupt_pending,
                    interrupt_vectoring,
                    interrupt_configuration_invalid,
                    interrupt_reset_baseline_provisional,
                    instruction_valid,
                    transaction_pending,
                    core_phase_conflict,
                    core_integration_conflict,
                    internal_conflict,
                    pc,
                    opcode,
                    pm_request_accepted,
                    pm_completion_event,
                    pm_read_sample_event,
                    pm_bus_active,
                    pm_address_oe,
                    pm_control_oe,
                    pm_data_oe,
                    pma_valid,
                    pma,
                    pmda,
                    pmda_valid,
                    pms_n,
                    pmrd_n,
                    pmwr_n,
                    dm_request_accepted,
                    dmack_sample_event,
                    dmack_accepted,
                    dm_wait_extension_event,
                    dm_completion_event,
                    dm_read_sample_event,
                    dm_transaction_active,
                    dm_waiting,
                    dm_response_valid,
                    dm_response_write,
                    dm_response_read_data_valid,
                    dm_response_read_data,
                    dm_address_oe,
                    dm_control_oe,
                    dm_data_oe,
                    dma_valid,
                    dma,
                    dms_n,
                    dmrd_n,
                    dmwr_n,
                    dmd_write_data_valid,
                    dmd_write_data
                } !== expected_pre) begin
                    $display("actual   %043h", {
                        architectural_phase_advance,
                        interrupt_wait_sample,
                        dm_companion_accepted,
                        phase_conflict,
                        attachment_conflict,
                        integration_conflict,
                        issue_boundary,
                        setup_accepted,
                        instruction_issue,
                        retire_event,
                        interrupt_recognition_event,
                        interrupt_entry_event,
                        interrupt_vector_issue_event,
                        interrupt_vector_fetch_event,
                        interrupt_level,
                        interrupt_vector,
                        interrupt_pending,
                        interrupt_vectoring,
                        interrupt_configuration_invalid,
                        interrupt_reset_baseline_provisional,
                        instruction_valid,
                        transaction_pending,
                        core_phase_conflict,
                        core_integration_conflict,
                        internal_conflict,
                        pc,
                        opcode,
                        pm_request_accepted,
                        pm_completion_event,
                        pm_read_sample_event,
                        pm_bus_active,
                        pm_address_oe,
                        pm_control_oe,
                        pm_data_oe,
                        pma_valid,
                        pma,
                        pmda,
                        pmda_valid,
                        pms_n,
                        pmrd_n,
                        pmwr_n,
                        dm_request_accepted,
                        dmack_sample_event,
                        dmack_accepted,
                        dm_wait_extension_event,
                        dm_completion_event,
                        dm_read_sample_event,
                        dm_transaction_active,
                        dm_waiting,
                        dm_response_valid,
                        dm_response_write,
                        dm_response_read_data_valid,
                        dm_response_read_data,
                        dm_address_oe,
                        dm_control_oe,
                        dm_data_oe,
                        dma_valid,
                        dma,
                        dms_n,
                        dmrd_n,
                        dmwr_n,
                        dmd_write_data_valid,
                        dmd_write_data
                    });
                    $display("expected %043h", expected_pre);
                    $fatal(1, "pre-edge mismatch at vector %0d", vector_count);
                end
                #4 clk = 1'b1;
                #1;
                if ({
                    instruction_valid,
                    transaction_pending,
                    pc,
                    opcode,
                    interrupt_pending,
                    interrupt_vectoring,
                    interrupt_level,
                    pm_bus_active,
                    dm_transaction_active,
                    dm_waiting,
                    dm_response_valid,
                    dm_response_write,
                    dm_response_read_data_valid,
                    dm_response_read_data,
                    icntl,
                    imask,
                    sstat
                } !== expected_post) begin
                    $fatal(1, "post-edge mismatch at vector %0d", vector_count);
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display("PASS %0d linear/native-DM clocks", vector_count);
        $finish;
    end
endmodule

`default_nettype wire
