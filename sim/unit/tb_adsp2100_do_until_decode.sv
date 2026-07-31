`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_do_until_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic [13:0] end_address;
    logic [3:0]  termination;
    logic        expected_class;
    integer      word;
    integer      class_count;

    adsp2100_do_until_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .end_address_o(end_address),
        .termination_o(termination)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'hfc0000) == 24'h140000);
            if (class_valid !== expected_class
                || action_valid !== expected_class) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                if (end_address !== opcode[17:4]
                    || termination !== opcode[3:0]) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
                class_count = class_count + 1;
            end else if (end_address !== 14'h0000
                || termination !== 4'h0) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
        end
        if (class_count != 262_144) begin
            $fatal(1, "unexpected Type 11 count=%0d", class_count);
        end
        $display("PASS Type 11 decode: %0d legal field words", class_count);
        $finish;
    end
endmodule

`default_nettype wire
