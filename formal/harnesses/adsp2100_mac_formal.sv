`default_nettype none

module adsp2100_mac_formal (
    input logic [4:0]  amf,
    input logic [15:0] x,
    input logic [15:0] y,
    input logic [39:0] mr,
    input logic        saturation_mv
);
    logic                      valid;
    logic [39:0]               unrounded_result;
    logic [39:0]               result;
    logic [15:0]               mf_result;
    logic                      mv;
    logic [39:0]               saturated_mr;

    adsp2100_mac dut (
        .amf_i(amf),
        .x_i(x),
        .y_i(y),
        .mr_i(mr),
        .saturation_mv_i(saturation_mv),
        .valid_o(valid),
        .unrounded_result_o(unrounded_result),
        .result_o(result),
        .mf_result_o(mf_result),
        .mv_o(mv),
        .saturated_mr_o(saturated_mr)
    );

    always_comb begin
        assert (valid == ((amf >= 5'h01) && (amf <= 5'h0f)));

        if (!saturation_mv) begin
            assert (saturated_mr == mr);
        end else if (mr[39]) begin
            assert (saturated_mr == 40'hff80000000);
        end else begin
            assert (saturated_mr == 40'h007fffffff);
        end

        if (valid) begin
            assert (mf_result == result[31:16]);
            assert (
                mv == (
                    (result[39:31] != 9'h000)
                    && (result[39:31] != 9'h1ff)
                )
            );
            if (amf <= 5'h03) begin
                assert (result[15:0] == 16'h0000);
            end else begin
                assert (result == unrounded_result);
            end

            if ((amf >= 5'h04) && (amf <= 5'h07)) begin
                assert (unrounded_result[0] == 1'b0);
                if ((x == 16'h0000) || (y == 16'h0000)) begin
                    assert (unrounded_result == 40'h0000000000);
                end
            end
            if ((amf >= 5'h08) && (amf <= 5'h0f)
                && ((x == 16'h0000) || (y == 16'h0000))) begin
                assert (unrounded_result == mr);
            end
        end
    end
endmodule

`default_nettype wire
