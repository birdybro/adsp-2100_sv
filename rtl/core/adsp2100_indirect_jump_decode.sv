`default_nettype none

module adsp2100_indirect_jump_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_call_ce_o,
    output logic        call_o,
    output logic [1:0]  i_local_o,
    output logic [2:0]  i_address_o,
    output logic [3:0]  condition_o
);
    // Original Type 19 fixes bit 5 to zero. Accepting it as variable imports
    // a later/emulator decode conflict recorded as SC-007.
    assign class_valid_o = (
        (opcode_i & 24'hffff20) == 24'h0b0000
    );
    assign i_local_o = class_valid_o ? opcode_i[7:6] : 2'b00;
    assign i_address_o = class_valid_o ? {1'b1, opcode_i[7:6]} : 3'b000;
    assign call_o = class_valid_o ? opcode_i[4] : 1'b0;
    assign condition_o = class_valid_o ? opcode_i[3:0] : 4'h0;

    assign unsupported_call_ce_o = (
        class_valid_o && call_o && (condition_o == 4'he)
    );
    assign action_valid_o = class_valid_o && !unsupported_call_ce_o;
endmodule

`default_nettype wire
