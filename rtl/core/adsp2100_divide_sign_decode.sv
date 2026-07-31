`default_nettype none

module adsp2100_divide_sign_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_yop_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  upper_source_dreg_o,
    output logic        upper_source_feedback_o
);
    import adsp2100_register_pkg::*;

    assign class_valid_o = (
        (opcode_i & 24'hffe0ff) == 24'h060000
    );
    assign yop_o = class_valid_o ? opcode_i[12:11] : 2'b00;
    assign xop_o = class_valid_o ? opcode_i[10:8] : 3'b000;
    assign action_valid_o = class_valid_o && (
        (opcode_i[12:11] == 2'd1) || (opcode_i[12:11] == 2'd2)
    );
    assign unsupported_yop_o = class_valid_o && !action_valid_o;
    assign upper_source_feedback_o = action_valid_o && (yop_o == 2'd2);
    assign upper_source_dreg_o = (
        action_valid_o && (yop_o == 2'd1) ? DREG_AY1 : DREG_AX0
    );

    always_comb begin
        unique case (xop_o)
            3'd0: x_source_dreg_o = DREG_AX0;
            3'd1: x_source_dreg_o = DREG_AX1;
            3'd2: x_source_dreg_o = DREG_AR;
            3'd3: x_source_dreg_o = DREG_MR0;
            3'd4: x_source_dreg_o = DREG_MR1;
            3'd5: x_source_dreg_o = DREG_MR2;
            3'd6: x_source_dreg_o = DREG_SR0;
            default: x_source_dreg_o = DREG_SR1;
        endcase
    end
endmodule

`default_nettype wire
