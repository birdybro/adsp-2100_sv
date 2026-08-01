`default_nettype none

// Stateless Type 15 action producer for attachment to a shared architectural
// state owner. The caller qualifies the returned write intent at the sourced
// instruction-retirement boundary.
module adsp2100_immediate_shift_action (
    input  logic [23:0] opcode_i,
    input  logic [15:0] source_data_i,
    input  logic [31:0] sr_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic [3:0]  source_dreg_o,
    output logic        sr_write_o,
    output logic [31:0] sr_result_o
);
    logic [3:0] sf;
    logic [2:0] xop_unused;
    logic [7:0] exponent;
    logic raw_sr_write;
    logic [7:0] se_result_unused;
    logic se_write_unused;
    logic [4:0] sb_result_unused;
    logic sb_write_unused;
    logic ss_result_unused;
    logic ss_write_unused;
    logic unused_observation;

    adsp2100_immediate_shift_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .sf_o(sf),
        .xop_o(xop_unused),
        .source_dreg_o(source_dreg_o),
        .exponent_o(exponent)
    );

    adsp2100_shifter shifter (
        .sf_i(sf),
        .x_i(source_data_i),
        .shift_or_se_i(exponent),
        .sr_i(sr_i),
        .sb_i(5'h00),
        .av_i(1'b0),
        .ac_i(1'b0),
        .ss_i(1'b0),
        .sr_result_o(sr_result_o),
        .sr_write_o(raw_sr_write),
        .se_result_o(se_result_unused),
        .se_write_o(se_write_unused),
        .sb_result_o(sb_result_unused),
        .sb_write_o(sb_write_unused),
        .ss_result_o(ss_result_unused),
        .ss_write_o(ss_write_unused)
    );

    assign sr_write_o = action_valid_o && raw_sr_write;
    assign unused_observation = ^{
        xop_unused, se_result_unused, se_write_unused,
        sb_result_unused, sb_write_unused, ss_result_unused, ss_write_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        if (action_valid_o) begin
            assert (sr_write_o);
            assert (!se_write_unused && !sb_write_unused && !ss_write_unused);
        end
        if (unsupported_subencoding_o) begin
            assert (class_valid_o && !action_valid_o);
        end
    end
`endif
endmodule

`default_nettype wire
