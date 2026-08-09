`default_nettype none

// Bounded composition of normal BR/BG control with the linear PM owner.
//
// The bus controller inhibits only future state-8 issue after recognizing BR;
// the already-active PM fetch remains driven through its state-7 completion.
// BG later masks all native PM output enables. The RESET-time asynchronous
// relationship remains confined to the native pin wrapper instantiated here.
module adsp2100_linear_bus_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        br_n_i,
    input  logic [3:0]  irq_n_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,
    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [5:0]  probe_code_i,

    output logic [2:0]  bus_mode_o,
    output logic        state_three_boundary_o,
    output logic        request_recognized_o,
    output logic        grant_assert_event_o,
    output logic        release_recognized_o,
    output logic        grant_release_event_o,
    output logic        resume_event_o,
    output logic        request_withdrawn_o,
    output logic        release_cancelled_o,
    output logic        instruction_issue_inhibit_o,
    output logic        normal_bus_relinquished_o,
    output logic        normal_bg_n_o,
    output logic        reset_br_request_o,
    output logic        bg_n_o,
    output logic        bus_relinquished_o,

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
    logic trap_event_unused;
    logic [27:0] interrupt_unused;

    adsp2100_bus_control bus_control (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .br_n_i(br_n_i),
        .service_inhibit_i(1'b0),
        .mode_o(bus_mode_o),
        .state_three_boundary_o(state_three_boundary_o),
        .request_recognized_o(request_recognized_o),
        .grant_assert_event_o(grant_assert_event_o),
        .release_recognized_o(release_recognized_o),
        .grant_release_event_o(grant_release_event_o),
        .resume_event_o(resume_event_o),
        .request_withdrawn_o(request_withdrawn_o),
        .release_cancelled_o(release_cancelled_o),
        .instruction_issue_inhibit_o(instruction_issue_inhibit_o),
        .bus_relinquished_o(normal_bus_relinquished_o),
        .bg_n_o(normal_bg_n_o),
        .reset_br_request_o(reset_br_request_o)
    );

    adsp2100_reset_bus_grant reset_bus_grant (
        .reset_active_i(reset_i),
        .br_n_i(br_n_i),
        .normal_bg_n_i(normal_bg_n_o),
        .normal_bus_relinquished_i(normal_bus_relinquished_o),
        .bg_n_o(bg_n_o),
        .bus_relinquished_o(bus_relinquished_o)
    );

    /* verilator lint_off PINCONNECTEMPTY */
    adsp2100_linear_core_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .interrupt_sample_advance_i(1'b0),
        .instruction_issue_inhibit_i(instruction_issue_inhibit_o),
        .bus_relinquished_i(bus_relinquished_o),
        .instruction_setup_i(instruction_setup_i),
        .instruction_setup_pc_i(instruction_setup_pc_i),
        .instruction_setup_opcode_i(instruction_setup_opcode_i),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .dmd_read_data_i(16'h0000),
        .dmd_read_data_valid_i(1'b0),
        .irq_n_i(irq_n_i),
        .probe_code_i(probe_code_i),
        .issue_boundary_o(issue_boundary_o),
        .instruction_setup_accepted_o(instruction_setup_accepted_o),
        .instruction_issue_o(instruction_issue_o),
        .retire_event_o(retire_event_o),
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
        .integration_conflict_o(integration_conflict_o),
        .internal_conflict_o(internal_conflict_o),
        .provisional_source_extension_o(provisional_source_extension_o),
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
    /* verilator lint_on PINCONNECTEMPTY */

`ifndef SYNTHESIS
    always_comb begin
        assert (trap_event_unused == trap_event_unused);
        assert (^interrupt_unused == ^interrupt_unused);
        assert (bg_n_o == !bus_relinquished_o);
        if (instruction_issue_inhibit_o) begin
            assert (!instruction_issue_o);
        end
        if (bus_relinquished_o) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
        end
        if (normal_bus_relinquished_o) begin
            assert (!transaction_pending_o);
        end
        if (resume_event_o && instruction_valid_o) begin
            assert (issue_boundary_o);
        end
    end
`endif
endmodule

`default_nettype wire
