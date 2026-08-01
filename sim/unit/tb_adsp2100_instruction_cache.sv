`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_instruction_cache;
    logic clk;
    logic [56:0] stimulus;
    logic [49:0] expected;
    logic reset;
    logic fill;
    logic [13:0] fill_address;
    logic fill_address_valid;
    logic [23:0] fill_instruction;
    logic fill_instruction_valid;
    logic [13:0] lookup_address;
    logic lookup_address_valid;
    logic lookup_hit;
    logic [23:0] lookup_instruction;
    logic lookup_instruction_valid;
    logic fill_accepted;
    logic region_restarted;
    logic oldest_replaced;
    logic [13:0] region_start;
    logic region_start_valid;
    logic [4:0] region_count;
    logic compare_state;
    logic expected_lookup_hit;
    logic expected_instruction_valid;
    logic [23:0] expected_instruction;
    logic expected_fill_accepted;
    logic expected_region_restarted;
    logic expected_oldest_replaced;
    logic expected_region_start_valid;
    logic [13:0] expected_region_start;
    logic [4:0] expected_region_count;
    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset,
        fill,
        fill_address,
        fill_address_valid,
        fill_instruction,
        fill_instruction_valid,
        lookup_address,
        lookup_address_valid
    } = stimulus;

    assign {
        compare_state,
        expected_lookup_hit,
        expected_instruction_valid,
        expected_instruction,
        expected_fill_accepted,
        expected_region_restarted,
        expected_oldest_replaced,
        expected_region_start_valid,
        expected_region_start,
        expected_region_count
    } = expected;

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

    initial begin
        clk = 1'b0;
        stimulus = 57'h000000000000000;
        expected = 50'h0000000000000;
        vector_file = $fopen("build/instruction_cache_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/instruction_cache_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(vector_file, "%h %h\n", stimulus, expected);
            if (scan_count == 2) begin
                #1;
                if (
                    {
                        lookup_hit,
                        lookup_instruction_valid,
                        fill_accepted,
                        region_restarted,
                        oldest_replaced
                    }
                    !==
                    {
                        expected_lookup_hit,
                        expected_instruction_valid,
                        expected_fill_accepted,
                        expected_region_restarted,
                        expected_oldest_replaced
                    }
                ) begin
                    $fatal(1, "cache control mismatch vector=%0d", vector_count);
                end
                if (
                    expected_instruction_valid
                    && lookup_instruction !== expected_instruction
                ) begin
                    $fatal(1, "cache instruction mismatch vector=%0d", vector_count);
                end
                if (
                    compare_state
                    && {
                        region_start_valid,
                        region_start,
                        region_count
                    }
                    !==
                    {
                        expected_region_start_valid,
                        expected_region_start,
                        expected_region_count
                    }
                ) begin
                    $fatal(1, "cache monitor mismatch vector=%0d", vector_count);
                end
                clk = 1'b1;
                #1;
                clk = 1'b0;
                #1;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display(
            "PASS original ADSP-2100 instruction cache differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
