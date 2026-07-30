`default_nettype none

module adsp2100_shifter_formal (
    input logic [3:0]  sf,
    input logic [15:0] x,
    input logic [7:0]  shift_or_se,
    input logic [31:0] sr,
    input logic [4:0]  sb,
    input logic        av,
    input logic        ac,
    input logic        ss
);
    logic [31:0] sr_result;
    logic        sr_write;
    logic [7:0]  se_result;
    logic        se_write;
    logic [4:0]  sb_result;
    logic        sb_write;
    logic        ss_result;
    logic        ss_write;

    adsp2100_shifter dut (
        .sf_i(sf),
        .x_i(x),
        .shift_or_se_i(shift_or_se),
        .sr_i(sr),
        .sb_i(sb),
        .av_i(av),
        .ac_i(ac),
        .ss_i(ss),
        .sr_result_o(sr_result),
        .sr_write_o(sr_write),
        .se_result_o(se_result),
        .se_write_o(se_write),
        .sb_result_o(sb_result),
        .sb_write_o(sb_write),
        .ss_result_o(ss_result),
        .ss_write_o(ss_write)
    );

    always_comb begin
        if (sf <= 4'hb) begin
            assert (sr_write);
            assert (!se_write);
            assert (!sb_write);
            assert (!ss_write);
            if (sf[0]) begin
                assert ((sr_result & sr) == sr);
            end
        end else begin
            assert (!sr_write);
            assert (sr_result == sr);
        end

        if ((sf == 4'hc) || (sf == 4'hd)) begin
            assert (se_write);
            assert (ss_write);
        end
        if ((sf == 4'hd) && av) begin
            assert (se_result == 8'h01);
            assert (ss_result == ~x[15]);
        end
        if ((sf == 4'he) && (shift_or_se != 8'hf1)) begin
            assert (!se_write);
            assert (se_result == shift_or_se);
        end
        if ((sf == 4'hf) && !sb_write) begin
            assert (sb_result == sb);
        end

        if ((sf == 4'h0) && (shift_or_se == 8'h10)) begin
            assert (sr_result == 32'h00000000);
        end
        if ((sf == 4'h2) && (shift_or_se == 8'hf0)) begin
            assert (sr_result == 32'h00000000);
        end
        if ((sf == 4'hc) && ((x == 16'h0000) || (x == 16'hffff))) begin
            assert (se_result == 8'hf1);
        end
    end
endmodule

`default_nettype wire
