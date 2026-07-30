`default_nettype none

module adsp2100_alu_formal (
    input logic [4:0]  amf,
    input logic [15:0] x,
    input logic [15:0] y,
    input logic        carry,
    input logic        previous_av,
    input logic        sticky_av,
    input logic        saturate_ar,
    input logic        destination_is_ar
);
    logic                      valid;
    logic [15:0]               raw_result;
    logic [15:0]               destination_result;
    logic                      az;
    logic                      an;
    logic                      av;
    logic                      ac;
    logic                      as_value;
    logic                      as_write;

    adsp2100_alu dut (
        .amf_i(amf),
        .x_i(x),
        .y_i(y),
        .carry_i(carry),
        .previous_av_i(previous_av),
        .sticky_av_i(sticky_av),
        .saturate_ar_i(saturate_ar),
        .destination_is_ar_i(destination_is_ar),
        .valid_o(valid),
        .raw_result_o(raw_result),
        .destination_result_o(destination_result),
        .az_o(az),
        .an_o(an),
        .av_o(av),
        .ac_o(ac),
        .as_value_o(as_value),
        .as_write_o(as_write)
    );

    always_comb begin
        assert (valid == amf[4]);
        if (valid) begin
            assert (az == (raw_result == 16'h0000));
            assert (an == raw_result[15]);
            assert (as_write == (amf == 5'h1f));
            if (sticky_av && previous_av) begin
                assert (av);
            end
            if (!destination_is_ar || !saturate_ar) begin
                assert (destination_result == raw_result);
            end
            if (destination_result != raw_result) begin
                assert (destination_is_ar && saturate_ar);
                assert (
                    (destination_result == 16'h7fff)
                    || (destination_result == 16'h8000)
                );
            end

            unique case (amf)
                5'h10: begin
                    assert (raw_result == y);
                    assert (!ac);
                end
                5'h14: begin
                    assert (raw_result == ~y);
                    assert (!ac);
                end
                5'h1b: begin
                    assert (raw_result == ~x);
                    assert (!ac);
                end
                5'h1c: begin
                    assert (raw_result == (x & y));
                    assert (!ac);
                end
                5'h1d: begin
                    assert (raw_result == (x | y));
                    assert (!ac);
                end
                5'h1e: begin
                    assert (raw_result == (x ^ y));
                    assert (!ac);
                end
                5'h1f: begin
                    assert (as_value == x[15]);
                    assert (raw_result == (x[15] ? (~x + 16'h0001) : x));
                    assert (!ac);
                end
                default: assert (!as_write);
            endcase
        end
    end
endmodule

`default_nettype wire
