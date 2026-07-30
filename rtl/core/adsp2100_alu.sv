`default_nettype none

module adsp2100_alu (
    input  logic [4:0]  amf_i,
    input  logic [15:0] x_i,
    input  logic [15:0] y_i,
    input  logic        carry_i,
    input  logic        previous_av_i,
    input  logic        sticky_av_i,
    input  logic        saturate_ar_i,
    input  logic        destination_is_ar_i,
    output logic        valid_o,
    output logic [15:0] raw_result_o,
    output logic [15:0] destination_result_o,
    output logic        az_o,
    output logic        an_o,
    output logic        av_o,
    output logic        ac_o,
    output logic        as_value_o,
    output logic        as_write_o
);
    logic [15:0] adder_left;
    logic [15:0] adder_right;
    logic        adder_carry;
    logic        use_adder;
    logic [16:0] sum_full;
    logic        av_generated;

    always_comb begin
        valid_o = amf_i[4];
        raw_result_o = 16'h0000;
        destination_result_o = 16'h0000;
        az_o = 1'b0;
        an_o = 1'b0;
        av_o = 1'b0;
        ac_o = 1'b0;
        as_value_o = 1'b0;
        as_write_o = 1'b0;
        adder_left = 16'h0000;
        adder_right = 16'h0000;
        adder_carry = 1'b0;
        use_adder = 1'b0;
        sum_full = 17'h00000;
        av_generated = 1'b0;

        unique case (amf_i)
            5'h10: raw_result_o = y_i;
            5'h11: begin
                use_adder = 1'b1;
                adder_left = y_i;
                adder_carry = 1'b1;
            end
            5'h12: begin
                use_adder = 1'b1;
                adder_left = x_i;
                adder_right = y_i;
                adder_carry = carry_i;
            end
            5'h13: begin
                use_adder = 1'b1;
                adder_left = x_i;
                adder_right = y_i;
            end
            5'h14: raw_result_o = ~y_i;
            5'h15: begin
                use_adder = 1'b1;
                adder_right = ~y_i;
                adder_carry = 1'b1;
            end
            5'h16: begin
                use_adder = 1'b1;
                adder_left = x_i;
                adder_right = ~y_i;
                adder_carry = carry_i;
            end
            5'h17: begin
                use_adder = 1'b1;
                adder_left = x_i;
                adder_right = ~y_i;
                adder_carry = 1'b1;
            end
            5'h18: begin
                use_adder = 1'b1;
                adder_left = y_i;
                adder_right = 16'hffff;
            end
            5'h19: begin
                use_adder = 1'b1;
                adder_left = y_i;
                adder_right = ~x_i;
                adder_carry = 1'b1;
            end
            5'h1a: begin
                use_adder = 1'b1;
                adder_left = y_i;
                adder_right = ~x_i;
                adder_carry = carry_i;
            end
            5'h1b: raw_result_o = ~x_i;
            5'h1c: raw_result_o = x_i & y_i;
            5'h1d: raw_result_o = x_i | y_i;
            5'h1e: raw_result_o = x_i ^ y_i;
            5'h1f: begin
                as_value_o = x_i[15];
                as_write_o = 1'b1;
                raw_result_o = x_i[15] ? (~x_i + 16'h0001) : x_i;
                av_generated = x_i == 16'h8000;
            end
            default: valid_o = 1'b0;
        endcase

        if (use_adder) begin
            sum_full = {1'b0, adder_left} + {1'b0, adder_right}
                + {{16{1'b0}}, adder_carry};
            raw_result_o = sum_full[15:0];
            ac_o = sum_full[16];
            av_generated = (~(adder_left[15] ^ adder_right[15]))
                & (raw_result_o[15] ^ adder_left[15]);
        end

        if (valid_o) begin
            az_o = raw_result_o == 16'h0000;
            an_o = raw_result_o[15];
            av_o = av_generated | (sticky_av_i & previous_av_i);
            destination_result_o = raw_result_o;
            if (destination_is_ar_i && saturate_ar_i && av_generated) begin
                destination_result_o = ac_o ? 16'h8000 : 16'h7fff;
            end
        end
    end
endmodule

`default_nettype wire
