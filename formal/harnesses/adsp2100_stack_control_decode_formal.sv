`default_nettype none

module adsp2100_stack_control_decode_formal (
    input logic [23:0] opcode
);
    logic       valid;
    logic [1:0] status_operation;
    logic       count_pop;
    logic       loop_pop;
    logic       pc_pop;
    logic       has_effect;

    adsp2100_stack_control_decode dut (
        .opcode_i(opcode),
        .valid_o(valid),
        .status_operation_o(status_operation),
        .count_pop_o(count_pop),
        .loop_pop_o(loop_pop),
        .pc_pop_o(pc_pop),
        .has_effect_o(has_effect)
    );

    always_comb begin
        assert (valid == (
            opcode[23:5] == 19'b0000010000000000000
        ));
        if (valid) begin
            assert (status_operation == opcode[1:0]);
            assert (count_pop == opcode[2]);
            assert (loop_pop == opcode[3]);
            assert (pc_pop == opcode[4]);
            assert (has_effect == (|opcode[4:1]));
        end else begin
            assert (status_operation == 2'b00);
            assert (!count_pop);
            assert (!loop_pop);
            assert (!pc_pop);
            assert (!has_effect);
        end
    end
endmodule

`default_nettype wire
