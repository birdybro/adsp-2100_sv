`default_nettype none

module adsp2100_modify_address_decode (
    input  logic [23:0] opcode_i,

    output logic       valid_o,
    output logic       dag2_o,
    output logic [1:0] i_local_o,
    output logic [1:0] m_local_o,
    output logic [2:0] i_address_o,
    output logic [2:0] m_address_o,
    output logic [2:0] l_address_o
);
    localparam logic [23:0] TYPE_21_MASK = 24'hffffe0;
    localparam logic [23:0] TYPE_21_VALUE = 24'h090000;

    always_comb begin
        valid_o = (opcode_i & TYPE_21_MASK) == TYPE_21_VALUE;
        dag2_o = 1'b0;
        i_local_o = 2'b00;
        m_local_o = 2'b00;
        i_address_o = 3'b000;
        m_address_o = 3'b000;
        l_address_o = 3'b000;

        if (valid_o) begin
            dag2_o = opcode_i[4];
            i_local_o = opcode_i[3:2];
            m_local_o = opcode_i[1:0];
            i_address_o = {opcode_i[4], opcode_i[3:2]};
            m_address_o = {opcode_i[4], opcode_i[1:0]};
            l_address_o = {opcode_i[4], opcode_i[3:2]};
        end
    end
endmodule

`default_nettype wire
