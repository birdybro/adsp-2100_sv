`default_nettype none

module adsp2100_modify_address_decode_formal (
    input logic [23:0] opcode
);
    logic       valid;
    logic       dag2;
    logic [1:0] i_local;
    logic [1:0] m_local;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic [2:0] l_address;
    logic       expected_valid;

    assign expected_valid = (
        (opcode & 24'hffffe0) == 24'h090000
    );

    adsp2100_modify_address_decode dut (
        .opcode_i(opcode),
        .valid_o(valid),
        .dag2_o(dag2),
        .i_local_o(i_local),
        .m_local_o(m_local),
        .i_address_o(i_address),
        .m_address_o(m_address),
        .l_address_o(l_address)
    );

    always_comb begin
        assert (valid == expected_valid);
        if (valid) begin
            assert (dag2 == opcode[4]);
            assert (i_local == opcode[3:2]);
            assert (m_local == opcode[1:0]);
            assert (i_address == {opcode[4], opcode[3:2]});
            assert (m_address == {opcode[4], opcode[1:0]});
            assert (l_address == i_address);
            assert (i_address[2] == m_address[2]);
        end else begin
            assert (!dag2);
            assert (i_local == 2'b00);
            assert (m_local == 2'b00);
            assert (i_address == 3'b000);
            assert (m_address == 3'b000);
            assert (l_address == 3'b000);
        end
        cover (valid && !dag2 && (i_local != m_local));
        cover (valid && dag2 && (i_local != m_local));
        cover (!valid);
    end
endmodule

`default_nettype wire
