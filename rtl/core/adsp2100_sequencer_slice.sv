`default_nettype none

module adsp2100_sequencer_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [13:0] pc_i,
    input  logic        do_until_i,
    input  logic [13:0] do_end_i,
    input  logic [3:0]  do_condition_i,
    input  logic [1:0]  explicit_flow_i,
    input  logic [3:0]  explicit_condition_i,
    input  logic [13:0] explicit_target_i,
    input  logic        counter_load_i,
    input  logic [13:0] counter_load_data_i,
    input  logic        pc_manual_pop_i,
    input  logic        count_manual_pop_i,
    input  logic        loop_manual_pop_i,
    input  logic        az_i,
    input  logic        an_i,
    input  logic        av_i,
    input  logic        ac_i,
    input  logic        as_i,
    input  logic        mv_i,

    output logic [13:0] next_pc_o,
    output logic        boundary_valid_o,
    output logic        integration_conflict_o,
    output logic        unsupported_call_ce_o,
    output logic        invalid_counter_condition_o,
    output logic        invalid_loop_context_o,
    output logic        invalid_return_context_o,
    output logic        unsupported_do_at_loop_end_o,
    output logic        explicit_condition_true_o,
    output logic        loop_termination_true_o,
    output logic        explicit_transfer_o,
    output logic        loop_back_o,
    output logic        loop_exit_o,

    output logic [13:0] cntr_data_o,
    output logic        cntr_valid_o,
    output logic        counter_condition_valid_o,
    output logic        counter_expired_o,
    output logic        not_counter_expired_o,
    output logic        counter_test_o,
    output logic        counter_decrement_o,
    output logic        counter_restore_o,
    output logic        counter_empty_invalidate_o,
    output logic        counter_invalid_test_o,
    output logic        counter_empty_manual_pop_o,

    output logic [13:0] pc_top_data_o,
    output logic [13:0] count_top_data_o,
    output logic [17:0] loop_top_data_o,
    output logic [2:0]  stack_top_valid_o,
    output logic [4:0]  pc_depth_o,
    output logic [2:0]  count_depth_o,
    output logic [2:0]  loop_depth_o,
    output logic [2:0]  stack_empty_o,
    output logic [2:0]  stack_overflow_o,
    output logic [2:0]  stack_pop_valid_o,
    output logic [2:0]  stack_push_accepted_o,
    output logic [2:0]  stack_overflow_event_o,
    output logic [2:0]  stack_empty_pop_o,
    output logic [7:0]  sstat_fragment_o,

    output logic        pc_stack_push_o,
    output logic        pc_stack_pop_o,
    output logic        count_stack_push_o,
    output logic        count_stack_pop_o,
    output logic        loop_stack_push_o,
    output logic        loop_stack_pop_o,
    output logic        internal_storage_conflict_o
);
    localparam logic [1:0] FLOW_NONE = 2'b00;
    localparam logic [1:0] FLOW_JUMP = 2'b01;
    localparam logic [1:0] FLOW_CALL = 2'b10;
    localparam logic [1:0] FLOW_RETURN = 2'b11;

    logic [13:0] sequential_pc;
    logic        raw_not_counter_expired;
    logic        raw_counter_expired;
    logic        loop_active;
    logic [13:0] loop_end;
    logic [3:0]  loop_condition;
    logic        loop_uses_counter;
    logic        loop_if_predicate;
    logic        explicit_uses_counter;
    logic        instruction_class_conflict;
    logic        manual_control_conflict;
    logic        empty_taken_return;
    logic        unsupported_boundary;

    logic        raw_explicit_taken;
    logic [13:0] raw_explicit_target;
    logic        raw_flow_loop_active;
    logic [13:0] raw_next_pc;
    logic        raw_pc_stack_push;
    logic [13:0] raw_pc_stack_push_value;
    logic        raw_pc_stack_pop;
    logic        raw_loop_stack_pop;
    logic        raw_flow_count_stack_pop;
    logic        raw_loop_counter_test;
    logic        raw_loop_back;
    logic        raw_loop_exit;
    logic        raw_explicit_transfer;

    logic        raw_jump_counter_test;
    logic        raw_counter_test;
    logic [1:0]  raw_counter_action_count;
    logic        raw_do_push;
    logic        raw_pc_push;
    logic        raw_pc_pop;
    logic        raw_count_push;
    logic        raw_count_pop;
    logic        raw_loop_push;
    logic        raw_loop_pop;
    logic        flow_count_pop_mismatch;

    logic        counter_count_push;
    logic [13:0] counter_count_push_data;
    logic        counter_count_pop;
    logic        counter_write_conflict;
    logic        stack_write_conflict;

    logic        pc_top_valid;
    logic        count_top_valid;
    logic        loop_top_valid;
    logic        pc_pop_valid;
    logic        count_pop_valid;
    logic        loop_pop_valid;
    logic        pc_empty;
    logic        count_empty;
    logic        loop_empty;
    logic        pc_overflow;
    logic        count_overflow;
    logic        loop_overflow;
    logic        pc_push_accepted;
    logic        count_push_accepted;
    logic        loop_push_accepted;
    logic        pc_overflow_event;
    logic        count_overflow_event;
    logic        loop_overflow_event;
    logic        pc_empty_pop;
    logic        count_empty_pop;
    logic        loop_empty_pop;

    assign sequential_pc = pc_i + 14'h0001;
    assign raw_not_counter_expired = (
        cntr_valid_o
        && (cntr_data_o != 14'h0001)
    );
    assign raw_counter_expired = (
        cntr_valid_o
        && (cntr_data_o == 14'h0001)
    );
    assign loop_active = loop_top_valid;
    assign loop_end = loop_top_data_o[13:0];
    assign loop_condition = loop_top_data_o[17:14];
    assign loop_uses_counter = loop_condition == 4'he;
    assign loop_termination_true_o = ~loop_if_predicate;
    assign explicit_uses_counter = (
        (explicit_flow_i != FLOW_NONE)
        && (explicit_condition_i == 4'he)
    );

    assign unsupported_call_ce_o = (
        (explicit_flow_i == FLOW_CALL)
        && (explicit_condition_i == 4'he)
    );
    assign invalid_counter_condition_o = (
        !cntr_valid_o
        && (
            explicit_uses_counter
            || (
                loop_active
                && loop_uses_counter
            )
        )
    );
    assign invalid_loop_context_o = (
        loop_active
        && (
            !pc_top_valid
            || (
                loop_uses_counter
                && !cntr_valid_o
            )
        )
    );
    assign unsupported_do_at_loop_end_o = (
        do_until_i
        && loop_active
        && (pc_i == loop_end)
    );
    assign instruction_class_conflict = (
        do_until_i
        && (explicit_flow_i != FLOW_NONE)
    );
    assign manual_control_conflict = (
        (
            pc_manual_pop_i
            || count_manual_pop_i
            || loop_manual_pop_i
        )
        && (
            do_until_i
            || (explicit_flow_i != FLOW_NONE)
        )
    );
    assign empty_taken_return = (
        (explicit_flow_i == FLOW_RETURN)
        && explicit_condition_true_o
        && !pc_top_valid
    );
    assign invalid_return_context_o = empty_taken_return;
    assign unsupported_boundary = (
        unsupported_call_ce_o
        || invalid_counter_condition_o
        || invalid_loop_context_o
        || unsupported_do_at_loop_end_o
        || instruction_class_conflict
        || manual_control_conflict
        || empty_taken_return
    );

    assign raw_explicit_taken = (
        !reset_i
        && !unsupported_boundary
        && explicit_condition_true_o
    );
    assign raw_explicit_target = (
        (explicit_flow_i == FLOW_RETURN)
        ? pc_top_data_o
        : explicit_target_i
    );
    assign raw_flow_loop_active = (
        !reset_i
        && !unsupported_boundary
        && loop_active
    );
    assign raw_jump_counter_test = (
        !reset_i
        && !unsupported_boundary
        && (explicit_flow_i == FLOW_JUMP)
        && (explicit_condition_i == 4'he)
    );
    assign raw_counter_test = (
        raw_jump_counter_test
        || raw_loop_counter_test
    );
    assign raw_counter_action_count = (
        {1'b0, counter_load_i}
        + {1'b0, count_manual_pop_i}
        + {1'b0, raw_counter_test}
    );
    assign raw_do_push = (
        do_until_i
        && !reset_i
        && !unsupported_boundary
    );
    assign raw_pc_push = raw_pc_stack_push || raw_do_push;
    assign raw_pc_pop = raw_pc_stack_pop || pc_manual_pop_i;
    assign raw_count_push = counter_load_i && cntr_valid_o;
    assign raw_count_pop = (
        count_manual_pop_i
        || (raw_counter_test && raw_counter_expired)
    );
    assign raw_loop_push = raw_do_push;
    assign raw_loop_pop = raw_loop_stack_pop || loop_manual_pop_i;
    assign flow_count_pop_mismatch = (
        raw_flow_count_stack_pop
        != (raw_loop_counter_test && raw_counter_expired)
    );

    assign integration_conflict_o = !reset_i && (
        instruction_class_conflict
        || manual_control_conflict
        || (raw_counter_action_count > 2'd1)
        || (raw_pc_push && raw_pc_pop)
        || (raw_count_push && raw_count_pop)
        || (raw_loop_push && raw_loop_pop)
        || flow_count_pop_mismatch
    );
    assign boundary_valid_o = (
        !reset_i
        && !unsupported_boundary
        && !integration_conflict_o
    );

    assign next_pc_o = (
        boundary_valid_o
        ? raw_next_pc
        : sequential_pc
    );
    assign explicit_transfer_o = (
        boundary_valid_o
        && raw_explicit_transfer
    );
    assign loop_back_o = boundary_valid_o && raw_loop_back;
    assign loop_exit_o = boundary_valid_o && raw_loop_exit;
    assign counter_test_o = (
        boundary_valid_o
        && raw_counter_test
    );
    assign pc_stack_push_o = boundary_valid_o && raw_pc_push;
    assign pc_stack_pop_o = boundary_valid_o && raw_pc_pop;
    assign count_stack_push_o = counter_count_push;
    assign count_stack_pop_o = counter_count_pop;
    assign loop_stack_push_o = boundary_valid_o && raw_loop_push;
    assign loop_stack_pop_o = boundary_valid_o && raw_loop_pop;
    assign internal_storage_conflict_o = (
        counter_write_conflict
        || stack_write_conflict
    );

    assign stack_top_valid_o = {
        loop_top_valid,
        count_top_valid,
        pc_top_valid
    };
    assign stack_empty_o = {
        loop_empty,
        count_empty,
        pc_empty
    };
    assign stack_overflow_o = {
        loop_overflow,
        count_overflow,
        pc_overflow
    };
    assign stack_pop_valid_o = {
        loop_pop_valid,
        count_pop_valid,
        pc_pop_valid
    };
    assign stack_push_accepted_o = {
        loop_push_accepted,
        count_push_accepted,
        pc_push_accepted
    };
    assign stack_overflow_event_o = {
        loop_overflow_event,
        count_overflow_event,
        pc_overflow_event
    };
    assign stack_empty_pop_o = {
        loop_empty_pop,
        count_empty_pop,
        pc_empty_pop
    };

    adsp2100_condition_logic explicit_condition_logic (
        .condition_i(explicit_condition_i),
        .az_i(az_i),
        .an_i(an_i),
        .av_i(av_i),
        .ac_i(ac_i),
        .as_i(as_i),
        .mv_i(mv_i),
        .not_counter_expired_i(raw_not_counter_expired),
        .condition_true_o(explicit_condition_true_o)
    );

    adsp2100_condition_logic loop_condition_logic (
        .condition_i(loop_condition),
        .az_i(az_i),
        .an_i(an_i),
        .av_i(av_i),
        .ac_i(ac_i),
        .as_i(as_i),
        .mv_i(mv_i),
        .not_counter_expired_i(raw_not_counter_expired),
        .condition_true_o(loop_if_predicate)
    );

    adsp2100_sequencer_flow flow (
        .pc_i(pc_i),
        .explicit_flow_i(explicit_flow_i),
        .explicit_taken_i(raw_explicit_taken),
        .explicit_target_i(raw_explicit_target),
        .loop_active_i(raw_flow_loop_active),
        .loop_end_i(loop_end),
        .loop_start_i(pc_top_data_o),
        .loop_termination_true_i(loop_termination_true_o),
        .loop_uses_counter_i(loop_uses_counter),
        .next_pc_o(raw_next_pc),
        .pc_stack_push_o(raw_pc_stack_push),
        .pc_stack_push_value_o(raw_pc_stack_push_value),
        .pc_stack_pop_o(raw_pc_stack_pop),
        .loop_stack_pop_o(raw_loop_stack_pop),
        .count_stack_pop_o(raw_flow_count_stack_pop),
        .loop_counter_test_o(raw_loop_counter_test),
        .loop_back_o(raw_loop_back),
        .loop_exit_o(raw_loop_exit),
        .explicit_transfer_o(raw_explicit_transfer)
    );

    adsp2100_counter counter (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .load_i(boundary_valid_o && counter_load_i),
        .load_data_i(counter_load_data_i),
        .ce_test_i(boundary_valid_o && raw_counter_test),
        .manual_pop_i(boundary_valid_o && count_manual_pop_i),
        .count_stack_top_data_i(count_top_data_o),
        .count_stack_top_valid_i(count_top_valid),
        .cntr_data_o(cntr_data_o),
        .cntr_valid_o(cntr_valid_o),
        .condition_valid_o(counter_condition_valid_o),
        .counter_expired_o(counter_expired_o),
        .not_counter_expired_o(not_counter_expired_o),
        .count_stack_push_o(counter_count_push),
        .count_stack_push_data_o(counter_count_push_data),
        .count_stack_pop_o(counter_count_pop),
        .decrement_o(counter_decrement_o),
        .restore_o(counter_restore_o),
        .empty_ce_invalidate_o(counter_empty_invalidate_o),
        .invalid_ce_test_o(counter_invalid_test_o),
        .empty_manual_pop_o(counter_empty_manual_pop_o),
        .write_conflict_o(counter_write_conflict)
    );

    adsp2100_sequencer_stacks stacks (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .pc_push_i(pc_stack_push_o),
        .pc_pop_i(pc_stack_pop_o),
        .pc_push_data_i(raw_pc_stack_push_value),
        .pc_top_data_o(pc_top_data_o),
        .pc_top_valid_o(pc_top_valid),
        .pc_pop_valid_o(pc_pop_valid),
        .pc_empty_o(pc_empty),
        .pc_overflow_o(pc_overflow),
        .pc_depth_o(pc_depth_o),
        .pc_push_accepted_o(pc_push_accepted),
        .pc_overflow_event_o(pc_overflow_event),
        .pc_empty_pop_o(pc_empty_pop),
        .count_push_i(counter_count_push),
        .count_pop_i(counter_count_pop),
        .count_push_data_i(counter_count_push_data),
        .count_top_data_o(count_top_data_o),
        .count_top_valid_o(count_top_valid),
        .count_pop_valid_o(count_pop_valid),
        .count_empty_o(count_empty),
        .count_overflow_o(count_overflow),
        .count_depth_o(count_depth_o),
        .count_push_accepted_o(count_push_accepted),
        .count_overflow_event_o(count_overflow_event),
        .count_empty_pop_o(count_empty_pop),
        .loop_push_i(loop_stack_push_o),
        .loop_pop_i(loop_stack_pop_o),
        .loop_push_data_i({do_condition_i, do_end_i}),
        .loop_top_data_o(loop_top_data_o),
        .loop_top_valid_o(loop_top_valid),
        .loop_pop_valid_o(loop_pop_valid),
        .loop_empty_o(loop_empty),
        .loop_overflow_o(loop_overflow),
        .loop_depth_o(loop_depth_o),
        .loop_push_accepted_o(loop_push_accepted),
        .loop_overflow_event_o(loop_overflow_event),
        .loop_empty_pop_o(loop_empty_pop),
        .sstat_fragment_o(sstat_fragment_o),
        .write_conflict_o(stack_write_conflict)
    );
endmodule

`default_nettype wire
