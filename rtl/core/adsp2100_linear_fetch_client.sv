`default_nettype none

// Bounded steady-state ordinary-fetch architectural client.
//
// The client retains the current instruction and all supported architectural
// state.  It presents PC+1 until an external PM owner accepts the request,
// then retires only when that owner routes the corresponding completion back.
// Native PM pin phases and multi-owner arbitration are deliberately external.
module adsp2100_linear_fetch_client (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        instruction_issue_inhibit_i,
    input  logic        bus_relinquished_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,

    input  logic        pm_request_accepted_i,
    input  logic        pm_completion_event_i,
    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [5:0]  probe_code_i,

    output logic        issue_boundary_o,
    output logic        instruction_setup_accepted_o,
    output logic        fetch_request_presented_o,
    output logic [13:0] fetch_address_o,
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
    output logic        count_stack_overflow_o
);
    import adsp2100_pkg::*;

    logic [13:0] pc_q;
    logic [23:0] opcode_q;
    logic instruction_valid_q;
    logic pending_q;

    logic nop_valid;
    logic type6_valid;
    logic [3:0] type6_destination;
    logic [15:0] type6_data;
    logic type7_class_valid;
    logic type7_action_valid;
    logic type7_invalid_subencoding;
    logic [1:0] type7_group_unused;
    logic [3:0] type7_index_unused;
    logic [5:0] type7_code;
    logic [13:0] type7_data;
    logic type7_present_unused;
    logic type7_writable_unused;
    logic type7_dreg_unused;
    logic type7_reserved_unused;
    logic type7_read_only_unused;
    logic type18_valid;
    logic [1:0] type18_mode_sr;
    logic [1:0] type18_mode_br;
    logic [1:0] type18_mode_ol;
    logic [1:0] type18_mode_as;
    logic type18_has_effect_unused;
    logic type18_has_alias_unused;
    logic type17_class_valid;
    logic type17_action_valid;
    logic type17_invalid_subencoding;
    logic [1:0] type17_destination_group_unused;
    logic [1:0] type17_source_group_unused;
    logic [3:0] type17_destination_index_unused;
    logic [3:0] type17_source_index_unused;
    logic [5:0] type17_destination_code;
    logic [5:0] type17_source_code;
    logic type17_destination_present_unused;
    logic type17_destination_writable_unused;
    logic type17_source_valid_unused;
    logic type9_class_valid;
    logic type9_action_valid;
    logic type9_nop_action;
    logic type9_condition_true;
    logic type9_is_mac;
    logic type9_is_alu;
    logic type9_destination_feedback;
    logic [3:0] type9_x_source_dreg;
    logic [3:0] type9_y_source_dreg;
    logic [15:0] type9_x_source_data_unused;
    logic [15:0] type9_y_source_data_unused;
    logic type9_alu_write;
    logic [15:0] type9_alu_result;
    logic type9_alu_az;
    logic type9_alu_an;
    logic type9_alu_av;
    logic type9_alu_ac;
    logic type9_alu_as_write;
    logic type9_alu_as;
    logic type9_mac_write;
    logic [39:0] type9_mac_result;
    logic type9_mac_mv;
    logic type25_action_valid;
    logic type25_condition_mv_unused;
    logic type25_mr_write;
    logic [39:0] type25_mr_result;
    logic type14_class_valid;
    logic type14_action_valid;
    logic type14_unsupported_subencoding;
    logic type14_unverified_unused_x_unused;
    logic type14_unavailable_xop_unused;
    logic type14_destination_collision_unused;
    logic [3:0] type14_shifter_source_dreg;
    logic [3:0] type14_move_destination_dreg;
    logic [3:0] type14_move_source_dreg;
    logic type14_move_write;
    logic [15:0] type14_move_data;
    logic type14_sr_write;
    logic [31:0] type14_sr_result;
    logic type14_se_write;
    logic [7:0] type14_se_result;
    logic type14_sb_write;
    logic [4:0] type14_sb_result;
    logic type14_ss_write;
    logic type14_ss_result;
    logic type15_class_valid;
    logic type15_action_valid;
    logic type15_unsupported_subencoding;
    logic [3:0] type15_source_dreg;
    logic type15_sr_write;
    logic [31:0] type15_sr_result;
    logic type16_class_valid;
    logic type16_action_valid;
    logic type16_unsupported_subencoding;
    logic type16_condition_true;
    logic [3:0] type16_source_dreg;
    logic type16_sr_write;
    logic [31:0] type16_sr_result;
    logic type16_se_write;
    logic [7:0] type16_se_result;
    logic type16_sb_write;
    logic [4:0] type16_sb_result;
    logic type16_ss_write;
    logic type16_ss_result;
    logic supported_instruction;
    logic state_write;
    logic [5:0] state_write_code;
    logic [15:0] state_write_data;
    logic state_invalid_setup;
    logic [5:0] state_read_code;
    logic [15:0] state_read_data;
    logic [15:0] state_dreg_read_data;
    logic state_count_push_unused;
    logic [13:0] state_count_push_data_unused;
    logic state_not_counter_expired;
    logic state_bit_reverse_unused;
    logic state_overflow_latch;
    logic state_saturate_ar;
    logic [15:0] state_af;
    logic [15:0] state_mf;
    logic [39:0] state_mr;
    logic [7:0] state_se;
    logic [4:0] state_sb;
    logic [31:0] state_sr;
    logic unused_observation;

    assign issue_boundary_o = (
        !reset_i && !instruction_issue_inhibit_i
        && !bus_relinquished_i && phase_advance_i
        && phase_i == PHASE_STATE_8
    );
    assign instruction_setup_accepted_o = (
        issue_boundary_o && instruction_setup_i
        && !instruction_valid_q && !pending_q
    );
    assign phase_conflict_o = (
        !reset_i && instruction_setup_i && !issue_boundary_o
    );
    assign integration_conflict_o = (
        !reset_i && instruction_setup_i
        && (instruction_valid_q || pending_q)
    );

    assign nop_valid = opcode_q == 24'h000000;
    assign supported_instruction = (
        nop_valid || type6_valid || type7_action_valid || type17_action_valid
        || type18_valid || type9_action_valid || type15_action_valid
        || type16_action_valid || type14_action_valid || type25_action_valid
    );
    assign reserved_subencoding_o = (
        issue_boundary_o && instruction_valid_q
        && (
            (type7_class_valid && type7_invalid_subencoding)
            || (type17_class_valid && type17_invalid_subencoding)
            || (type14_class_valid && type14_unsupported_subencoding)
            || (type15_class_valid && type15_unsupported_subencoding)
            || (type16_class_valid && type16_unsupported_subencoding)
        )
    );
    assign unsupported_instruction_o = (
        issue_boundary_o && instruction_valid_q
        && !supported_instruction && !reserved_subencoding_o
    );
    assign fetch_address_o = pc_q + 14'h0001;
    assign fetch_request_presented_o = (
        issue_boundary_o && instruction_valid_q
        && supported_instruction && !pending_q
        && !instruction_setup_i
    );
    assign instruction_issue_o = pm_request_accepted_i;
    assign retire_event_o = pending_q && pm_completion_event_i;

    assign state_write = retire_event_o && (
        type6_valid || type7_action_valid || type17_action_valid
    );
    assign state_write_code = type6_valid
        ? {2'b00, type6_destination}
        : (
            type7_action_valid ? type7_code
            : type17_destination_code
        );
    assign state_write_data = type6_valid
        ? type6_data
        : (
            type7_action_valid
                ? {2'b00, type7_data}
                : state_read_data
        );
    always_comb begin
        state_read_code = {2'b00, type9_x_source_dreg};
        if (type14_action_valid) begin
            state_read_code = {2'b00, type14_shifter_source_dreg};
        end
        if (type16_action_valid) begin
            state_read_code = {2'b00, type16_source_dreg};
        end
        if (type15_action_valid) begin
            state_read_code = {2'b00, type15_source_dreg};
        end
        if (type17_action_valid) begin
            state_read_code = type17_source_code;
        end
    end

    assign instruction_valid_o = instruction_valid_q;
    assign transaction_pending_o = pending_q;
    assign pc_o = pc_q;
    assign opcode_o = opcode_q;
    assign provisional_source_extension_o = (
        retire_event_o && type17_action_valid
        && (type17_source_code[5:4] == 2'b11)
        && (type17_source_code[3:0] <= 4'd4)
    );

    adsp2100_load_dreg_immediate_decode type6_decode (
        .opcode_i(opcode_q),
        .valid_o(type6_valid),
        .destination_dreg_o(type6_destination),
        .immediate_data_o(type6_data)
    );

    adsp2100_load_non_dreg_immediate_decode type7_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type7_class_valid),
        .action_valid_o(type7_action_valid),
        .invalid_subencoding_o(type7_invalid_subencoding),
        .register_group_o(type7_group_unused),
        .register_index_o(type7_index_unused),
        .register_code_o(type7_code),
        .immediate_data_o(type7_data),
        .register_present_o(type7_present_unused),
        .register_writable_o(type7_writable_unused),
        .data_register_destination_o(type7_dreg_unused),
        .reserved_destination_o(type7_reserved_unused),
        .read_only_destination_o(type7_read_only_unused)
    );

    adsp2100_mode_control_decode type18_decode (
        .opcode_i(opcode_q),
        .valid_o(type18_valid),
        .mode_sr_o(type18_mode_sr),
        .mode_br_o(type18_mode_br),
        .mode_ol_o(type18_mode_ol),
        .mode_as_o(type18_mode_as),
        .has_effect_o(type18_has_effect_unused),
        .has_no_change_one_alias_o(type18_has_alias_unused)
    );

    adsp2100_internal_move_decode type17_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type17_class_valid),
        .move_valid_o(type17_action_valid),
        .invalid_subencoding_o(type17_invalid_subencoding),
        .destination_group_o(type17_destination_group_unused),
        .source_group_o(type17_source_group_unused),
        .destination_index_o(type17_destination_index_unused),
        .source_index_o(type17_source_index_unused),
        .destination_code_o(type17_destination_code),
        .source_code_o(type17_source_code),
        .destination_present_o(type17_destination_present_unused),
        .destination_writable_o(type17_destination_writable_unused),
        .source_valid_o(type17_source_valid_unused)
    );

    adsp2100_conditional_compute_action type9_action (
        .opcode_i(opcode_q),
        .not_counter_expired_i(state_not_counter_expired),
        .x_dreg_data_i(state_read_data),
        .y_dreg_data_i(state_dreg_read_data),
        .af_i(state_af),
        .mf_i(state_mf),
        .mr_i(state_mr),
        .astat_i(astat_o),
        .overflow_latch_i(state_overflow_latch),
        .saturate_ar_i(state_saturate_ar),
        .class_valid_o(type9_class_valid),
        .action_valid_o(type9_action_valid),
        .nop_action_o(type9_nop_action),
        .condition_true_o(type9_condition_true),
        .is_mac_o(type9_is_mac),
        .is_alu_o(type9_is_alu),
        .destination_feedback_o(type9_destination_feedback),
        .x_source_dreg_o(type9_x_source_dreg),
        .y_source_dreg_o(type9_y_source_dreg),
        .x_source_data_o(type9_x_source_data_unused),
        .y_source_data_o(type9_y_source_data_unused),
        .alu_write_o(type9_alu_write),
        .alu_result_o(type9_alu_result),
        .alu_az_o(type9_alu_az),
        .alu_an_o(type9_alu_an),
        .alu_av_o(type9_alu_av),
        .alu_ac_o(type9_alu_ac),
        .alu_as_write_o(type9_alu_as_write),
        .alu_as_o(type9_alu_as),
        .mac_write_o(type9_mac_write),
        .mac_result_o(type9_mac_result),
        .mac_mv_o(type9_mac_mv)
    );

    adsp2100_shift_move_action type14_action (
        .opcode_i(opcode_q),
        .shifter_source_data_i(state_read_data),
        .move_source_data_i(state_dreg_read_data),
        .sr_i(state_sr),
        .se_i(state_se),
        .sb_i(state_sb),
        .astat_i(astat_o),
        .class_valid_o(type14_class_valid),
        .action_valid_o(type14_action_valid),
        .unsupported_subencoding_o(type14_unsupported_subencoding),
        .unverified_unused_x_o(type14_unverified_unused_x_unused),
        .unavailable_xop_o(type14_unavailable_xop_unused),
        .destination_collision_o(type14_destination_collision_unused),
        .shifter_source_dreg_o(type14_shifter_source_dreg),
        .move_destination_dreg_o(type14_move_destination_dreg),
        .move_source_dreg_o(type14_move_source_dreg),
        .move_write_o(type14_move_write),
        .move_data_o(type14_move_data),
        .sr_write_o(type14_sr_write),
        .sr_result_o(type14_sr_result),
        .se_write_o(type14_se_write),
        .se_result_o(type14_se_result),
        .sb_write_o(type14_sb_write),
        .sb_result_o(type14_sb_result),
        .ss_write_o(type14_ss_write),
        .ss_result_o(type14_ss_result)
    );

    adsp2100_mr_saturation_action type25_action (
        .opcode_i(opcode_q),
        .mr_i(state_mr),
        .mv_i(astat_o[6]),
        .action_valid_o(type25_action_valid),
        .condition_mv_o(type25_condition_mv_unused),
        .mr_write_o(type25_mr_write),
        .mr_result_o(type25_mr_result)
    );

    adsp2100_immediate_shift_action type15_action (
        .opcode_i(opcode_q),
        .source_data_i(state_read_data),
        .sr_i(state_sr),
        .class_valid_o(type15_class_valid),
        .action_valid_o(type15_action_valid),
        .unsupported_subencoding_o(type15_unsupported_subencoding),
        .source_dreg_o(type15_source_dreg),
        .sr_write_o(type15_sr_write),
        .sr_result_o(type15_sr_result)
    );

    adsp2100_conditional_shift_action type16_action (
        .opcode_i(opcode_q),
        .not_counter_expired_i(state_not_counter_expired),
        .source_data_i(state_read_data),
        .sr_i(state_sr),
        .se_i(state_se),
        .sb_i(state_sb),
        .astat_i(astat_o),
        .class_valid_o(type16_class_valid),
        .action_valid_o(type16_action_valid),
        .unsupported_subencoding_o(type16_unsupported_subencoding),
        .condition_true_o(type16_condition_true),
        .source_dreg_o(type16_source_dreg),
        .sr_write_o(type16_sr_write),
        .sr_result_o(type16_sr_result),
        .se_write_o(type16_se_write),
        .se_result_o(type16_se_result),
        .sb_write_o(type16_sb_write),
        .sb_result_o(type16_sb_result),
        .ss_write_o(type16_ss_write),
        .ss_result_o(type16_ss_result)
    );

    adsp2100_architectural_state state (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .move_write_i(state_write),
        .move_data_valid_i(1'b1),
        .move_code_i(state_write_code),
        .move_data_i(state_write_data),
        .read_code_i(state_read_code),
        .read_data_o(state_read_data),
        .probe_code_i(probe_code_i),
        .probe_data_o(probe_data_o),
        .dreg_read_address_i(
            type14_action_valid
                ? type14_move_source_dreg : type9_y_source_dreg
        ),
        .dreg_read_data_o(state_dreg_read_data),
        .dreg_write_enable_1_i(retire_event_o && type14_move_write),
        .dreg_write_address_1_i(type14_move_destination_dreg),
        .dreg_write_data_1_i(type14_move_data),
        .dreg_write_enable_2_i(1'b0),
        .dreg_write_address_2_i(4'h0),
        .dreg_write_data_2_i(16'h0000),
        .alu_write_enable_i(retire_event_o && type9_alu_write),
        .alu_destination_feedback_i(type9_destination_feedback),
        .alu_result_i(type9_alu_result),
        .mac_write_enable_i(
            retire_event_o && (type9_mac_write || type25_mr_write)
        ),
        .mac_destination_feedback_i(
            type25_mr_write ? 1'b0 : type9_destination_feedback
        ),
        .mac_result_i(
            type25_mr_write ? type25_mr_result : type9_mac_result
        ),
        .shifter_sr_write_enable_i(
            retire_event_o
            && (type14_sr_write || type15_sr_write || type16_sr_write)
        ),
        .shifter_sr_result_i(
            type14_sr_write
                ? type14_sr_result
                : (type15_sr_write ? type15_sr_result : type16_sr_result)
        ),
        .shifter_se_write_enable_i(
            retire_event_o && (type14_se_write || type16_se_write)
        ),
        .shifter_se_result_i(
            type14_se_write ? type14_se_result : type16_se_result
        ),
        .shifter_sb_write_enable_i(
            retire_event_o && (type14_sb_write || type16_sb_write)
        ),
        .shifter_sb_result_i(
            type14_sb_write ? type14_sb_result : type16_sb_result
        ),
        .dag_i_write_enable_i(1'b0),
        .dag_i_write_address_i(3'b000),
        .dag_i_write_data_i(14'h0000),
        .dag_i_write_result_valid_i(1'b0),
        .mode_sr_i(
            retire_event_o && type18_valid ? type18_mode_sr : 2'b00
        ),
        .mode_br_i(
            retire_event_o && type18_valid ? type18_mode_br : 2'b00
        ),
        .mode_ol_i(
            retire_event_o && type18_valid ? type18_mode_ol : 2'b00
        ),
        .mode_as_i(
            retire_event_o && type18_valid ? type18_mode_as : 2'b00
        ),
        .alu_status_write_enable_i(retire_event_o && type9_alu_write),
        .alu_az_i(type9_alu_az),
        .alu_an_i(type9_alu_an),
        .alu_av_i(type9_alu_av),
        .alu_ac_i(type9_alu_ac),
        .alu_as_write_enable_i(type9_alu_as_write),
        .alu_as_i(type9_alu_as),
        .divide_status_write_enable_i(1'b0),
        .divide_aq_i(1'b0),
        .mac_status_write_enable_i(retire_event_o && type9_mac_write),
        .mac_mv_i(type9_mac_mv),
        .shifter_status_write_enable_i(
            retire_event_o && (type14_ss_write || type16_ss_write)
        ),
        .shifter_ss_i(type14_ss_write ? type14_ss_result : type16_ss_result),
        .invalid_move_write_o(state_invalid_setup),
        .internal_conflict_o(internal_conflict_o),
        .count_stack_push_o(state_count_push_unused),
        .count_stack_push_data_o(state_count_push_data_unused),
        .count_stack_depth_o(count_stack_depth_o),
        .count_stack_overflow_o(count_stack_overflow_o),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .cntr_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .not_counter_expired_o(state_not_counter_expired),
        .px_o(px_o),
        .sstat_o(sstat_o),
        .alternate_bank_o(alternate_bank_o),
        .bit_reverse_o(state_bit_reverse_unused),
        .overflow_latch_o(state_overflow_latch),
        .saturate_ar_o(state_saturate_ar),
        .af_o(state_af),
        .mf_o(state_mf),
        .mr_o(state_mr),
        .se_o(state_se),
        .sb_o(state_sb),
        .sr_o(state_sr)
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pc_q <= 14'h0004;
            opcode_q <= 24'h000000;
            instruction_valid_q <= 1'b0;
            pending_q <= 1'b0;
        end else begin
            if (pm_request_accepted_i) begin
                pending_q <= 1'b1;
            end
            if (retire_event_o) begin
                pc_q <= fetch_address_o;
                opcode_q <= pmd_read_data_i;
                instruction_valid_q <= pmd_read_data_valid_i;
                pending_q <= 1'b0;
            end
            if (instruction_setup_accepted_o) begin
                pc_q <= instruction_setup_pc_i;
                opcode_q <= instruction_setup_opcode_i;
                instruction_valid_q <= 1'b1;
                pending_q <= 1'b0;
            end
        end
    end

    assign unused_observation = ^{
        type7_group_unused, type7_index_unused, type7_present_unused,
        type7_writable_unused, type7_dreg_unused, type7_reserved_unused,
        type7_read_only_unused, type18_has_effect_unused,
        type18_has_alias_unused, type17_destination_group_unused,
        type17_source_group_unused, type17_destination_index_unused,
        type17_source_index_unused, type17_destination_present_unused,
        type17_destination_writable_unused, type17_source_valid_unused,
        type9_class_valid, type9_nop_action, type9_condition_true,
        type9_is_mac, type9_is_alu, type9_x_source_data_unused,
        type9_y_source_data_unused, type16_condition_true,
        type25_condition_mv_unused,
        type14_unverified_unused_x_unused, type14_unavailable_xop_unused,
        type14_destination_collision_unused,
        state_invalid_setup,
        state_count_push_unused, state_count_push_data_unused,
        state_bit_reverse_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(retire_event_o && !pending_q));
        assert (!(instruction_issue_o && !fetch_request_presented_o));
        if (instruction_issue_o) begin
            assert (issue_boundary_o);
        end
        if (instruction_issue_inhibit_i || bus_relinquished_i) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
        if (retire_event_o) begin
            assert (phase_i == PHASE_STATE_7 && phase_advance_i);
        end
        if (provisional_source_extension_o) begin
            assert (retire_event_o);
        end
        if (reserved_subencoding_o || unsupported_instruction_o) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
    end
`endif
endmodule

`default_nettype wire
