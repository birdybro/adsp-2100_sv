`default_nettype none

module adsp2100_mr_saturation_decode_formal (
    input logic [23:0] opcode
);
    logic valid;

    adsp2100_mr_saturation_decode dut (
        .opcode_i(opcode),
        .valid_o(valid)
    );

    always_comb begin
        assert (valid == (opcode == 24'h050000));
        cover (valid);
        cover (!valid);
    end
endmodule

`default_nettype wire
