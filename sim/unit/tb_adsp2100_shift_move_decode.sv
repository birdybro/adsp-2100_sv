`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_shift_move_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        unverified_unused_x;
    logic        unavailable_xop;
    logic        destination_collision;
    logic [3:0]  sf;
    logic [2:0]  xop;
    logic [3:0]  shifter_source;
    logic [3:0]  move_destination;
    logic [3:0]  move_source;
    logic        expected_class;
    logic        expected_unused_x;
    logic        expected_unavailable_xop;
    logic        expected_collision;
    logic        expected_action;
    logic [3:0]  expected_shifter_source;
    integer      word;
    integer      class_count;
    integer      action_count;
    integer      unused_x_count;
    integer      unavailable_xop_count;
    integer      collision_count;

    adsp2100_shift_move_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .unverified_unused_x_o(unverified_unused_x),
        .unavailable_xop_o(unavailable_xop),
        .destination_collision_o(destination_collision),
        .sf_o(sf),
        .xop_o(xop),
        .shifter_source_dreg_o(shifter_source),
        .move_destination_dreg_o(move_destination),
        .move_source_dreg_o(move_source)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        action_count = 0;
        unused_x_count = 0;
        unavailable_xop_count = 0;
        collision_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'hff0000) == 24'h100000);
            expected_unused_x = expected_class && opcode[15];
            expected_unavailable_xop = (
                expected_class
                && !opcode[15]
                && (opcode[10:8] == 3'b001)
            );
            expected_collision = (
                expected_class
                && !opcode[15]
                && (opcode[10:8] != 3'b001)
                && (
                    (
                        (opcode[14:11] <= 4'hb)
                        && (
                            (opcode[7:4] == 4'he)
                            || (opcode[7:4] == 4'hf)
                        )
                    )
                    || (
                        (opcode[14:11] >= 4'hc)
                        && (opcode[14:11] <= 4'he)
                        && (opcode[7:4] == 4'h9)
                    )
                )
            );
            expected_action = (
                expected_class
                && !expected_unused_x
                && !expected_unavailable_xop
                && !expected_collision
            );
            if (class_valid !== expected_class
                || action_valid !== expected_action
                || unverified_unused_x !== expected_unused_x
                || unavailable_xop !== expected_unavailable_xop
                || destination_collision !== expected_collision
                || unsupported_subencoding
                    !== (expected_class && !expected_action)) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                class_count = class_count + 1;
                if (sf !== opcode[14:11] || xop !== opcode[10:8]
                    || move_destination !== opcode[7:4]
                    || move_source !== opcode[3:0]) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
            end else if (sf !== 4'h0 || xop !== 3'h0
                || move_destination !== 4'h0 || move_source !== 4'h0) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
            if (expected_action) begin
                unique case (opcode[10:8])
                    3'b000: expected_shifter_source = 4'h8;
                    3'b010: expected_shifter_source = 4'ha;
                    3'b011: expected_shifter_source = 4'hb;
                    3'b100: expected_shifter_source = 4'hc;
                    3'b101: expected_shifter_source = 4'hd;
                    3'b110: expected_shifter_source = 4'he;
                    default: expected_shifter_source = 4'hf;
                endcase
                if (shifter_source !== expected_shifter_source) begin
                    $fatal(1, "source mismatch word=%06x", word);
                end
                action_count = action_count + 1;
            end else if (shifter_source !== 4'h0) begin
                $fatal(1, "invalid source leakage word=%06x", word);
            end
            if (expected_unused_x) begin
                unused_x_count = unused_x_count + 1;
            end
            if (expected_unavailable_xop) begin
                unavailable_xop_count = unavailable_xop_count + 1;
            end
            if (expected_collision) begin
                collision_count = collision_count + 1;
            end
        end
        if (class_count != 65_536 || action_count != 25_648
            || unused_x_count != 32_768
            || unavailable_xop_count != 4_096
            || collision_count != 3_024) begin
            $fatal(
                1,
                "counts class=%0d action=%0d x=%0d xop=%0d collision=%0d",
                class_count,
                action_count,
                unused_x_count,
                unavailable_xop_count,
                collision_count
            );
        end
        $display(
            "PASS Type 14 decode: %0d supported, %0d unsupported",
            action_count,
            class_count - action_count
        );
        $finish;
    end
endmodule

`default_nettype wire
