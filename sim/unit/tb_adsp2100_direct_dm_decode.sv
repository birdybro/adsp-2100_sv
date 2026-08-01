`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_direct_dm_decode;
    logic [23:0] opcode;
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

    integer unsigned opcode_index;
    integer unsigned class_count;
    integer unsigned legal_read_count;
    integer unsigned legal_write_count;
    integer unsigned invalid_count;
    logic expected_class;
    logic expected_present;
    logic expected_writable;
    logic expected_action;

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

    initial begin
        class_count = 0;
        legal_read_count = 0;
        legal_write_count = 0;
        invalid_count = 0;
        for (
            opcode_index = 0;
            opcode_index < 32'h01000000;
            opcode_index = opcode_index + 1
        ) begin
            opcode = opcode_index[23:0];
            #1;
            expected_class = (opcode & 24'he00000) == 24'h800000;
            if (class_valid !== expected_class) begin
                $fatal(1, "class mismatch at opcode=%06x", opcode);
            end
            if (expected_class) begin
                class_count = class_count + 1;
                expected_present = expected_selector_present(
                    opcode[19:18], opcode[3:0]
                );
                expected_writable = expected_present && !(
                    opcode[19:18] == 2'b11 && opcode[3:0] == 4'd2
                );
                expected_action = (
                    (opcode[20] && expected_present)
                    || (!opcode[20] && expected_writable)
                );
                if (
                    write !== opcode[20]
                    || address !== opcode[17:4]
                    || register_group !== opcode[19:18]
                    || register_index !== opcode[3:0]
                    || register_code !== {opcode[19:18], opcode[3:0]}
                    || register_present !== expected_present
                    || register_writable !== expected_writable
                    || action_valid !== expected_action
                    || invalid_subencoding !== !expected_action
                    || reserved_source !== (opcode[20] && !expected_present)
                    || reserved_destination !== (!opcode[20] && !expected_present)
                    || read_only_destination !== (
                        !opcode[20] && expected_present && !expected_writable
                    )
                ) begin
                    $fatal(1, "Type 3 action mismatch at opcode=%06x", opcode);
                end
                if (!action_valid) begin
                    invalid_count = invalid_count + 1;
                end else if (write) begin
                    legal_write_count = legal_write_count + 1;
                end else begin
                    legal_read_count = legal_read_count + 1;
                end
            end else if (
                action_valid || invalid_subencoding || write
                || address != 14'h0000 || register_group != 2'b00
                || register_index != 4'h0 || register_code != 6'h00
                || register_present || register_writable
                || reserved_source || reserved_destination
                || read_only_destination
            ) begin
                $fatal(1, "non-Type-3 word emitted action at opcode=%06x", opcode);
            end
        end
        if (
            class_count != 2097152
            || legal_read_count != 770048
            || legal_write_count != 786432
            || invalid_count != 540672
        ) begin
            $fatal(
                1,
                "Type 3 counts wrong: class=%0d read=%0d write=%0d invalid=%0d",
                class_count, legal_read_count, legal_write_count, invalid_count
            );
        end
        $display(
            "PASS Type 3 decode: 770048 reads, 786432 writes, 540672 invalid"
        );
        $finish;
    end
endmodule

`default_nettype wire
