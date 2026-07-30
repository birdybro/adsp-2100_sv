`default_nettype none

module adsp2100_mode_slice (
    input  logic        clk_i,
    input  logic        reset_i,

    input  logic        astat_move_write_enable_i,
    input  logic [7:0]  astat_move_write_data_i,
    input  logic        mstat_move_write_enable_i,
    input  logic [3:0]  mstat_move_write_data_i,
    input  logic [1:0]  mode_sr_i,
    input  logic [1:0]  mode_br_i,
    input  logic [1:0]  mode_ol_i,
    input  logic [1:0]  mode_as_i,

    input  logic [3:0]  dreg_read_address_i,
    output logic [15:0] dreg_read_data_o,
    input  logic        dreg_write_enable_i,
    input  logic [3:0]  dreg_write_address_i,
    input  logic [15:0] dreg_write_data_i,

    input  logic        alu_execute_i,
    input  logic [4:0]  alu_amf_i,
    input  logic [15:0] alu_x_i,
    input  logic [15:0] alu_y_i,
    input  logic        alu_destination_feedback_i,
    output logic        alu_valid_o,
    output logic [15:0] alu_raw_result_o,
    output logic [15:0] alu_destination_result_o,

    input  logic [13:0] dag1_i_i,
    input  logic [13:0] dag1_m_i,
    input  logic [13:0] dag1_l_i,
    output logic [13:0] dag1_address_o,
    output logic [13:0] dag1_next_i_o,

    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o,
    output logic        bit_reverse_o,
    output logic        overflow_latch_o,
    output logic        saturate_ar_o,
    output logic        status_write_conflict_o,
    output logic        register_write_conflict_o
);
    logic        alu_az;
    logic        alu_an;
    logic        alu_av;
    logic        alu_ac;
    logic        alu_as_value;
    logic        alu_as_write;
    logic        alu_commit;
    logic [4:0]  unused_icntl;
    logic [3:0]  unused_imask;
    logic [15:0] unused_read_1;
    logic [15:0] unused_read_2;
    logic [15:0] unused_af;
    logic [15:0] unused_mf;
    logic [39:0] unused_mr;
    logic [7:0]  unused_se;
    logic [4:0]  unused_sb;
    logic [31:0] unused_sr;
    logic [13:0] unused_dag_base;
    logic        unused_dag_circular;
    logic        unused_dag_valid;
    logic        unused_status_push;
    logic [7:0]  unused_status_push_astat;
    logic [3:0]  unused_status_push_mstat;
    logic [3:0]  unused_status_push_imask;

    assign alu_commit = alu_execute_i && alu_valid_o && !reset_i;

    adsp2100_alu alu (
        .amf_i(alu_amf_i),
        .x_i(alu_x_i),
        .y_i(alu_y_i),
        .carry_i(astat_o[3]),
        .previous_av_i(astat_o[2]),
        .sticky_av_i(overflow_latch_o),
        .saturate_ar_i(saturate_ar_o),
        .destination_is_ar_i(!alu_destination_feedback_i),
        .valid_o(alu_valid_o),
        .raw_result_o(alu_raw_result_o),
        .destination_result_o(alu_destination_result_o),
        .az_o(alu_az),
        .an_o(alu_an),
        .av_o(alu_av),
        .ac_o(alu_ac),
        .as_value_o(alu_as_value),
        .as_write_o(alu_as_write)
    );

    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b1)
    ) dag1 (
        .i_i(dag1_i_i),
        .m_i(dag1_m_i),
        .l_i(dag1_l_i),
        .bit_reverse_enable_i(bit_reverse_o),
        .address_o(dag1_address_o),
        .next_i_o(dag1_next_i_o),
        .base_o(unused_dag_base),
        .circular_o(unused_dag_circular),
        .configuration_valid_o(unused_dag_valid)
    );

    adsp2100_status_registers status_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(astat_move_write_enable_i),
        .astat_move_write_data_i(astat_move_write_data_i),
        .mstat_move_write_enable_i(mstat_move_write_enable_i),
        .mstat_move_write_data_i(mstat_move_write_data_i),
        .icntl_move_write_enable_i(1'b0),
        .icntl_move_write_data_i(5'h00),
        .imask_move_write_enable_i(1'b0),
        .imask_move_write_data_i(4'h0),
        .mode_sr_i(mode_sr_i),
        .mode_br_i(mode_br_i),
        .mode_ol_i(mode_ol_i),
        .mode_as_i(mode_as_i),
        .alu_status_write_enable_i(alu_commit),
        .alu_az_i(alu_az),
        .alu_an_i(alu_an),
        .alu_av_i(alu_av),
        .alu_ac_i(alu_ac),
        .alu_as_write_enable_i(alu_as_write),
        .alu_as_i(alu_as_value),
        .divide_status_write_enable_i(1'b0),
        .divide_aq_i(1'b0),
        .mac_status_write_enable_i(1'b0),
        .mac_mv_i(1'b0),
        .shifter_status_write_enable_i(1'b0),
        .shifter_ss_i(1'b0),
        .interrupt_entry_i(1'b0),
        .interrupt_level_i(2'b00),
        .status_restore_i(1'b0),
        .restore_astat_i(8'h00),
        .restore_mstat_i(4'h0),
        .restore_imask_i(4'h0),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(unused_icntl),
        .imask_o(unused_imask),
        .alternate_bank_o(alternate_bank_o),
        .bit_reverse_o(bit_reverse_o),
        .overflow_latch_o(overflow_latch_o),
        .saturate_ar_o(saturate_ar_o),
        .write_conflict_o(status_write_conflict_o),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );

    adsp2100_register_file register_file (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(dreg_read_address_i),
        .read_address_1_i(4'h0),
        .read_address_2_i(4'h0),
        .read_data_0_o(dreg_read_data_o),
        .read_data_1_o(unused_read_1),
        .read_data_2_o(unused_read_2),
        .write_enable_0_i(dreg_write_enable_i && !reset_i),
        .write_address_0_i(dreg_write_address_i),
        .write_data_0_i(dreg_write_data_i),
        .write_enable_1_i(1'b0),
        .write_address_1_i(4'h0),
        .write_data_1_i(16'h0000),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(1'b0),
        .sb_move_write_data_i(5'h00),
        .alu_write_enable_i(alu_commit),
        .alu_destination_feedback_i(alu_destination_feedback_i),
        .alu_result_i(alu_destination_result_o),
        .mac_write_enable_i(1'b0),
        .mac_destination_feedback_i(1'b0),
        .mac_result_i(40'h0000000000),
        .shifter_sr_write_enable_i(1'b0),
        .shifter_sr_result_i(32'h00000000),
        .shifter_se_write_enable_i(1'b0),
        .shifter_se_result_i(8'h00),
        .shifter_sb_write_enable_i(1'b0),
        .shifter_sb_result_i(5'h00),
        .af_o(unused_af),
        .mf_o(unused_mf),
        .mr_o(unused_mr),
        .se_o(unused_se),
        .sb_o(unused_sb),
        .sr_o(unused_sr),
        .write_conflict_o(register_write_conflict_o)
    );
endmodule

`default_nettype wire
