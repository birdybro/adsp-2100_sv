`default_nettype none

module adsp2100_linear_dm_wait_control_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic [3:0]  irq_n,
    input logic        instruction_setup,
    input logic [13:0] instruction_setup_pc,
    input logic [23:0] instruction_setup_opcode,
    input logic        dm_request_valid,
    input logic [13:0] dm_request_address,
    input logic        dm_request_address_valid,
    input logic        dm_request_write,
    input logic [15:0] dm_request_write_data,
    input logic        dm_request_write_data_valid,
    input logic        dm_ack,
    input logic [15:0] dmd_read_data,
    input logic        dmd_read_data_valid,
    input logic [23:0] pmd_read_data,
    input logic        pmd_read_data_valid
);
    import adsp2100_pkg::*;

    logic architectural_phase_advance;
    logic interrupt_wait_sample;
    logic dm_companion_accepted;
    logic phase_conflict;
    logic attachment_conflict;
    logic integration_conflict;
    logic instruction_issue;
    logic retire_event;
    logic interrupt_recognition_event;
    logic interrupt_entry_event;
    logic interrupt_vector_issue_event;
    logic pm_request_accepted;
    logic pm_completion_event;
    logic dm_request_accepted;
    logic dm_wait_extension_event;
    logic dm_completion_event;
    logic dm_transaction_active;
    logic dm_waiting;
    logic past_valid;

    adsp2100_linear_dm_wait_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .irq_n_i(irq_n),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(instruction_setup_pc),
        .instruction_setup_opcode_i(instruction_setup_opcode),
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
        .probe_code_i(6'h00),
        .architectural_phase_advance_o(architectural_phase_advance),
        .interrupt_wait_sample_o(interrupt_wait_sample),
        .dm_companion_accepted_o(dm_companion_accepted),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .issue_boundary_o(),
        .instruction_setup_accepted_o(),
        .instruction_issue_o(instruction_issue),
        .retire_event_o(retire_event),
        .trap_event_o(),
        .interrupt_recognition_event_o(interrupt_recognition_event),
        .interrupt_entry_event_o(interrupt_entry_event),
        .interrupt_vector_issue_event_o(interrupt_vector_issue_event),
        .interrupt_vector_fetch_event_o(),
        .interrupt_level_o(),
        .interrupt_vector_o(),
        .interrupt_pending_o(),
        .interrupt_vectoring_o(),
        .interrupt_configuration_invalid_o(),
        .interrupt_reset_baseline_provisional_o(),
        .interrupt_adjacent_control_conflict_o(),
        .instruction_valid_o(),
        .transaction_pending_o(),
        .unsupported_instruction_o(),
        .reserved_subencoding_o(),
        .core_phase_conflict_o(),
        .core_integration_conflict_o(),
        .internal_conflict_o(),
        .provisional_source_extension_o(),
        .pc_o(),
        .opcode_o(),
        .probe_data_o(),
        .astat_o(),
        .mstat_o(),
        .icntl_o(),
        .imask_o(),
        .cntr_o(),
        .cntr_valid_o(),
        .px_o(),
        .sstat_o(),
        .alternate_bank_o(),
        .count_stack_depth_o(),
        .count_stack_overflow_o(),
        .pm_request_accepted_o(pm_request_accepted),
        .pm_completion_event_o(pm_completion_event),
        .pm_read_sample_event_o(),
        .pm_bus_active_o(),
        .pm_address_output_enable_o(),
        .pm_control_output_enable_o(),
        .pm_data_output_enable_o(),
        .pma_o(),
        .pma_valid_o(),
        .pmda_o(),
        .pmda_valid_o(),
        .pms_n_o(),
        .pmrd_n_o(),
        .pmwr_n_o(),
        .pmd_write_data_o(),
        .pmd_write_data_valid_o(),
        .dm_request_accepted_o(dm_request_accepted),
        .dmack_sample_event_o(),
        .dmack_accepted_o(),
        .dm_wait_extension_event_o(dm_wait_extension_event),
        .dm_completion_event_o(dm_completion_event),
        .dm_read_sample_event_o(),
        .dm_transaction_active_o(dm_transaction_active),
        .dm_waiting_o(dm_waiting),
        .dm_response_valid_o(),
        .dm_response_write_o(),
        .dm_response_read_data_o(),
        .dm_response_read_data_valid_o(),
        .dm_address_output_enable_o(),
        .dm_control_output_enable_o(),
        .dm_data_output_enable_o(),
        .dma_o(),
        .dma_valid_o(),
        .dms_n_o(),
        .dmrd_n_o(),
        .dmwr_n_o(),
        .dmd_write_data_o(),
        .dmd_write_data_valid_o()
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (architectural_phase_advance
            == (phase_advance && !dm_waiting));
        assert (interrupt_wait_sample == (
            phase_advance && dm_waiting && phase == PHASE_STATE_7
        ));
        assert (dm_companion_accepted == dm_request_accepted);
        if (dm_request_accepted) begin
            assert (pm_request_accepted && instruction_issue);
        end
        if (dm_waiting) begin
            assert (!architectural_phase_advance);
            assert (!retire_event && !pm_completion_event);
            assert (!interrupt_recognition_event);
            assert (!interrupt_entry_event);
            assert (!interrupt_vector_issue_event);
        end
        if (dm_completion_event) begin
            assert (pm_completion_event && retire_event);
        end
        if (!dm_request_valid) begin
            assert (!phase_conflict && !dm_companion_accepted);
        end
        cover (dm_wait_extension_event);
        cover (interrupt_wait_sample);
        cover (dm_completion_event && pm_completion_event);
        cover (integration_conflict || attachment_conflict);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end
        past_valid <= 1'b1;
        cover (
            past_valid && $past(dm_waiting)
            && !dm_waiting && dm_transaction_active
        );
    end
endmodule

`default_nettype wire
