`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_mode_control_decode;
    logic [23:0] opcode;
    logic        valid;
    logic [1:0]  mode_sr;
    logic [1:0]  mode_br;
    logic [1:0]  mode_ol;
    logic [1:0]  mode_as;
    logic        has_effect;
    logic        has_alias;
    integer unsigned opcode_index;
    integer unsigned valid_count;

    adsp2100_mode_control_decode dut (
        .opcode_i(opcode),
        .valid_o(valid),
        .mode_sr_o(mode_sr),
        .mode_br_o(mode_br),
        .mode_ol_o(mode_ol),
        .mode_as_o(mode_as),
        .has_effect_o(has_effect),
        .has_no_change_one_alias_o(has_alias)
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
                !== ((opcode & 24'hfff00f) == 24'h0c0000)
            ) begin
                $fatal(1, "valid mismatch at opcode=%06x", opcode);
            end
            if (valid) begin
                valid_count = valid_count + 1;
                if (
                    mode_sr !== opcode[5:4]
                    || mode_br !== opcode[7:6]
                    || mode_ol !== opcode[9:8]
                    || mode_as !== opcode[11:10]
                    || has_effect !== (
                        opcode[5]
                        || opcode[7]
                        || opcode[9]
                        || opcode[11]
                    )
                    || has_alias !== (
                        (opcode[5:4] == 2'b01)
                        || (opcode[7:6] == 2'b01)
                        || (opcode[9:8] == 2'b01)
                        || (opcode[11:10] == 2'b01)
                    )
                ) begin
                    $fatal(1, "action mismatch at opcode=%06x", opcode);
                end
            end else if (
                mode_sr !== 2'b00
                || mode_br !== 2'b00
                || mode_ol !== 2'b00
                || mode_as !== 2'b00
                || has_effect !== 1'b0
                || has_alias !== 1'b0
            ) begin
                $fatal(1, "invalid opcode emitted action: %06x", opcode);
            end
        end
        if (valid_count != 256) begin
            $fatal(1, "Type 18 encoding count mismatch: %0d", valid_count);
        end
        $display(
            "PASS mode-control decode: 256 encodings, invalid words fail closed"
        );
        $finish;
    end
endmodule

`default_nettype wire
