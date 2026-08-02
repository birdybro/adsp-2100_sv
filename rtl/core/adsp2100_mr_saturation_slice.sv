`default_nettype none

module adsp2100_mr_saturation_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        astat_write_i,
    input  logic [7:0]  astat_write_data_i,
    input  logic        mstat_write_i,
    input  logic [3:0]  mstat_write_data_i,
    input  logic        mr_setup_write_i,
    input  logic [39:0] mr_setup_write_data_i,

    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        condition_mv_o,
    output logic        selected_bank_alternate_o,
    output logic        mr_write_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [39:0] mr_o
);
    logic decode_valid;
    logic setup_action;
    logic setup_allowed;
    logic status_write_conflict;
    logic register_write_conflict;
    logic mac_write_enable;
    logic [39:0] saturated_mr;
    logic [39:0] mac_write_data;
    logic [4:0] unused_icntl;
    logic [3:0] unused_imask;
    logic unused_bit_reverse;
    logic unused_overflow_latch;
    logic unused_saturate_ar;
    logic unused_status_push;
    logic [7:0] unused_status_push_astat;
    logic [3:0] unused_status_push_mstat;
    logic [3:0] unused_status_push_imask;
    logic [15:0] unused_read_data_0;
    logic [15:0] unused_read_data_1;
    logic [15:0] unused_read_data_2;
    logic [15:0] unused_read_data_3;
    logic [47:0] unused_additional_read_data;
    logic [15:0] unused_af;
    logic [15:0] unused_mf;
    logic [7:0] unused_se;
    logic [4:0] unused_sb;
    logic [31:0] unused_sr;

    adsp2100_mr_saturation_decode decode (
        .opcode_i(opcode_i),
        .valid_o(decode_valid)
    );

    assign setup_action = (
        astat_write_i
        || mstat_write_i
        || mr_setup_write_i
    );
    assign integration_conflict_o = (
        !reset_i
        && execute_i
        && setup_action
    );
    assign invalid_opcode_o = (
        !reset_i
        && execute_i
        && !decode_valid
    );
    assign boundary_valid_o = (
        !reset_i
        && execute_i
        && decode_valid
        && !integration_conflict_o
    );
    assign setup_allowed = (
        !reset_i
        && !integration_conflict_o
    );
    assign condition_mv_o = astat_o[6];
    assign mr_write_o = boundary_valid_o && condition_mv_o;
    assign mac_write_enable = (
        (setup_allowed && mr_setup_write_i)
        || mr_write_o
    );
    assign mac_write_data = (
        (setup_allowed && mr_setup_write_i)
        ? mr_setup_write_data_i
        : saturated_mr
    );
    assign internal_conflict_o = (
        status_write_conflict
        || register_write_conflict
    );

    adsp2100_mr_saturate saturation (
        .mr_i(mr_o),
        .mv_i(condition_mv_o),
        .result_o(saturated_mr)
    );

    adsp2100_status_registers status (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(
            setup_allowed && astat_write_i
        ),
        .astat_move_write_data_i(astat_write_data_i),
        .mstat_move_write_enable_i(
            setup_allowed && mstat_write_i
        ),
        .mstat_move_write_data_i(mstat_write_data_i),
        .icntl_move_write_enable_i(1'b0),
        .icntl_move_write_data_i(5'h00),
        .imask_move_write_enable_i(1'b0),
        .imask_move_write_data_i(4'h0),
        .mode_sr_i(2'b00),
        .mode_br_i(2'b00),
        .mode_ol_i(2'b00),
        .mode_as_i(2'b00),
        .alu_status_write_enable_i(1'b0),
        .alu_az_i(1'b0),
        .alu_an_i(1'b0),
        .alu_av_i(1'b0),
        .alu_ac_i(1'b0),
        .alu_as_write_enable_i(1'b0),
        .alu_as_i(1'b0),
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
        .alternate_bank_o(selected_bank_alternate_o),
        .bit_reverse_o(unused_bit_reverse),
        .overflow_latch_o(unused_overflow_latch),
        .saturate_ar_o(unused_saturate_ar),
        .write_conflict_o(status_write_conflict),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );

    adsp2100_register_file registers (
        .clk_i(clk_i),
        .alternate_bank_i(selected_bank_alternate_o),
        .read_address_0_i(4'h0),
        .read_address_1_i(4'h0),
        .read_address_2_i(4'h0),
        .read_address_3_i(4'h0),
        .read_address_4_i(4'h0),
        .read_address_5_i(4'h0),
        .read_address_6_i(4'h0),
        .read_data_0_o(unused_read_data_0),
        .read_data_1_o(unused_read_data_1),
        .read_data_2_o(unused_read_data_2),
        .read_data_3_o(unused_read_data_3),
        .read_data_4_o(unused_additional_read_data[15:0]),
        .read_data_5_o(unused_additional_read_data[31:16]),
        .read_data_6_o(unused_additional_read_data[47:32]),
        .write_enable_0_i(1'b0),
        .write_address_0_i(4'h0),
        .write_data_0_i(16'h0000),
        .write_enable_1_i(1'b0),
        .write_address_1_i(4'h0),
        .write_data_1_i(16'h0000),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(1'b0),
        .sb_move_write_data_i(5'h00),
        .alu_write_enable_i(1'b0),
        .alu_destination_feedback_i(1'b0),
        .alu_result_i(16'h0000),
        .mac_write_enable_i(mac_write_enable),
        .mac_destination_feedback_i(1'b0),
        .mac_result_i(mac_write_data),
        .shifter_sr_write_enable_i(1'b0),
        .shifter_sr_result_i(32'h00000000),
        .shifter_se_write_enable_i(1'b0),
        .shifter_se_result_i(8'h00),
        .shifter_sb_write_enable_i(1'b0),
        .shifter_sb_result_i(5'h00),
        .af_o(unused_af),
        .mf_o(unused_mf),
        .mr_o(mr_o),
        .se_o(unused_se),
        .sb_o(unused_sb),
        .sr_o(unused_sr),
        .write_conflict_o(register_write_conflict)
    );
endmodule

`default_nettype wire
