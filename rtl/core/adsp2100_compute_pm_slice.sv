`default_nettype none

module adsp2100_compute_pm_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic [23:0] pm_read_data_i,
    input  logic        pm_read_data_valid_i,
    input  logic        pm_cycle_complete_i,
    input  logic [13:0] next_fetch_address_i,
    input  logic        next_fetch_address_valid_i,
    input  logic        cache_next_instruction_valid_i,
    input  logic        force_instruction_fetch_i,

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
    output logic        destination_collision_o,
    output logic        computation_enable_o,
    output logic        is_mac_o,
    output logic        destination_feedback_o,
    output logic        write_direction_o,
    output logic [4:0]  amf_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  y_source_dreg_o,
    output logic [3:0]  memory_dreg_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,

    output logic        boundary_valid_o,
    output logic        accepted_o,
    output logic        data_action_complete_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        held_transaction_o,
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
    output logic        dm_access_o,

    output logic        compute_result_known_o,
    output logic        dag_configuration_valid_o,
    output logic        i_write_o,
    output logic        i_write_known_o,
    output logic        dreg_write_o,
    output logic        dreg_write_known_o,
    output logic        px_write_o,
    output logic        px_write_known_o,
    output logic        alu_write_o,
    output logic        mac_write_o,
    output logic        alu_status_write_o,
    output logic        mac_status_write_o,
    output logic [15:0] alu_result_o,
    output logic [39:0] mac_result_o,

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
    logic controls_present;
    logic setup_boundary_valid;
    logic core_execute;
    logic [23:0] translated_type4_opcode;
    logic core_class_valid;
    logic core_action_valid;
    logic core_unsupported;
    logic core_destination_collision;
    logic core_computation_enable;
    logic core_is_mac;
    logic core_destination_feedback;
    logic core_dag_select;
    logic core_write_direction;
    logic [4:0] core_amf;
    logic [1:0] core_yop;
    logic [2:0] core_xop;
    logic [3:0] core_x_source;
    logic [3:0] core_y_source;
    logic [3:0] core_memory_dreg;
    logic [2:0] core_i_address;
    logic [2:0] core_m_address;
    logic core_boundary_valid;
    logic core_accepted;
    logic core_data_complete;
    logic core_transaction_active;
    logic core_stalled;
    logic core_busy;
    logic core_invalid_opcode;
    logic core_integration_conflict;
    logic core_internal_conflict;
    logic core_dm_select;
    logic core_dm_read;
    logic core_dm_write;
    logic [13:0] core_dm_address;
    logic core_dm_address_valid;
    logic [15:0] core_dm_write_data;
    logic core_dm_write_data_valid;
    logic core_pm_data_access_unused;
    logic core_dm_access;

    logic recovery_q;
    logic [13:0] recovery_address_q;
    logic recovery_address_valid_q;
    logic data_pending_q;
    logic pending_needs_recovery_q;
    logic [13:0] pending_next_fetch_address_q;
    logic pending_next_fetch_address_valid_q;
    logic [7:0] pending_px_q;
    logic pending_px_valid_q;
    logic needs_recovery;
    logic active_needs_recovery;
    logic [13:0] active_next_fetch_address;
    logic active_next_fetch_address_valid;
    logic [7:0] active_px;
    logic active_px_valid;
    logic px_setup_enable;
    logic [7:0] px_q;
    logic px_valid_q;

    assign translated_type4_opcode = {4'b0111, opcode_i[19:0]};

    adsp2100_compute_pm_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .destination_collision_o(destination_collision_o),
        .computation_enable_o(computation_enable_o),
        .is_mac_o(is_mac_o),
        .destination_feedback_o(destination_feedback_o),
        .write_o(write_direction_o),
        .amf_o(amf_o),
        .yop_o(yop_o),
        .xop_o(xop_o),
        .x_source_dreg_o(x_source_dreg_o),
        .y_source_dreg_o(y_source_dreg_o),
        .memory_dreg_o(memory_dreg_o),
        .i_address_o(i_address_o),
        .m_address_o(m_address_o)
    );

    assign setup_count = (
        {3'h0, astat_setup_write_i}
        + {3'h0, mstat_setup_write_i}
        + {3'h0, dreg_setup_write_i}
        + {3'h0, af_setup_write_i}
        + {3'h0, mf_setup_write_i}
        + {3'h0, dag_setup_write_i}
        + {3'h0, px_setup_write_i}
    );
    assign controls_present = execute_i || setup_count != 4'h0;
    assign setup_boundary_valid = (
        !reset_i && !recovery_q && !data_pending_q
        && !execute_i && setup_count == 4'h1
    );
    assign core_execute = (
        !reset_i && !recovery_q && execute_i && action_valid_o
        && setup_count == 4'h0
    );
    assign px_setup_enable = setup_boundary_valid && px_setup_write_i;
    assign integration_conflict_o = !reset_i && (
        ((recovery_q || data_pending_q) && controls_present)
        || (
            !recovery_q && !data_pending_q
            && ((execute_i && setup_count != 4'h0) || setup_count > 4'h1)
        )
        || core_integration_conflict
    );
    assign invalid_opcode_o = (
        !reset_i && !recovery_q && !data_pending_q
        && execute_i && !action_valid_o
    );
    assign boundary_valid_o = core_boundary_valid;
    assign accepted_o = core_accepted;
    assign data_action_complete_o = core_data_complete;
    assign needs_recovery = (
        core_accepted
        && (force_instruction_fetch_i || !cache_next_instruction_valid_i)
    );
    assign active_needs_recovery = data_pending_q
        ? pending_needs_recovery_q : needs_recovery;
    assign active_next_fetch_address = data_pending_q
        ? pending_next_fetch_address_q : next_fetch_address_i;
    assign active_next_fetch_address_valid = data_pending_q
        ? pending_next_fetch_address_valid_q : next_fetch_address_valid_i;
    assign cache_instruction_selected_o = (
        core_accepted && cache_next_instruction_valid_i
        && !force_instruction_fetch_i
    );
    assign recovery_required_o = needs_recovery;
    assign recovery_fetch_o = !reset_i && recovery_q;
    assign instruction_complete_o = !reset_i && (
        (core_data_complete && !active_needs_recovery)
        || (recovery_q && pm_cycle_complete_i)
    );
    assign event_boundary_o = instruction_complete_o;
    assign transaction_active_o = !reset_i && (
        core_transaction_active || recovery_q
    );
    assign held_transaction_o = !reset_i && (
        data_pending_q || recovery_q
    );
    assign busy_o = !reset_i && (
        core_stalled
        || (core_data_complete && active_needs_recovery)
        || (recovery_q && !pm_cycle_complete_i)
    );

    assign active_px = data_pending_q ? pending_px_q : px_q;
    assign active_px_valid = data_pending_q
        ? pending_px_valid_q : px_valid_q;
    assign pm_select_o = !reset_i && (core_dm_select || recovery_q);
    assign pm_data_access_o = core_dm_access;
    assign pm_read_o = !reset_i && (recovery_q || core_dm_read);
    assign pm_write_o = core_dm_write;
    assign pm_address_o = recovery_q
        ? (recovery_address_valid_q ? recovery_address_q : 14'h0000)
        : core_dm_address;
    assign pm_address_valid_o = recovery_q
        ? recovery_address_valid_q : core_dm_address_valid;
    assign pm_write_data_o = pm_write_data_valid_o
        ? {core_dm_write_data, active_px} : 24'h000000;
    assign pm_write_data_valid_o = (
        core_dm_write_data_valid && active_px_valid
    );
    assign fetched_instruction_valid_o = (
        recovery_q && pm_cycle_complete_i
        && recovery_address_valid_q && pm_read_data_valid_i
    );
    assign fetched_instruction_o = fetched_instruction_valid_o
        ? pm_read_data_i : 24'h000000;
    assign dm_access_o = 1'b0;
    assign px_write_o = core_data_complete && core_dm_read;
    assign px_write_known_o = px_write_o && pm_read_data_valid_i;
    assign px_o = px_valid_q ? px_q : 8'h00;
    assign px_valid_o = px_valid_q;
    assign internal_conflict_o = core_internal_conflict;

    adsp2100_compute_dm_slice compute_memory_engine (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(core_execute),
        .opcode_i(translated_type4_opcode),
        .dm_ack_i(pm_cycle_complete_i),
        .dm_read_data_i(pm_read_data_i[23:8]),
        .dm_read_data_valid_i(pm_read_data_valid_i),
        .astat_setup_write_i(
            astat_setup_write_i && setup_boundary_valid
        ),
        .astat_setup_data_i(astat_setup_data_i),
        .mstat_setup_write_i(
            mstat_setup_write_i && setup_boundary_valid
        ),
        .mstat_setup_data_i(mstat_setup_data_i),
        .dreg_setup_write_i(
            dreg_setup_write_i && setup_boundary_valid
        ),
        .dreg_setup_code_i(dreg_setup_code_i),
        .dreg_setup_data_i(dreg_setup_data_i),
        .af_setup_write_i(af_setup_write_i && setup_boundary_valid),
        .af_setup_data_i(af_setup_data_i),
        .mf_setup_write_i(mf_setup_write_i && setup_boundary_valid),
        .mf_setup_data_i(mf_setup_data_i),
        .dag_setup_write_i(dag_setup_write_i && setup_boundary_valid),
        .dag_setup_kind_i(dag_setup_kind_i),
        .dag_setup_address_i(dag_setup_address_i),
        .dag_setup_data_i(dag_setup_data_i),
        .inspect_probe_i(1'b0),
        .probe_dreg_code_i(probe_dreg_code_i),
        .probe_dag_address_i(probe_dag_address_i),
        .class_valid_o(core_class_valid),
        .action_valid_o(core_action_valid),
        .unsupported_subencoding_o(core_unsupported),
        .destination_collision_o(core_destination_collision),
        .computation_enable_o(core_computation_enable),
        .is_mac_o(core_is_mac),
        .destination_feedback_o(core_destination_feedback),
        .dag_select_o(core_dag_select),
        .write_direction_o(core_write_direction),
        .amf_o(core_amf),
        .yop_o(core_yop),
        .xop_o(core_xop),
        .x_source_dreg_o(core_x_source),
        .y_source_dreg_o(core_y_source),
        .memory_dreg_o(core_memory_dreg),
        .i_address_o(core_i_address),
        .m_address_o(core_m_address),
        .boundary_valid_o(core_boundary_valid),
        .accepted_o(core_accepted),
        .instruction_complete_o(core_data_complete),
        .transaction_active_o(core_transaction_active),
        .stalled_o(core_stalled),
        .busy_o(core_busy),
        .invalid_opcode_o(core_invalid_opcode),
        .integration_conflict_o(core_integration_conflict),
        .internal_conflict_o(core_internal_conflict),
        .dm_select_o(core_dm_select),
        .dm_read_o(core_dm_read),
        .dm_write_o(core_dm_write),
        .dm_address_o(core_dm_address),
        .dm_address_valid_o(core_dm_address_valid),
        .dm_write_data_o(core_dm_write_data),
        .dm_write_data_valid_o(core_dm_write_data_valid),
        .pm_data_access_o(core_pm_data_access_unused),
        .dm_access_o(core_dm_access),
        .compute_result_known_o(compute_result_known_o),
        .dag_configuration_valid_o(dag_configuration_valid_o),
        .i_write_o(i_write_o),
        .i_write_known_o(i_write_known_o),
        .dreg_write_o(dreg_write_o),
        .dreg_write_known_o(dreg_write_known_o),
        .alu_write_o(alu_write_o),
        .mac_write_o(mac_write_o),
        .alu_status_write_o(alu_status_write_o),
        .mac_status_write_o(mac_status_write_o),
        .alu_result_o(alu_result_o),
        .mac_result_o(mac_result_o),
        .probe_dreg_data_o(probe_dreg_data_o),
        .probe_dreg_valid_o(probe_dreg_valid_o),
        .probe_i_data_o(probe_i_data_o),
        .probe_i_valid_o(probe_i_valid_o),
        .probe_m_data_o(probe_m_data_o),
        .probe_m_valid_o(probe_m_valid_o),
        .probe_l_data_o(probe_l_data_o),
        .probe_l_valid_o(probe_l_valid_o),
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
            recovery_q <= 1'b0;
            recovery_address_q <= 14'h0000;
            recovery_address_valid_q <= 1'b0;
            data_pending_q <= 1'b0;
            pending_needs_recovery_q <= 1'b0;
            pending_next_fetch_address_q <= 14'h0000;
            pending_next_fetch_address_valid_q <= 1'b0;
            pending_px_q <= 8'h00;
            pending_px_valid_q <= 1'b0;
            px_q <= 8'h00;
            px_valid_q <= 1'b0;
        end else begin
            if (recovery_q) begin
                if (pm_cycle_complete_i) begin
                    recovery_q <= 1'b0;
                end
            end else if (core_data_complete && active_needs_recovery) begin
                recovery_q <= 1'b1;
                recovery_address_q <= active_next_fetch_address;
                recovery_address_valid_q <= active_next_fetch_address_valid;
            end

            if (core_data_complete) begin
                data_pending_q <= 1'b0;
            end else if (core_accepted) begin
                data_pending_q <= 1'b1;
                pending_needs_recovery_q <= needs_recovery;
                pending_next_fetch_address_q <= next_fetch_address_i;
                pending_next_fetch_address_valid_q <=
                    next_fetch_address_valid_i;
                pending_px_q <= px_q;
                pending_px_valid_q <= px_valid_q;
            end

            if (px_setup_enable) begin
                px_q <= px_setup_data_i;
                px_valid_q <= 1'b1;
            end
            if (px_write_o) begin
                px_q <= pm_read_data_i[7:0];
                px_valid_q <= pm_read_data_valid_i;
            end
        end
    end

    always_comb begin
        assert (core_class_valid);
        if (class_valid_o) begin
            assert (core_action_valid == action_valid_o);
            assert (core_unsupported == unsupported_subencoding_o);
            assert (core_destination_collision == destination_collision_o);
            assert (core_dag_select);
            assert (core_computation_enable == computation_enable_o);
            assert (core_is_mac == is_mac_o);
            assert (core_destination_feedback == destination_feedback_o);
            assert (core_write_direction == write_direction_o);
            assert (
                core_amf == amf_o && core_yop == yop_o && core_xop == xop_o
            );
            assert (core_x_source == x_source_dreg_o);
            assert (core_y_source == y_source_dreg_o);
            assert (core_memory_dreg == memory_dreg_o);
            assert (
                core_i_address == i_address_o
                && core_m_address == m_address_o
            );
        end
        assert (!core_pm_data_access_unused);
        assert (core_dm_access == core_dm_select);
        assert (!(pm_read_o && pm_write_o));
        assert (pm_select_o == (pm_read_o || pm_write_o));
        assert (!dm_access_o);
        assert (event_boundary_o == instruction_complete_o);
        assert (px_write_o == dreg_write_o);
        if (recovery_fetch_o) begin
            assert (pm_read_o && !pm_write_o && !pm_data_access_o);
            assert (!data_action_complete_o);
            assert (!i_write_o && !dreg_write_o && !px_write_o);
            assert (!alu_write_o && !mac_write_o);
        end
        if (recovery_required_o) begin
            assert (accepted_o && !cache_instruction_selected_o);
        end
        if (pm_write_o && pm_write_data_valid_o) begin
            assert (pm_write_data_o[7:0] == active_px);
        end
        // Reset synchronously cancels a retained descriptor at this edge; the
        // translated execution engine therefore reports no active operation
        // while data_pending_q still reflects its pre-edge value.
        if (data_pending_q && !reset_i) begin
            assert (core_transaction_active);
            assert (active_px == pending_px_q);
        end
        assert (core_busy == core_stalled);
        assert (!core_invalid_opcode);
    end
endmodule

`default_nettype wire
