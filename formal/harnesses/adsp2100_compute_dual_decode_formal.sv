`default_nettype none

module adsp2100_compute_dual_decode_formal (
    input logic [23:0] opcode
);
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
    logic        expected_class;
    logic        expected_compute;
    logic        expected_mac;
    logic [3:0]  expected_x_source;
    logic [3:0]  expected_y_source;

    assign expected_class = ((opcode & 24'hc00000) == 24'hc00000);
    assign expected_compute = expected_class && opcode[17:13] != 5'h00;
    assign expected_mac = expected_compute && !opcode[17];

    always_comb begin
        expected_x_source = 4'h0;
        expected_y_source = 4'h0;
        if (expected_compute) begin
            if (opcode[10:8] <= 3'd1) begin
                expected_x_source = {2'b00, expected_mac, opcode[8]};
            end else begin
                expected_x_source = {1'b1, opcode[10:8]};
            end
            if (opcode[12:11] <= 2'd1) begin
                expected_y_source = {2'b01, expected_mac, opcode[11]};
            end
        end
    end

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

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_class);
        assert (!unsupported_subencoding);
        assert (computation_enable == expected_compute);
        assert (is_mac == expected_mac);
        assert (!destination_feedback);
        assert (amf == (expected_class ? opcode[17:13] : 5'h00));
        assert (yop == (expected_class ? opcode[12:11] : 2'b00));
        assert (xop == (expected_class ? opcode[10:8] : 3'b000));
        assert (x_source == expected_x_source);
        assert (y_source == expected_y_source);
        assert (compute_destination_ar == (expected_compute && !expected_mac));
        assert (compute_destination_mr == (expected_compute && expected_mac));
        assert (pm_destination == (expected_class
            ? {2'b01, opcode[21:20]} : 4'h0));
        assert (dm_destination == (expected_class
            ? {2'b00, opcode[19:18]} : 4'h0));
        assert (pm_i_address == (expected_class
            ? {1'b1, opcode[7:6]} : 3'h0));
        assert (pm_m_address == (expected_class
            ? {1'b1, opcode[5:4]} : 3'h0));
        assert (dm_i_address == (expected_class
            ? {1'b0, opcode[3:2]} : 3'h0));
        assert (dm_m_address == (expected_class
            ? {1'b0, opcode[1:0]} : 3'h0));
        if (action_valid) begin
            assert (pm_destination >= 4'h4 && pm_destination <= 4'h7);
            assert (dm_destination <= 4'h3);
            assert (pm_i_address[2] && pm_m_address[2]);
            assert (!dm_i_address[2] && !dm_m_address[2]);
        end
        cover (action_valid && !computation_enable);
        cover (action_valid && computation_enable && is_mac);
        cover (action_valid && computation_enable && !is_mac);
    end
endmodule

`default_nettype wire
