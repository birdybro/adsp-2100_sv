`default_nettype none

module adsp2100_compute_dm_decode_formal (
    input logic [23:0] opcode
);
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        destination_collision;
    logic        computation_enable;
    logic        is_mac;
    logic        destination_feedback;
    logic        dag_select;
    logic        write;
    logic [4:0]  amf;
    logic [1:0]  yop;
    logic [2:0]  xop;
    logic [3:0]  x_source_dreg;
    logic [3:0]  y_source_dreg;
    logic [3:0]  memory_dreg;
    logic [2:0]  i_address;
    logic [2:0]  m_address;
    logic        expected_class;
    logic        expected_compute;
    logic        expected_mac;
    logic        expected_collision;
    logic [3:0]  expected_x_source;
    logic [3:0]  expected_y_source;

    assign expected_class = ((opcode & 24'he00000) == 24'h600000);
    assign expected_compute = expected_class && opcode[17:13] != 5'h00;
    assign expected_mac = expected_compute && !opcode[17];
    assign expected_collision = (
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

    always_comb begin
        expected_x_source = 4'h0;
        expected_y_source = 4'h0;
        if (expected_class && !expected_collision && expected_compute) begin
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
        .write_o(write),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source_dreg),
        .y_source_dreg_o(y_source_dreg),
        .memory_dreg_o(memory_dreg),
        .i_address_o(i_address),
        .m_address_o(m_address)
    );

    always_comb begin
        assert (class_valid == expected_class);
        assert (computation_enable == expected_compute);
        assert (is_mac == expected_mac);
        assert (destination_collision == expected_collision);
        assert (action_valid == (expected_class && !expected_collision));
        assert (unsupported_subencoding == expected_collision);
        assert (destination_feedback == (expected_class ? opcode[18] : 1'b0));
        assert (dag_select == (expected_class ? opcode[20] : 1'b0));
        assert (write == (expected_class ? opcode[19] : 1'b0));
        assert (amf == (expected_class ? opcode[17:13] : 5'h00));
        assert (yop == (expected_class ? opcode[12:11] : 2'b00));
        assert (xop == (expected_class ? opcode[10:8] : 3'b000));
        assert (memory_dreg == (expected_class ? opcode[7:4] : 4'h0));
        assert (i_address == (expected_class
            ? {opcode[20], opcode[3:2]} : 3'h0));
        assert (m_address == (expected_class
            ? {opcode[20], opcode[1:0]} : 3'h0));
        assert (x_source_dreg == expected_x_source);
        assert (y_source_dreg == expected_y_source);
        if (action_valid) begin
            assert (i_address[2] == m_address[2]);
        end
        cover (action_valid && !write && !computation_enable);
        cover (action_valid && write && computation_enable && is_mac);
        cover (action_valid && !write && computation_enable && !is_mac);
        cover (destination_collision);
    end
endmodule

`default_nettype wire
