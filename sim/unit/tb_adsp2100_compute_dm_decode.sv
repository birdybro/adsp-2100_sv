`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_compute_dm_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        destination_collision;
    logic        computation_enable;
    logic        is_mac;
    logic        destination_feedback;
    logic        dag_select;
    logic        write_direction;
    logic [4:0]  amf;
    logic [1:0]  yop;
    logic [2:0]  xop;
    logic [3:0]  x_source;
    logic [3:0]  y_source;
    logic [3:0]  memory_dreg;
    logic [2:0]  i_address;
    logic [2:0]  m_address;
    logic        expected_class;
    logic        expected_compute;
    logic        expected_collision;
    logic        expected_action;
    logic        expected_is_mac;
    logic [3:0]  expected_x_source;
    logic [3:0]  expected_y_source;
    integer      word;
    integer      class_count;
    integer      action_count;
    integer      collision_count;

    adsp2100_compute_dm_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .destination_collision_o(destination_collision),
        .computation_enable_o(computation_enable),
        .is_mac_o(is_mac),
        .destination_feedback_o(destination_feedback),
        .dag_select_o(dag_select),
        .write_o(write_direction),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .y_source_dreg_o(y_source),
        .memory_dreg_o(memory_dreg),
        .i_address_o(i_address),
        .m_address_o(m_address)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        action_count = 0;
        collision_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'he00000) == 24'h600000);
            expected_compute = expected_class && opcode[17:13] != 5'h00;
            expected_collision = (
                expected_compute
                && !opcode[19]
                && !opcode[18]
                && (
                    (opcode[17] && opcode[7:4] == 4'ha)
                    || (
                        !opcode[17]
                        && opcode[7:4] >= 4'hb
                        && opcode[7:4] <= 4'hd
                    )
                )
            );
            expected_action = expected_class && !expected_collision;
            expected_is_mac = expected_compute && !opcode[17];
            if (class_valid !== expected_class
                || action_valid !== expected_action
                || unsupported_subencoding
                    !== (expected_class && !expected_action)
                || destination_collision !== expected_collision
                || computation_enable !== expected_compute
                || is_mac !== expected_is_mac) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                if (dag_select !== opcode[20]
                    || write_direction !== opcode[19]
                    || destination_feedback !== opcode[18]
                    || amf !== opcode[17:13]
                    || yop !== opcode[12:11]
                    || xop !== opcode[10:8]
                    || memory_dreg !== opcode[7:4]
                    || i_address !== {opcode[20], opcode[3:2]}
                    || m_address !== {opcode[20], opcode[1:0]}) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
            end else if (dag_select !== 1'b0
                || write_direction !== 1'b0
                || destination_feedback !== 1'b0
                || amf !== 5'h00 || yop !== 2'b00 || xop !== 3'b000
                || memory_dreg !== 4'h0
                || i_address !== 3'h0 || m_address !== 3'h0) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
            expected_x_source = 4'h0;
            expected_y_source = 4'h0;
            if (expected_action && expected_compute) begin
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
            if (expected_collision) collision_count = collision_count + 1;
        end
        if (class_count != 2_097_152 || action_count != 2_034_688
            || collision_count != 62_464) begin
            $fatal(
                1,
                "counts class=%0d action=%0d collision=%0d",
                class_count,
                action_count,
                collision_count
            );
        end

        opcode = 24'h626003;
        #1;
        if (!action_valid || write_direction || amf != 5'h13
            || memory_dreg != 4'h0 || i_address != 3'h0
            || m_address != 3'h3) begin
            $fatal(1, "manual ALU/read fixture mismatch");
        end
        opcode = 24'h6a60a0;
        #1;
        if (!action_valid || !write_direction || amf != 5'h13
            || memory_dreg != 4'ha || i_address != 3'h0
            || m_address != 3'h0) begin
            $fatal(1, "manual ALU/write fixture mismatch");
        end
        $display(
            "PASS Type 4 decode: %0d supported, %0d collisions",
            action_count,
            collision_count
        );
        $finish;
    end
endmodule

`default_nettype wire
