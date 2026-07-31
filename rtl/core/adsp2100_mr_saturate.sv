`default_nettype none

module adsp2100_mr_saturate (
    input  logic [39:0] mr_i,
    input  logic        mv_i,
    output logic [39:0] result_o
);
    always_comb begin
        if (!mv_i) begin
            result_o = mr_i;
        end else if (mr_i[39]) begin
            result_o = 40'hff80000000;
        end else begin
            result_o = 40'h007fffffff;
        end
    end
endmodule

`default_nettype wire
