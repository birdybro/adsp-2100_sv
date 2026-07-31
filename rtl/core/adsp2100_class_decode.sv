`default_nettype none

module adsp2100_class_decode (
    input  logic [23:0] opcode_i,
    output logic [4:0]  instruction_class_o
);
    import adsp2100_pkg::*;
    import adsp2100_decode_pkg::*;

    instruction_class_t decoded_class;

    always_comb begin
        decoded_class = decode_instruction_class(program_word_t'(opcode_i));
        instruction_class_o = decoded_class;
    end
endmodule

`default_nettype wire
