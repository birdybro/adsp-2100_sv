`default_nettype none

module adsp2100_sequencer_stacks_formal (
    input logic        clk,
    input logic        reset,
    input logic        pc_push,
    input logic        pc_pop,
    input logic [13:0] pc_push_data,
    input logic        count_push,
    input logic        count_pop,
    input logic [13:0] count_push_data,
    input logic        loop_push,
    input logic        loop_pop,
    input logic [17:0] loop_push_data
);
    logic [13:0] pc_top_data;
    logic        pc_top_valid;
    logic        pc_pop_valid;
    logic        pc_empty;
    logic        pc_overflow;
    logic [4:0]  pc_depth;
    logic        pc_push_accepted;
    logic        pc_overflow_event;
    logic        pc_empty_pop;
    logic [13:0] count_top_data;
    logic        count_top_valid;
    logic        count_pop_valid;
    logic        count_empty;
    logic        count_overflow;
    logic [2:0]  count_depth;
    logic        count_push_accepted;
    logic        count_overflow_event;
    logic        count_empty_pop;
    logic [17:0] loop_top_data;
    logic        loop_top_valid;
    logic        loop_pop_valid;
    logic        loop_empty;
    logic        loop_overflow;
    logic [2:0]  loop_depth;
    logic        loop_push_accepted;
    logic        loop_overflow_event;
    logic        loop_empty_pop;
    logic [7:0]  sstat_fragment;
    logic        write_conflict;
    logic        expected_conflict;
    logic        past_valid;

    assign expected_conflict = !reset && (
        (pc_push && pc_pop)
        || (count_push && count_pop)
        || (loop_push && loop_pop)
    );

    adsp2100_sequencer_stacks dut (
        .clk_i(clk),
        .reset_i(reset),
        .pc_push_i(pc_push),
        .pc_pop_i(pc_pop),
        .pc_push_data_i(pc_push_data),
        .pc_top_data_o(pc_top_data),
        .pc_top_valid_o(pc_top_valid),
        .pc_pop_valid_o(pc_pop_valid),
        .pc_empty_o(pc_empty),
        .pc_overflow_o(pc_overflow),
        .pc_depth_o(pc_depth),
        .pc_push_accepted_o(pc_push_accepted),
        .pc_overflow_event_o(pc_overflow_event),
        .pc_empty_pop_o(pc_empty_pop),
        .count_push_i(count_push),
        .count_pop_i(count_pop),
        .count_push_data_i(count_push_data),
        .count_top_data_o(count_top_data),
        .count_top_valid_o(count_top_valid),
        .count_pop_valid_o(count_pop_valid),
        .count_empty_o(count_empty),
        .count_overflow_o(count_overflow),
        .count_depth_o(count_depth),
        .count_push_accepted_o(count_push_accepted),
        .count_overflow_event_o(count_overflow_event),
        .count_empty_pop_o(count_empty_pop),
        .loop_push_i(loop_push),
        .loop_pop_i(loop_pop),
        .loop_push_data_i(loop_push_data),
        .loop_top_data_o(loop_top_data),
        .loop_top_valid_o(loop_top_valid),
        .loop_pop_valid_o(loop_pop_valid),
        .loop_empty_o(loop_empty),
        .loop_overflow_o(loop_overflow),
        .loop_depth_o(loop_depth),
        .loop_push_accepted_o(loop_push_accepted),
        .loop_overflow_event_o(loop_overflow_event),
        .loop_empty_pop_o(loop_empty_pop),
        .sstat_fragment_o(sstat_fragment),
        .write_conflict_o(write_conflict)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (write_conflict == expected_conflict);
        assert (pc_empty == (pc_depth == 5'd0));
        assert (count_empty == (count_depth == 3'd0));
        assert (loop_empty == (loop_depth == 3'd0));
        assert (pc_top_valid == !pc_empty);
        assert (count_top_valid == !count_empty);
        assert (loop_top_valid == !loop_empty);
        assert (
            sstat_fragment
            == {
                loop_overflow,
                loop_empty,
                2'b00,
                count_overflow,
                count_empty,
                pc_overflow,
                pc_empty
            }
        );
        assert (
            pc_pop_valid
            == (
                pc_pop
                && !pc_empty
                && !reset
                && !write_conflict
            )
        );
        assert (
            count_pop_valid
            == (
                count_pop
                && !count_empty
                && !reset
                && !write_conflict
            )
        );
        assert (
            loop_pop_valid
            == (
                loop_pop
                && !loop_empty
                && !reset
                && !write_conflict
            )
        );
        assert (
            pc_push_accepted
            == (
                pc_push
                && (pc_depth < 5'd16)
                && !reset
                && !write_conflict
            )
        );
        assert (
            count_push_accepted
            == (
                count_push
                && (count_depth < 3'd4)
                && !reset
                && !write_conflict
            )
        );
        assert (
            loop_push_accepted
            == (
                loop_push
                && (loop_depth < 3'd4)
                && !reset
                && !write_conflict
            )
        );
        assert (
            pc_overflow_event
            == (
                pc_push
                && (pc_depth == 5'd16)
                && !reset
                && !write_conflict
            )
        );
        assert (
            count_overflow_event
            == (
                count_push
                && (count_depth == 3'd4)
                && !reset
                && !write_conflict
            )
        );
        assert (
            loop_overflow_event
            == (
                loop_push
                && (loop_depth == 3'd4)
                && !reset
                && !write_conflict
            )
        );
        assert (
            pc_empty_pop
            == (
                pc_pop
                && pc_empty
                && !reset
                && !write_conflict
            )
        );
        assert (
            count_empty_pop
            == (
                count_pop
                && count_empty
                && !reset
                && !write_conflict
            )
        );
        assert (
            loop_empty_pop
            == (
                loop_pop
                && loop_empty
                && !reset
                && !write_conflict
            )
        );
        if (pc_empty) begin
            assert (pc_top_data == 14'h0000);
        end
        if (count_empty) begin
            assert (count_top_data == 14'h0000);
        end
        if (loop_empty) begin
            assert (loop_top_data == 18'h00000);
        end
        if (past_valid) begin
            assert (pc_depth <= 5'd16);
            assert (count_depth <= 3'd4);
            assert (loop_depth <= 3'd4);
        end
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (pc_depth == 5'd0);
            assert (count_depth == 3'd0);
            assert (loop_depth == 3'd0);
            assert (!pc_overflow);
            assert (!count_overflow);
            assert (!loop_overflow);
        end else if ($past(write_conflict)) begin
            assert (pc_depth == $past(pc_depth));
            assert (count_depth == $past(count_depth));
            assert (loop_depth == $past(loop_depth));
            assert (pc_overflow == $past(pc_overflow));
            assert (count_overflow == $past(count_overflow));
            assert (loop_overflow == $past(loop_overflow));
        end else begin
            if ($past(pc_push)) begin
                if ($past(pc_depth) < 5'd16) begin
                    assert (pc_depth == ($past(pc_depth) + 5'd1));
                    assert (pc_top_data == $past(pc_push_data));
                    assert (pc_overflow == $past(pc_overflow));
                end else begin
                    assert (pc_depth == 5'd16);
                    assert (pc_overflow);
                end
            end else if ($past(pc_pop)) begin
                if ($past(pc_depth) != 5'd0) begin
                    assert (pc_depth == ($past(pc_depth) - 5'd1));
                end else begin
                    assert (pc_depth == 5'd0);
                end
                assert (pc_overflow == $past(pc_overflow));
            end else begin
                assert (pc_depth == $past(pc_depth));
                assert (pc_overflow == $past(pc_overflow));
                if ($past(pc_top_valid)) begin
                    assert (pc_top_data == $past(pc_top_data));
                end
            end

            if ($past(count_push)) begin
                if ($past(count_depth) < 3'd4) begin
                    assert (count_depth == ($past(count_depth) + 3'd1));
                    assert (count_top_data == $past(count_push_data));
                    assert (count_overflow == $past(count_overflow));
                end else begin
                    assert (count_depth == 3'd4);
                    assert (count_overflow);
                end
            end else if ($past(count_pop)) begin
                if ($past(count_depth) != 3'd0) begin
                    assert (count_depth == ($past(count_depth) - 3'd1));
                end else begin
                    assert (count_depth == 3'd0);
                end
                assert (count_overflow == $past(count_overflow));
            end else begin
                assert (count_depth == $past(count_depth));
                assert (count_overflow == $past(count_overflow));
                if ($past(count_top_valid)) begin
                    assert (count_top_data == $past(count_top_data));
                end
            end

            if ($past(loop_push)) begin
                if ($past(loop_depth) < 3'd4) begin
                    assert (loop_depth == ($past(loop_depth) + 3'd1));
                    assert (loop_top_data == $past(loop_push_data));
                    assert (loop_overflow == $past(loop_overflow));
                end else begin
                    assert (loop_depth == 3'd4);
                    assert (loop_overflow);
                end
            end else if ($past(loop_pop)) begin
                if ($past(loop_depth) != 3'd0) begin
                    assert (loop_depth == ($past(loop_depth) - 3'd1));
                end else begin
                    assert (loop_depth == 3'd0);
                end
                assert (loop_overflow == $past(loop_overflow));
            end else begin
                assert (loop_depth == $past(loop_depth));
                assert (loop_overflow == $past(loop_overflow));
                if ($past(loop_top_valid)) begin
                    assert (loop_top_data == $past(loop_top_data));
                end
            end
        end

        cover (pc_depth == 5'd16);
        cover (count_depth == 3'd4);
        cover (loop_depth == 3'd4);
        cover (
            pc_overflow
            && count_overflow
            && loop_overflow
            && pc_empty
            && count_empty
            && loop_empty
        );
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
