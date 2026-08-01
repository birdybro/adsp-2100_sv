`default_nettype none

module adsp2100_compute_pm_cache_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic [23:0] pm_read_data_i,
    input  logic        pm_read_data_valid_i,
    input  logic        pm_cycle_complete_i,
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

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        boundary_valid_o,
    output logic        accepted_o,
    output logic        data_action_complete_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        busy_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        cache_instruction_selected_o,
    output logic        recovery_required_o,
    output logic        recovery_fetch_o,
    output logic        event_boundary_o,

    output logic        pm_select_o,
    output logic        pm_data_access_o,
    output logic        pm_read_o,
    output logic        pm_write_o,
    output logic [13:0] pm_address_o,
    output logic        pm_address_valid_o,
    output logic [23:0] pm_write_data_o,
    output logic        pm_write_data_valid_o,
    output logic [23:0] fetched_instruction_o,
    output logic        fetched_instruction_valid_o,

    output logic        cache_lookup_address_hit_o,
    output logic [23:0] cache_lookup_instruction_o,
    output logic        cache_lookup_instruction_valid_o,
    output logic        cache_fill_o,
    output logic        cache_fill_from_recovery_o,
    output logic        external_fill_selected_o,
    output logic        cache_fill_accepted_o,
    output logic        cache_region_restarted_o,
    output logic        cache_oldest_replaced_o,
    output logic        external_fill_conflict_o,
    output logic [13:0] cache_region_start_o,
    output logic        cache_region_start_valid_o,
    output logic [4:0]  cache_region_count_o,

    output logic [23:0] next_instruction_o,
    output logic        next_instruction_valid_o,
    output logic        instruction_from_cache_o,
    output logic        instruction_from_external_o,

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
    logic [3:0] setup_count;
    logic suppress_controls;
    logic core_integration_conflict;
    logic core_recovery_fetch;
    logic core_held_transaction;
    logic [23:0] core_fetched_instruction;
    logic core_fetched_instruction_valid;
    logic pending_cache_q;
    logic [23:0] pending_cache_instruction_q;
    logic issue_cache_instruction_valid;
    logic cache_fill_address_valid;
    logic [13:0] cache_fill_address;
    logic cache_fill_instruction_valid;
    logic [23:0] cache_fill_instruction;

    logic destination_collision_unused;
    logic computation_enable_unused;
    logic is_mac_unused;
    logic destination_feedback_unused;
    logic write_direction_unused;
    logic [4:0] amf_unused;
    logic [1:0] yop_unused;
    logic [2:0] xop_unused;
    logic [3:0] x_source_unused;
    logic [3:0] y_source_unused;
    logic [3:0] memory_dreg_unused;
    logic [2:0] i_address_unused;
    logic [2:0] m_address_unused;
    logic dm_access_unused;
    logic compute_result_known_unused;
    logic dag_configuration_valid_unused;
    logic i_write_unused;
    logic i_write_known_unused;
    logic dreg_write_unused;
    logic dreg_write_known_unused;
    logic px_write_unused;
    logic px_write_known_unused;
    logic alu_write_unused;
    logic mac_write_unused;
    logic alu_status_write_unused;
    logic mac_status_write_unused;
    logic [15:0] alu_result_unused;
    logic [39:0] mac_result_unused;
    logic unused_observation;

    assign setup_count = (
        {3'h0, astat_setup_write_i}
        + {3'h0, mstat_setup_write_i}
        + {3'h0, dreg_setup_write_i}
        + {3'h0, af_setup_write_i}
        + {3'h0, mf_setup_write_i}
        + {3'h0, dag_setup_write_i}
        + {3'h0, px_setup_write_i}
    );
    assign cache_fill_from_recovery_o = (
        core_recovery_fetch && instruction_complete_o
    );
    assign external_fill_conflict_o = (
        !reset_i && external_fetch_fill_i
        && (core_held_transaction || execute_i || setup_count != 4'h0)
    );
    assign external_fill_selected_o = (
        !reset_i && external_fetch_fill_i && !core_held_transaction
    );
    assign suppress_controls = external_fill_selected_o;
    assign integration_conflict_o = (
        core_integration_conflict || external_fill_conflict_o
    );

    assign cache_fill_o = (
        cache_fill_from_recovery_o || external_fill_selected_o
    );
    assign cache_fill_address = cache_fill_from_recovery_o
        ? pm_address_o : external_fetch_address_i;
    assign cache_fill_address_valid = cache_fill_from_recovery_o
        ? pm_address_valid_o : external_fetch_address_valid_i;
    assign cache_fill_instruction = cache_fill_from_recovery_o
        ? core_fetched_instruction : external_fetch_instruction_i;
    assign cache_fill_instruction_valid = cache_fill_from_recovery_o
        ? core_fetched_instruction_valid
        : external_fetch_instruction_valid_i;

    assign issue_cache_instruction_valid = (
        cache_instruction_selected_o
        && cache_lookup_instruction_valid_o
    );
    assign instruction_from_cache_o = (
        data_action_complete_o
        && (issue_cache_instruction_valid || pending_cache_q)
    );
    assign instruction_from_external_o = (
        core_recovery_fetch && core_fetched_instruction_valid
    );
    assign next_instruction_valid_o = (
        instruction_from_cache_o || instruction_from_external_o
    );
    assign next_instruction_o = instruction_from_cache_o
        ? (issue_cache_instruction_valid
            ? cache_lookup_instruction_o : pending_cache_instruction_q)
        : (instruction_from_external_o
            ? core_fetched_instruction : 24'h000000);
    assign fetched_instruction_o = core_fetched_instruction;
    assign fetched_instruction_valid_o = core_fetched_instruction_valid;
    assign recovery_fetch_o = core_recovery_fetch;

    assign unused_observation = ^{
        destination_collision_unused, computation_enable_unused,
        is_mac_unused, destination_feedback_unused, write_direction_unused,
        amf_unused, yop_unused, xop_unused, x_source_unused, y_source_unused,
        memory_dreg_unused, i_address_unused, m_address_unused,
        dm_access_unused, compute_result_known_unused,
        dag_configuration_valid_unused, i_write_unused, i_write_known_unused,
        dreg_write_unused, dreg_write_known_unused, px_write_unused,
        px_write_known_unused, alu_write_unused, mac_write_unused,
        alu_status_write_unused, mac_status_write_unused,
        alu_result_unused, mac_result_unused
    };

    adsp2100_instruction_cache cache (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .fill_i(cache_fill_o),
        .fill_address_i(cache_fill_address),
        .fill_address_valid_i(cache_fill_address_valid),
        .fill_instruction_i(cache_fill_instruction),
        .fill_instruction_valid_i(cache_fill_instruction_valid),
        .lookup_address_i(next_fetch_address_i),
        .lookup_address_valid_i(next_fetch_address_valid_i),
        .lookup_hit_o(cache_lookup_address_hit_o),
        .lookup_instruction_o(cache_lookup_instruction_o),
        .lookup_instruction_valid_o(cache_lookup_instruction_valid_o),
        .fill_accepted_o(cache_fill_accepted_o),
        .region_restarted_o(cache_region_restarted_o),
        .oldest_replaced_o(cache_oldest_replaced_o),
        .region_start_o(cache_region_start_o),
        .region_start_valid_o(cache_region_start_valid_o),
        .region_count_o(cache_region_count_o)
    );

    adsp2100_compute_pm_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(execute_i && !suppress_controls),
        .opcode_i(opcode_i),
        .pm_read_data_i(pm_read_data_i),
        .pm_read_data_valid_i(pm_read_data_valid_i),
        .pm_cycle_complete_i(pm_cycle_complete_i),
        .next_fetch_address_i(next_fetch_address_i),
        .next_fetch_address_valid_i(next_fetch_address_valid_i),
        .cache_next_instruction_valid_i(cache_lookup_instruction_valid_o),
        .force_instruction_fetch_i(force_instruction_fetch_i),
        .astat_setup_write_i(astat_setup_write_i && !suppress_controls),
        .astat_setup_data_i(astat_setup_data_i),
        .mstat_setup_write_i(mstat_setup_write_i && !suppress_controls),
        .mstat_setup_data_i(mstat_setup_data_i),
        .dreg_setup_write_i(dreg_setup_write_i && !suppress_controls),
        .dreg_setup_code_i(dreg_setup_code_i),
        .dreg_setup_data_i(dreg_setup_data_i),
        .af_setup_write_i(af_setup_write_i && !suppress_controls),
        .af_setup_data_i(af_setup_data_i),
        .mf_setup_write_i(mf_setup_write_i && !suppress_controls),
        .mf_setup_data_i(mf_setup_data_i),
        .dag_setup_write_i(dag_setup_write_i && !suppress_controls),
        .dag_setup_kind_i(dag_setup_kind_i),
        .dag_setup_address_i(dag_setup_address_i),
        .dag_setup_data_i(dag_setup_data_i),
        .px_setup_write_i(px_setup_write_i && !suppress_controls),
        .px_setup_data_i(px_setup_data_i),
        .probe_dreg_code_i(probe_dreg_code_i),
        .probe_dag_address_i(probe_dag_address_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .destination_collision_o(destination_collision_unused),
        .computation_enable_o(computation_enable_unused),
        .is_mac_o(is_mac_unused),
        .destination_feedback_o(destination_feedback_unused),
        .write_direction_o(write_direction_unused),
        .amf_o(amf_unused),
        .yop_o(yop_unused),
        .xop_o(xop_unused),
        .x_source_dreg_o(x_source_unused),
        .y_source_dreg_o(y_source_unused),
        .memory_dreg_o(memory_dreg_unused),
        .i_address_o(i_address_unused),
        .m_address_o(m_address_unused),
        .boundary_valid_o(boundary_valid_o),
        .accepted_o(accepted_o),
        .data_action_complete_o(data_action_complete_o),
        .instruction_complete_o(instruction_complete_o),
        .transaction_active_o(transaction_active_o),
        .held_transaction_o(core_held_transaction),
        .busy_o(busy_o),
        .invalid_opcode_o(invalid_opcode_o),
        .integration_conflict_o(core_integration_conflict),
        .internal_conflict_o(internal_conflict_o),
        .cache_instruction_selected_o(cache_instruction_selected_o),
        .recovery_required_o(recovery_required_o),
        .recovery_fetch_o(core_recovery_fetch),
        .event_boundary_o(event_boundary_o),
        .pm_select_o(pm_select_o),
        .pm_data_access_o(pm_data_access_o),
        .pm_read_o(pm_read_o),
        .pm_write_o(pm_write_o),
        .pm_address_o(pm_address_o),
        .pm_address_valid_o(pm_address_valid_o),
        .pm_write_data_o(pm_write_data_o),
        .pm_write_data_valid_o(pm_write_data_valid_o),
        .fetched_instruction_o(core_fetched_instruction),
        .fetched_instruction_valid_o(core_fetched_instruction_valid),
        .dm_access_o(dm_access_unused),
        .compute_result_known_o(compute_result_known_unused),
        .dag_configuration_valid_o(dag_configuration_valid_unused),
        .i_write_o(i_write_unused),
        .i_write_known_o(i_write_known_unused),
        .dreg_write_o(dreg_write_unused),
        .dreg_write_known_o(dreg_write_known_unused),
        .px_write_o(px_write_unused),
        .px_write_known_o(px_write_known_unused),
        .alu_write_o(alu_write_unused),
        .mac_write_o(mac_write_unused),
        .alu_status_write_o(alu_status_write_unused),
        .mac_status_write_o(mac_status_write_unused),
        .alu_result_o(alu_result_unused),
        .mac_result_o(mac_result_unused),
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

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pending_cache_q <= 1'b0;
            pending_cache_instruction_q <= 24'h000000;
        end else if (data_action_complete_o) begin
            pending_cache_q <= 1'b0;
            pending_cache_instruction_q <= 24'h000000;
        end else if (accepted_o) begin
            pending_cache_q <= issue_cache_instruction_valid;
            pending_cache_instruction_q <= cache_lookup_instruction_o;
        end
    end

    always_comb begin
        assert (next_instruction_valid_o
            == (instruction_from_cache_o || instruction_from_external_o));
        assert (!(instruction_from_cache_o && instruction_from_external_o));
        assert (cache_fill_from_recovery_o
            == (recovery_fetch_o && instruction_complete_o));
        assert (!(cache_fill_from_recovery_o && external_fill_selected_o));
        assert (cache_fill_o
            == (cache_fill_from_recovery_o || external_fill_selected_o));
        assert (integration_conflict_o
            == (core_integration_conflict || external_fill_conflict_o));
        assert (unused_observation == unused_observation);
        if (!next_instruction_valid_o) begin
            assert (next_instruction_o == 24'h000000);
        end
        if (cache_instruction_selected_o) begin
            assert (cache_lookup_instruction_valid_o);
            assert (!recovery_required_o);
        end
        if (pending_cache_q) begin
            assert (transaction_active_o);
        end
        if (reset_i) begin
            assert (!cache_fill_o && !next_instruction_valid_o);
        end
    end
endmodule

`default_nettype wire
