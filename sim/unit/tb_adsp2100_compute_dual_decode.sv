`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_compute_dual_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        computation_enable;
    logic        is_mac;
    logic        destination_feedback;
    logic [4:0]  amf;
    logic [1:0]  yop;
    logic [2:0]  xop;
    logic [3:0]  x_source;
    logic [3:0]  y_source;
    logic        compute_destination_ar;
    logic        compute_destination_mr;
    logic [3:0]  pm_destination;
    logic [3:0]  dm_destination;
    logic [2:0]  pm_i_address;
    logic [2:0]  pm_m_address;
    logic [2:0]  dm_i_address;
    logic [2:0]  dm_m_address;
    logic        expected_compute;
    logic        expected_mac;
    logic [3:0]  expected_x_source;
    logic [3:0]  expected_y_source;
    integer      payload;
    integer      action_count;

    adsp2100_compute_dual_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .computation_enable_o(computation_enable),
        .is_mac_o(is_mac),
        .destination_feedback_o(destination_feedback),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .y_source_dreg_o(y_source),
        .compute_destination_ar_o(compute_destination_ar),
        .compute_destination_mr_o(compute_destination_mr),
        .pm_destination_dreg_o(pm_destination),
        .dm_destination_dreg_o(dm_destination),
        .pm_i_address_o(pm_i_address),
        .pm_m_address_o(pm_m_address),
        .dm_i_address_o(dm_i_address),
        .dm_m_address_o(dm_m_address)
    );

    task automatic check_nonclass(input logic [23:0] word);
        begin
            opcode = word;
            #1;
            if (class_valid || action_valid || unsupported_subencoding
                || computation_enable || is_mac || destination_feedback
                || amf != 5'h00 || yop != 2'b00 || xop != 3'b000
                || x_source != 4'h0 || y_source != 4'h0
                || compute_destination_ar || compute_destination_mr
                || pm_destination != 4'h0 || dm_destination != 4'h0
                || pm_i_address != 3'h0 || pm_m_address != 3'h0
                || dm_i_address != 3'h0 || dm_m_address != 3'h0) begin
                $fatal(1, "nonclass leakage word=%06x", word);
            end
        end
    endtask

    initial begin
        opcode = 24'h000000;
        action_count = 0;
        check_nonclass(24'h000000);
        check_nonclass(24'h7fffff);
        check_nonclass(24'h800000);
        check_nonclass(24'hbfffff);

        for (payload = 0; payload < 4_194_304; payload = payload + 1) begin
            opcode = 24'hc00000 | payload[23:0];
            #1;
            expected_compute = opcode[17:13] != 5'h00;
            expected_mac = expected_compute && !opcode[17];
            if (!class_valid || !action_valid || unsupported_subencoding
                || computation_enable !== expected_compute
                || is_mac !== expected_mac || destination_feedback) begin
                $fatal(1, "classification mismatch word=%06x", opcode);
            end
            if (amf !== opcode[17:13] || yop !== opcode[12:11]
                || xop !== opcode[10:8]
                || pm_destination !== {2'b01, opcode[21:20]}
                || dm_destination !== {2'b00, opcode[19:18]}
                || pm_i_address !== {1'b1, opcode[7:6]}
                || pm_m_address !== {1'b1, opcode[5:4]}
                || dm_i_address !== {1'b0, opcode[3:2]}
                || dm_m_address !== {1'b0, opcode[1:0]}) begin
                $fatal(1, "field mismatch word=%06x", opcode);
            end
            if (compute_destination_ar !== (expected_compute && !expected_mac)
                || compute_destination_mr !== (expected_compute && expected_mac)) begin
                $fatal(1, "result mapping mismatch word=%06x", opcode);
            end
            expected_x_source = 4'h0;
            expected_y_source = 4'h0;
            if (expected_compute) begin
                if (opcode[10:8] <= 3'd1) begin
                    expected_x_source = {
                        2'b00,
                        expected_mac,
                        opcode[8]
                    };
                end else begin
                    expected_x_source = {1'b1, opcode[10:8]};
                end
                if (opcode[12:11] <= 2'd1) begin
                    expected_y_source = {
                        2'b01,
                        expected_mac,
                        opcode[11]
                    };
                end
            end
            if (x_source !== expected_x_source
                || y_source !== expected_y_source) begin
                $fatal(1, "operand mapping mismatch word=%06x", opcode);
            end
            action_count = action_count + 1;
        end
        if (action_count != 4_194_304) begin
            $fatal(1, "action count=%0d", action_count);
        end

        opcode = 24'he96011;
        #1;
        if (!action_valid || amf != 5'h0b
            || pm_destination != 4'h6 || dm_destination != 4'h2
            || pm_i_address != 3'h4 || pm_m_address != 3'h5
            || dm_i_address != 3'h0 || dm_m_address != 3'h1) begin
            $fatal(1, "manual MAC dual-read fixture mismatch");
        end
        opcode = 24'hc00028;
        #1;
        if (!action_valid || computation_enable
            || pm_destination != 4'h4 || dm_destination != 4'h0
            || pm_i_address != 3'h4 || pm_m_address != 3'h6
            || dm_i_address != 3'h2 || dm_m_address != 3'h0) begin
            $fatal(1, "manual dual-read-only fixture mismatch");
        end
        $display("PASS Type 1 decode: %0d source-closed actions", action_count);
        $finish;
    end
endmodule

`default_nettype wire
