`default_nettype none

module adsp2100_direct_dm_decode (
    input  logic [23:0] opcode_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        invalid_subencoding_o,
    output logic        write_o,
    output logic [13:0] address_o,
    output logic [1:0]  register_group_o,
    output logic [3:0]  register_index_o,
    output logic [5:0]  register_code_o,
    output logic        register_present_o,
    output logic        register_writable_o,
    output logic        reserved_source_o,
    output logic        reserved_destination_o,
    output logic        read_only_destination_o
);
    localparam logic [23:0] TYPE_03_MASK = 24'he00000;
    localparam logic [23:0] TYPE_03_VALUE = 24'h800000;

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
        class_valid_o = (opcode_i & TYPE_03_MASK) == TYPE_03_VALUE;
        action_valid_o = 1'b0;
        invalid_subencoding_o = 1'b0;
        write_o = 1'b0;
        address_o = 14'h0000;
        register_group_o = 2'b00;
        register_index_o = 4'h0;
        register_code_o = 6'h00;
        register_present_o = 1'b0;
        register_writable_o = 1'b0;
        reserved_source_o = 1'b0;
        reserved_destination_o = 1'b0;
        read_only_destination_o = 1'b0;

        if (class_valid_o) begin
            write_o = opcode_i[20];
            address_o = opcode_i[17:4];
            register_group_o = opcode_i[19:18];
            register_index_o = opcode_i[3:0];
            register_code_o = {opcode_i[19:18], opcode_i[3:0]};
            register_present_o = selector_present(
                opcode_i[19:18], opcode_i[3:0]
            );
            register_writable_o = (
                register_present_o
                && !(
                    opcode_i[19:18] == 2'b11
                    && opcode_i[3:0] == 4'd2
                )
            );
            reserved_source_o = opcode_i[20] && !register_present_o;
            reserved_destination_o = !opcode_i[20] && !register_present_o;
            read_only_destination_o = (
                !opcode_i[20]
                && register_present_o
                && !register_writable_o
            );
            action_valid_o = (
                (opcode_i[20] && register_present_o)
                || (!opcode_i[20] && register_writable_o)
            );
            invalid_subencoding_o = !action_valid_o;
        end
    end
endmodule

`default_nettype wire
