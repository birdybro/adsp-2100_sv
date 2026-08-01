`default_nettype none

// Stateless original Type 8 computation-plus-DREG-move action producer.
// Every operand is a cycle-start value; the caller owns the retirement edge
// that commits the noncolliding compute, status, and move write intents.
module adsp2100_compute_move_action (
    input  logic [23:0] opcode_i,
    input  logic [15:0] x_dreg_data_i,
    input  logic [15:0] y_dreg_data_i,
    input  logic [15:0] move_source_data_i,
    input  logic [15:0] af_i,
    input  logic [15:0] mf_i,
    input  logic [39:0] mr_i,
    input  logic [7:0]  astat_i,
    input  logic        overflow_latch_i,
    input  logic        saturate_ar_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        unverified_amf_zero_o,
    output logic        destination_collision_o,
    output logic        is_mac_o,
    output logic        destination_feedback_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  y_source_dreg_o,
    output logic [3:0]  move_destination_dreg_o,
    output logic [3:0]  move_source_dreg_o,
    output logic        move_write_o,
    output logic [15:0] move_data_o,
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
    logic [4:0] amf;
    logic [1:0] yop;
    logic [2:0] xop_unused;
    logic [15:0] y_source_data;
    logic alu_valid;
    logic mac_valid;
    logic [15:0] alu_raw_unused;
    logic [39:0] mac_unrounded_unused;
    logic [15:0] mac_mf_unused;
    logic [39:0] mac_saturated_unused;
    logic unused_observation;

    adsp2100_compute_move_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .unverified_amf_zero_o(unverified_amf_zero_o),
        .destination_collision_o(destination_collision_o),
        .is_mac_o(is_mac_o),
        .destination_feedback_o(destination_feedback_o),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop_unused),
        .x_source_dreg_o(x_source_dreg_o),
        .y_source_dreg_o(y_source_dreg_o),
        .move_destination_dreg_o(move_destination_dreg_o),
        .move_source_dreg_o(move_source_dreg_o)
    );

    assign y_source_data = (
        (yop == 2'd3) ? 16'h0000
        : (yop == 2'd2) ? (is_mac_o ? mf_i : af_i)
        : y_dreg_data_i
    );
    assign move_write_o = action_valid_o;
    assign move_data_o = move_source_data_i;
    assign alu_write_o = action_valid_o && !is_mac_o;
    assign mac_write_o = action_valid_o && is_mac_o;

    adsp2100_alu alu (
        .amf_i(amf),
        .x_i(x_dreg_data_i),
        .y_i(y_source_data),
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
        .x_i(x_dreg_data_i),
        .y_i(y_source_data),
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
        xop_unused, alu_raw_unused, mac_unrounded_unused, mac_mf_unused,
        mac_saturated_unused, astat_i[7], astat_i[5], astat_i[4], astat_i[1:0]
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        if (action_valid_o) begin
            assert (move_write_o);
            assert (alu_write_o ^ mac_write_o);
        end
        if (alu_write_o) begin
            assert (alu_valid && !mac_valid);
        end
        if (mac_write_o) begin
            assert (mac_valid && !alu_valid);
        end
        if (!action_valid_o) begin
            assert (!move_write_o && !alu_write_o && !mac_write_o);
        end
        if (unsupported_subencoding_o) begin
            assert (class_valid_o && !action_valid_o);
        end
    end
`endif
endmodule

`default_nettype wire
