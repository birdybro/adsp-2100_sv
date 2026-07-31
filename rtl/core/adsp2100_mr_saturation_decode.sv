`default_nettype none

module adsp2100_mr_saturation_decode (
    input  logic [23:0] opcode_i,
    output logic        valid_o
);
    assign valid_o = opcode_i == 24'h050000;
endmodule

`default_nettype wire
