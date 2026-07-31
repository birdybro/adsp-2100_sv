`default_nettype none

module adsp2100_shift_move_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        dreg_setup_write_i,
    input  logic [3:0]  dreg_setup_code_i,
    input  logic [15:0] dreg_setup_data_i,
    input  logic        sb_setup_write_i,
    input  logic [4:0]  sb_setup_data_i,
    input  logic [3:0]  probe_code_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        unverified_unused_x_o,
    output logic        unavailable_xop_o,
    output logic        destination_collision_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic [3:0]  sf_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  shifter_source_dreg_o,
    output logic [3:0]  move_destination_dreg_o,
    output logic [3:0]  move_source_dreg_o,
    output logic [15:0] shifter_source_data_o,
    output logic [15:0] move_source_data_o,
    output logic [31:0] sr_result_o,
    output logic [7:0]  se_result_o,
    output logic [4:0]  sb_result_o,
    output logic        ss_result_o,
    output logic        move_write_o,
    output logic        sr_write_o,
    output logic        se_write_o,
    output logic        sb_write_o,
    output logic        ss_write_o,
    output logic [15:0] probe_data_o,
    output logic [31:0] sr_o,
    output logic [7:0]  se_o,
    output logic [4:0]  sb_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic [3:0] setup_count;
    logic       dreg_setup_enable;
    logic       sb_setup_enable;
    logic       astat_setup_enable;
    logic       mstat_setup_enable;
    logic       raw_sr_write;
    logic       raw_se_write;
    logic       raw_sb_write;
    logic       raw_ss_write;
    logic       register_write_enable;
    logic [3:0] register_write_address;
    logic [15:0] register_write_data;
    logic       register_conflict;
    logic       status_conflict;
    logic [15:0] unused_af;
    logic [15:0] unused_mf;
    logic [39:0] unused_mr;
    logic [4:0] unused_icntl;
    logic [3:0] unused_imask;
    logic       unused_bit_reverse;
    logic       unused_overflow_latch;
    logic       unused_saturate_ar;
    logic       unused_status_push;
    logic [7:0] unused_status_push_astat;
    logic [3:0] unused_status_push_mstat;
    logic [3:0] unused_status_push_imask;

    adsp2100_shift_move_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .unverified_unused_x_o(unverified_unused_x_o),
        .unavailable_xop_o(unavailable_xop_o),
        .destination_collision_o(destination_collision_o),
        .sf_o(sf_o),
        .xop_o(xop_o),
        .shifter_source_dreg_o(shifter_source_dreg_o),
        .move_destination_dreg_o(move_destination_dreg_o),
        .move_source_dreg_o(move_source_dreg_o)
    );

    assign setup_count = (
        {3'h0, astat_setup_write_i}
        + {3'h0, mstat_setup_write_i}
        + {3'h0, dreg_setup_write_i}
        + {3'h0, sb_setup_write_i}
    );
    assign integration_conflict_o = (
        !reset_i
        && (
            (execute_i && (setup_count != 4'h0))
            || (setup_count > 4'h1)
        )
    );
    assign boundary_valid_o = (
        !reset_i
        && execute_i
        && action_valid_o
        && (setup_count == 4'h0)
    );
    assign invalid_opcode_o = (
        !reset_i
        && execute_i
        && !action_valid_o
    );
    assign dreg_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && dreg_setup_write_i
    );
    assign sb_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && sb_setup_write_i
    );
    assign astat_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && astat_setup_write_i
    );
    assign mstat_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && mstat_setup_write_i
    );
    assign move_write_o = boundary_valid_o;
    assign sr_write_o = boundary_valid_o && raw_sr_write;
    assign se_write_o = boundary_valid_o && raw_se_write;
    assign sb_write_o = boundary_valid_o && raw_sb_write;
    assign ss_write_o = boundary_valid_o && raw_ss_write;
    assign register_write_enable = dreg_setup_enable || move_write_o;
    assign register_write_address = (
        dreg_setup_enable ? dreg_setup_code_i : move_destination_dreg_o
    );
    assign register_write_data = (
        dreg_setup_enable ? dreg_setup_data_i : move_source_data_o
    );
    assign internal_conflict_o = register_conflict || status_conflict;
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    adsp2100_shifter shifter (
        .sf_i(sf_o),
        .x_i(shifter_source_data_o),
        .shift_or_se_i(se_o),
        .sr_i(sr_o),
        .sb_i(sb_o),
        .av_i(astat_o[2]),
        .ac_i(astat_o[3]),
        .ss_i(astat_o[7]),
        .sr_result_o(sr_result_o),
        .sr_write_o(raw_sr_write),
        .se_result_o(se_result_o),
        .se_write_o(raw_se_write),
        .sb_result_o(sb_result_o),
        .sb_write_o(raw_sb_write),
        .ss_result_o(ss_result_o),
        .ss_write_o(raw_ss_write)
    );

    adsp2100_register_file registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(shifter_source_dreg_o),
        .read_address_1_i(move_source_dreg_o),
        .read_address_2_i(probe_code_i),
        .read_data_0_o(shifter_source_data_o),
        .read_data_1_o(move_source_data_o),
        .read_data_2_o(probe_data_o),
        .write_enable_0_i(register_write_enable),
        .write_address_0_i(register_write_address),
        .write_data_0_i(register_write_data),
        .write_enable_1_i(1'b0),
        .write_address_1_i(4'h0),
        .write_data_1_i(16'h0000),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(sb_setup_enable),
        .sb_move_write_data_i(sb_setup_data_i),
        .alu_write_enable_i(1'b0),
        .alu_destination_feedback_i(1'b0),
        .alu_result_i(16'h0000),
        .mac_write_enable_i(1'b0),
        .mac_destination_feedback_i(1'b0),
        .mac_result_i(40'h0000000000),
        .shifter_sr_write_enable_i(sr_write_o),
        .shifter_sr_result_i(sr_result_o),
        .shifter_se_write_enable_i(se_write_o),
        .shifter_se_result_i(se_result_o),
        .shifter_sb_write_enable_i(sb_write_o),
        .shifter_sb_result_i(sb_result_o),
        .af_o(unused_af),
        .mf_o(unused_mf),
        .mr_o(unused_mr),
        .se_o(se_o),
        .sb_o(sb_o),
        .sr_o(sr_o),
        .write_conflict_o(register_conflict)
    );

    adsp2100_status_registers status (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(astat_setup_enable),
        .astat_move_write_data_i(astat_setup_data_i),
        .mstat_move_write_enable_i(mstat_setup_enable),
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
        .shifter_status_write_enable_i(ss_write_o),
        .shifter_ss_i(ss_result_o),
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
