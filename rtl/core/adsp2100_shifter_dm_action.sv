`default_nettype none

// Stateless original Type 12 shifter-plus-DM action producer.
//
// Every input is a captured cycle-start value. The caller owns the native DM
// descriptor and the qualified retirement edge that atomically commits the
// noncolliding shifter/status, optional read-DREG, and DAG-I write intents.
module adsp2100_shifter_dm_action (
    input  logic [23:0] opcode_i,
    input  logic [15:0] shifter_source_data_i,
    input  logic [15:0] memory_dreg_data_i,
    input  logic [31:0] sr_i,
    input  logic [7:0]  se_i,
    input  logic [4:0]  sb_i,
    input  logic [7:0]  astat_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        unavailable_xop_o,
    output logic        destination_collision_o,
    output logic        dag_select_o,
    output logic        write_o,
    output logic [3:0]  shifter_source_dreg_o,
    output logic [3:0]  memory_dreg_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,
    output logic [15:0] memory_source_data_o,
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
    logic raw_sr_write;
    logic raw_se_write;
    logic raw_sb_write;
    logic raw_ss_write;
    logic unused_observation;

    adsp2100_shifter_dm_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .unavailable_xop_o(unavailable_xop_o),
        .destination_collision_o(destination_collision_o),
        .dag_select_o(dag_select_o),
        .write_o(write_o),
        .sf_o(sf),
        .xop_o(xop_unused),
        .shifter_source_dreg_o(shifter_source_dreg_o),
        .memory_dreg_o(memory_dreg_o),
        .i_address_o(i_address_o),
        .m_address_o(m_address_o)
    );

    adsp2100_shifter shifter (
        .sf_i(sf),
        .x_i(shifter_source_data_i),
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

    assign memory_source_data_o = memory_dreg_data_i;
    assign sr_write_o = action_valid_o && raw_sr_write;
    assign se_write_o = action_valid_o && raw_se_write;
    assign sb_write_o = action_valid_o && raw_sb_write;
    assign ss_write_o = action_valid_o && raw_ss_write;
    assign unused_observation = ^{xop_unused, astat_i[6:4], astat_i[1:0]};

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        if (action_valid_o) begin
            assert ($onehot0({sr_write_o, se_write_o, sb_write_o}));
        end
        if (!action_valid_o) begin
            assert (!sr_write_o && !se_write_o && !sb_write_o && !ss_write_o);
        end
        if (unsupported_subencoding_o) begin
            assert (class_valid_o && !action_valid_o);
        end
    end
`endif
endmodule

`default_nettype wire
