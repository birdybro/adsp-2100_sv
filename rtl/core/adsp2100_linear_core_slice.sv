`default_nettype none

// Bounded steady-state instruction owner for ordinary linear flow.
//
// The architectural client is separated from this private native PM
// controller so the same retained fetch state can also be attached to the
// shared Type 5/Type 13 owner.  This compatibility composition intentionally
// preserves the original bounded linear-core interface and behavior.
module adsp2100_linear_core_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        interrupt_sample_advance_i,
    input  logic        instruction_issue_inhibit_i,
    input  logic        bus_relinquished_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,

    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [3:0]  irq_n_i,
    input  logic [5:0]  probe_code_i,

    output logic        issue_boundary_o,
    output logic        instruction_setup_accepted_o,
    output logic        instruction_issue_o,
    output logic        retire_event_o,
    output logic        trap_event_o,
    output logic        interrupt_recognition_event_o,
    output logic        interrupt_entry_event_o,
    output logic        interrupt_vector_issue_event_o,
    output logic        interrupt_vector_fetch_event_o,
    output logic [1:0]  interrupt_level_o,
    output logic [13:0] interrupt_vector_o,
    output logic [3:0]  interrupt_pending_o,
    output logic        interrupt_vectoring_o,
    output logic        interrupt_configuration_invalid_o,
    output logic        interrupt_reset_baseline_provisional_o,
    output logic        interrupt_adjacent_control_conflict_o,
    output logic        instruction_valid_o,
    output logic        transaction_pending_o,
    output logic        unsupported_instruction_o,
    output logic        reserved_subencoding_o,
    output logic        phase_conflict_o,
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

    output logic        pm_request_accepted_o,
    output logic        pm_completion_event_o,
    output logic        pm_read_sample_event_o,
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
    logic fetch_request;
    logic [13:0] fetch_address;
    logic pm_request_ready_unused;
    logic pm_response_valid_unused;
    logic pm_response_write_unused;
    logic [23:0] pm_response_data_unused;
    logic pm_response_data_valid_unused;
    logic [13:0] pm_descriptor_address_unused;
    logic pm_descriptor_address_valid_unused;
    logic pm_descriptor_data_access_unused;
    logic pm_descriptor_write_unused;
    logic [23:0] pm_descriptor_write_data_unused;
    logic pm_descriptor_write_data_valid_unused;
    logic unused_observation;

    /* verilator lint_off PINCONNECTEMPTY */
    adsp2100_linear_fetch_client client (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .interrupt_sample_advance_i(interrupt_sample_advance_i),
        .instruction_issue_inhibit_i(instruction_issue_inhibit_i),
        .bus_relinquished_i(bus_relinquished_i),
        .instruction_setup_i(instruction_setup_i),
        .instruction_setup_pc_i(instruction_setup_pc_i),
        .instruction_setup_opcode_i(instruction_setup_opcode_i),
        .pm_request_accepted_i(pm_request_accepted_o),
        .pm_completion_event_i(pm_completion_event_o),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
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
        .fetch_request_presented_o(fetch_request),
        .fetch_address_o(fetch_address),
        .instruction_issue_o(instruction_issue_o),
        .retire_event_o(retire_event_o),
        .pm_instruction_sequential_allowed_o(),
        .pm_instruction_flow_blocked_o(),
        .trap_event_o(trap_event_o),
        .interrupt_recognition_event_o(
            interrupt_recognition_event_o
        ),
        .interrupt_entry_event_o(interrupt_entry_event_o),
        .interrupt_vector_issue_event_o(
            interrupt_vector_issue_event_o
        ),
        .interrupt_vector_fetch_event_o(
            interrupt_vector_fetch_event_o
        ),
        .interrupt_level_o(interrupt_level_o),
        .interrupt_vector_o(interrupt_vector_o),
        .interrupt_pending_o(interrupt_pending_o),
        .interrupt_vectoring_o(interrupt_vectoring_o),
        .interrupt_configuration_invalid_o(
            interrupt_configuration_invalid_o
        ),
        .interrupt_reset_baseline_provisional_o(
            interrupt_reset_baseline_provisional_o
        ),
        .interrupt_adjacent_control_conflict_o(
            interrupt_adjacent_control_conflict_o
        ),
        .instruction_valid_o(instruction_valid_o),
        .transaction_pending_o(transaction_pending_o),
        .unsupported_instruction_o(unsupported_instruction_o),
        .reserved_subencoding_o(reserved_subencoding_o),
        .phase_conflict_o(phase_conflict_o),
        .integration_conflict_o(integration_conflict_o),
        .internal_conflict_o(internal_conflict_o),
        .provisional_source_extension_o(provisional_source_extension_o),
        .pc_o(pc_o),
        .opcode_o(opcode_o),
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

    adsp2100_program_bus bus (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .request_valid_i(fetch_request),
        .request_address_i(fetch_address),
        .request_address_valid_i(1'b1),
        .request_data_access_i(1'b0),
        .request_write_i(1'b0),
        .request_write_data_i(24'h000000),
        .request_write_data_valid_i(1'b0),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .bus_relinquished_i(bus_relinquished_i),
        .request_ready_o(pm_request_ready_unused),
        .request_accepted_o(pm_request_accepted_o),
        .completion_event_o(pm_completion_event_o),
        .read_sample_event_o(pm_read_sample_event_o),
        .transaction_active_o(pm_bus_active_o),
        .response_valid_o(pm_response_valid_unused),
        .response_write_o(pm_response_write_unused),
        .response_read_data_o(pm_response_data_unused),
        .response_read_data_valid_o(pm_response_data_valid_unused),
        .pm_address_output_enable_o(pm_address_output_enable_o),
        .pm_control_output_enable_o(pm_control_output_enable_o),
        .pm_data_output_enable_o(pm_data_output_enable_o),
        .pma_o(pma_o),
        .pma_valid_o(pma_valid_o),
        .pmda_o(pmda_o),
        .pmda_valid_o(pmda_valid_o),
        .pms_n_o(pms_n_o),
        .pmrd_n_o(pmrd_n_o),
        .pmwr_n_o(pmwr_n_o),
        .pmd_write_data_o(pmd_write_data_o),
        .pmd_write_data_valid_o(pmd_write_data_valid_o),
        .descriptor_address_o(pm_descriptor_address_unused),
        .descriptor_address_valid_o(pm_descriptor_address_valid_unused),
        .descriptor_data_access_o(pm_descriptor_data_access_unused),
        .descriptor_write_o(pm_descriptor_write_unused),
        .descriptor_write_data_o(pm_descriptor_write_data_unused),
        .descriptor_write_data_valid_o(
            pm_descriptor_write_data_valid_unused
        )
    );

    assign unused_observation = ^{
        pm_request_ready_unused, pm_response_valid_unused,
        pm_response_write_unused, pm_response_data_unused,
        pm_response_data_valid_unused, pm_descriptor_address_unused,
        pm_descriptor_address_valid_unused,
        pm_descriptor_data_access_unused, pm_descriptor_write_unused,
        pm_descriptor_write_data_unused,
        pm_descriptor_write_data_valid_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(pmda_valid_o && pmda_o));
        assert (!pm_data_output_enable_o);
        assert (!pmd_write_data_valid_o);
        if (retire_event_o) begin
            assert (pm_read_sample_event_o);
        end
        if (bus_relinquished_i || reset_i) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
        end
    end
`endif
endmodule

`default_nettype wire
