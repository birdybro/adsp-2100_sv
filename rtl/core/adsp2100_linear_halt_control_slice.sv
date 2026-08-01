`default_nettype none

// Bounded composition of ordinary linear PM fetch ownership and HALT control.
module adsp2100_linear_halt_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        halt_n_i,
    input  logic        dmack_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,
    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [5:0]  probe_code_i,

    output logic [1:0]  halt_mode_o,
    output logic        state_three_boundary_o,
    output logic        halt_recognized_o,
    output logic        halt_stop_event_o,
    output logic        resume_event_o,
    output logic        release_blocked_o,
    output logic        instruction_issue_inhibit_o,
    output logic        phase_hold_o,
    output logic        effective_phase_advance_o,
    output logic        halted_o,
    output logic        halt_phase_conflict_o,

    output logic        issue_boundary_o,
    output logic        instruction_setup_accepted_o,
    output logic        instruction_issue_o,
    output logic        retire_event_o,
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
    logic ordinary_force_fetch_issue;

    adsp2100_halt_control halt_control (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .halt_n_i(halt_n_i),
        .dmack_i(dmack_i),
        .pm_data_cycle_i(1'b0),
        .mode_o(halt_mode_o),
        .state_three_boundary_o(state_three_boundary_o),
        .halt_recognized_o(halt_recognized_o),
        .halt_stop_event_o(halt_stop_event_o),
        .force_fetch_issue_o(ordinary_force_fetch_issue),
        .resume_event_o(resume_event_o),
        .release_blocked_o(release_blocked_o),
        .instruction_issue_inhibit_o(instruction_issue_inhibit_o),
        .phase_hold_o(phase_hold_o),
        .effective_phase_advance_o(effective_phase_advance_o),
        .halted_o(halted_o),
        .phase_conflict_o(halt_phase_conflict_o)
    );

    adsp2100_linear_core_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(effective_phase_advance_o),
        .instruction_issue_inhibit_i(instruction_issue_inhibit_o),
        .bus_relinquished_i(1'b0),
        .instruction_setup_i(instruction_setup_i),
        .instruction_setup_pc_i(instruction_setup_pc_i),
        .instruction_setup_opcode_i(instruction_setup_opcode_i),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .probe_code_i(probe_code_i),
        .issue_boundary_o(issue_boundary_o),
        .instruction_setup_accepted_o(instruction_setup_accepted_o),
        .instruction_issue_o(instruction_issue_o),
        .retire_event_o(retire_event_o),
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
        .pm_request_accepted_o(pm_request_accepted_o),
        .pm_completion_event_o(pm_completion_event_o),
        .pm_read_sample_event_o(pm_read_sample_event_o),
        .pm_bus_active_o(pm_bus_active_o),
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
        .pmd_write_data_valid_o(pmd_write_data_valid_o)
    );

`ifndef SYNTHESIS
    always_comb begin
        // This wrapper owns ordinary instruction fetches only. The PM-data
        // discriminator is tied low, so the forced-fetch state is unreachable.
        assert (!ordinary_force_fetch_issue);
        if (instruction_issue_inhibit_o) begin
            assert (!instruction_issue_o);
        end
        if (phase_hold_o) begin
            assert (!effective_phase_advance_o);
            assert (!instruction_issue_o);
            assert (!retire_event_o);
        end
        if (halt_stop_event_o && transaction_pending_o) begin
            assert (retire_event_o);
            assert (pm_completion_event_o);
        end
        if (resume_event_o && instruction_valid_o) begin
            assert (issue_boundary_o);
        end
        if (halted_o && !halt_phase_conflict_o) begin
            assert (phase_i == 3'd7);
        end
    end
`endif
endmodule

`default_nettype wire
