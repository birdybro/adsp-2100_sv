`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_shifter_dm_decode;
    logic [23:0] opcode;
    logic class_valid;
    logic action_valid;
    logic unsupported;
    logic unavailable_xop;
    logic collision;
    logic dag_select;
    logic write_direction;
    logic [3:0] sf;
    logic [2:0] xop;
    logic [3:0] shifter_source;
    logic [3:0] memory_dreg;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic expected_class;
    logic expected_unavailable;
    logic expected_raw_collision;
    logic expected_collision;
    logic expected_action;
    logic [3:0] expected_source;
    integer word;
    integer class_count;
    integer action_count;
    integer unavailable_count;
    integer collision_count;

    adsp2100_shifter_dm_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported),
        .unavailable_xop_o(unavailable_xop),
        .destination_collision_o(collision),
        .dag_select_o(dag_select),
        .write_o(write_direction),
        .sf_o(sf),
        .xop_o(xop),
        .shifter_source_dreg_o(shifter_source),
        .memory_dreg_o(memory_dreg),
        .i_address_o(i_address),
        .m_address_o(m_address)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        action_count = 0;
        unavailable_count = 0;
        collision_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'hfe0000) == 24'h120000);
            expected_unavailable = expected_class && opcode[10:8] == 3'b001;
            expected_raw_collision = (
                (
                    opcode[14:11] <= 4'hb
                    && (opcode[7:4] == 4'he || opcode[7:4] == 4'hf)
                )
                || (
                    opcode[14:11] >= 4'hc
                    && opcode[14:11] <= 4'he
                    && opcode[7:4] == 4'h9
                )
            );
            expected_collision = (
                expected_class
                && !opcode[15]
                && opcode[10:8] != 3'b001
                && expected_raw_collision
            );
            expected_action = (
                expected_class
                && !expected_unavailable
                && (opcode[15] || !expected_raw_collision)
            );
            if (class_valid !== expected_class
                || unavailable_xop !== expected_unavailable
                || collision !== expected_collision
                || action_valid !== expected_action
                || unsupported !== (expected_class && !expected_action)) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                if (dag_select !== opcode[16] || write_direction !== opcode[15]
                    || sf !== opcode[14:11] || xop !== opcode[10:8]
                    || memory_dreg !== opcode[7:4]
                    || i_address !== {opcode[16], opcode[3:2]}
                    || m_address !== {opcode[16], opcode[1:0]}) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
                class_count = class_count + 1;
            end else if (dag_select || write_direction || sf != 0 || xop != 0
                || memory_dreg != 0 || i_address != 0 || m_address != 0) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
            if (expected_action) begin
                unique case (opcode[10:8])
                    3'd0: expected_source = 4'h8;
                    3'd2: expected_source = 4'ha;
                    3'd3: expected_source = 4'hb;
                    3'd4: expected_source = 4'hc;
                    3'd5: expected_source = 4'hd;
                    3'd6: expected_source = 4'he;
                    default: expected_source = 4'hf;
                endcase
                if (shifter_source !== expected_source) begin
                    $fatal(1, "source mismatch word=%06x", word);
                end
                action_count = action_count + 1;
            end else if (shifter_source !== 4'h0) begin
                $fatal(1, "invalid source leakage word=%06x", word);
            end
            if (expected_unavailable) unavailable_count = unavailable_count + 1;
            if (expected_collision) collision_count = collision_count + 1;
        end
        if (class_count != 131_072 || action_count != 108_640
            || unavailable_count != 16_384 || collision_count != 6_048) begin
            $fatal(
                1,
                "counts class=%0d action=%0d xop=%0d collision=%0d",
                class_count,
                action_count,
                unavailable_count,
                collision_count
            );
        end
        $display(
            "PASS Type 12 exhaustive decode: %0d supported, %0d unsupported",
            action_count,
            class_count - action_count
        );
        $finish;
    end
endmodule

`default_nettype wire
