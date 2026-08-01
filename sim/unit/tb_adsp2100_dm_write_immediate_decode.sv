`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_dm_write_immediate_decode;
    logic [23:0] opcode;
    logic valid;
    logic [15:0] immediate;
    logic dag2;
    logic [1:0] i_local;
    logic [1:0] m_local;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic [2:0] l_address;
    integer unsigned word;
    integer unsigned valid_count;

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

    initial begin
        opcode = 24'h000000;
        valid_count = 0;
        for (word = 0; word < 24'hffffff; word = word + 1) begin
            opcode = word[23:0];
            #1;
            if (valid !== (opcode[23:21] == 3'b101)) begin
                $fatal(1, "Type 2 class mismatch opcode=%06x", opcode);
            end
            if (valid) begin
                valid_count = valid_count + 1;
                if (
                    immediate !== opcode[19:4]
                    || dag2 !== opcode[20]
                    || i_local !== opcode[3:2]
                    || m_local !== opcode[1:0]
                    || i_address !== {opcode[20], opcode[3:2]}
                    || m_address !== {opcode[20], opcode[1:0]}
                    || l_address !== {opcode[20], opcode[3:2]}
                ) begin
                    $fatal(1, "Type 2 field mismatch opcode=%06x", opcode);
                end
            end else if (
                {immediate, dag2, i_local, m_local,
                 i_address, m_address, l_address} !== 30'h00000000
            ) begin
                $fatal(1, "Type 2 invalid output activity opcode=%06x", opcode);
            end
        end
        opcode = 24'hffffff;
        #1;
        if (
            valid
            || {immediate, dag2, i_local, m_local,
                i_address, m_address, l_address} !== 30'h00000000
        ) begin
            $fatal(1, "Type 2 final nonclass word produced action");
        end
        if (valid_count != 32'd2097152) begin
            $fatal(1, "Type 2 count mismatch count=%0d", valid_count);
        end
        $display(
            "PASS Type 2 exhaustive decode: %0d field-defined words",
            valid_count
        );
        $finish;
    end
endmodule

`default_nettype wire
