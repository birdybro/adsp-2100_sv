`default_nettype none

module adsp2100_divide_sign_slice (
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
    input  logic        af_setup_write_i,
    input  logic [15:0] af_setup_data_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_yop_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  upper_source_dreg_o,
    output logic        upper_source_feedback_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        source_known_o,
    output logic        result_known_o,
    output logic        quotient_sign_o,
    output logic [15:0] divisor_before_o,
    output logic [15:0] upper_before_o,
    output logic [15:0] ay0_before_o,
    output logic [15:0] af_result_o,
    output logic [15:0] ay0_result_o,
    output logic        af_write_o,
    output logic        ay0_write_o,
    output logic        aq_write_o,
    output logic [15:0] af_o,
    output logic        af_valid_o,
    output logic [15:0] ay0_o,
    output logic        ay0_valid_o,
    output logic [7:0]  astat_o,
    output logic [7:0]  astat_valid_mask_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    import adsp2100_register_pkg::*;

    logic [2:0] setup_count;
    logic       astat_setup_enable;
    logic       mstat_setup_enable;
    logic       dreg_setup_enable;
    logic       af_setup_enable;
    logic       known_execute_enable;
    logic [15:0] dreg_valid_q [0:1];
    logic        af_valid_q [0:1];
    logic [7:0]  astat_valid_mask_q;
    logic [15:0] divisor_data;
    logic [15:0] upper_dreg_data;
    logic [15:0] upper_data;
    logic [15:0] ay0_data;
    logic        divisor_valid;
    logic        upper_valid;
    logic        register_conflict;
    logic        status_conflict;
    logic [15:0] unused_mf;
    logic [15:0] unused_read_data_3;
    logic [39:0] unused_mr;
    logic [7:0]  unused_se;
    logic [4:0]  unused_sb;
    logic [31:0] unused_sr;
    logic [4:0]  unused_icntl;
    logic [3:0]  unused_imask;
    logic        unused_bit_reverse;
    logic        unused_overflow_latch;
    logic        unused_saturate_ar;
    logic        unused_status_push;
    logic [7:0]  unused_status_push_astat;
    logic [3:0]  unused_status_push_mstat;
    logic [3:0]  unused_status_push_imask;

    adsp2100_divide_sign_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_yop_o(unsupported_yop_o),
        .yop_o(yop_o),
        .xop_o(xop_o),
        .x_source_dreg_o(x_source_dreg_o),
        .upper_source_dreg_o(upper_source_dreg_o),
        .upper_source_feedback_o(upper_source_feedback_o)
    );

    assign setup_count = (
        {2'b00, astat_setup_write_i}
        + {2'b00, mstat_setup_write_i}
        + {2'b00, dreg_setup_write_i}
        + {2'b00, af_setup_write_i}
    );
    assign integration_conflict_o = !reset_i && (
        (execute_i && setup_count != 3'd0) || setup_count > 3'd1
    );
    assign boundary_valid_o = (
        !reset_i && execute_i && action_valid_o && setup_count == 3'd0
    );
    assign invalid_opcode_o = (
        !reset_i && execute_i && !action_valid_o
    );
    assign astat_setup_enable = (
        !reset_i && !execute_i && setup_count == 3'd1
        && astat_setup_write_i
    );
    assign mstat_setup_enable = (
        !reset_i && !execute_i && setup_count == 3'd1
        && mstat_setup_write_i
    );
    assign dreg_setup_enable = (
        !reset_i && !execute_i && setup_count == 3'd1
        && dreg_setup_write_i
    );
    assign af_setup_enable = (
        !reset_i && !execute_i && setup_count == 3'd1
        && af_setup_write_i
    );

    assign divisor_valid = dreg_valid_q[alternate_bank_o][x_source_dreg_o];
    assign upper_valid = upper_source_feedback_o
        ? af_valid_q[alternate_bank_o]
        : dreg_valid_q[alternate_bank_o][upper_source_dreg_o];
    assign source_known_o = (
        boundary_valid_o
        && divisor_valid
        && upper_valid
        && dreg_valid_q[alternate_bank_o][DREG_AY0]
    );
    assign result_known_o = source_known_o;
    assign known_execute_enable = boundary_valid_o && source_known_o;
    assign upper_data = upper_source_feedback_o ? af_o : upper_dreg_data;
    assign quotient_sign_o = divisor_data[15] ^ upper_data[15];
    assign af_result_o = {upper_data[14:0], ay0_data[15]};
    assign ay0_result_o = {ay0_data[14:0], quotient_sign_o};
    assign divisor_before_o = divisor_data;
    assign upper_before_o = upper_data;
    assign ay0_before_o = ay0_data;
    assign af_write_o = boundary_valid_o;
    assign ay0_write_o = boundary_valid_o;
    assign aq_write_o = boundary_valid_o;
    assign af_valid_o = af_valid_q[alternate_bank_o];
    assign ay0_o = ay0_data;
    assign ay0_valid_o = dreg_valid_q[alternate_bank_o][DREG_AY0];
    assign astat_valid_mask_o = astat_valid_mask_q;
    assign internal_conflict_o = register_conflict || status_conflict;
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    adsp2100_register_file registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(x_source_dreg_o),
        .read_address_1_i(upper_source_dreg_o),
        .read_address_2_i(DREG_AY0),
        .read_address_3_i(4'h0),
        .read_data_0_o(divisor_data),
        .read_data_1_o(upper_dreg_data),
        .read_data_2_o(ay0_data),
        .read_data_3_o(unused_read_data_3),
        .write_enable_0_i(dreg_setup_enable || known_execute_enable),
        .write_address_0_i(
            known_execute_enable ? DREG_AY0 : dreg_setup_code_i
        ),
        .write_data_0_i(
            known_execute_enable ? ay0_result_o : dreg_setup_data_i
        ),
        .write_enable_1_i(1'b0),
        .write_address_1_i(4'h0),
        .write_data_1_i(16'h0000),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(1'b0),
        .sb_move_write_data_i(5'h00),
        .alu_write_enable_i(af_setup_enable || known_execute_enable),
        .alu_destination_feedback_i(1'b1),
        .alu_result_i(af_setup_enable ? af_setup_data_i : af_result_o),
        .mac_write_enable_i(1'b0),
        .mac_destination_feedback_i(1'b0),
        .mac_result_i(40'h0000000000),
        .shifter_sr_write_enable_i(1'b0),
        .shifter_sr_result_i(32'h00000000),
        .shifter_se_write_enable_i(1'b0),
        .shifter_se_result_i(8'h00),
        .shifter_sb_write_enable_i(1'b0),
        .shifter_sb_result_i(5'h00),
        .af_o(af_o),
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
        .divide_status_write_enable_i(known_execute_enable),
        .divide_aq_i(quotient_sign_o),
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
        .bit_reverse_o(unused_bit_reverse),
        .overflow_latch_o(unused_overflow_latch),
        .saturate_ar_o(unused_saturate_ar),
        .write_conflict_o(status_conflict),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );

    // Validity is verification metadata, not substituted architectural data.
    // It prevents FPGA/simulator power-up convenience from becoming a claim
    // that the original computational registers or ASTAT reset to zero.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            dreg_valid_q[0] <= 16'h0000;
            dreg_valid_q[1] <= 16'h0000;
            af_valid_q[0] <= 1'b0;
            af_valid_q[1] <= 1'b0;
            astat_valid_mask_q <= 8'h00;
        end else if (!integration_conflict_o && !internal_conflict_o) begin
            if (astat_setup_enable) begin
                astat_valid_mask_q <= 8'hff;
            end
            if (dreg_setup_enable) begin
                dreg_valid_q[alternate_bank_o][dreg_setup_code_i] <= 1'b1;
                if (dreg_setup_code_i == DREG_MR1) begin
                    dreg_valid_q[alternate_bank_o][DREG_MR2] <= 1'b1;
                end
            end
            if (af_setup_enable) begin
                af_valid_q[alternate_bank_o] <= 1'b1;
            end
            if (boundary_valid_o) begin
                dreg_valid_q[alternate_bank_o][DREG_AY0] <= source_known_o;
                af_valid_q[alternate_bank_o] <= source_known_o;
                astat_valid_mask_q[5] <= source_known_o;
            end
        end
    end

    always_comb begin
        if (!boundary_valid_o) begin
            assert (!af_write_o && !ay0_write_o && !aq_write_o);
        end
        if (known_execute_enable) begin
            assert (!register_conflict && !status_conflict);
        end
        assert (!pm_data_access_o && !dm_access_o);
    end
endmodule

`default_nettype wire
