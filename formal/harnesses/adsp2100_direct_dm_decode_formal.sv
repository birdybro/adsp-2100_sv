`default_nettype none

module adsp2100_direct_dm_decode_formal (
    input logic [23:0] opcode
);
    logic        class_valid;
    logic        action_valid;
    logic        invalid_subencoding;
    logic        write;
    logic [13:0] address;
    logic [1:0]  register_group;
    logic [3:0]  register_index;
    logic [5:0]  register_code;
    logic        register_present;
    logic        register_writable;
    logic        reserved_source;
    logic        reserved_destination;
    logic        read_only_destination;
    logic        expected_class;
    logic        expected_present;
    logic        expected_writable;

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

    assign expected_class = (opcode & 24'he00000) == 24'h800000;
    assign expected_present = expected_class
        && selector_present(opcode[19:18], opcode[3:0]);
    assign expected_writable = expected_present && !(
        opcode[19:18] == 2'b11 && opcode[3:0] == 4'd2
    );

    adsp2100_direct_dm_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .invalid_subencoding_o(invalid_subencoding),
        .write_o(write),
        .address_o(address),
        .register_group_o(register_group),
        .register_index_o(register_index),
        .register_code_o(register_code),
        .register_present_o(register_present),
        .register_writable_o(register_writable),
        .reserved_source_o(reserved_source),
        .reserved_destination_o(reserved_destination),
        .read_only_destination_o(read_only_destination)
    );

    always_comb begin
        assert (class_valid == expected_class);
        assert (register_present == expected_present);
        assert (register_writable == expected_writable);
        assert (
            action_valid
            == (expected_class && (
                (opcode[20] && expected_present)
                || (!opcode[20] && expected_writable)
            ))
        );
        assert (invalid_subencoding == (expected_class && !action_valid));
        assert (reserved_source == (expected_class && opcode[20] && !expected_present));
        assert (reserved_destination == (expected_class && !opcode[20] && !expected_present));
        assert (read_only_destination == (
            expected_class && !opcode[20] && expected_present && !expected_writable
        ));
        if (expected_class) begin
            assert (write == opcode[20]);
            assert (address == opcode[17:4]);
            assert (register_group == opcode[19:18]);
            assert (register_index == opcode[3:0]);
            assert (register_code == {opcode[19:18], opcode[3:0]});
        end else begin
            assert (!write);
            assert (address == 14'h0000);
            assert (register_code == 6'h00);
        end
        cover (action_valid && !write);
        cover (action_valid && write);
        cover (reserved_source);
        cover (reserved_destination);
        cover (read_only_destination);
        cover (!class_valid);
    end
endmodule

`default_nettype wire
