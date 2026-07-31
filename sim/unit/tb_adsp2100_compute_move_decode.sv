`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_compute_move_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        unverified_amf_zero;
    logic        destination_collision;
    logic        is_mac;
    logic        destination_feedback;
    logic [4:0]  amf;
    logic [1:0]  yop;
    logic [2:0]  xop;
    logic [3:0]  x_source;
    logic [3:0]  y_source;
    logic [3:0]  move_destination;
    logic [3:0]  move_source;
    logic        expected_class;
    logic        expected_amf_zero;
    logic        expected_collision;
    logic        expected_action;
    logic        expected_is_mac;
    logic [3:0]  expected_x_source;
    logic [3:0]  expected_y_source;
    integer      word;
    integer      class_count;
    integer      action_count;
    integer      amf_zero_count;
    integer      collision_count;

    adsp2100_compute_move_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .unverified_amf_zero_o(unverified_amf_zero),
        .destination_collision_o(destination_collision),
        .is_mac_o(is_mac),
        .destination_feedback_o(destination_feedback),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .y_source_dreg_o(y_source),
        .move_destination_dreg_o(move_destination),
        .move_source_dreg_o(move_source)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        action_count = 0;
        amf_zero_count = 0;
        collision_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'hf80000) == 24'h280000);
            expected_amf_zero = expected_class && opcode[17:13] == 5'h00;
            expected_collision = (
                expected_class
                && !expected_amf_zero
                && !opcode[18]
                && (
                    (
                        opcode[17]
                        && opcode[7:4] == 4'ha
                    )
                    || (
                        !opcode[17]
                        && opcode[7:4] >= 4'hb
                        && opcode[7:4] <= 4'hd
                    )
                )
            );
            expected_action = (
                expected_class
                && !expected_amf_zero
                && !expected_collision
            );
            expected_is_mac = (
                expected_class
                && !opcode[17]
                && !expected_amf_zero
            );
            if (class_valid !== expected_class
                || action_valid !== expected_action
                || unverified_amf_zero !== expected_amf_zero
                || destination_collision !== expected_collision
                || unsupported_subencoding
                    !== (expected_class && !expected_action)
                || is_mac !== expected_is_mac) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                if (destination_feedback !== opcode[18]
                    || amf !== opcode[17:13]
                    || yop !== opcode[12:11]
                    || xop !== opcode[10:8]
                    || move_destination !== opcode[7:4]
                    || move_source !== opcode[3:0]) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
            end else if (destination_feedback !== 1'b0
                || amf !== 5'h00 || yop !== 2'b00 || xop !== 3'b000
                || move_destination !== 4'h0 || move_source !== 4'h0) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
            expected_x_source = 4'h0;
            expected_y_source = 4'h0;
            if (expected_action) begin
                if (opcode[10:8] <= 3'd1) begin
                    expected_x_source = {
                        2'b00,
                        expected_is_mac,
                        opcode[8]
                    };
                end else begin
                    expected_x_source = {1'b1, opcode[10:8]};
                end
                if (opcode[12:11] <= 2'd1) begin
                    expected_y_source = {
                        1'b0,
                        1'b1,
                        expected_is_mac,
                        opcode[11]
                    };
                end
            end
            if (x_source !== expected_x_source
                || y_source !== expected_y_source) begin
                $fatal(1, "operand mapping mismatch word=%06x", word);
            end
            if (expected_class) class_count = class_count + 1;
            if (expected_action) action_count = action_count + 1;
            if (expected_amf_zero) amf_zero_count = amf_zero_count + 1;
            if (expected_collision) collision_count = collision_count + 1;
        end
        if (class_count != 524_288 || action_count != 476_672
            || amf_zero_count != 16_384 || collision_count != 31_232) begin
            $fatal(
                1,
                "counts class=%0d action=%0d amf0=%0d collision=%0d",
                class_count,
                action_count,
                amf_zero_count,
                collision_count
            );
        end
        $display(
            "PASS Type 8 decode: %0d supported, %0d unsupported",
            action_count,
            class_count - action_count
        );
        $finish;
    end
endmodule

`default_nettype wire
