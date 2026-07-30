`default_nettype none

module adsp2100_shifter (
    input  logic [3:0]  sf_i,
    input  logic [15:0] x_i,
    input  logic [7:0]  shift_or_se_i,
    input  logic [31:0] sr_i,
    input  logic [4:0]  sb_i,
    input  logic        av_i,
    input  logic        ac_i,
    input  logic        ss_i,
    output logic [31:0] sr_result_o,
    output logic        sr_write_o,
    output logic [7:0]  se_result_o,
    output logic        se_write_o,
    output logic [4:0]  sb_result_o,
    output logic        sb_write_o,
    output logic        ss_result_o,
    output logic        ss_write_o
);
    logic [31:0] shifted;
    logic        high_reference;
    logic        combine_or;
    logic        extension_bit;
    logic [7:0]  hi_exponent;
    logic [7:0]  lo_exponent;
    logic [4:0]  detected_sb;
    integer      shift_amount;
    integer      reference_bit;
    integer      source_bit;
    integer      output_bit;
    integer      input_bit;
    integer      redundant_count;
    integer      matching_count;

    always_comb begin
        sr_result_o = sr_i;
        sr_write_o = 1'b0;
        se_result_o = shift_or_se_i;
        se_write_o = 1'b0;
        sb_result_o = sb_i;
        sb_write_o = 1'b0;
        ss_result_o = ss_i;
        ss_write_o = 1'b0;
        shifted = 32'h00000000;
        high_reference = 1'b0;
        combine_or = 1'b0;
        extension_bit = 1'b0;
        hi_exponent = 8'h00;
        lo_exponent = 8'hf1;
        detected_sb = 5'h00;
        shift_amount = 0;
        reference_bit = 0;
        source_bit = 0;
        output_bit = 0;
        input_bit = 0;
        redundant_count = 0;
        matching_count = 0;

        for (input_bit = 14; input_bit >= 0; input_bit = input_bit - 1) begin
            if ((redundant_count == (14 - input_bit))
                && (x_i[input_bit] == x_i[15])) begin
                redundant_count = redundant_count + 1;
            end
        end
        hi_exponent = 8'(0 - redundant_count);

        for (input_bit = 15; input_bit >= 0; input_bit = input_bit - 1) begin
            if ((matching_count == (15 - input_bit))
                && (x_i[input_bit] == ss_i)) begin
                matching_count = matching_count + 1;
            end
        end
        lo_exponent = 8'(0 - 15 - matching_count);

        if (sf_i <= 4'hb) begin
            high_reference = ~sf_i[1];
            combine_or = sf_i[0];
            reference_bit = high_reference ? 16 : 0;
            if (sf_i <= 4'h3) begin
                shift_amount = $signed(
                    {{24{shift_or_se_i[7]}}, shift_or_se_i}
                );
                extension_bit = 1'b0;
            end else if (sf_i <= 4'h7) begin
                shift_amount = $signed(
                    {{24{shift_or_se_i[7]}}, shift_or_se_i}
                );
                extension_bit = x_i[15];
            end else begin
                // OQ-011: retain mathematical +128 for SE=0x80 until an
                // original simulator or physical chip resolves negate width.
                shift_amount = -$signed(
                    {{24{shift_or_se_i[7]}}, shift_or_se_i}
                );
                extension_bit = high_reference ? ac_i : 1'b0;
            end

            for (
                output_bit = 0;
                output_bit < 32;
                output_bit = output_bit + 1
            ) begin
                source_bit = output_bit - reference_bit - shift_amount;
                if ((source_bit >= 0) && (source_bit < 16)) begin
                    shifted[output_bit] = x_i[source_bit];
                end else if (source_bit >= 16) begin
                    shifted[output_bit] = extension_bit;
                end
            end
            sr_result_o = combine_or ? (sr_i | shifted) : shifted;
            sr_write_o = 1'b1;
        end else begin
            unique case (sf_i)
                4'hc: begin
                    se_result_o = hi_exponent;
                    se_write_o = 1'b1;
                    ss_result_o = x_i[15];
                    ss_write_o = 1'b1;
                end
                4'hd: begin
                    se_result_o = av_i ? 8'h01 : hi_exponent;
                    se_write_o = 1'b1;
                    ss_result_o = av_i ? ~x_i[15] : x_i[15];
                    ss_write_o = 1'b1;
                end
                4'he: begin
                    if (shift_or_se_i == 8'hf1) begin
                        se_result_o = lo_exponent;
                        se_write_o = 1'b1;
                    end
                end
                4'hf: begin
                    detected_sb = hi_exponent[4:0];
                    if ($signed(detected_sb) > $signed(sb_i)) begin
                        sb_result_o = detected_sb;
                        sb_write_o = 1'b1;
                    end
                end
                default: begin
                end
            endcase
        end
    end
endmodule

`default_nettype wire
