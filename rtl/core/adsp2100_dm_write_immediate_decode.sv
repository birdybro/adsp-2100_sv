`default_nettype none

module adsp2100_dm_write_immediate_decode (
    input  logic [23:0] opcode_i,

    output logic        valid_o,
    output logic [15:0] immediate_o,
    output logic        dag2_o,
    output logic [1:0]  i_local_o,
    output logic [1:0]  m_local_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,
    output logic [2:0]  l_address_o
);
    localparam logic [23:0] TYPE_02_MASK = 24'he00000;
    localparam logic [23:0] TYPE_02_VALUE = 24'ha00000;

    always_comb begin
        valid_o = (opcode_i & TYPE_02_MASK) == TYPE_02_VALUE;
        immediate_o = 16'h0000;
        dag2_o = 1'b0;
        i_local_o = 2'b00;
        m_local_o = 2'b00;
        i_address_o = 3'b000;
        m_address_o = 3'b000;
        l_address_o = 3'b000;

        if (valid_o) begin
            immediate_o = opcode_i[19:4];
            dag2_o = opcode_i[20];
            i_local_o = opcode_i[3:2];
            m_local_o = opcode_i[1:0];
            i_address_o = {opcode_i[20], opcode_i[3:2]};
            m_address_o = {opcode_i[20], opcode_i[1:0]};
            l_address_o = {opcode_i[20], opcode_i[3:2]};
        end
    end
endmodule

`default_nettype wire
