`default_nettype none

// Stateless original Type 24 DIVS action producer for attachment to one
// shared architectural-state owner. The divisor sign, upper dividend, AF, and
// AY0 inputs are cycle-start values; the caller qualifies writes at retirement.
module adsp2100_divide_sign_action (
    input  logic [23:0] opcode_i,
    input  logic        divisor_sign_i,
    input  logic [15:0] upper_dreg_i,
    input  logic [15:0] partial_remainder_i,
    input  logic [15:0] ay0_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_yop_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  divisor_source_dreg_o,
    output logic [3:0]  upper_source_dreg_o,
    output logic        upper_source_feedback_o,
    output logic [15:0] upper_value_o,
    output logic        quotient_sign_o,
    output logic        af_write_o,
    output logic [15:0] af_result_o,
    output logic        ay0_write_o,
    output logic [15:0] ay0_result_o,
    output logic        aq_write_o,
    output logic        aq_result_o
);
    adsp2100_divide_sign_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_yop_o(unsupported_yop_o),
        .yop_o(yop_o),
        .xop_o(xop_o),
        .x_source_dreg_o(divisor_source_dreg_o),
        .upper_source_dreg_o(upper_source_dreg_o),
        .upper_source_feedback_o(upper_source_feedback_o)
    );

    assign upper_value_o = upper_source_feedback_o
        ? partial_remainder_i : upper_dreg_i;
    assign quotient_sign_o = divisor_sign_i ^ upper_value_o[15];
    assign af_result_o = {upper_value_o[14:0], ay0_i[15]};
    assign ay0_result_o = {ay0_i[14:0], quotient_sign_o};

    assign af_write_o = action_valid_o;
    assign ay0_write_o = action_valid_o;
    assign aq_write_o = action_valid_o;
    assign aq_result_o = quotient_sign_o;

`ifndef SYNTHESIS
    always_comb begin
        if (!action_valid_o) begin
            assert (!af_write_o && !ay0_write_o && !aq_write_o);
        end
        if (action_valid_o) begin
            assert (af_write_o && ay0_write_o && aq_write_o);
            assert (aq_result_o == (divisor_sign_i ^ upper_value_o[15]));
            assert (ay0_result_o[0] == aq_result_o);
        end
    end
`endif
endmodule

`default_nettype wire
