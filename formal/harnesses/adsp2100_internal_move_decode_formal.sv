`default_nettype none

module adsp2100_internal_move_decode_formal (
    input logic [23:0] opcode
);
    logic        class_valid;
    logic        move_valid;
    logic        invalid_subencoding;
    logic [1:0]  destination_group;
    logic [1:0]  source_group;
    logic [3:0]  destination_index;
    logic [3:0]  source_index;
    logic [5:0]  destination_code;
    logic [5:0]  source_code;
    logic        destination_present;
    logic        destination_writable;
    logic        source_valid;
    logic        expected_class;
    logic        expected_destination_present;
    logic        expected_source_valid;
    logic        expected_destination_writable;

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

    assign expected_class = (
        (opcode & 24'hfff000) == 24'h0d0000
    );
    assign expected_destination_present = (
        expected_class
        && selector_present(opcode[11:10], opcode[7:4])
    );
    assign expected_source_valid = (
        expected_class
        && selector_present(opcode[9:8], opcode[3:0])
    );
    assign expected_destination_writable = (
        expected_destination_present
        && !(
            opcode[11:10] == 2'b11
            && opcode[7:4] == 4'd2
        )
    );

    adsp2100_internal_move_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .move_valid_o(move_valid),
        .invalid_subencoding_o(invalid_subencoding),
        .destination_group_o(destination_group),
        .source_group_o(source_group),
        .destination_index_o(destination_index),
        .source_index_o(source_index),
        .destination_code_o(destination_code),
        .source_code_o(source_code),
        .destination_present_o(destination_present),
        .destination_writable_o(destination_writable),
        .source_valid_o(source_valid)
    );

    always_comb begin
        assert (class_valid == expected_class);
        assert (
            destination_present
            == expected_destination_present
        );
        assert (
            destination_writable
            == expected_destination_writable
        );
        assert (source_valid == expected_source_valid);
        assert (
            move_valid
            == (expected_source_valid && expected_destination_writable)
        );
        assert (
            invalid_subencoding
            == (expected_class && !move_valid)
        );
        if (expected_class) begin
            assert (destination_group == opcode[11:10]);
            assert (source_group == opcode[9:8]);
            assert (destination_index == opcode[7:4]);
            assert (source_index == opcode[3:0]);
            assert (
                destination_code
                == {opcode[11:10], opcode[7:4]}
            );
            assert (
                source_code
                == {opcode[9:8], opcode[3:0]}
            );
        end else begin
            assert (destination_code == 6'b000000);
            assert (source_code == 6'b000000);
        end
        cover (move_valid);
        cover (
            expected_class
            && destination_present
            && !destination_writable
        );
        cover (
            expected_class
            && (!destination_present || !source_valid)
        );
        cover (!expected_class);
    end
endmodule

`default_nettype wire
