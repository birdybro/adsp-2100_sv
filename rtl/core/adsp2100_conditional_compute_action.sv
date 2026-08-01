`default_nettype none

// Stateless Type 9 action producer for attachment to a shared architectural
// state owner. Decode and computation are combinational; the caller owns the
// instruction boundary that qualifies the returned write intents.
module adsp2100_conditional_compute_action (
    input  logic [23:0] opcode_i,
    input  logic        not_counter_expired_i,
    input  logic [15:0] x_dreg_data_i,
    input  logic [15:0] y_dreg_data_i,
    input  logic [15:0] af_i,
    input  logic [15:0] mf_i,
    input  logic [39:0] mr_i,
    input  logic [7:0]  astat_i,
    input  logic        overflow_latch_i,
    input  logic        saturate_ar_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        nop_action_o,
    output logic        condition_true_o,
    output logic        is_mac_o,
    output logic        is_alu_o,
    output logic        destination_feedback_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  y_source_dreg_o,
    output logic [15:0] x_source_data_o,
    output logic [15:0] y_source_data_o,
    output logic        alu_write_o,
    output logic [15:0] alu_result_o,
    output logic        alu_az_o,
    output logic        alu_an_o,
    output logic        alu_av_o,
    output logic        alu_ac_o,
    output logic        alu_as_write_o,
    output logic        alu_as_o,
    output logic        mac_write_o,
    output logic [39:0] mac_result_o,
    output logic        mac_mv_o
);
    logic unsupported_subencoding_unused;
    logic [4:0] amf;
    logic [1:0] yop;
    logic [2:0] xop_unused;
    logic [3:0] condition;
    logic raw_condition_true;
    logic alu_valid;
    logic mac_valid;
    logic [15:0] alu_raw_unused;
    logic [39:0] mac_unrounded_unused;
    logic [15:0] mac_mf_unused;
    logic [39:0] mac_saturated_unused;
    logic unused_observation;

    adsp2100_conditional_compute_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_unused),
        .nop_action_o(nop_action_o),
        .is_mac_o(is_mac_o),
        .is_alu_o(is_alu_o),
        .destination_feedback_o(destination_feedback_o),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop_unused),
        .condition_o(condition),
        .x_source_dreg_o(x_source_dreg_o),
        .y_source_dreg_o(y_source_dreg_o)
    );

    adsp2100_condition_logic condition_logic (
        .condition_i(condition),
        .az_i(astat_i[0]),
        .an_i(astat_i[1]),
        .av_i(astat_i[2]),
        .ac_i(astat_i[3]),
        .as_i(astat_i[4]),
        .mv_i(astat_i[6]),
        .not_counter_expired_i(not_counter_expired_i),
        .condition_true_o(raw_condition_true)
    );

    assign condition_true_o = action_valid_o && raw_condition_true;
    assign x_source_data_o = x_dreg_data_i;
    assign y_source_data_o = (
        (yop == 2'd3) ? 16'h0000
        : (yop == 2'd2) ? (is_mac_o ? mf_i : af_i)
        : y_dreg_data_i
    );
    assign alu_write_o = (
        action_valid_o && condition_true_o && is_alu_o && !nop_action_o
    );
    assign mac_write_o = (
        action_valid_o && condition_true_o && is_mac_o && !nop_action_o
    );

    adsp2100_alu alu (
        .amf_i(amf),
        .x_i(x_source_data_o),
        .y_i(y_source_data_o),
        .carry_i(astat_i[3]),
        .previous_av_i(astat_i[2]),
        .sticky_av_i(overflow_latch_i),
        .saturate_ar_i(saturate_ar_i),
        .destination_is_ar_i(!destination_feedback_o),
        .valid_o(alu_valid),
        .raw_result_o(alu_raw_unused),
        .destination_result_o(alu_result_o),
        .az_o(alu_az_o),
        .an_o(alu_an_o),
        .av_o(alu_av_o),
        .ac_o(alu_ac_o),
        .as_value_o(alu_as_o),
        .as_write_o(alu_as_write_o)
    );

    adsp2100_mac mac (
        .amf_i(amf),
        .x_i(x_source_data_o),
        .y_i(y_source_data_o),
        .mr_i(mr_i),
        .saturation_mv_i(astat_i[6]),
        .valid_o(mac_valid),
        .unrounded_result_o(mac_unrounded_unused),
        .result_o(mac_result_o),
        .mf_result_o(mac_mf_unused),
        .mv_o(mac_mv_o),
        .saturated_mr_o(mac_saturated_unused)
    );

    assign unused_observation = ^{
        unsupported_subencoding_unused, xop_unused, alu_raw_unused,
        mac_unrounded_unused, mac_mf_unused, mac_saturated_unused,
        astat_i[7], astat_i[5]
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!unsupported_subencoding_unused);
        if (alu_write_o) begin
            assert (alu_valid && !mac_valid);
        end
        if (mac_write_o) begin
            assert (mac_valid && !alu_valid);
        end
        if (!condition_true_o || nop_action_o || !action_valid_o) begin
            assert (!alu_write_o && !mac_write_o);
        end
    end
`endif
endmodule

`default_nettype wire
