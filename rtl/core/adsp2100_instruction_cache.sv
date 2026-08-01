`default_nettype none

module adsp2100_instruction_cache (
    input  logic        clk_i,
    input  logic        reset_i,

    input  logic        fill_i,
    input  logic [13:0] fill_address_i,
    input  logic        fill_address_valid_i,
    input  logic [23:0] fill_instruction_i,
    input  logic        fill_instruction_valid_i,

    input  logic [13:0] lookup_address_i,
    input  logic        lookup_address_valid_i,

    output logic        lookup_hit_o,
    output logic [23:0] lookup_instruction_o,
    output logic        lookup_instruction_valid_o,
    output logic        fill_accepted_o,
    output logic        region_restarted_o,
    output logic        oldest_replaced_o,
    output logic [13:0] region_start_o,
    output logic        region_start_valid_o,
    output logic [4:0]  region_count_o
);
    logic [23:0] cache_data_q [0:15];
    logic [15:0] cache_data_valid_q;
    logic [13:0] region_start_q;
    logic [4:0] region_count_q;

    logic [13:0] lookup_delta;
    logic [13:0] fill_delta;
    logic [13:0] append_address;
    logic fill_contained;
    logic [15:0] next_data_valid;
    logic [13:0] next_region_start;
    logic [4:0] next_region_count;

    assign lookup_delta = lookup_address_i - region_start_q;
    assign lookup_hit_o = (
        !reset_i
        && lookup_address_valid_i
        && region_count_q != 5'd0
        && {1'b0, lookup_delta} < {10'h000, region_count_q}
    );
    assign lookup_instruction_valid_o = (
        lookup_hit_o && cache_data_valid_q[lookup_address_i[3:0]]
    );
    assign lookup_instruction_o = (
        lookup_instruction_valid_o
        ? cache_data_q[lookup_address_i[3:0]] : 24'h000000
    );
    assign fill_accepted_o = !reset_i && fill_i && fill_address_valid_i;
    assign region_start_o = region_start_q;
    assign region_start_valid_o = !reset_i && region_count_q != 5'd0;
    assign region_count_o = reset_i ? 5'd0 : region_count_q;

    assign fill_delta = fill_address_i - region_start_q;
    assign fill_contained = (
        region_count_q != 5'd0
        && {1'b0, fill_delta} < {10'h000, region_count_q}
    );
    assign append_address = region_start_q + {9'h000, region_count_q};

    always_comb begin
        next_data_valid = cache_data_valid_q;
        next_region_start = region_start_q;
        next_region_count = region_count_q;
        region_restarted_o = 1'b0;
        oldest_replaced_o = 1'b0;

        if (!reset_i && fill_i) begin
            if (!fill_address_valid_i) begin
                next_data_valid = 16'h0000;
                next_region_start = 14'h0000;
                next_region_count = 5'd0;
                region_restarted_o = 1'b1;
            end else begin
                if (region_count_q == 5'd0) begin
                    next_data_valid = 16'h0000;
                    next_region_start = fill_address_i;
                    next_region_count = 5'd1;
                    region_restarted_o = 1'b1;
                end else if (fill_contained) begin
                    next_region_start = region_start_q;
                    next_region_count = region_count_q;
                end else if (fill_address_i == append_address) begin
                    if (region_count_q < 5'd16) begin
                        next_region_count = region_count_q + 5'd1;
                    end else begin
                        next_data_valid[region_start_q[3:0]] = 1'b0;
                        next_region_start = region_start_q + 14'd1;
                        oldest_replaced_o = 1'b1;
                    end
                end else begin
                    next_data_valid = 16'h0000;
                    next_region_start = fill_address_i;
                    next_region_count = 5'd1;
                    region_restarted_o = 1'b1;
                end
                next_data_valid[fill_address_i[3:0]] = (
                    fill_instruction_valid_i
                );
            end
        end
    end

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            cache_data_valid_q <= 16'h0000;
            region_start_q <= 14'h0000;
            region_count_q <= 5'd0;
        end else if (fill_i) begin
            cache_data_valid_q <= next_data_valid;
            region_start_q <= next_region_start;
            region_count_q <= next_region_count;
            if (fill_address_valid_i) begin
                cache_data_q[fill_address_i[3:0]] <= fill_instruction_i;
            end
        end
    end
endmodule

`default_nettype wire
