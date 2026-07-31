`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_modify_address_decode;
    logic [23:0] opcode;
    logic        valid;
    logic        dag2;
    logic [1:0]  i_local;
    logic [1:0]  m_local;
    logic [2:0]  i_address;
    logic [2:0]  m_address;
    logic [2:0]  l_address;
    integer unsigned opcode_index;
    integer unsigned valid_count;

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

    initial begin
        valid_count = 0;
        for (
            opcode_index = 0;
            opcode_index < 32'h01000000;
            opcode_index = opcode_index + 1
        ) begin
            opcode = opcode_index[23:0];
            #1;
            if (
                valid
                !== ((opcode & 24'hffffe0) == 24'h090000)
            ) begin
                $fatal(1, "valid mismatch at opcode=%06x", opcode);
            end
            if (valid) begin
                valid_count = valid_count + 1;
                if (
                    dag2 !== opcode[4]
                    || i_local !== opcode[3:2]
                    || m_local !== opcode[1:0]
                    || i_address !== {opcode[4], opcode[3:2]}
                    || m_address !== {opcode[4], opcode[1:0]}
                    || l_address !== {opcode[4], opcode[3:2]}
                ) begin
                    $fatal(1, "selection mismatch at opcode=%06x", opcode);
                end
            end else if (
                dag2 !== 1'b0
                || i_local !== 2'b00
                || m_local !== 2'b00
                || i_address !== 3'b000
                || m_address !== 3'b000
                || l_address !== 3'b000
            ) begin
                $fatal(1, "invalid opcode emitted selection: %06x", opcode);
            end
        end
        if (valid_count != 32) begin
            $fatal(1, "Type 21 encoding count mismatch: %0d", valid_count);
        end
        $display(
            "PASS modify-address decode: 32 encodings, invalid words fail closed"
        );
        $finish;
    end
endmodule

`default_nettype wire
