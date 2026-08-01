`default_nettype none

module adsp2100_instruction_cache_formal (
    input logic        clk,
    input logic        reset,
    input logic        fill,
    input logic [13:0] fill_address,
    input logic        fill_address_valid,
    input logic [23:0] fill_instruction,
    input logic        fill_instruction_valid,
    input logic [13:0] lookup_address,
    input logic        lookup_address_valid
);
    logic lookup_hit;
    logic [23:0] lookup_instruction;
    logic lookup_instruction_valid;
    logic fill_accepted;
    logic region_restarted;
    logic oldest_replaced;
    logic [13:0] region_start;
    logic region_start_valid;
    logic [4:0] region_count;
    logic past_valid;
    logic unused_observation;

    assign unused_observation = ^{lookup_instruction, fill_instruction};

    adsp2100_instruction_cache dut (
        .clk_i(clk),
        .reset_i(reset),
        .fill_i(fill),
        .fill_address_i(fill_address),
        .fill_address_valid_i(fill_address_valid),
        .fill_instruction_i(fill_instruction),
        .fill_instruction_valid_i(fill_instruction_valid),
        .lookup_address_i(lookup_address),
        .lookup_address_valid_i(lookup_address_valid),
        .lookup_hit_o(lookup_hit),
        .lookup_instruction_o(lookup_instruction),
        .lookup_instruction_valid_o(lookup_instruction_valid),
        .fill_accepted_o(fill_accepted),
        .region_restarted_o(region_restarted),
        .oldest_replaced_o(oldest_replaced),
        .region_start_o(region_start),
        .region_start_valid_o(region_start_valid),
        .region_count_o(region_count)
    );

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;

        assert (region_count <= 5'd16);
        assert (region_start_valid == (!reset && region_count != 5'd0));
        assert (!lookup_instruction_valid || lookup_hit);
        assert (!lookup_hit || lookup_address_valid);
        assert (fill_accepted == (!reset && fill && fill_address_valid));
        assert (!oldest_replaced || (fill_accepted && !region_restarted));

        if (past_valid && $past(reset)) begin
            assert (region_count == 5'd0);
            assert (!region_start_valid);
        end
        if (
            past_valid
            && !$past(reset)
            && !$past(fill)
        ) begin
            assert (region_count == $past(region_count));
            assert (region_start == $past(region_start));
        end
        if (
            past_valid
            && !$past(reset)
            && $past(fill)
            && !$past(fill_address_valid)
        ) begin
            assert (region_count == 5'd0);
        end
        if (
            past_valid
            && $past(fill_accepted)
            && $past(region_restarted)
        ) begin
            assert (region_count == 5'd1);
            assert (region_start == $past(fill_address));
        end
        if (past_valid && $past(oldest_replaced)) begin
            assert (region_count == 5'd16);
            assert (region_start == ($past(region_start) + 14'd1));
        end
    end
endmodule

`default_nettype wire
