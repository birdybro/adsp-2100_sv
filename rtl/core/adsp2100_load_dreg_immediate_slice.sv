`default_nettype none

module adsp2100_load_dreg_immediate_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        dreg_setup_write_i,
    input  logic [3:0]  dreg_setup_code_i,
    input  logic [15:0] dreg_setup_data_i,
    input  logic [3:0]  probe_code_i,

    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic [3:0]  destination_dreg_o,
    output logic [15:0] immediate_data_o,
    output logic [15:0] probe_data_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic       decode_valid;
    logic [3:0] decoded_destination;
    logic [15:0] decoded_data;
    logic       register_write;
    logic [3:0] register_write_code;
    logic [15:0] register_write_data;
    logic       register_conflict;
    logic       status_conflict;
    logic [15:0] unused_read_1;
    logic [15:0] unused_read_2;
    logic [15:0] unused_af;
    logic [15:0] unused_mf;
    logic [39:0] unused_mr;
    logic [7:0]  unused_se;
    logic [4:0]  unused_sb;
    logic [31:0] unused_sr;
    logic [7:0]  unused_astat;
    logic [4:0]  unused_icntl;
    logic [3:0]  unused_imask;
    logic        unused_bit_reverse;
    logic        unused_overflow_latch;
    logic        unused_saturate_ar;
    logic        unused_status_push;
    logic [7:0]  unused_status_push_astat;
    logic [3:0]  unused_status_push_mstat;
    logic [3:0]  unused_status_push_imask;

    adsp2100_load_dreg_immediate_decode decode (
        .opcode_i(opcode_i),
        .valid_o(decode_valid),
        .destination_dreg_o(decoded_destination),
        .immediate_data_o(decoded_data)
    );

    assign integration_conflict_o = (
        !reset_i
        && (
            (execute_i && (mstat_setup_write_i || dreg_setup_write_i))
            || (mstat_setup_write_i && dreg_setup_write_i)
        )
    );
    assign boundary_valid_o = (
        !reset_i
        && execute_i
        && decode_valid
        && !mstat_setup_write_i
        && !dreg_setup_write_i
    );
    assign invalid_opcode_o = (
        !reset_i
        && execute_i
        && !decode_valid
    );
    assign destination_dreg_o = decoded_destination;
    assign immediate_data_o = decoded_data;
    assign register_write = boundary_valid_o || (
        !reset_i
        && !execute_i
        && dreg_setup_write_i
        && !mstat_setup_write_i
    );
    assign register_write_code = boundary_valid_o
        ? decoded_destination
        : dreg_setup_code_i;
    assign register_write_data = boundary_valid_o
        ? decoded_data
        : dreg_setup_data_i;
    assign internal_conflict_o = register_conflict || status_conflict;
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    adsp2100_register_file registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(probe_code_i),
        .read_address_1_i(4'h0),
        .read_address_2_i(4'h0),
        .read_data_0_o(probe_data_o),
        .read_data_1_o(unused_read_1),
        .read_data_2_o(unused_read_2),
        .write_enable_0_i(register_write),
        .write_address_0_i(register_write_code),
        .write_data_0_i(register_write_data),
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
        .write_conflict_o(register_conflict)
    );

    adsp2100_status_registers status (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(1'b0),
        .astat_move_write_data_i(8'h00),
        .mstat_move_write_enable_i(
            !reset_i
            && !execute_i
            && mstat_setup_write_i
            && !dreg_setup_write_i
        ),
        .mstat_move_write_data_i(mstat_setup_data_i),
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
        .astat_o(unused_astat),
        .mstat_o(mstat_o),
        .icntl_o(unused_icntl),
        .imask_o(unused_imask),
        .alternate_bank_o(alternate_bank_o),
        .bit_reverse_o(unused_bit_reverse),
        .overflow_latch_o(unused_overflow_latch),
        .saturate_ar_o(unused_saturate_ar),
        .write_conflict_o(status_conflict),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );
endmodule

`default_nettype wire
