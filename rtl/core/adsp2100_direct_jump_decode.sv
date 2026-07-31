`default_nettype none

module adsp2100_direct_jump_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_call_ce_o,
    output logic        call_o,
    output logic [13:0] address_o,
    output logic [3:0]  condition_o
);
    assign class_valid_o = (
        (opcode_i & 24'hf80000) == 24'h180000
    );
    assign call_o = class_valid_o ? opcode_i[18] : 1'b0;
    assign address_o = class_valid_o ? opcode_i[17:4] : 14'h0000;
    assign condition_o = class_valid_o ? opcode_i[3:0] : 4'h0;

    // Original conditional-CALL NOT CE state effects remain OQ-012. The
    // encoding is recognized but cannot enter the execution boundary.
    assign unsupported_call_ce_o = (
        class_valid_o && call_o && (condition_o == 4'he)
    );
    assign action_valid_o = class_valid_o && !unsupported_call_ce_o;
endmodule

`default_nettype wire
