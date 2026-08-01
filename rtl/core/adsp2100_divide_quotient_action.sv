`default_nettype none

// Stateless original Type 23 DIVQ action producer for attachment to one
// shared architectural-state owner. All operands are cycle-start values; the
// caller qualifies the three simultaneous writes at instruction retirement.
module adsp2100_divide_quotient_action (
    input  logic [23:0] opcode_i,
    input  logic [15:0] divisor_i,
    input  logic [15:0] partial_remainder_i,
    input  logic [15:0] ay0_i,
    input  logic        old_aq_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  divisor_source_dreg_o,
    output logic        add_divisor_o,
    output logic [15:0] alu_result_o,
    output logic        new_aq_o,
    output logic        quotient_bit_o,
    output logic        af_write_o,
    output logic [15:0] af_result_o,
    output logic        ay0_write_o,
    output logic [15:0] ay0_result_o,
    output logic        aq_write_o,
    output logic        aq_result_o
);
    adsp2100_divide_quotient_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .xop_o(xop_o),
        .divisor_source_dreg_o(divisor_source_dreg_o)
    );

    assign add_divisor_o = old_aq_i;
    // The source defines a 16-bit ALU operation; carry/borrow past bit 15 is
    // intentionally discarded before the sign and shifted-result equations.
    assign alu_result_o = old_aq_i
        ? (partial_remainder_i + divisor_i)
        : (partial_remainder_i - divisor_i);
    assign new_aq_o = divisor_i[15] ^ alu_result_o[15];
    assign quotient_bit_o = !new_aq_o;
    assign af_result_o = {alu_result_o[14:0], ay0_i[15]};
    assign ay0_result_o = {ay0_i[14:0], quotient_bit_o};

    assign af_write_o = action_valid_o;
    assign ay0_write_o = action_valid_o;
    assign aq_write_o = action_valid_o;
    assign aq_result_o = new_aq_o;

`ifndef SYNTHESIS
    always_comb begin
        if (!action_valid_o) begin
            assert (!af_write_o && !ay0_write_o && !aq_write_o);
        end
        if (action_valid_o) begin
            assert (af_write_o && ay0_write_o && aq_write_o);
            assert (aq_result_o == (divisor_i[15] ^ alu_result_o[15]));
            assert (ay0_result_o[0] == !aq_result_o);
        end
    end
`endif
endmodule

`default_nettype wire
