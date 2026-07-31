`default_nettype none

module adsp2100_sequencer_slice_formal (
    input logic        clk,
    input logic        reset,
    input logic [13:0] pc,
    input logic        do_until,
    input logic [13:0] do_end,
    input logic [3:0]  do_condition,
    input logic [1:0]  explicit_flow,
    input logic [3:0]  explicit_condition,
    input logic [13:0] explicit_target,
    input logic        counter_load,
    input logic [13:0] counter_load_data,
    input logic        pc_manual_pop,
    input logic        count_manual_pop,
    input logic        loop_manual_pop,
    input logic        az,
    input logic        an,
    input logic        av,
    input logic        ac,
    input logic        as_flag,
    input logic        mv
);
    logic [13:0] next_pc;
    logic        boundary_valid;
    logic        integration_conflict;
    logic        unsupported_call_ce;
    logic        invalid_counter_condition;
    logic        invalid_loop_context;
    logic        invalid_return_context;
    logic        unsupported_do_at_loop_end;
    logic        unsupported_nested_same_end;
    logic        explicit_condition_true;
    logic        loop_termination_true;
    logic        explicit_transfer;
    logic        loop_back;
    logic        loop_exit;
    logic [13:0] cntr_data;
    logic        cntr_valid;
    logic        counter_condition_valid;
    logic        counter_expired;
    logic        not_counter_expired;
    logic        counter_test;
    logic        counter_decrement;
    logic        counter_restore;
    logic        counter_empty_invalidate;
    logic        counter_invalid_test;
    logic        counter_empty_manual_pop;
    logic [13:0] pc_top_data;
    logic [13:0] count_top_data;
    logic [17:0] loop_top_data;
    logic [2:0]  stack_top_valid;
    logic [4:0]  pc_depth;
    logic [2:0]  count_depth;
    logic [2:0]  loop_depth;
    logic [2:0]  stack_empty;
    logic [2:0]  stack_overflow;
    logic [2:0]  stack_pop_valid;
    logic [2:0]  stack_push_accepted;
    logic [2:0]  stack_overflow_event;
    logic [2:0]  stack_empty_pop;
    logic [7:0]  sstat_fragment;
    logic        pc_stack_push;
    logic        pc_stack_pop;
    logic        count_stack_push;
    logic        count_stack_pop;
    logic        loop_stack_push;
    logic        loop_stack_pop;
    logic        internal_storage_conflict;
    logic        past_valid;

    adsp2100_sequencer_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .pc_i(pc),
        .do_until_i(do_until),
        .do_end_i(do_end),
        .do_condition_i(do_condition),
        .explicit_flow_i(explicit_flow),
        .explicit_condition_i(explicit_condition),
        .explicit_target_i(explicit_target),
        .counter_load_i(counter_load),
        .counter_load_data_i(counter_load_data),
        .pc_manual_pop_i(pc_manual_pop),
        .count_manual_pop_i(count_manual_pop),
        .loop_manual_pop_i(loop_manual_pop),
        .az_i(az),
        .an_i(an),
        .av_i(av),
        .ac_i(ac),
        .as_i(as_flag),
        .mv_i(mv),
        .next_pc_o(next_pc),
        .boundary_valid_o(boundary_valid),
        .integration_conflict_o(integration_conflict),
        .unsupported_call_ce_o(unsupported_call_ce),
        .invalid_counter_condition_o(invalid_counter_condition),
        .invalid_loop_context_o(invalid_loop_context),
        .invalid_return_context_o(invalid_return_context),
        .unsupported_do_at_loop_end_o(unsupported_do_at_loop_end),
        .unsupported_nested_same_end_o(unsupported_nested_same_end),
        .explicit_condition_true_o(explicit_condition_true),
        .loop_termination_true_o(loop_termination_true),
        .explicit_transfer_o(explicit_transfer),
        .loop_back_o(loop_back),
        .loop_exit_o(loop_exit),
        .cntr_data_o(cntr_data),
        .cntr_valid_o(cntr_valid),
        .counter_condition_valid_o(counter_condition_valid),
        .counter_expired_o(counter_expired),
        .not_counter_expired_o(not_counter_expired),
        .counter_test_o(counter_test),
        .counter_decrement_o(counter_decrement),
        .counter_restore_o(counter_restore),
        .counter_empty_invalidate_o(counter_empty_invalidate),
        .counter_invalid_test_o(counter_invalid_test),
        .counter_empty_manual_pop_o(counter_empty_manual_pop),
        .pc_top_data_o(pc_top_data),
        .count_top_data_o(count_top_data),
        .loop_top_data_o(loop_top_data),
        .stack_top_valid_o(stack_top_valid),
        .pc_depth_o(pc_depth),
        .count_depth_o(count_depth),
        .loop_depth_o(loop_depth),
        .stack_empty_o(stack_empty),
        .stack_overflow_o(stack_overflow),
        .stack_pop_valid_o(stack_pop_valid),
        .stack_push_accepted_o(stack_push_accepted),
        .stack_overflow_event_o(stack_overflow_event),
        .stack_empty_pop_o(stack_empty_pop),
        .sstat_fragment_o(sstat_fragment),
        .pc_stack_push_o(pc_stack_push),
        .pc_stack_pop_o(pc_stack_pop),
        .count_stack_push_o(count_stack_push),
        .count_stack_pop_o(count_stack_pop),
        .loop_stack_push_o(loop_stack_push),
        .loop_stack_pop_o(loop_stack_pop),
        .internal_storage_conflict_o(internal_storage_conflict)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (stack_empty == ~stack_top_valid);
        assert (pc_depth <= 5'd16);
        assert (count_depth <= 3'd4);
        assert (loop_depth <= 3'd4);
        assert (stack_top_valid[0] == (pc_depth != 5'd0));
        assert (stack_top_valid[1] == (count_depth != 3'd0));
        assert (stack_top_valid[2] == (loop_depth != 3'd0));
        assert (sstat_fragment[0] == stack_empty[0]);
        assert (sstat_fragment[1] == stack_overflow[0]);
        assert (sstat_fragment[2] == stack_empty[1]);
        assert (sstat_fragment[3] == stack_overflow[1]);
        assert (sstat_fragment[5:4] == 2'b00);
        assert (sstat_fragment[6] == stack_empty[2]);
        assert (sstat_fragment[7] == stack_overflow[2]);

        assert (!internal_storage_conflict);
        assert (!(loop_back && loop_exit));
        assert (!(pc_stack_push && pc_stack_pop));
        assert (!(count_stack_push && count_stack_pop));
        assert (!(loop_stack_push && loop_stack_pop));
        assert ((stack_pop_valid & ~{
            loop_stack_pop,
            count_stack_pop,
            pc_stack_pop
        }) == 3'b000);
        assert ((stack_push_accepted & ~{
            loop_stack_push,
            count_stack_push,
            pc_stack_push
        }) == 3'b000);
        assert ((stack_overflow_event & ~{
            loop_stack_push,
            count_stack_push,
            pc_stack_push
        }) == 3'b000);
        assert ((stack_empty_pop & ~{
            loop_stack_pop,
            count_stack_pop,
            pc_stack_pop
        }) == 3'b000);

        assert (
            counter_condition_valid
            == (cntr_valid && !reset)
        );
        assert (
            counter_expired
            == (counter_condition_valid && (cntr_data == 14'h0001))
        );
        assert (
            not_counter_expired
            == (
                counter_condition_valid
                && (cntr_data != 14'h0001)
            )
        );
        assert (!(counter_expired && not_counter_expired));
        assert (!counter_invalid_test);
        assert (!counter_decrement || counter_test);
        assert (!counter_restore || count_stack_pop);
        assert (!counter_empty_invalidate || count_stack_pop);
        assert (
            !counter_empty_manual_pop
            || (count_manual_pop && stack_empty[1])
        );

        if (!boundary_valid) begin
            assert (next_pc == (pc + 14'h0001));
            assert (!explicit_transfer);
            assert (!loop_back);
            assert (!loop_exit);
            assert (!counter_test);
            assert (!pc_stack_push);
            assert (!pc_stack_pop);
            assert (!count_stack_push);
            assert (!count_stack_pop);
            assert (!loop_stack_push);
            assert (!loop_stack_pop);
        end
        if (boundary_valid) begin
            assert (!reset);
            assert (!integration_conflict);
            assert (!unsupported_call_ce);
            assert (!invalid_counter_condition);
            assert (!invalid_loop_context);
            assert (!invalid_return_context);
            assert (!unsupported_do_at_loop_end);
            assert (!unsupported_nested_same_end);
        end

        cover (explicit_condition_true);
        cover (loop_termination_true);
        cover (explicit_transfer);
        cover (loop_back);
        cover (loop_exit);
        cover (counter_decrement);
        cover (counter_restore);
        cover (counter_empty_invalidate);
        cover (stack_overflow_event != 3'b000);
        cover (stack_empty_pop != 3'b000);
        cover (do_end == explicit_target);
        cover (unsupported_nested_same_end);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (!cntr_valid);
            assert (pc_depth == 5'd0);
            assert (count_depth == 3'd0);
            assert (loop_depth == 3'd0);
            assert (stack_overflow == 3'b000);
        end else if (!$past(boundary_valid)) begin
            assert (cntr_valid == $past(cntr_valid));
            if ($past(cntr_valid)) begin
                assert (cntr_data == $past(cntr_data));
            end
            assert (pc_depth == $past(pc_depth));
            assert (count_depth == $past(count_depth));
            assert (loop_depth == $past(loop_depth));
            assert (stack_overflow == $past(stack_overflow));
            if ($past(stack_top_valid[0])) begin
                assert (pc_top_data == $past(pc_top_data));
            end
            if ($past(stack_top_valid[1])) begin
                assert (count_top_data == $past(count_top_data));
            end
            if ($past(stack_top_valid[2])) begin
                assert (loop_top_data == $past(loop_top_data));
            end
        end else if ($past(counter_load)) begin
            assert (cntr_valid);
            assert (cntr_data == $past(counter_load_data));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
