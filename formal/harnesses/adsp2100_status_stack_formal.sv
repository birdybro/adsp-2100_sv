`default_nettype none

module adsp2100_status_stack_formal (
    input logic        clk,
    input logic        reset,
    input logic [1:0]  operation,
    input logic [15:0] push_data,
    input logic [12:0] push_validity
);
    logic [15:0] pop_data;
    logic [12:0] pop_validity;
    logic        pop_valid;
    logic        empty;
    logic        overflow;
    logic [2:0]  depth;
    logic        push_accepted;
    logic        overflow_event;
    logic        empty_pop;
    logic        past_valid;

    adsp2100_status_stack dut (
        .clk_i(clk),
        .reset_i(reset),
        .operation_i(operation),
        .push_data_i(push_data),
        .push_validity_i(push_validity),
        .pop_data_o(pop_data),
        .pop_validity_o(pop_validity),
        .pop_valid_o(pop_valid),
        .empty_o(empty),
        .overflow_o(overflow),
        .depth_o(depth),
        .push_accepted_o(push_accepted),
        .overflow_event_o(overflow_event),
        .empty_pop_o(empty_pop)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (empty == (depth == 3'd0));
        assert (pop_valid == (!reset && (operation == 2'b11) && !empty));
        assert (
            push_accepted
            == (!reset && (operation == 2'b10) && (depth < 3'd4))
        );
        assert (
            overflow_event
            == (!reset && (operation == 2'b10) && (depth == 3'd4))
        );
        assert (
            empty_pop
            == (!reset && (operation == 2'b11) && empty)
        );
        if (empty) begin
            assert (pop_data == 16'h0000);
            assert (pop_validity == 13'h0000);
        end
        if (past_valid) begin
            assert (depth <= 3'd4);
        end
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (depth == 3'd0);
            assert (!overflow);
        end else begin
            if ($past(push_accepted) && ($past(depth) == 3'd0)) begin
                assert (pop_data == $past(push_data));
                assert (pop_validity == $past(push_validity));
            end
            unique case ($past(operation))
                2'b10: begin
                    if ($past(depth) < 3'd4) begin
                        assert (depth == ($past(depth) + 3'd1));
                        assert (overflow == $past(overflow));
                    end else begin
                        assert (depth == 3'd4);
                        assert (overflow);
                    end
                end
                2'b11: begin
                    if ($past(depth) != 3'd0) begin
                        assert (depth == ($past(depth) - 3'd1));
                    end else begin
                        assert (depth == 3'd0);
                    end
                    assert (overflow == $past(overflow));
                end
                default: begin
                    assert (depth == $past(depth));
                    assert (overflow == $past(overflow));
                end
            endcase
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
