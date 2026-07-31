`default_nettype none

module adsp2100_do_until_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        pc_setup_write_i,
    input  logic [13:0] pc_setup_data_i,
    input  logic        counter_setup_write_i,
    input  logic [13:0] counter_setup_data_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic [13:0] end_address_o,
    output logic [3:0]  termination_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        invalid_loop_context_o,
    output logic        unsupported_do_at_loop_end_o,
    output logic        unsupported_nested_same_end_o,
    output logic        internal_conflict_o,
    output logic [13:0] pc_o,
    output logic        pc_write_o,
    output logic        pc_stack_push_o,
    output logic        pc_stack_push_accepted_o,
    output logic        pc_stack_overflow_event_o,
    output logic [13:0] pc_stack_top_o,
    output logic        pc_stack_top_valid_o,
    output logic [4:0]  pc_stack_depth_o,
    output logic        pc_stack_overflow_o,
    output logic        loop_stack_push_o,
    output logic        loop_stack_push_accepted_o,
    output logic        loop_stack_overflow_event_o,
    output logic [17:0] loop_stack_top_o,
    output logic        loop_stack_top_valid_o,
    output logic [2:0]  loop_stack_depth_o,
    output logic        loop_stack_overflow_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic        count_stack_push_o,
    output logic [13:0] count_stack_top_o,
    output logic        count_stack_top_valid_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,
    output logic [7:0]  sstat_fragment_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic [13:0] pc_q;
    logic [1:0]  setup_count;
    logic        pc_setup_enable;
    logic        counter_setup_enable;
    logic [13:0] sequential_pc;
    logic        loop_uses_counter;
    logic        execution_attempt;
    logic [13:0] counter_count_push_data;
    logic        unused_counter_condition_valid;
    logic        unused_counter_expired;
    logic        unused_not_counter_expired;
    logic        unused_counter_count_pop;
    logic        unused_counter_decrement;
    logic        unused_counter_restore;
    logic        unused_counter_empty_invalidate;
    logic        counter_invalid_test;
    logic        counter_empty_manual_pop;
    logic        counter_write_conflict;
    logic        unused_pc_pop_valid;
    logic        unused_pc_empty;
    logic        unused_pc_empty_pop;
    logic        unused_count_pop_valid;
    logic        unused_count_empty;
    logic        unused_count_push_accepted;
    logic        unused_count_overflow_event;
    logic        unused_count_empty_pop;
    logic        unused_loop_pop_valid;
    logic        unused_loop_empty;
    logic        unused_loop_empty_pop;
    logic        stack_write_conflict;

    adsp2100_do_until_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .end_address_o(end_address_o),
        .termination_o(termination_o)
    );

    assign setup_count = (
        {1'b0, pc_setup_write_i}
        + {1'b0, counter_setup_write_i}
    );
    assign integration_conflict_o = !reset_i && (
        (execute_i && (setup_count != 2'd0))
        || (setup_count > 2'd1)
    );
    assign pc_setup_enable = (
        !reset_i && !execute_i && (setup_count == 2'd1)
        && pc_setup_write_i
    );
    assign counter_setup_enable = (
        !reset_i && !execute_i && (setup_count == 2'd1)
        && counter_setup_write_i
    );
    assign execution_attempt = (
        !reset_i && execute_i && action_valid_o
        && !integration_conflict_o
    );
    assign loop_uses_counter = (
        loop_stack_top_o[17:14] == 4'he
    );
    assign invalid_loop_context_o = (
        execution_attempt && loop_stack_top_valid_o
        && (
            !pc_stack_top_valid_o
            || (loop_uses_counter && !cntr_valid_o)
        )
    );
    assign unsupported_do_at_loop_end_o = (
        execution_attempt && loop_stack_top_valid_o
        && (pc_q == loop_stack_top_o[13:0])
    );
    assign unsupported_nested_same_end_o = (
        execution_attempt && loop_stack_top_valid_o
        && (end_address_o == loop_stack_top_o[13:0])
    );
    assign boundary_valid_o = (
        execution_attempt
        && !invalid_loop_context_o
        && !unsupported_do_at_loop_end_o
        && !unsupported_nested_same_end_o
    );
    assign invalid_opcode_o = (
        !reset_i && execute_i && !class_valid_o
    );
    assign sequential_pc = pc_q + 14'h0001;
    assign pc_write_o = boundary_valid_o;
    assign pc_stack_push_o = boundary_valid_o;
    assign loop_stack_push_o = boundary_valid_o;
    assign pc_o = pc_q;
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;
    assign internal_conflict_o = (
        stack_write_conflict || counter_write_conflict
        || counter_invalid_test || counter_empty_manual_pop
    );

    adsp2100_counter counter (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .load_i(counter_setup_enable),
        .load_data_i(counter_setup_data_i),
        .ce_test_i(1'b0),
        .manual_pop_i(1'b0),
        .count_stack_top_data_i(count_stack_top_o),
        .count_stack_top_valid_i(count_stack_top_valid_o),
        .cntr_data_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .condition_valid_o(unused_counter_condition_valid),
        .counter_expired_o(unused_counter_expired),
        .not_counter_expired_o(unused_not_counter_expired),
        .count_stack_push_o(count_stack_push_o),
        .count_stack_push_data_o(counter_count_push_data),
        .count_stack_pop_o(unused_counter_count_pop),
        .decrement_o(unused_counter_decrement),
        .restore_o(unused_counter_restore),
        .empty_ce_invalidate_o(unused_counter_empty_invalidate),
        .invalid_ce_test_o(counter_invalid_test),
        .empty_manual_pop_o(counter_empty_manual_pop),
        .write_conflict_o(counter_write_conflict)
    );

    adsp2100_sequencer_stacks stacks (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .pc_push_i(pc_stack_push_o),
        .pc_pop_i(1'b0),
        .pc_push_data_i(sequential_pc),
        .pc_top_data_o(pc_stack_top_o),
        .pc_top_valid_o(pc_stack_top_valid_o),
        .pc_pop_valid_o(unused_pc_pop_valid),
        .pc_empty_o(unused_pc_empty),
        .pc_overflow_o(pc_stack_overflow_o),
        .pc_depth_o(pc_stack_depth_o),
        .pc_push_accepted_o(pc_stack_push_accepted_o),
        .pc_overflow_event_o(pc_stack_overflow_event_o),
        .pc_empty_pop_o(unused_pc_empty_pop),
        .count_push_i(count_stack_push_o),
        .count_pop_i(1'b0),
        .count_push_data_i(counter_count_push_data),
        .count_top_data_o(count_stack_top_o),
        .count_top_valid_o(count_stack_top_valid_o),
        .count_pop_valid_o(unused_count_pop_valid),
        .count_empty_o(unused_count_empty),
        .count_overflow_o(count_stack_overflow_o),
        .count_depth_o(count_stack_depth_o),
        .count_push_accepted_o(unused_count_push_accepted),
        .count_overflow_event_o(unused_count_overflow_event),
        .count_empty_pop_o(unused_count_empty_pop),
        .loop_push_i(loop_stack_push_o),
        .loop_pop_i(1'b0),
        .loop_push_data_i({termination_o, end_address_o}),
        .loop_top_data_o(loop_stack_top_o),
        .loop_top_valid_o(loop_stack_top_valid_o),
        .loop_pop_valid_o(unused_loop_pop_valid),
        .loop_empty_o(unused_loop_empty),
        .loop_overflow_o(loop_stack_overflow_o),
        .loop_depth_o(loop_stack_depth_o),
        .loop_push_accepted_o(loop_stack_push_accepted_o),
        .loop_overflow_event_o(loop_stack_overflow_event_o),
        .loop_empty_pop_o(unused_loop_empty_pop),
        .sstat_fragment_o(sstat_fragment_o),
        .write_conflict_o(stack_write_conflict)
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pc_q <= 14'h0004;
        end else if (pc_setup_enable) begin
            pc_q <= pc_setup_data_i;
        end else if (boundary_valid_o) begin
            pc_q <= sequential_pc;
        end
    end

    always_comb begin
        assert (pc_stack_push_o == loop_stack_push_o);
        assert (!pm_data_access_o && !dm_access_o);
        if (!boundary_valid_o) begin
            assert (!pc_write_o && !pc_stack_push_o && !loop_stack_push_o);
        end
    end
endmodule

`default_nettype wire
