`default_nettype none

module adsp2100_sequencer_flow_formal (
    input logic [13:0] pc,
    input logic [1:0]  explicit_flow,
    input logic        explicit_taken,
    input logic [13:0] explicit_target,
    input logic        loop_active,
    input logic [13:0] loop_end,
    input logic [13:0] loop_start,
    input logic        loop_termination_true,
    input logic        loop_uses_counter
);
    logic [13:0] next_pc;
    logic        pc_stack_push;
    logic [13:0] pc_stack_push_value;
    logic        pc_stack_pop;
    logic        loop_stack_pop;
    logic        count_stack_pop;
    logic        loop_counter_test;
    logic        loop_back;
    logic        loop_exit;
    logic        explicit_transfer;
    logic [13:0] sequential_pc;
    logic        transfer;
    logic        at_loop_end;

    assign sequential_pc = pc + 14'h0001;
    assign transfer = explicit_taken && (explicit_flow != 2'b00);
    assign at_loop_end = loop_active && (pc == loop_end);

    adsp2100_sequencer_flow dut (
        .pc_i(pc),
        .explicit_flow_i(explicit_flow),
        .explicit_taken_i(explicit_taken),
        .explicit_target_i(explicit_target),
        .loop_active_i(loop_active),
        .loop_end_i(loop_end),
        .loop_start_i(loop_start),
        .loop_termination_true_i(loop_termination_true),
        .loop_uses_counter_i(loop_uses_counter),
        .next_pc_o(next_pc),
        .pc_stack_push_o(pc_stack_push),
        .pc_stack_push_value_o(pc_stack_push_value),
        .pc_stack_pop_o(pc_stack_pop),
        .loop_stack_pop_o(loop_stack_pop),
        .count_stack_pop_o(count_stack_pop),
        .loop_counter_test_o(loop_counter_test),
        .loop_back_o(loop_back),
        .loop_exit_o(loop_exit),
        .explicit_transfer_o(explicit_transfer)
    );

    always_comb begin
        assert (pc_stack_push_value == sequential_pc);
        assert (!(pc_stack_push && pc_stack_pop));
        assert (!(loop_back && loop_exit));

        if (transfer) begin
            assert (explicit_transfer);
            assert (next_pc == explicit_target);
            assert (!loop_stack_pop);
            assert (!count_stack_pop);
            assert (!loop_counter_test);
            assert (!loop_back);
            assert (!loop_exit);
            assert (pc_stack_push == (explicit_flow == 2'b10));
            assert (pc_stack_pop == (explicit_flow == 2'b11));
        end else if (at_loop_end) begin
            assert (!explicit_transfer);
            assert (loop_counter_test == loop_uses_counter);
            if (loop_termination_true) begin
                assert (next_pc == sequential_pc);
                assert (pc_stack_pop);
                assert (loop_stack_pop);
                assert (count_stack_pop == loop_uses_counter);
                assert (loop_exit);
                assert (!loop_back);
            end else begin
                assert (next_pc == loop_start);
                assert (!pc_stack_pop);
                assert (!loop_stack_pop);
                assert (!count_stack_pop);
                assert (loop_back);
                assert (!loop_exit);
            end
        end else begin
            assert (next_pc == sequential_pc);
            assert (!explicit_transfer);
            assert (!pc_stack_push);
            assert (!pc_stack_pop);
            assert (!loop_stack_pop);
            assert (!count_stack_pop);
            assert (!loop_counter_test);
            assert (!loop_back);
            assert (!loop_exit);
        end
    end
endmodule

`default_nettype wire
