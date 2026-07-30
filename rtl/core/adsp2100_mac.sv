`default_nettype none

module adsp2100_mac (
    input  logic [4:0]  amf_i,
    input  logic [15:0] x_i,
    input  logic [15:0] y_i,
    input  logic [39:0] mr_i,
    input  logic        saturation_mv_i,
    output logic        valid_o,
    output logic [39:0] unrounded_result_o,
    output logic [39:0] result_o,
    output logic [15:0] mf_result_o,
    output logic        mv_o,
    output logic [39:0] saturated_mr_o
);
    logic               rounded;
    logic               x_signed;
    logic               y_signed;
    logic [1:0]         operation;
    logic signed [16:0] x_extended;
    logic signed [16:0] y_extended;
    logic signed [33:0] product_full;
    logic signed [39:0] product_extended;
    logic [39:0]        aligned_product;
    logic [23:0]        rounded_upper;
    logic               round_increment;

    always_comb begin
        valid_o = (amf_i >= 5'h01) && (amf_i <= 5'h0f);
        rounded = amf_i <= 5'h03;
        x_signed = 1'b0;
        y_signed = 1'b0;
        operation = 2'b00;
        x_extended = $signed({1'b0, x_i});
        y_extended = $signed({1'b0, y_i});
        product_full = 34'sh000000000;
        product_extended = 40'sh0000000000;
        aligned_product = 40'h0000000000;
        unrounded_result_o = 40'h0000000000;
        result_o = 40'h0000000000;
        mf_result_o = 16'h0000;
        mv_o = 1'b0;
        rounded_upper = 24'h000000;
        round_increment = 1'b0;

        if (rounded) begin
            x_signed = 1'b1;
            y_signed = 1'b1;
            operation = amf_i[1:0];
        end else begin
            x_signed = ~amf_i[1];
            y_signed = ~amf_i[0];
            operation = amf_i[3:2];
        end

        if (x_signed) begin
            x_extended = $signed({x_i[15], x_i});
        end
        if (y_signed) begin
            y_extended = $signed({y_i[15], y_i});
        end

        product_full = x_extended * y_extended;
        product_extended = $signed(
            {{6{product_full[33]}}, product_full}
        );
        aligned_product = product_extended <<< 1;

        unique case (operation)
            2'b01: unrounded_result_o = aligned_product;
            2'b10: unrounded_result_o = mr_i + aligned_product;
            2'b11: unrounded_result_o = mr_i - aligned_product;
            default: unrounded_result_o = 40'h0000000000;
        endcase

        if (rounded) begin
            round_increment = (unrounded_result_o[15:0] > 16'h8000)
                || ((unrounded_result_o[15:0] == 16'h8000)
                    && unrounded_result_o[16]);
            rounded_upper = unrounded_result_o[39:16]
                + {{23{1'b0}}, round_increment};
            result_o = {rounded_upper, 16'h0000};
        end else begin
            result_o = unrounded_result_o;
        end

        if (valid_o) begin
            mf_result_o = result_o[31:16];
            mv_o = (result_o[39:31] != 9'h000)
                && (result_o[39:31] != 9'h1ff);
        end

        if (!saturation_mv_i) begin
            saturated_mr_o = mr_i;
        end else if (mr_i[39]) begin
            saturated_mr_o = 40'hff80000000;
        end else begin
            saturated_mr_o = 40'h007fffffff;
        end
    end
endmodule

`default_nettype wire
