`default_nettype none

// Bounded original Type 13/cache/native-PM owner with HALT attachment.
//
// A HALT recognized during the PM-data phase latches a late recovery request
// in the Type 13 owner. The data action commits once, the following state-8
// boundary accepts one real external fetch, and state 8 is held only after
// that fetch completes. Ordinary fetch ownership outside an active recovery,
// BR/BG, DM waits, TRAP, interrupts, and reset release remain outside.
module adsp2100_shifter_pm_halt_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        halt_n_i,
    input  logic        dmack_i,
    input  logic        bus_relinquished_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [13:0] next_fetch_address_i,
    input  logic        next_fetch_address_valid_i,
    input  logic        force_instruction_fetch_i,
    input  logic        external_fetch_fill_i,
    input  logic [13:0] external_fetch_address_i,
    input  logic        external_fetch_address_valid_i,
    input  logic [23:0] external_fetch_instruction_i,
    input  logic        external_fetch_instruction_valid_i,

    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        dreg_setup_write_i,
    input  logic [3:0]  dreg_setup_code_i,
    input  logic [15:0] dreg_setup_data_i,
    input  logic        sb_setup_write_i,
    input  logic [4:0]  sb_setup_data_i,
    input  logic        dag_setup_write_i,
    input  logic [1:0]  dag_setup_kind_i,
    input  logic [2:0]  dag_setup_address_i,
    input  logic [13:0] dag_setup_data_i,
    input  logic        px_setup_write_i,
    input  logic [7:0]  px_setup_data_i,
    input  logic [3:0]  probe_dreg_code_i,
    input  logic [2:0]  probe_dag_address_i,

    output logic [1:0]  halt_mode_o,
    output logic        halt_recognized_o,
    output logic        halt_stop_event_o,
    output logic        force_fetch_issue_o,
    output logic        resume_event_o,
    output logic        release_blocked_o,
    output logic        instruction_issue_inhibit_o,
    output logic        phase_hold_o,
    output logic        effective_phase_advance_o,
    output logic        halted_o,
    output logic        pm_data_cycle_o,
    output logic        late_force_request_o,
    output logic        execute_suppressed_o,
    output logic        owner_conflict_o,
    output logic        halt_attachment_conflict_o,
    output logic        integration_conflict_o,

    output logic        issue_boundary_o,
    output logic        accepted_o,
    output logic        data_action_complete_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        busy_o,
    output logic        cache_instruction_selected_o,
    output logic        recovery_fetch_o,
    output logic [23:0] next_instruction_o,
    output logic        next_instruction_valid_o,
    output logic        instruction_from_cache_o,
    output logic        instruction_from_external_o,
    output logic        cache_fill_o,
    output logic        cache_fill_from_recovery_o,
    output logic        cache_fill_accepted_o,
    output logic [13:0] cache_region_start_o,
    output logic        cache_region_start_valid_o,
    output logic [4:0]  cache_region_count_o,

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
    output logic        pmd_write_data_valid_o,

    output logic [15:0] probe_dreg_data_o,
    output logic        probe_dreg_valid_o,
    output logic [13:0] probe_i_data_o,
    output logic        probe_i_valid_o,
    output logic [13:0] probe_m_data_o,
    output logic        probe_m_valid_o,
    output logic [13:0] probe_l_data_o,
    output logic        probe_l_valid_o,
    output logic [7:0]  px_o,
    output logic        px_valid_o,
    output logic [31:0] sr_o,
    output logic        sr_valid_o,
    output logic [7:0]  se_o,
    output logic        se_valid_o,
    output logic [4:0]  sb_o,
    output logic        sb_valid_o,
    output logic [7:0]  astat_o,
    output logic [7:0]  astat_valid_mask_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o
);
    logic state_three_boundary_unused;
    logic halt_phase_conflict;
    logic native_phase_conflict;
    logic native_attachment_conflict;
    logic native_integration_conflict;
    logic recovery_required_unused;
    logic event_boundary_unused;
    logic owner_execute;
    logic attached_force;
    logic class_valid_unused;
    logic action_valid_unused;
    logic unsupported_subencoding_unused;

    assign pm_data_cycle_o = transaction_active_o && !recovery_fetch_o;
    assign late_force_request_o = (
        !reset_i
        && (
            halt_mode_o == 2'd3
            || (halt_recognized_o && pm_data_cycle_o)
        )
    );
    assign attached_force = (
        force_instruction_fetch_i || late_force_request_o
    );
    assign owner_execute = (
        execute_i
        && !instruction_issue_inhibit_o
        && !force_fetch_issue_o
    );
    assign execute_suppressed_o = execute_i && !owner_execute;
    assign owner_conflict_o = (
        !reset_i
        && (
            (halt_recognized_o && !pm_bus_active_o)
            || execute_suppressed_o
        )
    );
    assign halt_attachment_conflict_o = (
        force_fetch_issue_o
        && !(pm_request_accepted_o && recovery_fetch_o)
    );
    assign integration_conflict_o = (
        native_integration_conflict
        || halt_phase_conflict
        || owner_conflict_o
        || halt_attachment_conflict_o
    );

    adsp2100_halt_control halt_control (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .halt_n_i(halt_n_i),
        .dmack_i(dmack_i),
        .pm_data_cycle_i(pm_data_cycle_o),
        .mode_o(halt_mode_o),
        .state_three_boundary_o(state_three_boundary_unused),
        .halt_recognized_o(halt_recognized_o),
        .halt_stop_event_o(halt_stop_event_o),
        .force_fetch_issue_o(force_fetch_issue_o),
        .resume_event_o(resume_event_o),
        .release_blocked_o(release_blocked_o),
        .instruction_issue_inhibit_o(instruction_issue_inhibit_o),
        .phase_hold_o(phase_hold_o),
        .effective_phase_advance_o(effective_phase_advance_o),
        .halted_o(halted_o),
        .phase_conflict_o(halt_phase_conflict)
    );

    adsp2100_shifter_pm_native_slice owner (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(effective_phase_advance_o),
        .bus_relinquished_i(bus_relinquished_i),
        .execute_i(owner_execute),
        .opcode_i(opcode_i),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .next_fetch_address_i(next_fetch_address_i),
        .next_fetch_address_valid_i(next_fetch_address_valid_i),
        .force_instruction_fetch_i(attached_force),
        .external_fetch_fill_i(external_fetch_fill_i),
        .external_fetch_address_i(external_fetch_address_i),
        .external_fetch_address_valid_i(external_fetch_address_valid_i),
        .external_fetch_instruction_i(external_fetch_instruction_i),
        .external_fetch_instruction_valid_i(
            external_fetch_instruction_valid_i
        ),
        .astat_setup_write_i(astat_setup_write_i),
        .astat_setup_data_i(astat_setup_data_i),
        .mstat_setup_write_i(mstat_setup_write_i),
        .mstat_setup_data_i(mstat_setup_data_i),
        .dreg_setup_write_i(dreg_setup_write_i),
        .dreg_setup_code_i(dreg_setup_code_i),
        .dreg_setup_data_i(dreg_setup_data_i),
        .sb_setup_write_i(sb_setup_write_i),
        .sb_setup_data_i(sb_setup_data_i),
        .dag_setup_write_i(dag_setup_write_i),
        .dag_setup_kind_i(dag_setup_kind_i),
        .dag_setup_address_i(dag_setup_address_i),
        .dag_setup_data_i(dag_setup_data_i),
        .px_setup_write_i(px_setup_write_i),
        .px_setup_data_i(px_setup_data_i),
        .probe_dreg_code_i(probe_dreg_code_i),
        .probe_dag_address_i(probe_dag_address_i),
        .issue_boundary_o(issue_boundary_o),
        .phase_conflict_o(native_phase_conflict),
        .attachment_conflict_o(native_attachment_conflict),
        .integration_conflict_o(native_integration_conflict),
        .class_valid_o(class_valid_unused),
        .action_valid_o(action_valid_unused),
        .unsupported_subencoding_o(unsupported_subencoding_unused),
        .accepted_o(accepted_o),
        .data_action_complete_o(data_action_complete_o),
        .instruction_complete_o(instruction_complete_o),
        .transaction_active_o(transaction_active_o),
        .busy_o(busy_o),
        .cache_instruction_selected_o(cache_instruction_selected_o),
        .recovery_required_o(recovery_required_unused),
        .recovery_fetch_o(recovery_fetch_o),
        .event_boundary_o(event_boundary_unused),
        .next_instruction_o(next_instruction_o),
        .next_instruction_valid_o(next_instruction_valid_o),
        .instruction_from_cache_o(instruction_from_cache_o),
        .instruction_from_external_o(instruction_from_external_o),
        .cache_fill_o(cache_fill_o),
        .cache_fill_from_recovery_o(cache_fill_from_recovery_o),
        .cache_fill_accepted_o(cache_fill_accepted_o),
        .cache_region_start_o(cache_region_start_o),
        .cache_region_start_valid_o(cache_region_start_valid_o),
        .cache_region_count_o(cache_region_count_o),
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
        .pmd_write_data_valid_o(pmd_write_data_valid_o),
        .probe_dreg_data_o(probe_dreg_data_o),
        .probe_dreg_valid_o(probe_dreg_valid_o),
        .probe_i_data_o(probe_i_data_o),
        .probe_i_valid_o(probe_i_valid_o),
        .probe_m_data_o(probe_m_data_o),
        .probe_m_valid_o(probe_m_valid_o),
        .probe_l_data_o(probe_l_data_o),
        .probe_l_valid_o(probe_l_valid_o),
        .px_o(px_o),
        .px_valid_o(px_valid_o),
        .sr_o(sr_o),
        .sr_valid_o(sr_valid_o),
        .se_o(se_o),
        .se_valid_o(se_valid_o),
        .sb_o(sb_o),
        .sb_valid_o(sb_valid_o),
        .astat_o(astat_o),
        .astat_valid_mask_o(astat_valid_mask_o),
        .mstat_o(mstat_o),
        .alternate_bank_o(alternate_bank_o)
    );

`ifndef SYNTHESIS
    always_comb begin
        if (native_phase_conflict || native_attachment_conflict) begin
            assert (native_integration_conflict);
        end
        if (force_fetch_issue_o) begin
            assert (pm_request_accepted_o);
            assert (recovery_fetch_o);
            assert (!owner_execute);
        end
        if (late_force_request_o && data_action_complete_o) begin
            assert (!instruction_complete_o);
            assert (!instruction_from_cache_o);
        end
        if (halt_stop_event_o && recovery_fetch_o) begin
            assert (pm_completion_event_o);
            assert (instruction_complete_o);
        end
        if (phase_hold_o) begin
            assert (!effective_phase_advance_o);
            assert (!pm_request_accepted_o);
            assert (!data_action_complete_o);
            assert (!instruction_complete_o);
        end
        if (halted_o && !halt_phase_conflict) begin
            assert (phase_i == 3'd7);
        end
    end
`endif
endmodule

`default_nettype wire
