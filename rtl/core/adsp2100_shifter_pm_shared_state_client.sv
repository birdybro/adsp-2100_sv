`default_nettype none

// Type 13 PM transaction/action client with no architectural storage.
//
// All operands are supplied by one external architectural-state owner at the
// issue boundary.  The descriptor and every shifter/DAG writeback value are
// retained until the routed PM completion.  This is an implementation
// composition boundary; instruction semantics remain those of the bounded
// Type 13 slice.
module adsp2100_shifter_pm_shared_state_client (
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

    input  logic [15:0] shifter_source_data_i,
    input  logic        shifter_source_data_valid_i,
    input  logic [15:0] memory_source_data_i,
    input  logic        memory_source_data_valid_i,
    input  logic [31:0] sr_i,
    input  logic        sr_valid_i,
    input  logic [7:0]  se_i,
    input  logic        se_valid_i,
    input  logic [4:0]  sb_i,
    input  logic        sb_valid_i,
    input  logic [7:0]  astat_i,
    input  logic [7:0]  astat_valid_mask_i,
    input  logic [13:0] dag_i_data_i,
    input  logic        dag_i_data_valid_i,
    input  logic [13:0] dag_m_data_i,
    input  logic        dag_m_data_valid_i,
    input  logic [13:0] dag_l_data_i,
    input  logic        dag_l_data_valid_i,
    input  logic [7:0]  px_i,
    input  logic        px_valid_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        unavailable_xop_o,
    output logic        destination_collision_o,
    output logic        write_direction_o,
    output logic [3:0]  sf_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  shifter_source_dreg_o,
    output logic [3:0]  memory_dreg_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,

    output logic        accepted_o,
    output logic        data_action_complete_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        held_transaction_o,
    output logic        busy_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
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

    output logic        shifter_result_known_o,
    output logic        dag_configuration_valid_o,
    output logic        i_write_o,
    output logic [2:0]  i_write_address_o,
    output logic [13:0] i_write_data_o,
    output logic        i_write_known_o,
    output logic        dreg_write_o,
    output logic [3:0]  dreg_write_address_o,
    output logic [15:0] dreg_write_data_o,
    output logic        dreg_write_known_o,
    output logic        px_write_o,
    output logic [7:0]  px_write_data_o,
    output logic        px_write_known_o,
    output logic        sr_write_o,
    output logic        se_write_o,
    output logic        sb_write_o,
    output logic        ss_write_o,
    output logic [31:0] sr_result_o,
    output logic [7:0]  se_result_o,
    output logic [4:0]  sb_result_o,
    output logic        ss_result_o,
    output logic [3:0]  active_sf_o,
    output logic        active_exp_lo_destination_o
);
    logic issue;
    logic needs_recovery;
    logic pending_q;
    logic recovery_q;
    logic [13:0] recovery_address_q;
    logic recovery_address_valid_q;

    logic pending_write_q;
    logic [3:0] pending_memory_dreg_q;
    logic [2:0] pending_i_address_q;
    logic [13:0] pending_address_q;
    logic pending_address_valid_q;
    logic [23:0] pending_write_data_q;
    logic pending_write_data_valid_q;
    logic [13:0] pending_next_i_q;
    logic pending_next_i_valid_q;
    logic pending_dag_configuration_valid_q;
    logic pending_shifter_known_q;
    logic pending_sr_write_q;
    logic pending_se_write_q;
    logic pending_sb_write_q;
    logic pending_ss_write_q;
    logic [31:0] pending_sr_result_q;
    logic [7:0] pending_se_result_q;
    logic [4:0] pending_sb_result_q;
    logic pending_ss_result_q;
    logic [3:0] pending_sf_q;
    logic pending_exp_lo_destination_q;
    logic pending_needs_recovery_q;
    logic [13:0] pending_next_fetch_address_q;
    logic pending_next_fetch_address_valid_q;

    logic data_active;
    logic data_request_active;
    logic data_complete;
    logic active_write;
    logic [13:0] active_address;
    logic active_address_valid;
    logic [23:0] active_write_data;
    logic active_write_data_valid;
    logic active_dag_configuration_valid;
    logic active_needs_recovery;
    logic [13:0] active_next_fetch_address;
    logic active_next_fetch_address_valid;

    logic live_shifter_known;
    logic live_sr_pair_valid;
    logic [31:0] live_sr_result;
    logic live_sr_write;
    logic [7:0] live_se_result;
    logic live_se_write;
    logic [4:0] live_sb_result;
    logic live_sb_write;
    logic live_ss_result;
    logic live_ss_write;
    logic [13:0] live_pm_address;
    logic [13:0] live_next_i;
    logic [13:0] unused_dag_base;
    logic unused_dag_circular;
    logic live_dag_configuration_valid;
    logic live_next_i_valid;
    logic live_exp_lo_destination;
    logic unused_observation;

    assign unused_observation = ^{
        astat_i[6:4], astat_i[1:0],
        astat_valid_mask_i[6:4], astat_valid_mask_i[1:0]
    };

    adsp2100_shifter_pm_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .unavailable_xop_o(unavailable_xop_o),
        .destination_collision_o(destination_collision_o),
        .write_o(write_direction_o),
        .sf_o(sf_o),
        .xop_o(xop_o),
        .shifter_source_dreg_o(shifter_source_dreg_o),
        .memory_dreg_o(memory_dreg_o),
        .i_address_o(i_address_o),
        .m_address_o(m_address_o)
    );

    assign issue = !reset_i && !pending_q && !recovery_q
        && execute_i && action_valid_o;
    assign accepted_o = issue;
    assign invalid_opcode_o = !reset_i && !pending_q && !recovery_q
        && execute_i && !action_valid_o;
    assign integration_conflict_o = !reset_i && (pending_q || recovery_q)
        && execute_i;
    assign needs_recovery = issue
        && (force_instruction_fetch_i || !cache_next_instruction_valid_i);
    assign cache_instruction_selected_o = issue
        && cache_next_instruction_valid_i && !force_instruction_fetch_i;
    assign recovery_required_o = needs_recovery;

    assign live_sr_pair_valid = sr_valid_i;
    always_comb begin
        live_shifter_known = shifter_source_data_valid_i;
        if (sf_o <= 4'hb) begin
            live_shifter_known = live_shifter_known && se_valid_i
                && (!sf_o[0] || live_sr_pair_valid)
                && ((sf_o != 4'h8 && sf_o != 4'h9)
                    || astat_valid_mask_i[3]);
        end else if (sf_o == 4'hd) begin
            live_shifter_known = live_shifter_known
                && astat_valid_mask_i[2];
        end else if (sf_o == 4'he) begin
            live_shifter_known = live_shifter_known && se_valid_i
                && (se_i != 8'hf1 || astat_valid_mask_i[7]);
        end else if (sf_o == 4'hf) begin
            live_shifter_known = live_shifter_known && sb_valid_i;
        end
    end

    assign live_next_i_valid = dag_i_data_valid_i && dag_m_data_valid_i
        && dag_l_data_valid_i && live_dag_configuration_valid;
    assign live_exp_lo_destination = !se_valid_i || se_i == 8'hf1;

    always_comb begin
        active_write = write_direction_o;
        active_address = live_pm_address;
        active_address_valid = dag_i_data_valid_i;
        active_write_data = {memory_source_data_i, px_i};
        active_write_data_valid = memory_source_data_valid_i && px_valid_i;
        active_dag_configuration_valid = dag_i_data_valid_i
            && dag_m_data_valid_i && dag_l_data_valid_i
            && live_dag_configuration_valid;
        active_needs_recovery = needs_recovery;
        active_next_fetch_address = next_fetch_address_i;
        active_next_fetch_address_valid = next_fetch_address_valid_i;
        if (pending_q) begin
            active_write = pending_write_q;
            active_address = pending_address_q;
            active_address_valid = pending_address_valid_q;
            active_write_data = pending_write_data_q;
            active_write_data_valid = pending_write_data_valid_q;
            active_dag_configuration_valid =
                pending_dag_configuration_valid_q;
            active_needs_recovery = pending_needs_recovery_q
                || force_instruction_fetch_i;
            active_next_fetch_address = pending_next_fetch_address_q;
            active_next_fetch_address_valid =
                pending_next_fetch_address_valid_q;
        end
    end

    // The state-8 issue descriptor may be presented immediately, but native
    // PM completion cannot occur until a later state-7 edge.  Qualifying
    // architectural completion only from the captured pending descriptor
    // removes an impossible same-edge issue/complete bypass.
    assign data_request_active = !reset_i && (pending_q || issue);
    assign data_active = !reset_i && pending_q;
    assign data_complete = data_active && pm_cycle_complete_i;
    assign data_action_complete_o = data_complete;
    assign instruction_complete_o = !reset_i
        && ((data_complete
                && !(pending_needs_recovery_q || force_instruction_fetch_i))
            || (recovery_q && pm_cycle_complete_i));
    assign event_boundary_o = instruction_complete_o;
    assign transaction_active_o = !reset_i
        && (data_request_active || recovery_q);
    assign held_transaction_o = !reset_i && (pending_q || recovery_q);
    assign busy_o = !reset_i
        && ((data_request_active && !data_complete)
            || (data_complete && active_needs_recovery)
            || (recovery_q && !pm_cycle_complete_i));
    assign recovery_fetch_o = !reset_i && recovery_q;

    assign pm_select_o = transaction_active_o;
    assign pm_data_access_o = data_request_active;
    assign pm_read_o = !reset_i
        && (recovery_q || (data_request_active && !active_write));
    assign pm_write_o = data_request_active && active_write;
    assign pm_address_o = recovery_q
        ? (recovery_address_valid_q ? recovery_address_q : 14'h0000)
        : (data_request_active && active_address_valid
            ? active_address : 14'h0000);
    assign pm_address_valid_o = recovery_q
        ? recovery_address_valid_q
        : (data_request_active && active_address_valid);
    assign pm_write_data_valid_o = pm_write_o && active_write_data_valid;
    assign pm_write_data_o = pm_write_data_valid_o
        ? active_write_data : 24'h000000;
    assign fetched_instruction_valid_o = recovery_q
        && pm_cycle_complete_i && recovery_address_valid_q
        && pm_read_data_valid_i;
    assign fetched_instruction_o = fetched_instruction_valid_o
        ? pm_read_data_i : 24'h000000;

    assign shifter_result_known_o = data_complete
        && pending_shifter_known_q;
    assign dag_configuration_valid_o = data_request_active
        && active_dag_configuration_valid;
    assign i_write_o = data_complete;
    assign i_write_address_o = pending_i_address_q;
    assign i_write_data_o = pending_next_i_q;
    assign i_write_known_o = data_complete && pending_next_i_valid_q;
    assign dreg_write_o = data_complete && !pending_write_q;
    assign dreg_write_address_o = pending_memory_dreg_q;
    assign dreg_write_data_o = pm_read_data_i[23:8];
    assign dreg_write_known_o = dreg_write_o && pm_read_data_valid_i;
    assign px_write_o = dreg_write_o;
    assign px_write_data_o = pm_read_data_i[7:0];
    assign px_write_known_o = px_write_o && pm_read_data_valid_i;
    // Completion is reachable only from pending_q. Drive every architectural
    // action from that captured descriptor explicitly so synthesis cannot
    // retain an impossible live issue/decode-to-completion bypass.
    assign sr_write_o = data_complete && pending_shifter_known_q
        && pending_sr_write_q;
    assign se_write_o = data_complete && pending_shifter_known_q
        && pending_se_write_q;
    assign sb_write_o = data_complete && pending_shifter_known_q
        && pending_sb_write_q;
    assign ss_write_o = data_complete && pending_shifter_known_q
        && pending_ss_write_q;
    assign sr_result_o = sr_write_o ? pending_sr_result_q : 32'h00000000;
    assign se_result_o = se_write_o ? pending_se_result_q : 8'h00;
    assign sb_result_o = sb_write_o ? pending_sb_result_q : 5'h00;
    assign ss_result_o = ss_write_o ? pending_ss_result_q : 1'b0;
    assign active_sf_o = pending_sf_q;
    assign active_exp_lo_destination_o = pending_exp_lo_destination_q;

    adsp2100_shifter shifter (
        .sf_i(sf_o),
        .x_i(shifter_source_data_i),
        .shift_or_se_i(se_i),
        .sr_i(sr_i),
        .sb_i(sb_i),
        .av_i(astat_i[2]),
        .ac_i(astat_i[3]),
        .ss_i(astat_i[7]),
        .sr_result_o(live_sr_result),
        .sr_write_o(live_sr_write),
        .se_result_o(live_se_result),
        .se_write_o(live_se_write),
        .sb_result_o(live_sb_result),
        .sb_write_o(live_sb_write),
        .ss_result_o(live_ss_result),
        .ss_write_o(live_ss_write)
    );

    adsp2100_dag #(.BIT_REVERSE_CAPABLE(1'b0)) dag (
        .i_i(dag_i_data_i),
        .m_i(dag_m_data_i),
        .l_i(dag_l_data_i),
        .bit_reverse_enable_i(1'b0),
        .address_o(live_pm_address),
        .next_i_o(live_next_i),
        .base_o(unused_dag_base),
        .circular_o(unused_dag_circular),
        .configuration_valid_o(live_dag_configuration_valid)
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pending_q <= 1'b0;
            recovery_q <= 1'b0;
            recovery_address_q <= 14'h0000;
            recovery_address_valid_q <= 1'b0;
            pending_write_q <= 1'b0;
            pending_memory_dreg_q <= 4'h0;
            pending_i_address_q <= 3'h0;
            pending_address_q <= 14'h0000;
            pending_address_valid_q <= 1'b0;
            pending_write_data_q <= 24'h000000;
            pending_write_data_valid_q <= 1'b0;
            pending_next_i_q <= 14'h0000;
            pending_next_i_valid_q <= 1'b0;
            pending_dag_configuration_valid_q <= 1'b0;
            pending_shifter_known_q <= 1'b0;
            pending_sr_write_q <= 1'b0;
            pending_se_write_q <= 1'b0;
            pending_sb_write_q <= 1'b0;
            pending_ss_write_q <= 1'b0;
            pending_sr_result_q <= 32'h00000000;
            pending_se_result_q <= 8'h00;
            pending_sb_result_q <= 5'h00;
            pending_ss_result_q <= 1'b0;
            pending_sf_q <= 4'h0;
            pending_exp_lo_destination_q <= 1'b0;
            pending_needs_recovery_q <= 1'b0;
            pending_next_fetch_address_q <= 14'h0000;
            pending_next_fetch_address_valid_q <= 1'b0;
        end else begin
            if (recovery_q) begin
                if (pm_cycle_complete_i) begin
                    recovery_q <= 1'b0;
                end
            end else if (data_complete && active_needs_recovery) begin
                recovery_q <= 1'b1;
                recovery_address_q <= active_next_fetch_address;
                recovery_address_valid_q <=
                    active_next_fetch_address_valid;
            end

            if (data_complete) begin
                pending_q <= 1'b0;
            end else if (issue) begin
                pending_q <= 1'b1;
                pending_write_q <= write_direction_o;
                pending_memory_dreg_q <= memory_dreg_o;
                pending_i_address_q <= i_address_o;
                pending_address_q <= live_pm_address;
                pending_address_valid_q <= dag_i_data_valid_i;
                pending_write_data_q <= {memory_source_data_i, px_i};
                pending_write_data_valid_q <=
                    memory_source_data_valid_i && px_valid_i;
                pending_next_i_q <= live_next_i;
                pending_next_i_valid_q <= live_next_i_valid;
                pending_dag_configuration_valid_q <=
                    dag_i_data_valid_i && dag_m_data_valid_i
                    && dag_l_data_valid_i
                    && live_dag_configuration_valid;
                pending_shifter_known_q <= live_shifter_known;
                pending_sr_write_q <= live_sr_write;
                pending_se_write_q <= live_se_write;
                pending_sb_write_q <= live_sb_write;
                pending_ss_write_q <= live_ss_write;
                pending_sr_result_q <= live_sr_result;
                pending_se_result_q <= live_se_result;
                pending_sb_result_q <= live_sb_result;
                pending_ss_result_q <= live_ss_result;
                pending_sf_q <= sf_o;
                pending_exp_lo_destination_q <= live_exp_lo_destination;
                pending_needs_recovery_q <= needs_recovery;
                pending_next_fetch_address_q <= next_fetch_address_i;
                pending_next_fetch_address_valid_q <=
                    next_fetch_address_valid_i;
            end else if (pending_q && force_instruction_fetch_i) begin
                pending_needs_recovery_q <= 1'b1;
            end
        end
    end

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(pm_read_o && pm_write_o));
        assert (pm_select_o == (pm_read_o || pm_write_o));
        assert (!(sr_write_o && (se_write_o || sb_write_o)));
        assert (!(se_write_o && sb_write_o));
        if (recovery_fetch_o) begin
            assert (!data_action_complete_o);
            assert (!i_write_o && !dreg_write_o && !px_write_o);
            assert (!sr_write_o && !se_write_o && !sb_write_o && !ss_write_o);
        end
    end
endmodule

`default_nettype wire
