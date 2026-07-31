`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_conditional_return_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        interrupt_return;
    logic [3:0]  condition;
    logic        expected_class;
    integer      word;
    integer      class_count;

    adsp2100_conditional_return_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .interrupt_return_o(interrupt_return),
        .condition_o(condition)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'hffffe0) == 24'h0a0000);
            if (class_valid !== expected_class
                || action_valid !== expected_class) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                if (interrupt_return !== opcode[4]
                    || condition !== opcode[3:0]) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
                class_count = class_count + 1;
            end else if (interrupt_return !== 1'b0
                || condition !== 4'h0) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
        end
        if (class_count != 32) begin
            $fatal(1, "unexpected Type 20 count=%0d", class_count);
        end
        $display("PASS Type 20 decode: %0d source-backed words", class_count);
        $finish;
    end
endmodule

`default_nettype wire
