`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_conditional_compute_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported;
    logic        nop_action;
    logic        is_mac;
    logic        is_alu;
    logic        destination_feedback;
    logic [4:0]  amf;
    logic [1:0]  yop;
    logic [2:0]  xop;
    logic [3:0]  condition;
    logic [3:0]  x_source;
    logic [3:0]  y_source;
    logic        expected_class;
    logic        expected_nop;
    logic        expected_mac;
    logic        expected_alu;
    logic [3:0]  expected_x_source;
    logic [3:0]  expected_y_source;
    integer      word;
    integer      class_count;
    integer      nop_count;
    integer      compute_count;

    adsp2100_conditional_compute_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported),
        .nop_action_o(nop_action),
        .is_mac_o(is_mac),
        .is_alu_o(is_alu),
        .destination_feedback_o(destination_feedback),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .condition_o(condition),
        .x_source_dreg_o(x_source),
        .y_source_dreg_o(y_source)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        nop_count = 0;
        compute_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'hf800f0) == 24'h200000);
            expected_nop = expected_class && opcode[17:13] == 5'h00;
            expected_mac = (
                expected_class && opcode[17:13] > 5'h00 && !opcode[17]
            );
            expected_alu = expected_class && opcode[17];
            if (class_valid !== expected_class
                || action_valid !== expected_class
                || unsupported !== 1'b0
                || nop_action !== expected_nop
                || is_mac !== expected_mac
                || is_alu !== expected_alu) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                if (destination_feedback !== opcode[18]
                    || amf !== opcode[17:13]
                    || yop !== opcode[12:11]
                    || xop !== opcode[10:8]
                    || condition !== opcode[3:0]) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
            end else if (destination_feedback !== 1'b0
                || amf !== 5'h00 || yop !== 2'b00 || xop !== 3'b000
                || condition !== 4'h0) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
            expected_x_source = 4'h0;
            expected_y_source = 4'h0;
            if (expected_class && !expected_nop) begin
                if (opcode[10:8] <= 3'd1) begin
                    expected_x_source = {
                        2'b00, expected_mac, opcode[8]
                    };
                end else begin
                    expected_x_source = {1'b1, opcode[10:8]};
                end
                if (opcode[12:11] <= 2'd1) begin
                    expected_y_source = {
                        2'b01, expected_mac, opcode[11]
                    };
                end
            end
            if (x_source !== expected_x_source
                || y_source !== expected_y_source) begin
                $fatal(1, "operand mapping mismatch word=%06x", word);
            end
            if (expected_class) class_count = class_count + 1;
            if (expected_nop) nop_count = nop_count + 1;
            if (expected_mac || expected_alu) compute_count = compute_count + 1;
        end
        if (class_count != 32_768 || nop_count != 1_024
            || compute_count != 31_744) begin
            $fatal(
                1,
                "counts class=%0d nop=%0d compute=%0d",
                class_count,
                nop_count,
                compute_count
            );
        end
        $display(
            "PASS Type 9 decode: %0d compute words, %0d NOP aliases",
            compute_count,
            nop_count
        );
        $finish;
    end
endmodule

`default_nettype wire
