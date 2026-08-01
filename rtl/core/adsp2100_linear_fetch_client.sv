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
    logic [3:0] type18_mstat_next;
    logic type17_class_valid;
    logic type17_action_valid;
    logic type17_invalid_subencoding;
    logic [1:0] type17_destination_group_unused;
    logic [1:0] type17_source_group_unused;
    logic [3:0] type17_destination_index_unused;
    logic [3:0] type17_source_index_unused;
    logic [5:0] type17_destination_code_unused;
    logic [5:0] type17_source_code_unused;
    logic type17_destination_present_unused;
    logic type17_destination_writable_unused;
    logic type17_source_valid_unused;
    logic supported_instruction;
    logic state_write;
    logic [5:0] state_write_code;
    logic [15:0] state_write_data;

    logic state_class_valid_unused;
    logic state_boundary_valid_unused;
    logic state_invalid_opcode_unused;
    logic state_invalid_subencoding_unused;
    logic state_invalid_setup;
    logic state_integration_conflict_unused;
    logic [5:0] state_source_code_unused;
    logic [5:0] state_destination_code_unused;
    logic [15:0] state_source_data_unused;
    logic state_source_extension;
    logic state_count_push_unused;
    logic [13:0] state_count_push_data_unused;
    logic state_pm_data_access_unused;
    logic state_dm_access_unused;
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
        || type18_valid
    );
    assign reserved_subencoding_o = (
        issue_boundary_o && instruction_valid_q
        && (
            (type7_class_valid && type7_invalid_subencoding)
            || (type17_class_valid && type17_invalid_subencoding)
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
        type6_valid || type7_action_valid || type18_valid
    );
    assign state_write_code = type6_valid
        ? {2'b00, type6_destination}
        : (type7_action_valid ? type7_code : 6'h31);
    assign state_write_data = type6_valid
        ? type6_data
        : (
            type7_action_valid
                ? {2'b00, type7_data}
                : {12'h000, type18_mstat_next}
        );

    assign instruction_valid_o = instruction_valid_q;
    assign transaction_pending_o = pending_q;
    assign pc_o = pc_q;
    assign opcode_o = opcode_q;
    assign alternate_bank_o = mstat_o[0];
    assign provisional_source_extension_o = state_source_extension;

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
        .destination_code_o(type17_destination_code_unused),
        .source_code_o(type17_source_code_unused),
        .destination_present_o(type17_destination_present_unused),
        .destination_writable_o(type17_destination_writable_unused),
        .source_valid_o(type17_source_valid_unused)
    );

    always_comb begin
        type18_mstat_next = mstat_o;
        if (type18_mode_sr[1]) begin
            type18_mstat_next[0] = type18_mode_sr[0];
        end
        if (type18_mode_br[1]) begin
            type18_mstat_next[1] = type18_mode_br[0];
        end
        if (type18_mode_ol[1]) begin
            type18_mstat_next[2] = type18_mode_ol[0];
        end
        if (type18_mode_as[1]) begin
            type18_mstat_next[3] = type18_mode_as[0];
        end
    end

    adsp2100_internal_move_slice state (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(retire_event_o && type17_action_valid),
        .opcode_i(opcode_q),
        .setup_write_i(state_write),
        .setup_data_valid_i(1'b1),
        .setup_code_i(state_write_code),
        .setup_data_i(state_write_data),
        .probe_code_i(probe_code_i),
        .probe_data_o(probe_data_o),
        .class_valid_o(state_class_valid_unused),
        .boundary_valid_o(state_boundary_valid_unused),
        .invalid_opcode_o(state_invalid_opcode_unused),
        .invalid_subencoding_o(state_invalid_subencoding_unused),
        .invalid_setup_o(state_invalid_setup),
        .integration_conflict_o(state_integration_conflict_unused),
        .internal_conflict_o(internal_conflict_o),
        .source_code_o(state_source_code_unused),
        .destination_code_o(state_destination_code_unused),
        .source_data_o(state_source_data_unused),
        .source_extension_provisional_o(state_source_extension),
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
        .px_o(px_o),
        .sstat_o(sstat_o),
        .pm_data_access_o(state_pm_data_access_unused),
        .dm_access_o(state_dm_access_unused)
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
        type17_source_index_unused, type17_destination_code_unused,
        type17_source_code_unused, type17_destination_present_unused,
        type17_destination_writable_unused, type17_source_valid_unused,
        state_class_valid_unused, state_boundary_valid_unused,
        state_invalid_opcode_unused, state_invalid_subencoding_unused,
        state_invalid_setup, state_integration_conflict_unused,
        state_source_code_unused, state_destination_code_unused,
        state_source_data_unused, state_count_push_unused,
        state_count_push_data_unused, state_pm_data_access_unused,
        state_dm_access_unused
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
