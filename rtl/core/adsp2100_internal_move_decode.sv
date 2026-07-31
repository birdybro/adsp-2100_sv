`default_nettype none

module adsp2100_internal_move_decode (
    input  logic [23:0] opcode_i,

    output logic        class_valid_o,
    output logic        move_valid_o,
    output logic        invalid_subencoding_o,
    output logic [1:0]  destination_group_o,
    output logic [1:0]  source_group_o,
    output logic [3:0]  destination_index_o,
    output logic [3:0]  source_index_o,
    output logic [5:0]  destination_code_o,
    output logic [5:0]  source_code_o,
    output logic        destination_present_o,
    output logic        destination_writable_o,
    output logic        source_valid_o
);
    localparam logic [23:0] TYPE_17_MASK = 24'hfff000;
    localparam logic [23:0] TYPE_17_VALUE = 24'h0d0000;

    function automatic logic selector_present (
        input logic [1:0] group,
        input logic [3:0] index
    );
        case (group)
            2'b00: selector_present = 1'b1;
            2'b01,
            2'b10: selector_present = index < 4'd12;
            2'b11: selector_present = index < 4'd8;
            default: selector_present = 1'b0;
        endcase
    endfunction

    always_comb begin
        class_valid_o = (
            (opcode_i & TYPE_17_MASK) == TYPE_17_VALUE
        );
        destination_group_o = 2'b00;
        source_group_o = 2'b00;
        destination_index_o = 4'b0000;
        source_index_o = 4'b0000;
        destination_code_o = 6'b000000;
        source_code_o = 6'b000000;
        destination_present_o = 1'b0;
        destination_writable_o = 1'b0;
        source_valid_o = 1'b0;
        move_valid_o = 1'b0;
        invalid_subencoding_o = 1'b0;

        if (class_valid_o) begin
            destination_group_o = opcode_i[11:10];
            source_group_o = opcode_i[9:8];
            destination_index_o = opcode_i[7:4];
            source_index_o = opcode_i[3:0];
            destination_code_o = {
                opcode_i[11:10],
                opcode_i[7:4]
            };
            source_code_o = {
                opcode_i[9:8],
                opcode_i[3:0]
            };
            destination_present_o = selector_present(
                opcode_i[11:10],
                opcode_i[7:4]
            );
            source_valid_o = selector_present(
                opcode_i[9:8],
                opcode_i[3:0]
            );
            destination_writable_o = (
                destination_present_o
                && !(
                    opcode_i[11:10] == 2'b11
                    && opcode_i[7:4] == 4'd2
                )
            );
            move_valid_o = (
                source_valid_o
                && destination_writable_o
            );
            invalid_subencoding_o = !move_valid_o;
        end
    end
endmodule

`default_nettype wire
