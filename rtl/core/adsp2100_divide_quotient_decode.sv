`default_nettype none

module adsp2100_divide_quotient_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  divisor_source_dreg_o
);
    import adsp2100_register_pkg::*;

    assign class_valid_o = (
        (opcode_i & 24'hfff8ff) == 24'h071000
    );
    assign action_valid_o = class_valid_o;
    assign xop_o = class_valid_o ? opcode_i[10:8] : 3'b000;

    always_comb begin
        unique case (xop_o)
            3'd0: divisor_source_dreg_o = DREG_AX0;
            3'd1: divisor_source_dreg_o = DREG_AX1;
            3'd2: divisor_source_dreg_o = DREG_AR;
            3'd3: divisor_source_dreg_o = DREG_MR0;
            3'd4: divisor_source_dreg_o = DREG_MR1;
            3'd5: divisor_source_dreg_o = DREG_MR2;
            3'd6: divisor_source_dreg_o = DREG_SR0;
            default: divisor_source_dreg_o = DREG_SR1;
        endcase
    end
endmodule

`default_nettype wire
