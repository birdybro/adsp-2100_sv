`default_nettype none

module adsp2100_compute_move_slice (
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
    input  logic        mf_setup_write_i,
    input  logic [15:0] mf_setup_data_i,
    input  logic        inspect_probe_i,
    input  logic [3:0]  probe_code_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        unverified_amf_zero_o,
    output logic        destination_collision_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        is_mac_o,
    output logic        destination_feedback_o,
    output logic [4:0]  amf_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  y_source_dreg_o,
    output logic [3:0]  move_destination_dreg_o,
    output logic [3:0]  move_source_dreg_o,
    output logic [15:0] x_source_data_o,
    output logic [15:0] y_source_data_o,
    output logic [15:0] move_source_data_o,
    output logic [15:0] alu_result_o,
    output logic [39:0] mac_result_o,
    output logic        move_write_o,
    output logic        alu_write_o,
    output logic        mac_write_o,
    output logic        alu_status_write_o,
    output logic        mac_status_write_o,
    output logic [15:0] probe_data_o,
    output logic [15:0] af_o,
    output logic [15:0] mf_o,
    output logic [39:0] mr_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic [3:0] setup_count;
    logic       astat_setup_enable;
    logic       mstat_setup_enable;
    logic       dreg_setup_enable;
    logic       af_setup_enable;
    logic       mf_setup_enable;
    logic       register_write_enable;
    logic [3:0] register_write_address;
    logic [15:0] register_write_data;
    logic [3:0] read_address_2;
    logic [15:0] y_dreg_data;
    logic [15:0] read_data_2;
    logic [15:0] unused_read_3;
    logic [47:0] unused_additional_read_data;
    logic       alu_valid;
    logic       mac_valid;
    logic [15:0] unused_alu_raw_result;
    logic       alu_az;
    logic       alu_an;
    logic       alu_av;
    logic       alu_ac;
    logic       alu_as;
    logic       alu_as_write;
    logic [39:0] unused_mac_unrounded;
    logic [15:0] unused_mac_mf_result;
    logic       mac_mv;
    logic [39:0] unused_saturated_mr;
    logic       register_conflict;
    logic       status_conflict;
    logic [7:0] unused_se;
    logic [4:0] unused_sb;
    logic [31:0] unused_sr;
    logic [4:0] unused_icntl;
    logic [3:0] unused_imask;
    logic       unused_bit_reverse;
    logic       overflow_latch;
    logic       saturate_ar;
    logic       unused_status_push;
    logic [7:0] unused_status_push_astat;
    logic [3:0] unused_status_push_mstat;
    logic [3:0] unused_status_push_imask;

    adsp2100_compute_move_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .unverified_amf_zero_o(unverified_amf_zero_o),
        .destination_collision_o(destination_collision_o),
        .is_mac_o(is_mac_o),
        .destination_feedback_o(destination_feedback_o),
        .amf_o(amf_o),
        .yop_o(yop_o),
        .xop_o(xop_o),
        .x_source_dreg_o(x_source_dreg_o),
        .y_source_dreg_o(y_source_dreg_o),
        .move_destination_dreg_o(move_destination_dreg_o),
        .move_source_dreg_o(move_source_dreg_o)
    );

    assign setup_count = (
        {3'h0, astat_setup_write_i}
        + {3'h0, mstat_setup_write_i}
        + {3'h0, dreg_setup_write_i}
        + {3'h0, af_setup_write_i}
        + {3'h0, mf_setup_write_i}
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
    assign invalid_opcode_o = !reset_i && execute_i && !action_valid_o;
    assign astat_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && astat_setup_write_i
    );
    assign mstat_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && mstat_setup_write_i
    );
    assign dreg_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && dreg_setup_write_i
    );
    assign af_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && af_setup_write_i
    );
    assign mf_setup_enable = (
        !reset_i && !execute_i && (setup_count == 4'h1)
        && mf_setup_write_i
    );
    assign move_write_o = boundary_valid_o;
    assign alu_write_o = boundary_valid_o && !is_mac_o;
    assign mac_write_o = boundary_valid_o && is_mac_o;
    assign alu_status_write_o = alu_write_o;
    assign mac_status_write_o = mac_write_o;
    assign register_write_enable = dreg_setup_enable || move_write_o;
    assign register_write_address = (
        dreg_setup_enable ? dreg_setup_code_i : move_destination_dreg_o
    );
    assign register_write_data = (
        dreg_setup_enable ? dreg_setup_data_i : move_source_data_o
    );
    assign read_address_2 = inspect_probe_i ? probe_code_i : move_source_dreg_o;
    assign probe_data_o = read_data_2;
    assign move_source_data_o = read_data_2;
    assign y_source_data_o = (
        (yop_o == 2'd3) ? 16'h0000
        : (yop_o == 2'd2) ? (is_mac_o ? mf_o : af_o)
        : y_dreg_data
    );
    assign internal_conflict_o = register_conflict || status_conflict;
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    adsp2100_alu alu (
        .amf_i(amf_o),
        .x_i(x_source_data_o),
        .y_i(y_source_data_o),
        .carry_i(astat_o[3]),
        .previous_av_i(astat_o[2]),
        .sticky_av_i(overflow_latch),
        .saturate_ar_i(saturate_ar),
        .destination_is_ar_i(!destination_feedback_o),
        .valid_o(alu_valid),
        .raw_result_o(unused_alu_raw_result),
        .destination_result_o(alu_result_o),
        .az_o(alu_az),
        .an_o(alu_an),
        .av_o(alu_av),
        .ac_o(alu_ac),
        .as_value_o(alu_as),
        .as_write_o(alu_as_write)
    );

    adsp2100_mac mac (
        .amf_i(amf_o),
        .x_i(x_source_data_o),
        .y_i(y_source_data_o),
        .mr_i(mr_o),
        .saturation_mv_i(astat_o[6]),
        .valid_o(mac_valid),
        .unrounded_result_o(unused_mac_unrounded),
        .result_o(mac_result_o),
        .mf_result_o(unused_mac_mf_result),
        .mv_o(mac_mv),
        .saturated_mr_o(unused_saturated_mr)
    );

    adsp2100_register_file registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(x_source_dreg_o),
        .read_address_1_i(y_source_dreg_o),
        .read_address_2_i(read_address_2),
        .read_address_3_i(4'h0),
        .read_address_4_i(4'h0),
        .read_address_5_i(4'h0),
        .read_address_6_i(4'h0),
        .read_data_0_o(x_source_data_o),
        .read_data_1_o(y_dreg_data),
        .read_data_2_o(read_data_2),
        .read_data_3_o(unused_read_3),
        .read_data_4_o(unused_additional_read_data[15:0]),
        .read_data_5_o(unused_additional_read_data[31:16]),
        .read_data_6_o(unused_additional_read_data[47:32]),
        .write_enable_0_i(register_write_enable),
        .write_address_0_i(register_write_address),
        .write_data_0_i(register_write_data),
        .write_enable_1_i(1'b0),
        .write_address_1_i(4'h0),
        .write_data_1_i(16'h0000),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(1'b0),
        .sb_move_write_data_i(5'h00),
        .alu_write_enable_i(alu_write_o || af_setup_enable),
        .alu_destination_feedback_i(destination_feedback_o || af_setup_enable),
        .alu_result_i(af_setup_enable ? af_setup_data_i : alu_result_o),
        .mac_write_enable_i(mac_write_o || mf_setup_enable),
        .mac_destination_feedback_i(destination_feedback_o || mf_setup_enable),
        .mac_result_i(
            mf_setup_enable ? {8'h00, mf_setup_data_i, 16'h0000}
            : mac_result_o
        ),
        .shifter_sr_write_enable_i(1'b0),
        .shifter_sr_result_i(32'h00000000),
        .shifter_se_write_enable_i(1'b0),
        .shifter_se_result_i(8'h00),
        .shifter_sb_write_enable_i(1'b0),
        .shifter_sb_result_i(5'h00),
        .af_o(af_o),
        .mf_o(mf_o),
        .mr_o(mr_o),
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
        .alu_status_write_enable_i(alu_status_write_o),
        .alu_az_i(alu_az),
        .alu_an_i(alu_an),
        .alu_av_i(alu_av),
        .alu_ac_i(alu_ac),
        .alu_as_write_enable_i(alu_as_write),
        .alu_as_i(alu_as),
        .divide_status_write_enable_i(1'b0),
        .divide_aq_i(1'b0),
        .mac_status_write_enable_i(mac_status_write_o),
        .mac_mv_i(mac_mv),
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
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .write_conflict_o(status_conflict),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );

    // Both compute blocks are present for portable inference, but exact Type 8
    // decode selects exactly one valid unit for every executable word.
    always_comb begin
        if (boundary_valid_o) begin
            if (is_mac_o) begin
                assert (mac_valid && !alu_valid);
            end else begin
                assert (alu_valid && !mac_valid);
            end
        end
    end
endmodule

`default_nettype wire
