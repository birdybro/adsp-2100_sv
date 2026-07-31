`default_nettype none

module adsp2100_mode_control_decode (
    input  logic [23:0] opcode_i,

    output logic        valid_o,
    output logic [1:0]  mode_sr_o,
    output logic [1:0]  mode_br_o,
    output logic [1:0]  mode_ol_o,
    output logic [1:0]  mode_as_o,
    output logic        has_effect_o,
    output logic        has_no_change_one_alias_o
);
    localparam logic [23:0] TYPE_18_MASK = 24'hfff00f;
    localparam logic [23:0] TYPE_18_VALUE = 24'h0c0000;

    always_comb begin
        valid_o = (opcode_i & TYPE_18_MASK) == TYPE_18_VALUE;
        mode_sr_o = 2'b00;
        mode_br_o = 2'b00;
        mode_ol_o = 2'b00;
        mode_as_o = 2'b00;
        has_effect_o = 1'b0;
        has_no_change_one_alias_o = 1'b0;

        if (valid_o) begin
            mode_sr_o = opcode_i[5:4];
            mode_br_o = opcode_i[7:6];
            mode_ol_o = opcode_i[9:8];
            mode_as_o = opcode_i[11:10];
            has_effect_o = (
                opcode_i[5]
                || opcode_i[7]
                || opcode_i[9]
                || opcode_i[11]
            );
            has_no_change_one_alias_o = (
                (opcode_i[5:4] == 2'b01)
                || (opcode_i[7:6] == 2'b01)
                || (opcode_i[9:8] == 2'b01)
                || (opcode_i[11:10] == 2'b01)
            );
        end
    end
endmodule

`default_nettype wire
