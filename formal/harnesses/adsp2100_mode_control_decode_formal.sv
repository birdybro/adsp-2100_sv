`default_nettype none

module adsp2100_mode_control_decode_formal (
    input logic [23:0] opcode
);
    logic       valid;
    logic [1:0] mode_sr;
    logic [1:0] mode_br;
    logic [1:0] mode_ol;
    logic [1:0] mode_as;
    logic       has_effect;
    logic       has_alias;
    logic       expected_valid;

    assign expected_valid = (
        (opcode & 24'hfff00f) == 24'h0c0000
    );

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

    always_comb begin
        assert (valid == expected_valid);
        if (valid) begin
            assert (mode_sr == opcode[5:4]);
            assert (mode_br == opcode[7:6]);
            assert (mode_ol == opcode[9:8]);
            assert (mode_as == opcode[11:10]);
            assert (
                has_effect
                == (
                    opcode[5]
                    || opcode[7]
                    || opcode[9]
                    || opcode[11]
                )
            );
            assert (
                has_alias
                == (
                    (opcode[5:4] == 2'b01)
                    || (opcode[7:6] == 2'b01)
                    || (opcode[9:8] == 2'b01)
                    || (opcode[11:10] == 2'b01)
                )
            );
        end else begin
            assert (mode_sr == 2'b00);
            assert (mode_br == 2'b00);
            assert (mode_ol == 2'b00);
            assert (mode_as == 2'b00);
            assert (!has_effect);
            assert (!has_alias);
        end
        cover (valid && has_effect && has_alias);
        cover (valid && !has_effect);
        cover (!valid);
    end
endmodule

`default_nettype wire
