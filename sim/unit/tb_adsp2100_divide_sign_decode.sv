`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_divide_sign_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_yop;
    logic [1:0]  yop;
    logic [2:0]  xop;
    logic [3:0]  x_source;
    logic [3:0]  upper_source;
    logic        upper_feedback;
    logic        expected_class;
    logic        expected_action;
    integer      word;
    integer      class_count;
    integer      action_count;

    adsp2100_divide_sign_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_yop_o(unsupported_yop),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .upper_source_dreg_o(upper_source),
        .upper_source_feedback_o(upper_feedback)
    );

    function automatic logic [3:0] expected_x_source(input logic [2:0] value);
        case (value)
            3'd0: expected_x_source = 4'h0;
            3'd1: expected_x_source = 4'h1;
            3'd2: expected_x_source = 4'ha;
            3'd3: expected_x_source = 4'hb;
            3'd4: expected_x_source = 4'hc;
            3'd5: expected_x_source = 4'hd;
            3'd6: expected_x_source = 4'he;
            default: expected_x_source = 4'hf;
        endcase
    endfunction

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        action_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'hffe0ff) == 24'h060000);
            expected_action = expected_class
                && (opcode[12:11] == 2'd1 || opcode[12:11] == 2'd2);
            if (class_valid !== expected_class
                || action_valid !== expected_action
                || unsupported_yop !== (expected_class && !expected_action)) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                if (yop !== opcode[12:11] || xop !== opcode[10:8]) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
                if (x_source !== expected_x_source(opcode[10:8])) begin
                    $fatal(1, "X source mismatch word=%06x", word);
                end
                if (expected_action && opcode[12:11] == 2'd1) begin
                    if (upper_source !== 4'h5 || upper_feedback) begin
                        $fatal(1, "AY1 source mismatch word=%06x", word);
                    end
                end else if (expected_action && opcode[12:11] == 2'd2) begin
                    if (upper_source !== 4'h0 || !upper_feedback) begin
                        $fatal(1, "AF source mismatch word=%06x", word);
                    end
                end
                class_count = class_count + 1;
                action_count = action_count + int'(expected_action);
            end else if (
                yop !== 2'd0 || xop !== 3'd0 || x_source !== 4'h0
                || upper_source !== 4'h0 || upper_feedback
            ) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
        end
        if (class_count != 32 || action_count != 16) begin
            $fatal(
                1,
                "unexpected Type 24 counts class=%0d action=%0d",
                class_count,
                action_count
            );
        end
        $display(
            "PASS Type 24 decode: %0d field words, %0d source-closed actions",
            class_count,
            action_count
        );
        $finish;
    end
endmodule

`default_nettype wire
