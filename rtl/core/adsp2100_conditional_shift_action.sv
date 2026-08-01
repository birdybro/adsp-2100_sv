`default_nettype none

// Stateless Type 16 action producer for attachment to a shared architectural
// state owner. Condition and shifter inputs observe cycle-start state; the
// caller qualifies returned writes at instruction retirement.
module adsp2100_conditional_shift_action (
    input  logic [23:0] opcode_i,
    input  logic        not_counter_expired_i,
    input  logic [15:0] source_data_i,
    input  logic [31:0] sr_i,
    input  logic [7:0]  se_i,
    input  logic [4:0]  sb_i,
    input  logic [7:0]  astat_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        condition_true_o,
    output logic [3:0]  source_dreg_o,
    output logic        sr_write_o,
    output logic [31:0] sr_result_o,
    output logic        se_write_o,
    output logic [7:0]  se_result_o,
    output logic        sb_write_o,
    output logic [4:0]  sb_result_o,
    output logic        ss_write_o,
    output logic        ss_result_o
);
    logic [3:0] sf;
    logic [2:0] xop_unused;
    logic [3:0] condition;
    logic raw_condition_true;
    logic raw_sr_write;
    logic raw_se_write;
    logic raw_sb_write;
    logic raw_ss_write;
    logic unused_observation;

    adsp2100_conditional_shift_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .sf_o(sf),
        .xop_o(xop_unused),
        .source_dreg_o(source_dreg_o),
        .condition_o(condition)
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

    adsp2100_shifter shifter (
        .sf_i(sf),
        .x_i(source_data_i),
        .shift_or_se_i(se_i),
        .sr_i(sr_i),
        .sb_i(sb_i),
        .av_i(astat_i[2]),
        .ac_i(astat_i[3]),
        .ss_i(astat_i[7]),
        .sr_result_o(sr_result_o),
        .sr_write_o(raw_sr_write),
        .se_result_o(se_result_o),
        .se_write_o(raw_se_write),
        .sb_result_o(sb_result_o),
        .sb_write_o(raw_sb_write),
        .ss_result_o(ss_result_o),
        .ss_write_o(raw_ss_write)
    );

    assign condition_true_o = action_valid_o && raw_condition_true;
    assign sr_write_o = condition_true_o && raw_sr_write;
    assign se_write_o = condition_true_o && raw_se_write;
    assign sb_write_o = condition_true_o && raw_sb_write;
    assign ss_write_o = condition_true_o && raw_ss_write;
    assign unused_observation = ^{xop_unused, astat_i[5]};

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        if (!condition_true_o) begin
            assert (!sr_write_o && !se_write_o && !sb_write_o && !ss_write_o);
        end
        if (action_valid_o && condition_true_o) begin
            assert ($onehot0({sr_write_o, se_write_o, sb_write_o}));
        end
        if (unsupported_subencoding_o) begin
            assert (class_valid_o && !action_valid_o);
        end
    end
`endif
endmodule

`default_nettype wire
