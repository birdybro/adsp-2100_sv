`default_nettype none

module adsp2100_load_dreg_immediate_decode (
    input  logic [23:0] opcode_i,
    output logic        valid_o,
    output logic [3:0]  destination_dreg_o,
    output logic [15:0] immediate_data_o
);
    assign valid_o = ((opcode_i & 24'hf00000) == 24'h400000);
    assign destination_dreg_o = valid_o ? opcode_i[3:0] : 4'h0;
    assign immediate_data_o = valid_o ? opcode_i[19:4] : 16'h0000;
endmodule

`default_nettype wire
