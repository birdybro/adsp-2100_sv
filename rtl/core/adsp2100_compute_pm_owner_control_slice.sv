`default_nettype none

// Bounded Type 5/cache architectural client attached to the shared native
// PM owner and original normal-operation BR/BG sequencing.
//
// Ordinary fetch and Type 13 remain raw descriptor inputs. A collision has no
// undocumented priority: all requests are rejected, while the Type 5 client
// retains its descriptor and retries at a later enabled state-8 boundary.
module adsp2100_compute_pm_owner_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        br_n_i,

    input  logic        fetch_valid_i,
    input  logic [13:0] fetch_address_i,
    input  logic        fetch_address_valid_i,
    input  logic        type13_valid_i,
    input  logic [13:0] type13_address_i,
    input  logic        type13_address_valid_i,
    input  logic        type13_data_access_i,
    input  logic        type13_write_i,
    input  logic [23:0] type13_write_data_i,
    input  logic        type13_write_data_valid_i,

    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [13:0] next_fetch_address_i,
    input  logic        next_fetch_address_valid_i,

    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        dreg_setup_write_i,
    input  logic [3:0]  dreg_setup_code_i,
    input  logic [15:0] dreg_setup_data_i,
    input  logic        af_setup_write_i,
    input  logic [15:0] af_setup_data_i,
    input  logic        mf_setup_write_i,
    input  logic [15:0] mf_setup_data_i,
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
    output logic        recovery_fetch_o,
    output logic        fetch_cache_fill_o,
    output logic        cache_fill_accepted_o,
    output logic [13:0] cache_region_start_o,
    output logic        cache_region_start_valid_o,
    output logic [4:0]  cache_region_count_o,
    output logic        type5_request_presented_o,
    output logic        type5_request_accepted_o,
    output logic        type5_retry_pending_o,
    output logic [23:0] next_instruction_o,
    output logic        next_instruction_valid_o,
    output logic        instruction_from_cache_o,
    output logic        instruction_from_external_o,

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
    output logic [15:0] af_o,
    output logic        af_valid_o,
    output logic [15:0] mf_o,
    output logic        mf_valid_o,
    output logic [39:0] mr_o,
    output logic        mr_valid_o,
    output logic [7:0]  astat_o,
    output logic [7:0]  astat_valid_mask_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o
);
    import adsp2100_pkg::*;

    logic controls_present;
    logic core_integration_conflict;
    logic core_internal_conflict_unused;
    logic core_pm_select;
    logic core_pm_data_access;
    logic core_pm_read_unused;
    logic core_pm_write;
    logic [13:0] core_pm_address;
    logic core_pm_address_valid;
    logic [23:0] core_pm_write_data;
    logic core_pm_write_data_valid;
    logic [23:0] core_fetched_instruction_unused;
    logic core_fetched_instruction_valid_unused;
    logic cache_lookup_address_hit_unused;
    logic [23:0] cache_lookup_instruction_unused;
    logic cache_lookup_instruction_valid_unused;
    logic cache_instruction_selected_unused;
    logic recovery_required_unused;
    logic event_boundary_unused;
    logic cache_fill_unused;
    logic cache_fill_from_recovery_unused;
    logic external_fill_selected_unused;
    logic cache_region_restarted_unused;
    logic cache_oldest_replaced_unused;
    logic external_fill_conflict_unused;
    logic boundary_valid_unused;
    logic invalid_opcode_unused;

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
    logic unused_observation;

    assign controls_present = (
        execute_i || astat_setup_write_i || mstat_setup_write_i
        || dreg_setup_write_i || af_setup_write_i || mf_setup_write_i
        || dag_setup_write_i
        || px_setup_write_i
    );
    assign issue_boundary_o = (
        !reset_i && !issue_inhibit_o && !bus_relinquished_o
        && phase_advance_i && phase_i == PHASE_STATE_8
    );
    assign phase_conflict_o = (
        !reset_i && controls_present && !issue_boundary_o
    );
    assign type5_request_presented_o = issue_boundary_o && core_pm_select;
    assign type5_request_accepted_o = request_accepted_o[1];
    assign type5_retry_pending_o = (
        type5_request_presented_o && !type5_request_accepted_o
    );
    assign fetch_cache_fill_o = completion_event_o[0] && !pmda_o;
    assign attachment_conflict_o = (
        (type5_request_accepted_o && !type5_request_presented_o)
        || (completion_event_o[1]
            && !(data_action_complete_o || instruction_complete_o))
    );
    assign integration_conflict_o = (
        phase_conflict_o || attachment_conflict_o
        || core_integration_conflict || request_conflict_o
        || request_out_of_phase_o
    );

    adsp2100_compute_pm_cache_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(execute_i && issue_boundary_o),
        .opcode_i(opcode_i),
        .pm_read_data_i(pmd_read_data_i),
        .pm_read_data_valid_i(pmd_read_data_valid_i),
        .pm_cycle_complete_i(completion_event_o[1]),
        .next_fetch_address_i(next_fetch_address_i),
        .next_fetch_address_valid_i(next_fetch_address_valid_i),
        .force_instruction_fetch_i(1'b0),
        .external_fetch_fill_i(fetch_cache_fill_o),
        .external_fetch_address_i(pma_o),
        .external_fetch_address_valid_i(pma_valid_o),
        .external_fetch_instruction_i(pmd_read_data_i),
        .external_fetch_instruction_valid_i(pmd_read_data_valid_i),
        .astat_setup_write_i(astat_setup_write_i && issue_boundary_o),
        .astat_setup_data_i(astat_setup_data_i),
        .mstat_setup_write_i(mstat_setup_write_i && issue_boundary_o),
        .mstat_setup_data_i(mstat_setup_data_i),
        .dreg_setup_write_i(dreg_setup_write_i && issue_boundary_o),
        .dreg_setup_code_i(dreg_setup_code_i),
        .dreg_setup_data_i(dreg_setup_data_i),
        .af_setup_write_i(af_setup_write_i && issue_boundary_o),
        .af_setup_data_i(af_setup_data_i),
        .mf_setup_write_i(mf_setup_write_i && issue_boundary_o),
        .mf_setup_data_i(mf_setup_data_i),
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
        .internal_conflict_o(core_internal_conflict_unused),
        .cache_instruction_selected_o(cache_instruction_selected_unused),
        .recovery_required_o(recovery_required_unused),
        .recovery_fetch_o(recovery_fetch_o),
        .event_boundary_o(event_boundary_unused),
        .pm_select_o(core_pm_select),
        .pm_data_access_o(core_pm_data_access),
        .pm_read_o(core_pm_read_unused),
        .pm_write_o(core_pm_write),
        .pm_address_o(core_pm_address),
        .pm_address_valid_o(core_pm_address_valid),
        .pm_write_data_o(core_pm_write_data),
        .pm_write_data_valid_o(core_pm_write_data_valid),
        .fetched_instruction_o(core_fetched_instruction_unused),
        .fetched_instruction_valid_o(
            core_fetched_instruction_valid_unused
        ),
        .cache_lookup_address_hit_o(cache_lookup_address_hit_unused),
        .cache_lookup_instruction_o(cache_lookup_instruction_unused),
        .cache_lookup_instruction_valid_o(
            cache_lookup_instruction_valid_unused
        ),
        .cache_fill_o(cache_fill_unused),
        .cache_fill_from_recovery_o(cache_fill_from_recovery_unused),
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
        .af_o(af_o),
        .af_valid_o(af_valid_o),
        .mf_o(mf_o),
        .mf_valid_o(mf_valid_o),
        .mr_o(mr_o),
        .mr_valid_o(mr_valid_o),
        .astat_o(astat_o),
        .astat_valid_mask_o(astat_valid_mask_o),
        .mstat_o(mstat_o),
        .alternate_bank_o(alternate_bank_o)
    );

    adsp2100_program_owner_bus_control owner_control (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .pm_phase_advance_i(phase_advance_i), .br_n_i(br_n_i),
        .service_inhibit_i(1'b0),
        .fetch_valid_i(fetch_valid_i),
        .fetch_address_i(fetch_address_i),
        .fetch_address_valid_i(fetch_address_valid_i),
        .type13_valid_i(type13_valid_i),
        .type13_address_i(type13_address_i),
        .type13_address_valid_i(type13_address_valid_i),
        .type13_data_access_i(type13_data_access_i),
        .type13_write_i(type13_write_i),
        .type13_write_data_i(type13_write_data_i),
        .type13_write_data_valid_i(type13_write_data_valid_i),
        .type5_valid_i(type5_request_presented_o),
        .type5_address_i(core_pm_address),
        .type5_address_valid_i(core_pm_address_valid),
        .type5_data_access_i(core_pm_data_access),
        .type5_write_i(core_pm_write),
        .type5_write_data_i(core_pm_write_data),
        .type5_write_data_valid_i(core_pm_write_data_valid),
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
        core_internal_conflict_unused, core_pm_data_access,
        core_pm_read_unused, core_fetched_instruction_unused,
        core_fetched_instruction_valid_unused,
        cache_lookup_address_hit_unused, cache_lookup_instruction_unused,
        cache_lookup_instruction_valid_unused,
        cache_instruction_selected_unused, recovery_required_unused,
        event_boundary_unused, cache_fill_unused,
        cache_fill_from_recovery_unused, external_fill_selected_unused,
        cache_region_restarted_unused, cache_oldest_replaced_unused,
        external_fill_conflict_unused,
        boundary_valid_unused, invalid_opcode_unused,
        state_three_boundary_unused, request_withdrawn_unused,
        release_cancelled_unused, normal_bus_relinquished_unused,
        normal_bg_n_unused, reset_br_request_unused, request_ready_unused,
        read_sample_event_unused, response_valid_unused,
        response_write_unused, response_read_data_unused,
        response_read_data_valid_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (type5_request_accepted_o == request_accepted_o[1]);
        if (type5_retry_pending_o) begin
            assert (transaction_active_o);
        end
        if (bus_relinquished_o) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
        end
    end

    always_ff @(posedge clk_i) begin
        if (!reset_i && completion_event_o[1]) begin
            assert (data_action_complete_o || instruction_complete_o);
        end
    end
`endif
endmodule

`default_nettype wire
