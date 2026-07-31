`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_load_dreg_immediate_decode;
    logic [23:0] opcode;
    logic        valid;
    logic [3:0]  destination;
    logic [15:0] immediate;
    integer      word;
    integer      valid_count;
    logic        expected_valid;

    adsp2100_load_dreg_immediate_decode dut (
        .opcode_i(opcode),
        .valid_o(valid),
        .destination_dreg_o(destination),
        .immediate_data_o(immediate)
    );

    initial begin
        opcode = 24'h000000;
        valid_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_valid = (opcode[23:20] == 4'h4);
            if (valid !== expected_valid) begin
                $fatal(1, "valid mismatch word=%06x", word);
            end
            if (expected_valid) begin
                valid_count = valid_count + 1;
                if (
                    destination !== word[3:0]
                    || immediate !== word[19:4]
                ) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
            end else if (
                destination !== 4'h0
                || immediate !== 16'h0000
            ) begin
                $fatal(1, "nonclass action word=%06x", word);
            end
        end
        if (valid_count != 1_048_576) begin
            $fatal(1, "unexpected Type 6 count=%0d", valid_count);
        end
        $display(
            "PASS Type 6 decode: %0d field-defined words",
            valid_count
        );
        $finish;
    end
endmodule

`default_nettype wire
