`default_nettype none

// Retained bounded ordinary-fetch client attached to the single shared PM
// owner and original normal-operation BR/BG sequencing.
//
// Type 5 and Type 13 remain raw descriptors.  A simultaneous request is
// rejected without invented priority; the ordinary-fetch client keeps the
// current instruction and presents PC+1 again at a later enabled state 8.
module adsp2100_linear_owner_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        br_n_i,
    input  logic [3:0]  irq_n_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,

    input  logic        type5_valid_i,
    input  logic [13:0] type5_address_i,
    input  logic        type5_address_valid_i,
    input  logic        type5_data_access_i,
    input  logic        type5_write_i,
    input  logic [23:0] type5_write_data_i,
    input  logic        type5_write_data_valid_i,
    input  logic        type13_valid_i,
    input  logic [13:0] type13_address_i,
    input  logic        type13_address_valid_i,
    input  logic        type13_data_access_i,
    input  logic        type13_write_i,
    input  logic [23:0] type13_write_data_i,
    input  logic        type13_write_data_valid_i,

    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [5:0]  probe_code_i,

    output logic        issue_boundary_o,
    output logic        instruction_setup_accepted_o,
    output logic        fetch_request_presented_o,
    output logic        fetch_request_accepted_o,
    output logic        fetch_retry_pending_o,
    output logic        instruction_issue_o,
    output logic        retire_event_o,
    output logic        instruction_valid_o,
    output logic        transaction_pending_o,
    output logic        unsupported_instruction_o,
    output logic        reserved_subencoding_o,
    output logic        phase_conflict_o,
    output logic        attachment_conflict_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        provisional_source_extension_o,
    output logic [13:0] pc_o,
    output logic [23:0] opcode_o,

    output logic [15:0] probe_data_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [4:0]  icntl_o,
    output logic [3:0]  imask_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic [7:0]  px_o,
    output logic [7:0]  sstat_o,
    output logic        alternate_bank_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,

    output logic [2:0]  bus_mode_o,
    output logic        bus_request_recognized_o,
    output logic        grant_assert_event_o,
    output logic        release_recognized_o,
    output logic        grant_release_event_o,
    output logic        resume_event_o,
    output logic        issue_inhibit_o,
    output logic        bg_n_o,
    output logic        bus_relinquished_o,
    output logic        request_blocked_o,
    output logic        request_conflict_o,
    output logic        request_out_of_phase_o,
    output logic [2:0]  request_accepted_o,
    output logic [2:0]  completion_event_o,
    output logic [1:0]  owner_o,
    output logic        pm_bus_active_o,

    output logic        pm_address_output_enable_o,
    output logic        pm_control_output_enable_o,
    output logic        pm_data_output_enable_o,
    output logic [13:0] pma_o,
    output logic        pma_valid_o,
    output logic        pmda_o,
    output logic        pmda_valid_o,
    output logic        pms_n_o,
    output logic        pmrd_n_o,
    output logic        pmwr_n_o,
    output logic [23:0] pmd_write_data_o,
    output logic        pmd_write_data_valid_o
);
    logic [13:0] fetch_address;
    logic client_integration_conflict;
    logic state_three_boundary_unused;
    logic request_withdrawn_unused;
    logic release_cancelled_unused;
    logic normal_bus_relinquished_unused;
    logic normal_bg_n_unused;
    logic reset_br_request_unused;
    logic request_ready_unused;
    logic [2:0] read_sample_event_unused;
    logic response_valid_unused;
    logic response_write_unused;
    logic [23:0] response_read_data_unused;
    logic response_read_data_valid_unused;
    logic trap_event_unused;
    logic [27:0] interrupt_unused;
    logic unused_observation;

    assign fetch_request_accepted_o = request_accepted_o[0];
    assign fetch_retry_pending_o = (
        fetch_request_presented_o && !fetch_request_accepted_o
    );
    assign attachment_conflict_o = (
        (fetch_request_accepted_o && !fetch_request_presented_o)
        || (completion_event_o[0] && !retire_event_o)
    );
    assign integration_conflict_o = (
        client_integration_conflict || attachment_conflict_o
        || request_conflict_o || request_out_of_phase_o
    );

    /* verilator lint_off PINCONNECTEMPTY */
    adsp2100_linear_fetch_client client (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .interrupt_sample_advance_i(1'b0),
        .instruction_issue_inhibit_i(issue_inhibit_o),
        .bus_relinquished_i(bus_relinquished_o),
        .instruction_setup_i(instruction_setup_i),
        .instruction_setup_pc_i(instruction_setup_pc_i),
        .instruction_setup_opcode_i(instruction_setup_opcode_i),
        .pm_request_accepted_i(fetch_request_accepted_o),
        .pm_completion_event_i(completion_event_o[0]),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .dmd_read_data_i(16'h0000),
        .dmd_read_data_valid_i(1'b0),
        .irq_n_i(irq_n_i),
        .probe_code_i(probe_code_i),
        .type17_source_data_valid_i(1'b1),
        .state_astat_valid_mask_i(8'hff),
        .state_mstat_valid_mask_i(4'hf),
        .state_imask_valid_i(1'b1),
        .pm_instruction_active_i(1'b0),
        .pm_instruction_complete_i(1'b0),
        .pm_instruction_next_opcode_i(24'h000000),
        .pm_instruction_next_opcode_valid_i(1'b0),
        .pm_state_operand_read_i(1'b0),
        .pm_state_memory_read_address_i(4'h0),
        .pm_state_dreg_read_address_1_i(4'h0),
        .pm_state_dreg_read_address_2_i(4'h0),
        .pm_state_dag_i_address_i(3'h0),
        .pm_state_dag_m_address_i(3'h0),
        .pm_state_move_write_i(1'b0),
        .pm_state_move_code_i(6'h00),
        .pm_state_move_data_i(16'h0000),
        .pm_state_dreg_write_i(1'b0),
        .pm_state_dreg_write_address_i(4'h0),
        .pm_state_dreg_write_data_i(16'h0000),
        .pm_state_alu_write_i(1'b0),
        .pm_state_alu_destination_feedback_i(1'b0),
        .pm_state_alu_result_i(16'h0000),
        .pm_state_mac_write_i(1'b0),
        .pm_state_mac_destination_feedback_i(1'b0),
        .pm_state_mac_result_i(40'h0000000000),
        .pm_state_sr_write_i(1'b0),
        .pm_state_sr_result_i(32'h00000000),
        .pm_state_se_write_i(1'b0),
        .pm_state_se_result_i(8'h00),
        .pm_state_sb_write_i(1'b0),
        .pm_state_sb_result_i(5'h00),
        .pm_state_dag_i_write_i(1'b0),
        .pm_state_dag_i_write_address_i(3'h0),
        .pm_state_dag_i_write_data_i(14'h0000),
        .pm_state_dag_i_write_valid_i(1'b0),
        .pm_state_alu_status_write_i(1'b0),
        .pm_state_alu_az_i(1'b0),
        .pm_state_alu_an_i(1'b0),
        .pm_state_alu_av_i(1'b0),
        .pm_state_alu_ac_i(1'b0),
        .pm_state_alu_as_write_i(1'b0),
        .pm_state_alu_as_i(1'b0),
        .pm_state_mac_status_write_i(1'b0),
        .pm_state_mac_mv_i(1'b0),
        .pm_state_shifter_status_write_i(1'b0),
        .pm_state_shifter_ss_i(1'b0),
        .status_restore_event_o(),
        .status_restore_astat_valid_mask_o(),
        .status_restore_mstat_valid_mask_o(),
        .status_restore_imask_valid_o(),
        .issue_boundary_o(issue_boundary_o),
        .instruction_setup_accepted_o(instruction_setup_accepted_o),
        .fetch_request_presented_o(fetch_request_presented_o),
        .fetch_address_o(fetch_address),
        .instruction_issue_o(instruction_issue_o),
        .retire_event_o(retire_event_o),
        .pm_instruction_sequential_allowed_o(),
        .pm_instruction_flow_blocked_o(),
        .trap_event_o(trap_event_unused),
        .interrupt_recognition_event_o(interrupt_unused[0]),
        .interrupt_entry_event_o(interrupt_unused[1]),
        .interrupt_vector_issue_event_o(interrupt_unused[2]),
        .interrupt_vector_fetch_event_o(interrupt_unused[3]),
        .interrupt_level_o(interrupt_unused[5:4]),
        .interrupt_vector_o(interrupt_unused[19:6]),
        .interrupt_pending_o(interrupt_unused[23:20]),
        .interrupt_vectoring_o(interrupt_unused[24]),
        .interrupt_configuration_invalid_o(interrupt_unused[25]),
        .interrupt_reset_baseline_provisional_o(interrupt_unused[26]),
        .interrupt_adjacent_control_conflict_o(interrupt_unused[27]),
        .instruction_valid_o(instruction_valid_o),
        .transaction_pending_o(transaction_pending_o),
        .unsupported_instruction_o(unsupported_instruction_o),
        .reserved_subencoding_o(reserved_subencoding_o),
        .phase_conflict_o(phase_conflict_o),
        .integration_conflict_o(client_integration_conflict),
        .internal_conflict_o(internal_conflict_o),
        .provisional_source_extension_o(
            provisional_source_extension_o
        ),
        .pc_o(pc_o),
        .opcode_o(opcode_o),
        .fetched_dm_request_candidate_o(),
        .fetched_dm_request_presented_o(),
        .fetched_dm_request_address_o(),
        .fetched_dm_request_address_valid_o(),
        .fetched_dm_request_write_o(),
        .fetched_dm_request_write_data_o(),
        .fetched_dm_request_write_data_valid_o(),
        .probe_data_o(probe_data_o),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .cntr_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .px_o(px_o),
        .sstat_o(sstat_o),
        .alternate_bank_o(alternate_bank_o),
        .count_stack_depth_o(count_stack_depth_o),
        .count_stack_overflow_o(count_stack_overflow_o),
        .pm_state_memory_read_data_o(),
        .pm_state_dreg_read_data_1_o(),
        .pm_state_dreg_read_data_2_o(),
        .pm_state_dag_i_data_o(), .pm_state_dag_i_valid_o(),
        .pm_state_dag_m_data_o(), .pm_state_dag_m_valid_o(),
        .pm_state_dag_l_data_o(), .pm_state_dag_l_valid_o(),
        .pm_state_af_o(), .pm_state_mf_o(), .pm_state_mr_o(),
        .pm_state_se_o(), .pm_state_sb_o(), .pm_state_sr_o(),
        .pm_state_action_conflict_o()
    );
    /* verilator lint_on PINCONNECTEMPTY */

    adsp2100_program_owner_bus_control owner_control (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .pm_phase_advance_i(phase_advance_i), .br_n_i(br_n_i),
        .service_inhibit_i(1'b0),
        .fetch_valid_i(fetch_request_presented_o),
        .fetch_address_i(fetch_address),
        .fetch_address_valid_i(1'b1),
        .type5_valid_i(type5_valid_i),
        .type5_address_i(type5_address_i),
        .type5_address_valid_i(type5_address_valid_i),
        .type5_data_access_i(type5_data_access_i),
        .type5_write_i(type5_write_i),
        .type5_write_data_i(type5_write_data_i),
        .type5_write_data_valid_i(type5_write_data_valid_i),
        .type13_valid_i(type13_valid_i),
        .type13_address_i(type13_address_i),
        .type13_address_valid_i(type13_address_valid_i),
        .type13_data_access_i(type13_data_access_i),
        .type13_write_i(type13_write_i),
        .type13_write_data_i(type13_write_data_i),
        .type13_write_data_valid_i(type13_write_data_valid_i),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .bus_mode_o(bus_mode_o),
        .state_three_boundary_o(state_three_boundary_unused),
        .bus_request_recognized_o(bus_request_recognized_o),
        .grant_assert_event_o(grant_assert_event_o),
        .release_recognized_o(release_recognized_o),
        .grant_release_event_o(grant_release_event_o),
        .resume_event_o(resume_event_o),
        .request_withdrawn_o(request_withdrawn_unused),
        .release_cancelled_o(release_cancelled_unused),
        .issue_inhibit_o(issue_inhibit_o),
        .normal_bus_relinquished_o(normal_bus_relinquished_unused),
        .normal_bg_n_o(normal_bg_n_unused),
        .reset_br_request_o(reset_br_request_unused),
        .bg_n_o(bg_n_o),
        .bus_relinquished_o(bus_relinquished_o),
        .request_ready_o(request_ready_unused),
        .request_blocked_o(request_blocked_o),
        .request_conflict_o(request_conflict_o),
        .request_out_of_phase_o(request_out_of_phase_o),
        .request_accepted_o(request_accepted_o),
        .completion_event_o(completion_event_o),
        .read_sample_event_o(read_sample_event_unused),
        .owner_o(owner_o),
        .transaction_active_o(pm_bus_active_o),
        .response_valid_o(response_valid_unused),
        .response_write_o(response_write_unused),
        .response_read_data_o(response_read_data_unused),
        .response_read_data_valid_o(response_read_data_valid_unused),
        .pm_address_output_enable_o(pm_address_output_enable_o),
        .pm_control_output_enable_o(pm_control_output_enable_o),
        .pm_data_output_enable_o(pm_data_output_enable_o),
        .pma_o(pma_o), .pma_valid_o(pma_valid_o),
        .pmda_o(pmda_o), .pmda_valid_o(pmda_valid_o),
        .pms_n_o(pms_n_o), .pmrd_n_o(pmrd_n_o), .pmwr_n_o(pmwr_n_o),
        .pmd_write_data_o(pmd_write_data_o),
        .pmd_write_data_valid_o(pmd_write_data_valid_o)
    );

    assign unused_observation = ^{
        state_three_boundary_unused, request_withdrawn_unused,
        release_cancelled_unused, normal_bus_relinquished_unused,
        normal_bg_n_unused, reset_br_request_unused, request_ready_unused,
        read_sample_event_unused, response_valid_unused,
        response_write_unused, response_read_data_unused,
        response_read_data_valid_unused, trap_event_unused, interrupt_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (fetch_request_accepted_o == request_accepted_o[0]);
        if (fetch_retry_pending_o) begin
            assert (instruction_valid_o && !transaction_pending_o);
        end
        if (bus_relinquished_o) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
        end
    end

    always_ff @(posedge clk_i) begin
        if (!reset_i && completion_event_o[0]) begin
            assert (retire_event_o);
        end
    end
`endif
endmodule

`default_nettype wire
