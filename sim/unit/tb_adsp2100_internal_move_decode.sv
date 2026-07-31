`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_internal_move_decode;
    logic [23:0] opcode;
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

    integer unsigned opcode_index;
    integer unsigned class_count;
    integer unsigned legal_count;
    integer unsigned invalid_count;
    logic expected_class;
    logic expected_destination_present;
    logic expected_destination_writable;
    logic expected_source_valid;
    logic expected_move;

    function automatic logic expected_selector_present (
        input logic [1:0] group,
        input logic [3:0] index
    );
        if (group == 2'b00) begin
            expected_selector_present = 1'b1;
        end else if (group == 2'b01 || group == 2'b10) begin
            expected_selector_present = index <= 4'd11;
        end else begin
            expected_selector_present = index <= 4'd7;
        end
    endfunction

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

    initial begin
        class_count = 0;
        legal_count = 0;
        invalid_count = 0;
        for (
            opcode_index = 0;
            opcode_index < 32'h01000000;
            opcode_index = opcode_index + 1
        ) begin
            opcode = opcode_index[23:0];
            #1;
            expected_class = (
                (opcode & 24'hfff000) == 24'h0d0000
            );
            if (class_valid !== expected_class) begin
                $fatal(1, "class mismatch at opcode=%06x", opcode);
            end
            if (expected_class) begin
                class_count = class_count + 1;
                expected_destination_present =
                    expected_selector_present(
                        opcode[11:10],
                        opcode[7:4]
                    );
                expected_source_valid = expected_selector_present(
                    opcode[9:8],
                    opcode[3:0]
                );
                expected_destination_writable = (
                    expected_destination_present
                    && !(
                        opcode[11:10] == 2'b11
                        && opcode[7:4] == 4'd2
                    )
                );
                expected_move = (
                    expected_source_valid
                    && expected_destination_writable
                );
                if (
                    destination_group !== opcode[11:10]
                    || source_group !== opcode[9:8]
                    || destination_index !== opcode[7:4]
                    || source_index !== opcode[3:0]
                    || destination_code
                        !== {opcode[11:10], opcode[7:4]}
                    || source_code
                        !== {opcode[9:8], opcode[3:0]}
                    || destination_present
                        !== expected_destination_present
                    || destination_writable
                        !== expected_destination_writable
                    || source_valid !== expected_source_valid
                    || move_valid !== expected_move
                    || invalid_subencoding !== !expected_move
                ) begin
                    $fatal(
                        1,
                        "Type 17 action mismatch at opcode=%06x",
                        opcode
                    );
                end
                if (move_valid) begin
                    legal_count = legal_count + 1;
                end else begin
                    invalid_count = invalid_count + 1;
                end
            end else if (
                move_valid
                || invalid_subencoding
                || destination_group != 2'b00
                || source_group != 2'b00
                || destination_index != 4'b0000
                || source_index != 4'b0000
                || destination_code != 6'b000000
                || source_code != 6'b000000
                || destination_present
                || destination_writable
                || source_valid
            ) begin
                $fatal(
                    1,
                    "non-Type-17 word emitted action at opcode=%06x",
                    opcode
                );
            end
        end
        if (
            class_count != 4096
            || legal_count != 2256
            || invalid_count != 1840
        ) begin
            $fatal(
                1,
                "Type 17 counts wrong: class=%0d legal=%0d invalid=%0d",
                class_count,
                legal_count,
                invalid_count
            );
        end
        $display(
            "PASS Type 17 decode: 2256 legal, 1840 invalid subencodings"
        );
        $finish;
    end
endmodule

`default_nettype wire
