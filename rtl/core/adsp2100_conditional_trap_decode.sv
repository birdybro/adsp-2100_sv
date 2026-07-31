`default_nettype none

module adsp2100_conditional_trap_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic [3:0]  condition_o
);
    assign class_valid_o = (
        (opcode_i & 24'hfffff0) == 24'h080000
    );
    assign action_valid_o = class_valid_o;
    assign condition_o = class_valid_o ? opcode_i[3:0] : 4'h0;
endmodule

`default_nettype wire
