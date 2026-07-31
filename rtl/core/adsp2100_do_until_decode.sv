`default_nettype none

module adsp2100_do_until_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic [13:0] end_address_o,
    output logic [3:0]  termination_o
);
    assign class_valid_o = (
        (opcode_i & 24'hfc0000) == 24'h140000
    );
    assign action_valid_o = class_valid_o;
    assign end_address_o = class_valid_o ? opcode_i[17:4] : 14'h0000;
    assign termination_o = class_valid_o ? opcode_i[3:0] : 4'h0;
endmodule

`default_nettype wire
