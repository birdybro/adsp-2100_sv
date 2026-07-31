`default_nettype none

module adsp2100_stack_control_decode (
    input  logic [23:0] opcode_i,

    output logic        valid_o,
    output logic [1:0]  status_operation_o,
    output logic        count_pop_o,
    output logic        loop_pop_o,
    output logic        pc_pop_o,
    output logic        has_effect_o
);
    localparam logic [23:0] TYPE_26_MASK = 24'hffffe0;
    localparam logic [23:0] TYPE_26_VALUE = 24'h040000;

    always_comb begin
        valid_o = (opcode_i & TYPE_26_MASK) == TYPE_26_VALUE;
        status_operation_o = 2'b00;
        count_pop_o = 1'b0;
        loop_pop_o = 1'b0;
        pc_pop_o = 1'b0;
        has_effect_o = 1'b0;

        if (valid_o) begin
            status_operation_o = opcode_i[1:0];
            count_pop_o = opcode_i[2];
            loop_pop_o = opcode_i[3];
            pc_pop_o = opcode_i[4];
            // SPP=00 and SPP=01 are both documented no-change codes.
            has_effect_o = |opcode_i[4:1];
        end
    end
endmodule

`default_nettype wire
