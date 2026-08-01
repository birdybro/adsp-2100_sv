`default_nettype none

module adsp2100_dm_write_immediate_decode_formal (
    input logic [23:0] opcode
);
    logic valid;
    logic [15:0] immediate;
    logic dag2;
    logic [1:0] i_local;
    logic [1:0] m_local;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic [2:0] l_address;

    adsp2100_dm_write_immediate_decode dut (
        .opcode_i(opcode),
        .valid_o(valid),
        .immediate_o(immediate),
        .dag2_o(dag2),
        .i_local_o(i_local),
        .m_local_o(m_local),
        .i_address_o(i_address),
        .m_address_o(m_address),
        .l_address_o(l_address)
    );

    always_comb begin
        assert (valid == (opcode[23:21] == 3'b101));
        if (valid) begin
            assert (immediate == opcode[19:4]);
            assert (dag2 == opcode[20]);
            assert (i_local == opcode[3:2]);
            assert (m_local == opcode[1:0]);
            assert (i_address == {opcode[20], opcode[3:2]});
            assert (m_address == {opcode[20], opcode[1:0]});
            assert (l_address == i_address);
            assert (i_address[2] == m_address[2]);
        end else begin
            assert (
                {immediate, dag2, i_local, m_local,
                 i_address, m_address, l_address} == 30'h00000000
            );
        end
    end
endmodule

`default_nettype wire
