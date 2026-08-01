`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_load_non_dreg_immediate_decode;
    logic [23:0] opcode;
    logic class_valid;
    logic action_valid;
    logic invalid_subencoding;
    logic [1:0] register_group;
    logic [3:0] register_index;
    logic [5:0] register_code;
    logic [13:0] immediate_data;
    logic register_present;
    logic register_writable;
    logic data_register_destination;
    logic reserved_destination;
    logic read_only_destination;
    logic expected_present;
    logic expected_writable;
    integer unsigned payload;
    integer unsigned legal_count;
    integer unsigned invalid_count;

    function automatic logic selector_present (
        input logic [1:0] group,
        input logic [3:0] index
    );
        if (group == 2'b00) begin
            selector_present = 1'b1;
        end else if (group == 2'b01 || group == 2'b10) begin
            selector_present = index < 4'd12;
        end else begin
            selector_present = index < 4'd8;
        end
    endfunction

    adsp2100_load_non_dreg_immediate_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .invalid_subencoding_o(invalid_subencoding),
        .register_group_o(register_group),
        .register_index_o(register_index),
        .register_code_o(register_code),
        .immediate_data_o(immediate_data),
        .register_present_o(register_present),
        .register_writable_o(register_writable),
        .data_register_destination_o(data_register_destination),
        .reserved_destination_o(reserved_destination),
        .read_only_destination_o(read_only_destination)
    );

    initial begin
        legal_count = 0;
        invalid_count = 0;
        for (payload = 0; payload < 32'h00100000; payload = payload + 1) begin
            opcode = 24'h300000 | {4'b0000, payload[19:0]};
            #1;
            expected_present = selector_present(opcode[19:18], opcode[3:0]);
            expected_writable = (
                expected_present
                && opcode[19:18] != 2'b00
                && !(opcode[19:18] == 2'b11 && opcode[3:0] == 4'd2)
            );
            if (
                !class_valid
                || register_group !== opcode[19:18]
                || register_index !== opcode[3:0]
                || register_code !== {opcode[19:18], opcode[3:0]}
                || immediate_data !== opcode[17:4]
                || register_present !== expected_present
                || register_writable !== expected_writable
                || data_register_destination !== (opcode[19:18] == 2'b00)
                || reserved_destination !== !expected_present
                || read_only_destination !== (
                    opcode[19:18] == 2'b11 && opcode[3:0] == 4'd2
                )
                || action_valid !== expected_writable
                || invalid_subencoding !== !expected_writable
            ) begin
                $fatal(1, "Type 7 mismatch opcode=%06x", opcode);
            end
            if (action_valid) legal_count = legal_count + 1;
            else invalid_count = invalid_count + 1;
        end
        if (legal_count != 507904 || invalid_count != 540672) begin
            $fatal(
                1,
                "Type 7 counts wrong legal=%0d invalid=%0d",
                legal_count,
                invalid_count
            );
        end
        opcode = 24'h400000;
        #1;
        if (
            class_valid || action_valid || invalid_subencoding
            || register_group != 2'b00 || register_index != 4'h0
            || register_code != 6'h00 || immediate_data != 14'h0000
            || register_present || register_writable
            || data_register_destination || reserved_destination
            || read_only_destination
        ) begin
            $fatal(1, "non-Type-7 word emitted an action");
        end
        $display(
            "PASS Type 7 decode: 507904 legal, 540672 invalid words"
        );
        $finish;
    end
endmodule

`default_nettype wire
