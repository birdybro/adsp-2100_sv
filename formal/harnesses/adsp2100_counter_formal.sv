`default_nettype none

module adsp2100_counter_formal (
    input logic        clk,
    input logic        reset,
    input logic        load,
    input logic [13:0] load_data,
    input logic        ce_test,
    input logic        manual_pop,
    input logic [13:0] count_stack_top_data,
    input logic        count_stack_top_valid
);
    logic [13:0] cntr_data;
    logic        cntr_valid;
    logic        condition_valid;
    logic        counter_expired;
    logic        not_counter_expired;
    logic        count_stack_push;
    logic [13:0] count_stack_push_data;
    logic        count_stack_pop;
    logic        decrement;
    logic        restore;
    logic        empty_ce_invalidate;
    logic        invalid_ce_test;
    logic        empty_manual_pop;
    logic        write_conflict;
    logic [1:0]  expected_action_count;
    logic        expected_conflict;
    logic        past_valid;

    assign expected_action_count = (
        {1'b0, load}
        + {1'b0, ce_test}
        + {1'b0, manual_pop}
    );
    assign expected_conflict = (
        !reset
        && (expected_action_count > 2'd1)
    );

    adsp2100_counter dut (
        .clk_i(clk),
        .reset_i(reset),
        .load_i(load),
        .load_data_i(load_data),
        .ce_test_i(ce_test),
        .manual_pop_i(manual_pop),
        .count_stack_top_data_i(count_stack_top_data),
        .count_stack_top_valid_i(count_stack_top_valid),
        .cntr_data_o(cntr_data),
        .cntr_valid_o(cntr_valid),
        .condition_valid_o(condition_valid),
        .counter_expired_o(counter_expired),
        .not_counter_expired_o(not_counter_expired),
        .count_stack_push_o(count_stack_push),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_pop_o(count_stack_pop),
        .decrement_o(decrement),
        .restore_o(restore),
        .empty_ce_invalidate_o(empty_ce_invalidate),
        .invalid_ce_test_o(invalid_ce_test),
        .empty_manual_pop_o(empty_manual_pop),
        .write_conflict_o(write_conflict)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (write_conflict == expected_conflict);
        assert (
            condition_valid
            == (cntr_valid && !reset && !write_conflict)
        );
        assert (
            counter_expired
            == (condition_valid && (cntr_data == 14'h0001))
        );
        assert (
            not_counter_expired
            == (condition_valid && (cntr_data != 14'h0001))
        );
        assert (!(counter_expired && not_counter_expired));
        assert (
            condition_valid
            == (counter_expired || not_counter_expired)
        );
        assert (
            count_stack_push
            == (
                load
                && cntr_valid
                && !reset
                && !write_conflict
            )
        );
        if (count_stack_push) begin
            assert (count_stack_push_data == cntr_data);
        end
        assert (
            count_stack_pop
            == (
                !reset
                && !write_conflict
                && (
                    manual_pop
                    || (ce_test && counter_expired)
                )
            )
        );
        assert (
            decrement
            == (
                ce_test
                && not_counter_expired
                && !reset
                && !write_conflict
            )
        );
        assert (
            restore
            == (count_stack_pop && count_stack_top_valid)
        );
        assert (
            empty_ce_invalidate
            == (
                ce_test
                && counter_expired
                && !count_stack_top_valid
                && !reset
                && !write_conflict
            )
        );
        assert (
            invalid_ce_test
            == (
                ce_test
                && !cntr_valid
                && !reset
                && !write_conflict
            )
        );
        assert (
            empty_manual_pop
            == (
                manual_pop
                && !count_stack_top_valid
                && !reset
                && !write_conflict
            )
        );
        assert (!(decrement && restore));
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (!cntr_valid);
        end else if ($past(write_conflict)) begin
            assert (cntr_valid == $past(cntr_valid));
            if ($past(cntr_valid)) begin
                assert (cntr_data == $past(cntr_data));
            end
        end else if ($past(load)) begin
            assert (cntr_valid);
            assert (cntr_data == $past(load_data));
        end else if ($past(manual_pop)) begin
            if ($past(count_stack_top_valid)) begin
                assert (cntr_valid);
                assert (cntr_data == $past(count_stack_top_data));
            end else begin
                assert (cntr_valid == $past(cntr_valid));
                if ($past(cntr_valid)) begin
                    assert (cntr_data == $past(cntr_data));
                end
            end
        end else if ($past(ce_test) && $past(cntr_valid)) begin
            if ($past(cntr_data) == 14'h0001) begin
                if ($past(count_stack_top_valid)) begin
                    assert (cntr_valid);
                    assert (cntr_data == $past(count_stack_top_data));
                end else begin
                    assert (!cntr_valid);
                end
            end else begin
                assert (cntr_valid);
                assert (
                    cntr_data
                    == ($past(cntr_data) - 14'h0001)
                );
            end
        end else begin
            assert (cntr_valid == $past(cntr_valid));
            if ($past(cntr_valid)) begin
                assert (cntr_data == $past(cntr_data));
            end
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
