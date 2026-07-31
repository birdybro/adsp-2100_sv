`default_nettype none

module adsp2100_mode_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic       mstat_setup_write_i,
    input  logic [3:0] mstat_setup_write_data_i,

    output logic       boundary_valid_o,
    output logic       invalid_opcode_o,
    output logic       integration_conflict_o,
    output logic       internal_conflict_o,
    output logic [1:0] decoded_mode_sr_o,
    output logic [1:0] decoded_mode_br_o,
    output logic [1:0] decoded_mode_ol_o,
    output logic [1:0] decoded_mode_as_o,
    output logic       decoded_has_effect_o,
    output logic       decoded_has_alias_o,
    output logic [3:0] mstat_o,
    output logic       alternate_bank_o,
    output logic       bit_reverse_o,
    output logic       overflow_latch_o,
    output logic       saturate_ar_o
);
    logic       decode_valid;
    logic [1:0] decoded_sr;
    logic [1:0] decoded_br;
    logic [1:0] decoded_ol;
    logic [1:0] decoded_as;
    logic       decoded_has_effect;
    logic       decoded_has_alias;
    logic [1:0] applied_sr;
    logic [1:0] applied_br;
    logic [1:0] applied_ol;
    logic [1:0] applied_as;
    logic       status_write_conflict;
    logic       setup_write_enable;
    logic [7:0] unused_astat;
    logic [4:0] unused_icntl;
    logic [3:0] unused_imask;
    logic       unused_status_push;
    logic [7:0] unused_status_push_astat;
    logic [3:0] unused_status_push_mstat;
    logic [3:0] unused_status_push_imask;

    adsp2100_mode_control_decode decode (
        .opcode_i(opcode_i),
        .valid_o(decode_valid),
        .mode_sr_o(decoded_sr),
        .mode_br_o(decoded_br),
        .mode_ol_o(decoded_ol),
        .mode_as_o(decoded_as),
        .has_effect_o(decoded_has_effect),
        .has_no_change_one_alias_o(decoded_has_alias)
    );

    assign boundary_valid_o = (
        !reset_i
        && execute_i
        && decode_valid
        && !mstat_setup_write_i
    );
    assign invalid_opcode_o = (
        !reset_i
        && execute_i
        && !decode_valid
    );
    assign integration_conflict_o = (
        !reset_i
        && execute_i
        && mstat_setup_write_i
    );
    assign decoded_mode_sr_o = decoded_sr;
    assign decoded_mode_br_o = decoded_br;
    assign decoded_mode_ol_o = decoded_ol;
    assign decoded_mode_as_o = decoded_as;
    assign decoded_has_effect_o = decode_valid && decoded_has_effect;
    assign decoded_has_alias_o = decode_valid && decoded_has_alias;

    assign applied_sr = boundary_valid_o ? decoded_sr : 2'b00;
    assign applied_br = boundary_valid_o ? decoded_br : 2'b00;
    assign applied_ol = boundary_valid_o ? decoded_ol : 2'b00;
    assign applied_as = boundary_valid_o ? decoded_as : 2'b00;
    assign setup_write_enable = (
        mstat_setup_write_i
        && !integration_conflict_o
    );
    assign internal_conflict_o = status_write_conflict;

    adsp2100_status_registers status_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(1'b0),
        .astat_move_write_data_i(8'h00),
        .mstat_move_write_enable_i(setup_write_enable),
        .mstat_move_write_data_i(mstat_setup_write_data_i),
        .icntl_move_write_enable_i(1'b0),
        .icntl_move_write_data_i(5'h00),
        .imask_move_write_enable_i(1'b0),
        .imask_move_write_data_i(4'h0),
        .mode_sr_i(applied_sr),
        .mode_br_i(applied_br),
        .mode_ol_i(applied_ol),
        .mode_as_i(applied_as),
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
        .bit_reverse_o(bit_reverse_o),
        .overflow_latch_o(overflow_latch_o),
        .saturate_ar_o(saturate_ar_o),
        .write_conflict_o(status_write_conflict),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );
endmodule

`default_nettype wire
