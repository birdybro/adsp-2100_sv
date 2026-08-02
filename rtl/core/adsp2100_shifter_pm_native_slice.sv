`default_nettype none

module adsp2100_shifter_pm_native_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
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

    input  logic [3:0]  irq_n_i,
    input  logic [4:0]  icntl_i,
    input  logic        icntl_valid_i,
    input  logic [3:0]  imask_i,
    input  logic        imask_valid_i,

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

    output logic        issue_boundary_o,
    output logic        phase_conflict_o,
    output logic        attachment_conflict_o,
    output logic        integration_conflict_o,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        accepted_o,
    output logic        data_action_complete_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        busy_o,
    output logic        cache_instruction_selected_o,
    output logic        recovery_required_o,
    output logic        recovery_fetch_o,
    output logic        event_boundary_o,
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

    output logic        interrupt_sample_event_o,
    output logic        interrupt_interval_block_o,
    output logic [3:0]  interrupt_enabled_requests_o,
    output logic        interrupt_recognition_event_o,
    output logic [1:0]  interrupt_recognized_level_o,
    output logic [13:0] interrupt_vector_address_o,
    output logic [3:0]  interrupt_edge_pending_o,
    output logic        interrupt_sample_history_valid_o,

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
    import adsp2100_pkg::*;

    logic controls_present;
    logic core_integration_conflict;
    logic core_internal_conflict;
    logic core_pm_select;
    logic core_pm_data_access;
    logic core_pm_read;
    logic core_pm_write;
    logic [13:0] core_pm_address;
    logic core_pm_address_valid;
    logic [23:0] core_pm_write_data;
    logic core_pm_write_data_valid;
    logic [23:0] core_fetched_instruction_unused;
    logic core_fetched_instruction_valid_unused;
    logic bus_request_ready;
    logic bus_response_valid_unused;
    logic bus_response_write_unused;
    logic [23:0] bus_response_data_unused;
    logic bus_response_data_valid_unused;
    logic [13:0] descriptor_address_unused;
    logic descriptor_address_valid_unused;
    logic descriptor_data_access_unused;
    logic descriptor_write_unused;
    logic [23:0] descriptor_write_data_unused;
    logic descriptor_write_data_valid_unused;
    logic boundary_valid_unused;
    logic invalid_opcode_unused;
    logic cache_lookup_hit_unused;
    logic [23:0] cache_lookup_instruction_unused;
    logic cache_lookup_instruction_valid_unused;
    logic external_fill_selected_unused;
    logic cache_region_restarted_unused;
    logic cache_oldest_replaced_unused;
    logic external_fill_conflict_unused;
    logic [3:0] interrupt_sampled_requests_unused;
    logic interrupt_configuration_invalid_unused;
    logic interrupt_reset_baseline_provisional_unused;
    logic unused_observation;

    assign controls_present = (
        execute_i || external_fetch_fill_i || astat_setup_write_i
        || mstat_setup_write_i || dreg_setup_write_i || sb_setup_write_i
        || dag_setup_write_i || px_setup_write_i
    );
    assign issue_boundary_o = (
        !reset_i && !bus_relinquished_i && phase_advance_i
        && phase_i == PHASE_STATE_8
    );
    assign phase_conflict_o = (
        !reset_i && controls_present && !issue_boundary_o
    );
    assign attachment_conflict_o = (
        pm_request_accepted_o
            != (issue_boundary_o && core_pm_select)
        || accepted_o
            != (pm_request_accepted_o && core_pm_data_access)
        || data_action_complete_o
            != (pm_completion_event_o && core_pm_data_access)
    );
    assign integration_conflict_o = (
        phase_conflict_o || attachment_conflict_o
        || core_integration_conflict
    );
    assign unused_observation = ^{
        bus_request_ready, bus_response_valid_unused,
        bus_response_write_unused, bus_response_data_unused,
        bus_response_data_valid_unused, descriptor_address_unused,
        descriptor_address_valid_unused, descriptor_data_access_unused,
        descriptor_write_unused, descriptor_write_data_unused,
        descriptor_write_data_valid_unused, boundary_valid_unused,
        invalid_opcode_unused, core_internal_conflict, core_pm_read,
        core_fetched_instruction_unused,
        core_fetched_instruction_valid_unused,
        cache_lookup_hit_unused, cache_lookup_instruction_unused,
        cache_lookup_instruction_valid_unused, external_fill_selected_unused,
        cache_region_restarted_unused,
        cache_oldest_replaced_unused, external_fill_conflict_unused,
        cache_region_start_o, cache_region_start_valid_o,
        cache_region_count_o, interrupt_sampled_requests_unused,
        interrupt_configuration_invalid_unused,
        interrupt_reset_baseline_provisional_unused
    };

    // ADI-UM-1989, p. 5-16: requests may latch but are not serviced
    // between the PM-data cycle and the recovery fetch of an uncached
    // instruction. The cache composition's instruction-complete boundary
    // is therefore the service gate; physical state-7 sampling continues.
    assign interrupt_interval_block_o = (
        interrupt_sample_event_o && data_action_complete_o
        && !instruction_complete_o
    );

    adsp2100_interrupt_control interrupt_control (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .irq_n_i(irq_n_i),
        .icntl_i(icntl_i),
        .icntl_valid_i(icntl_valid_i),
        .imask_i(imask_i),
        .imask_valid_i(imask_valid_i),
        .service_allowed_i(instruction_complete_o),
        .sample_event_o(interrupt_sample_event_o),
        .sampled_requests_o(interrupt_sampled_requests_unused),
        .enabled_requests_o(interrupt_enabled_requests_o),
        .recognition_event_o(interrupt_recognition_event_o),
        .recognized_level_o(interrupt_recognized_level_o),
        .vector_address_o(interrupt_vector_address_o),
        .edge_pending_o(interrupt_edge_pending_o),
        .sample_history_valid_o(interrupt_sample_history_valid_o),
        .configuration_invalid_o(
            interrupt_configuration_invalid_unused
        ),
        .reset_baseline_provisional_o(
            interrupt_reset_baseline_provisional_unused
        )
    );

    adsp2100_shifter_pm_cache_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(execute_i && issue_boundary_o),
        .opcode_i(opcode_i),
        .pm_read_data_i(pmd_read_data_i),
        .pm_read_data_valid_i(pmd_read_data_valid_i),
        .pm_cycle_complete_i(pm_completion_event_o),
        .next_fetch_address_i(next_fetch_address_i),
        .next_fetch_address_valid_i(next_fetch_address_valid_i),
        .force_instruction_fetch_i(force_instruction_fetch_i),
        .external_fetch_fill_i(
            external_fetch_fill_i && issue_boundary_o
        ),
        .external_fetch_address_i(external_fetch_address_i),
        .external_fetch_address_valid_i(
            external_fetch_address_valid_i
        ),
        .external_fetch_instruction_i(external_fetch_instruction_i),
        .external_fetch_instruction_valid_i(
            external_fetch_instruction_valid_i
        ),
        .astat_setup_write_i(astat_setup_write_i && issue_boundary_o),
        .astat_setup_data_i(astat_setup_data_i),
        .mstat_setup_write_i(mstat_setup_write_i && issue_boundary_o),
        .mstat_setup_data_i(mstat_setup_data_i),
        .dreg_setup_write_i(dreg_setup_write_i && issue_boundary_o),
        .dreg_setup_code_i(dreg_setup_code_i),
        .dreg_setup_data_i(dreg_setup_data_i),
        .sb_setup_write_i(sb_setup_write_i && issue_boundary_o),
        .sb_setup_data_i(sb_setup_data_i),
        .dag_setup_write_i(dag_setup_write_i && issue_boundary_o),
        .dag_setup_kind_i(dag_setup_kind_i),
        .dag_setup_address_i(dag_setup_address_i),
        .dag_setup_data_i(dag_setup_data_i),
        .px_setup_write_i(px_setup_write_i && issue_boundary_o),
        .px_setup_data_i(px_setup_data_i),
        .probe_dreg_code_i(probe_dreg_code_i),
        .probe_dag_address_i(probe_dag_address_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .boundary_valid_o(boundary_valid_unused),
        .accepted_o(accepted_o),
        .data_action_complete_o(data_action_complete_o),
        .instruction_complete_o(instruction_complete_o),
        .transaction_active_o(transaction_active_o),
        .busy_o(busy_o),
        .invalid_opcode_o(invalid_opcode_unused),
        .integration_conflict_o(core_integration_conflict),
        .internal_conflict_o(core_internal_conflict),
        .cache_instruction_selected_o(cache_instruction_selected_o),
        .recovery_required_o(recovery_required_o),
        .recovery_fetch_o(recovery_fetch_o),
        .event_boundary_o(event_boundary_o),
        .pm_select_o(core_pm_select),
        .pm_data_access_o(core_pm_data_access),
        .pm_read_o(core_pm_read),
        .pm_write_o(core_pm_write),
        .pm_address_o(core_pm_address),
        .pm_address_valid_o(core_pm_address_valid),
        .pm_write_data_o(core_pm_write_data),
        .pm_write_data_valid_o(core_pm_write_data_valid),
        .fetched_instruction_o(core_fetched_instruction_unused),
        .fetched_instruction_valid_o(
            core_fetched_instruction_valid_unused
        ),
        .cache_lookup_address_hit_o(cache_lookup_hit_unused),
        .cache_lookup_instruction_o(cache_lookup_instruction_unused),
        .cache_lookup_instruction_valid_o(
            cache_lookup_instruction_valid_unused
        ),
        .cache_fill_o(cache_fill_o),
        .cache_fill_from_recovery_o(cache_fill_from_recovery_o),
        .external_fill_selected_o(external_fill_selected_unused),
        .cache_fill_accepted_o(cache_fill_accepted_o),
        .cache_region_restarted_o(cache_region_restarted_unused),
        .cache_oldest_replaced_o(cache_oldest_replaced_unused),
        .external_fill_conflict_o(external_fill_conflict_unused),
        .cache_region_start_o(cache_region_start_o),
        .cache_region_start_valid_o(cache_region_start_valid_o),
        .cache_region_count_o(cache_region_count_o),
        .next_instruction_o(next_instruction_o),
        .next_instruction_valid_o(next_instruction_valid_o),
        .instruction_from_cache_o(instruction_from_cache_o),
        .instruction_from_external_o(instruction_from_external_o),
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

    adsp2100_program_bus bus (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .request_valid_i(core_pm_select),
        .request_address_i(core_pm_address),
        .request_address_valid_i(core_pm_address_valid),
        .request_data_access_i(core_pm_data_access),
        .request_write_i(core_pm_write),
        .request_write_data_i(core_pm_write_data),
        .request_write_data_valid_i(core_pm_write_data_valid),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .bus_relinquished_i(bus_relinquished_i),
        .request_ready_o(bus_request_ready),
        .request_accepted_o(pm_request_accepted_o),
        .completion_event_o(pm_completion_event_o),
        .read_sample_event_o(pm_read_sample_event_o),
        .transaction_active_o(pm_bus_active_o),
        .response_valid_o(bus_response_valid_unused),
        .response_write_o(bus_response_write_unused),
        .response_read_data_o(bus_response_data_unused),
        .response_read_data_valid_o(bus_response_data_valid_unused),
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
        .descriptor_address_o(descriptor_address_unused),
        .descriptor_address_valid_o(descriptor_address_valid_unused),
        .descriptor_data_access_o(descriptor_data_access_unused),
        .descriptor_write_o(descriptor_write_unused),
        .descriptor_write_data_o(descriptor_write_data_unused),
        .descriptor_write_data_valid_o(
            descriptor_write_data_valid_unused
        )
    );

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        if (recovery_fetch_o) begin
            assert (core_pm_select && !core_pm_data_access);
        end
        if (bus_relinquished_i) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
        end
        if (interrupt_interval_block_o) begin
            assert (!interrupt_recognition_event_o);
        end
        if (interrupt_recognition_event_o) begin
            assert (instruction_complete_o);
        end
    end
`endif
endmodule

`default_nettype wire
