`default_nettype none

// Type 5 PM transaction/action client with no architectural storage.
// Operands arrive from one external architectural-state owner and all
// cycle-start results are retained until the routed PM completion.
module adsp2100_compute_pm_shared_state_client (
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

    input  logic [15:0] x_source_data_i,
    input  logic        x_source_data_valid_i,
    input  logic [15:0] y_dreg_data_i,
    input  logic        y_dreg_data_valid_i,
    input  logic [15:0] memory_source_data_i,
    input  logic        memory_source_data_valid_i,
    input  logic [15:0] af_i,
    input  logic        af_valid_i,
    input  logic [15:0] mf_i,
    input  logic        mf_valid_i,
    input  logic [39:0] mr_i,
    input  logic        mr_valid_i,
    input  logic [7:0]  astat_i,
    input  logic [7:0]  astat_valid_mask_i,
    input  logic [3:0]  mstat_i,
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

    output logic        compute_result_known_o,
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
    output logic        alu_write_o,
    output logic        mac_write_o,
    output logic        active_destination_feedback_o,
    output logic [4:0]  active_amf_o,
    output logic [15:0] alu_result_o,
    output logic [39:0] mac_result_o,
    output logic        alu_az_o,
    output logic        alu_an_o,
    output logic        alu_av_o,
    output logic        alu_ac_o,
    output logic        alu_as_write_o,
    output logic        alu_as_o,
    output logic        mac_mv_o
);
    logic issue;
    logic needs_recovery;
    logic pending_q;
    logic recovery_q;
    logic [13:0] recovery_address_q;
    logic recovery_address_valid_q;

    logic pending_write_q;
    logic pending_computation_enable_q;
    logic pending_is_mac_q;
    logic pending_destination_feedback_q;
    logic [4:0] pending_amf_q;
    logic [3:0] pending_memory_dreg_q;
    logic [2:0] pending_i_address_q;
    logic [13:0] pending_address_q;
    logic pending_address_valid_q;
    logic [23:0] pending_write_data_q;
    logic pending_write_data_valid_q;
    logic [13:0] pending_next_i_q;
    logic pending_next_i_valid_q;
    logic pending_dag_configuration_valid_q;
    logic pending_compute_known_q;
    logic [15:0] pending_alu_result_q;
    logic [39:0] pending_mac_result_q;
    logic pending_alu_az_q;
    logic pending_alu_an_q;
    logic pending_alu_av_q;
    logic pending_alu_ac_q;
    logic pending_alu_as_write_q;
    logic pending_alu_as_q;
    logic pending_mac_mv_q;
    logic pending_needs_recovery_q;
    logic [13:0] pending_next_fetch_address_q;
    logic pending_next_fetch_address_valid_q;

    // Type 5 computation spans the already-explicit native PM phases.  The
    // issue edge captures cycle-start operands; the following phase retains
    // the ALU/MAC result well before the state-7 completion edge.  This is an
    // implementation pipeline only and does not add an architectural cycle.
    logic compute_stage_valid_q;
    logic compute_stage_known_q;
    logic [4:0] compute_stage_amf_q;
    logic compute_stage_destination_feedback_q;
    logic [15:0] compute_stage_x_q;
    logic [15:0] compute_stage_y_q;
    logic [39:0] compute_stage_mr_q;
    logic compute_stage_carry_q;
    logic compute_stage_previous_av_q;
    logic compute_stage_sticky_av_q;
    logic compute_stage_saturate_ar_q;
    logic compute_stage_saturation_mv_q;

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

    logic [15:0] y_source_data;
    logic live_y_known;
    logic live_compute_known;
    logic alu_needs_x;
    logic alu_needs_y;
    logic alu_needs_carry;
    logic mac_needs_mr;
    logic alu_valid_unused;
    logic [15:0] alu_raw_result_unused;
    logic [15:0] live_alu_result;
    logic live_alu_az;
    logic live_alu_an;
    logic live_alu_av;
    logic live_alu_ac;
    logic live_alu_as_write;
    logic live_alu_as;
    logic mac_valid_unused;
    logic [39:0] mac_unrounded_unused;
    logic [39:0] live_mac_result;
    logic [15:0] mac_mf_result_unused;
    logic live_mac_mv;
    logic [39:0] saturated_mr_unused;
    logic [13:0] live_pm_address;
    logic [13:0] live_next_i;
    logic [13:0] unused_dag_base;
    logic unused_dag_circular;
    logic live_dag_configuration_valid;
    logic live_next_i_valid;
    logic unused_observation;

    assign unused_observation = ^{
        astat_i[7], astat_i[5:4], astat_i[1:0],
        astat_valid_mask_i[7:4], astat_valid_mask_i[1:0],
        mstat_i[1:0]
    };

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

    always_comb begin
        if (yop_o == 2'd3) begin
            y_source_data = 16'h0000;
            live_y_known = 1'b1;
        end else if (yop_o == 2'd2) begin
            y_source_data = is_mac_o ? mf_i : af_i;
            live_y_known = is_mac_o ? mf_valid_i : af_valid_i;
        end else begin
            y_source_data = y_dreg_data_i;
            live_y_known = y_dreg_data_valid_i;
        end
        alu_needs_x = !(amf_o == 5'h10 || amf_o == 5'h11
            || amf_o == 5'h14 || amf_o == 5'h15 || amf_o == 5'h18);
        alu_needs_y = !(amf_o == 5'h1b || amf_o == 5'h1f);
        alu_needs_carry = amf_o == 5'h12 || amf_o == 5'h16
            || amf_o == 5'h1a;
        mac_needs_mr = amf_o == 5'h02 || amf_o == 5'h03
            || amf_o >= 5'h08;
        live_compute_known = 1'b0;
        if (computation_enable_o) begin
            if (is_mac_o) begin
                live_compute_known = x_source_data_valid_i && live_y_known
                    && (!mac_needs_mr || mr_valid_i);
            end else begin
                live_compute_known = (!alu_needs_x
                    || x_source_data_valid_i)
                    && (!alu_needs_y || live_y_known)
                    && (!alu_needs_carry || astat_valid_mask_i[3])
                    && (!mstat_i[2] || astat_valid_mask_i[2]);
            end
        end
    end

    assign live_next_i_valid = dag_i_data_valid_i && dag_m_data_valid_i
        && dag_l_data_valid_i && live_dag_configuration_valid;

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

    assign compute_result_known_o = data_complete
        && pending_computation_enable_q && pending_compute_known_q;
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
    assign alu_write_o = data_complete && pending_computation_enable_q
        && !pending_is_mac_q;
    assign mac_write_o = data_complete && pending_computation_enable_q
        && pending_is_mac_q;
    assign active_destination_feedback_o = pending_destination_feedback_q;
    assign active_amf_o = pending_amf_q;
    assign alu_result_o = compute_result_known_o && !pending_is_mac_q
        ? pending_alu_result_q : 16'h0000;
    assign mac_result_o = compute_result_known_o && pending_is_mac_q
        ? pending_mac_result_q : 40'h0000000000;
    assign alu_az_o = pending_compute_known_q ? pending_alu_az_q : 1'b0;
    assign alu_an_o = pending_compute_known_q ? pending_alu_an_q : 1'b0;
    assign alu_av_o = pending_compute_known_q ? pending_alu_av_q : 1'b0;
    assign alu_ac_o = pending_compute_known_q ? pending_alu_ac_q : 1'b0;
    assign alu_as_write_o = pending_compute_known_q
        && pending_alu_as_write_q;
    assign alu_as_o = pending_compute_known_q ? pending_alu_as_q : 1'b0;
    assign mac_mv_o = pending_compute_known_q ? pending_mac_mv_q : 1'b0;

    adsp2100_alu alu (
        .amf_i(compute_stage_amf_q),
        .x_i(compute_stage_x_q),
        .y_i(compute_stage_y_q),
        .carry_i(compute_stage_carry_q),
        .previous_av_i(compute_stage_previous_av_q),
        .sticky_av_i(compute_stage_sticky_av_q),
        .saturate_ar_i(compute_stage_saturate_ar_q),
        .destination_is_ar_i(!compute_stage_destination_feedback_q),
        .valid_o(alu_valid_unused),
        .raw_result_o(alu_raw_result_unused),
        .destination_result_o(live_alu_result),
        .az_o(live_alu_az),
        .an_o(live_alu_an),
        .av_o(live_alu_av),
        .ac_o(live_alu_ac),
        .as_value_o(live_alu_as),
        .as_write_o(live_alu_as_write)
    );

    adsp2100_mac mac (
        .amf_i(compute_stage_amf_q),
        .x_i(compute_stage_x_q),
        .y_i(compute_stage_y_q),
        .mr_i(compute_stage_mr_q),
        .saturation_mv_i(compute_stage_saturation_mv_q),
        .valid_o(mac_valid_unused),
        .unrounded_result_o(mac_unrounded_unused),
        .result_o(live_mac_result),
        .mf_result_o(mac_mf_result_unused),
        .mv_o(live_mac_mv),
        .saturated_mr_o(saturated_mr_unused)
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
            pending_computation_enable_q <= 1'b0;
            pending_is_mac_q <= 1'b0;
            pending_destination_feedback_q <= 1'b0;
            pending_amf_q <= 5'h00;
            pending_memory_dreg_q <= 4'h0;
            pending_i_address_q <= 3'h0;
            pending_address_q <= 14'h0000;
            pending_address_valid_q <= 1'b0;
            pending_write_data_q <= 24'h000000;
            pending_write_data_valid_q <= 1'b0;
            pending_next_i_q <= 14'h0000;
            pending_next_i_valid_q <= 1'b0;
            pending_dag_configuration_valid_q <= 1'b0;
            pending_compute_known_q <= 1'b0;
            pending_alu_result_q <= 16'h0000;
            pending_mac_result_q <= 40'h0000000000;
            pending_alu_az_q <= 1'b0;
            pending_alu_an_q <= 1'b0;
            pending_alu_av_q <= 1'b0;
            pending_alu_ac_q <= 1'b0;
            pending_alu_as_write_q <= 1'b0;
            pending_alu_as_q <= 1'b0;
            pending_mac_mv_q <= 1'b0;
            pending_needs_recovery_q <= 1'b0;
            pending_next_fetch_address_q <= 14'h0000;
            pending_next_fetch_address_valid_q <= 1'b0;
            compute_stage_valid_q <= 1'b0;
            compute_stage_known_q <= 1'b0;
            compute_stage_amf_q <= 5'h00;
            compute_stage_destination_feedback_q <= 1'b0;
            compute_stage_x_q <= 16'h0000;
            compute_stage_y_q <= 16'h0000;
            compute_stage_mr_q <= 40'h0000000000;
            compute_stage_carry_q <= 1'b0;
            compute_stage_previous_av_q <= 1'b0;
            compute_stage_sticky_av_q <= 1'b0;
            compute_stage_saturate_ar_q <= 1'b0;
            compute_stage_saturation_mv_q <= 1'b0;
        end else begin
            compute_stage_valid_q <= 1'b0;
            if (compute_stage_valid_q) begin
                pending_compute_known_q <= compute_stage_known_q;
                pending_alu_result_q <= live_alu_result;
                pending_mac_result_q <= live_mac_result;
                pending_alu_az_q <= live_alu_az;
                pending_alu_an_q <= live_alu_an;
                pending_alu_av_q <= live_alu_av;
                pending_alu_ac_q <= live_alu_ac;
                pending_alu_as_write_q <= live_alu_as_write;
                pending_alu_as_q <= live_alu_as;
                pending_mac_mv_q <= live_mac_mv;
            end

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
                pending_computation_enable_q <= computation_enable_o;
                pending_is_mac_q <= is_mac_o;
                pending_destination_feedback_q <= destination_feedback_o;
                pending_amf_q <= amf_o;
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
                pending_compute_known_q <= 1'b0;
                pending_alu_result_q <= 16'h0000;
                pending_mac_result_q <= 40'h0000000000;
                pending_alu_az_q <= 1'b0;
                pending_alu_an_q <= 1'b0;
                pending_alu_av_q <= 1'b0;
                pending_alu_ac_q <= 1'b0;
                pending_alu_as_write_q <= 1'b0;
                pending_alu_as_q <= 1'b0;
                pending_mac_mv_q <= 1'b0;
                pending_needs_recovery_q <= needs_recovery;
                pending_next_fetch_address_q <= next_fetch_address_i;
                pending_next_fetch_address_valid_q <=
                    next_fetch_address_valid_i;
                compute_stage_valid_q <= computation_enable_o;
                compute_stage_known_q <= live_compute_known;
                compute_stage_amf_q <= amf_o;
                compute_stage_destination_feedback_q <=
                    destination_feedback_o;
                compute_stage_x_q <= x_source_data_i;
                compute_stage_y_q <= y_source_data;
                compute_stage_mr_q <= mr_i;
                compute_stage_carry_q <= astat_i[3];
                compute_stage_previous_av_q <= astat_i[2];
                compute_stage_sticky_av_q <= mstat_i[2];
                compute_stage_saturate_ar_q <= mstat_i[3];
                compute_stage_saturation_mv_q <= astat_i[6];
            end else if (pending_q && force_instruction_fetch_i) begin
                pending_needs_recovery_q <= 1'b1;
            end
        end
    end

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(pm_read_o && pm_write_o));
        assert (pm_select_o == (pm_read_o || pm_write_o));
        if (recovery_fetch_o) begin
            assert (!data_action_complete_o);
            assert (!i_write_o && !dreg_write_o && !px_write_o);
            assert (!alu_write_o && !mac_write_o);
        end
    end
endmodule

`default_nettype wire
