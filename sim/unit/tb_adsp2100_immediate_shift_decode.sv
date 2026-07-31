`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_immediate_shift_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic [3:0]  sf;
    logic [2:0]  xop;
    logic [3:0]  source_dreg;
    logic [7:0]  exponent;
    logic        expected_class;
    logic        expected_action;
    logic [3:0]  expected_source;
    integer      word;
    integer      class_count;
    integer      action_count;
    integer      unsupported_count;

    adsp2100_immediate_shift_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .sf_o(sf),
        .xop_o(xop),
        .source_dreg_o(source_dreg),
        .exponent_o(exponent)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        action_count = 0;
        unsupported_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = (
                (opcode & 24'hff8000) == 24'h0f0000
            );
            expected_action = (
                expected_class
                && !opcode[14]
                && (opcode[10:8] != 3'b001)
            );
            if (class_valid !== expected_class) begin
                $fatal(1, "class mismatch word=%06x", word);
            end
            if (action_valid !== expected_action) begin
                $fatal(1, "action mismatch word=%06x", word);
            end
            if (
                unsupported_subencoding
                !== (expected_class && !expected_action)
            ) begin
                $fatal(1, "unsupported mismatch word=%06x", word);
            end
            if (expected_class) begin
                class_count = class_count + 1;
                if (sf !== opcode[14:11] || xop !== opcode[10:8]
                    || exponent !== opcode[7:0]) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
            end else if (sf !== 4'h0 || xop !== 3'h0
                || exponent !== 8'h00) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
            if (expected_action) begin
                unique case (opcode[10:8])
                    3'b000: expected_source = 4'h8;
                    3'b010: expected_source = 4'ha;
                    3'b011: expected_source = 4'hb;
                    3'b100: expected_source = 4'hc;
                    3'b101: expected_source = 4'hd;
                    3'b110: expected_source = 4'he;
                    default: expected_source = 4'hf;
                endcase
                if (source_dreg !== expected_source) begin
                    $fatal(1, "source mismatch word=%06x", word);
                end
                action_count = action_count + 1;
            end else begin
                if (source_dreg !== 4'h0) begin
                    $fatal(1, "invalid source leakage word=%06x", word);
                end
                if (expected_class) begin
                    unsupported_count = unsupported_count + 1;
                end
            end
        end
        if (class_count != 32_768 || action_count != 14_336
            || unsupported_count != 18_432) begin
            $fatal(
                1,
                "unexpected counts class=%0d action=%0d unsupported=%0d",
                class_count,
                action_count,
                unsupported_count
            );
        end
        $display(
            "PASS Type 15 decode: %0d legal, %0d unsupported subencodings",
            action_count,
            unsupported_count
        );
        $finish;
    end
endmodule

`default_nettype wire
