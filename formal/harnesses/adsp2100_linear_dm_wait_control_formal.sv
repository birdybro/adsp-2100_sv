`default_nettype none

module adsp2100_linear_dm_wait_control_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        br_n,
    input logic        halt_n,
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
    logic effective_phase_advance;
    logic interrupt_wait_sample;
    logic dm_companion_accepted;
    logic phase_conflict;
    logic attachment_conflict;
    logic integration_conflict;
    logic [1:0] halt_mode;
    logic halt_recognized;
    logic halt_stop_event;
    logic halt_resume_event;
    logic halt_release_blocked;
    logic halt_instruction_issue_inhibit;
    logic halt_phase_hold;
    logic halted;
    logic halt_br_conflict;
    logic [2:0] bus_mode;
    logic request_recognized;
    logic grant_assert_event;
    logic request_withdrawn;
    logic instruction_issue_inhibit;
    logic normal_bus_relinquished;
    logic bus_relinquished;
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
    logic dm_response_valid;
    logic pm_address_output_enable;
    logic pm_control_output_enable;
    logic pm_data_output_enable;
    logic dm_address_output_enable;
    logic dm_control_output_enable;
    logic dm_data_output_enable;
    logic [23:0] opcode;
    logic past_valid;

    adsp2100_linear_dm_wait_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .br_n_i(br_n),
        .halt_n_i(halt_n),
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
        .effective_phase_advance_o(effective_phase_advance),
        .interrupt_wait_sample_o(interrupt_wait_sample),
        .dm_companion_accepted_o(dm_companion_accepted),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .halt_mode_o(halt_mode),
        .halt_state_three_boundary_o(),
        .halt_recognized_o(halt_recognized),
        .halt_stop_event_o(halt_stop_event),
        .halt_resume_event_o(halt_resume_event),
        .halt_release_blocked_o(halt_release_blocked),
        .halt_instruction_issue_inhibit_o(
            halt_instruction_issue_inhibit
        ),
        .halt_phase_hold_o(halt_phase_hold),
        .halted_o(halted),
        .halt_br_conflict_o(halt_br_conflict),
        .halt_phase_conflict_o(),
        .bus_mode_o(bus_mode),
        .state_three_boundary_o(),
        .request_recognized_o(request_recognized),
        .grant_assert_event_o(grant_assert_event),
        .release_recognized_o(),
        .grant_release_event_o(),
        .resume_event_o(),
        .request_withdrawn_o(request_withdrawn),
        .release_cancelled_o(),
        .instruction_issue_inhibit_o(instruction_issue_inhibit),
        .normal_bus_relinquished_o(normal_bus_relinquished),
        .normal_bg_n_o(),
        .reset_br_request_o(),
        .bg_n_o(),
        .bus_relinquished_o(bus_relinquished),
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
        .opcode_o(opcode),
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
        .pm_address_output_enable_o(pm_address_output_enable),
        .pm_control_output_enable_o(pm_control_output_enable),
        .pm_data_output_enable_o(pm_data_output_enable),
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
        .dm_response_valid_o(dm_response_valid),
        .dm_response_write_o(),
        .dm_response_read_data_o(),
        .dm_response_read_data_valid_o(),
        .dm_address_output_enable_o(dm_address_output_enable),
        .dm_control_output_enable_o(dm_control_output_enable),
        .dm_data_output_enable_o(dm_data_output_enable),
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
            == (effective_phase_advance && !dm_waiting));
        assert (effective_phase_advance
            == (phase_advance && !halt_phase_hold));
        assert (interrupt_wait_sample == (
            effective_phase_advance
            && dm_waiting && phase == PHASE_STATE_7
        ));
        assert (!dm_companion_accepted || dm_request_accepted);
        assert (!dm_request_valid || !dm_companion_accepted
            || pm_request_accepted);
        if (dm_request_accepted) begin
            assert (pm_request_accepted && instruction_issue);
        end
        if (dm_waiting) begin
            assert (!architectural_phase_advance);
            assert (!retire_event && !pm_completion_event);
            assert (!interrupt_recognition_event);
            assert (!interrupt_entry_event);
            assert (!interrupt_vector_issue_event);
            assert (!halt_stop_event);
        end
        if (dm_completion_event) begin
            assert (pm_completion_event && retire_event);
        end
        if (dm_transaction_active && !dm_response_valid) begin
            assert (!grant_assert_event);
            assert (!request_withdrawn);
        end
        if (instruction_issue_inhibit) begin
            assert (!instruction_issue);
        end
        if (halt_instruction_issue_inhibit) begin
            assert (!instruction_issue);
        end
        if (halt_stop_event) begin
            assert (phase == PHASE_STATE_7);
            assert (pm_completion_event && retire_event);
            if (
                opcode[23:21] == 3'b101
                || opcode[23:21] == 3'b100
                || opcode[23:21] == 3'b011
                || (opcode & 24'hfe0000) == 24'h120000
            ) begin
                assert (dm_completion_event);
            end
        end
        if (halted && !halt_resume_event) begin
            assert (halt_mode == 2'd2);
            assert (halt_phase_hold);
            assert (!effective_phase_advance);
            assert (!architectural_phase_advance);
            assert (!instruction_issue && !retire_event);
        end
        if (halt_resume_event) begin
            assert (phase == PHASE_STATE_8);
            assert (halt_n && dm_ack && effective_phase_advance);
        end
        if (halt_release_blocked) begin
            assert (halted && halt_n && !dm_ack);
            assert (halt_phase_hold);
        end
        if (
            halt_br_conflict && halt_mode == 2'd0
            && bus_mode == 3'd0
        ) begin
            assert (!halt_recognized && !request_recognized);
        end
        if (halt_br_conflict && halt_mode != 2'd0) begin
            assert (!request_recognized);
            if (!halt_n) begin
                assert (!halt_resume_event);
            end
        end
        if (halt_br_conflict && bus_mode != 3'd0) begin
            assert (!halt_recognized);
            if (!br_n) begin
                assert (!request_withdrawn);
            end
        end
        if (bus_relinquished) begin
            assert (!pm_address_output_enable);
            assert (!pm_control_output_enable);
            assert (!pm_data_output_enable);
            assert (!dm_address_output_enable);
            assert (!dm_control_output_enable);
            assert (!dm_data_output_enable);
        end
        if (
            (bus_mode != 3'd0 || request_recognized)
            && (
                interrupt_recognition_event
                || interrupt_entry_event
                || interrupt_vector_issue_event
            )
        ) begin
            assert (integration_conflict);
        end
        assert (!normal_bus_relinquished || bus_relinquished);
        if (!dm_request_valid) begin
            assert (!phase_conflict);
            assert (!dm_companion_accepted);
            if (dm_request_accepted) begin
                assert (
                    opcode[23:21] == 3'b101
                    || opcode[23:21] == 3'b100
                    || opcode[23:21] == 3'b011
                    || (opcode & 24'hfe0000) == 24'h120000
                );
            end
        end
        if (
            retire_event
            && (
                opcode[23:21] == 3'b101
                || opcode[23:21] == 3'b100
                || opcode[23:21] == 3'b011
                || (opcode & 24'hfe0000) == 24'h120000
            )
        ) begin
            assert (dm_completion_event);
        end
        cover (dm_wait_extension_event);
        cover (interrupt_wait_sample);
        cover (dm_completion_event && pm_completion_event);
        cover (integration_conflict || attachment_conflict);
        cover (dm_request_accepted && !dm_request_valid);
        cover (
            dm_request_accepted && !dm_request_valid
            && opcode[20:0] != 21'h000000
        );
        cover (
            dm_request_accepted && !dm_request_valid
            && opcode[23:21] == 3'b100 && !opcode[20]
        );
        cover (
            dm_request_accepted && !dm_request_valid
            && opcode[23:21] == 3'b100 && opcode[20]
        );
        cover (
            dm_request_accepted && !dm_request_valid
            && opcode[23:21] == 3'b011 && !opcode[19]
            && opcode[17:13] != 5'h00
        );
        cover (
            dm_request_accepted && !dm_request_valid
            && opcode[23:21] == 3'b011 && opcode[19]
            && opcode[17:13] != 5'h00
        );
        cover (
            dm_request_accepted && !dm_request_valid
            && opcode[23:21] == 3'b011
            && opcode[17:13] == 5'h00
        );
        cover (
            dm_request_accepted && !dm_request_valid
            && (opcode & 24'hfe0000) == 24'h120000
            && !opcode[15]
        );
        cover (
            dm_request_accepted && !dm_request_valid
            && (opcode & 24'hfe0000) == 24'h120000
            && opcode[15]
        );
        cover (
            dm_request_accepted && !dm_request_valid
            && (opcode & 24'hfe0000) == 24'h120000
            && opcode[14:11] >= 4'hc
        );
        cover (request_recognized && dm_waiting);
        cover (
            dm_request_valid && attachment_conflict
            && !pm_request_accepted && !dm_request_accepted
        );
        cover (grant_assert_event && bus_mode == 3'd1);
        cover (bus_relinquished);
        cover (halt_recognized && dm_transaction_active);
        cover (halt_recognized && dm_waiting);
        cover (halt_stop_event && dm_completion_event);
        cover (halt_release_blocked);
        cover (halt_resume_event);
        cover (halt_br_conflict);
        cover (halt_br_conflict && halt_mode != 2'd0 && !halt_n);
        cover (halt_br_conflict && bus_mode != 3'd0 && !br_n);
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
