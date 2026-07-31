`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_mr_saturation_decode;
    logic [23:0] opcode;
    logic        valid;
    integer unsigned opcode_index;
    integer unsigned valid_count;

    adsp2100_mr_saturation_decode dut (
        .opcode_i(opcode),
        .valid_o(valid)
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
            if (valid !== (opcode == 24'h050000)) begin
                $fatal(1, "valid mismatch at opcode=%06x", opcode);
            end
            if (valid) begin
                valid_count = valid_count + 1;
            end
        end
        if (valid_count != 1) begin
            $fatal(1, "Type 25 encoding count mismatch: %0d", valid_count);
        end
        $display(
            "PASS MR-saturation decode: exact opcode, invalid words fail closed"
        );
        $finish;
    end
endmodule

`default_nettype wire
