`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_shifter;
    logic [67:0] stimulus;
    logic [49:0] expected;
    logic [49:0] actual;
    logic [3:0]  sf;
    logic [15:0] x;
    logic [7:0]  shift_or_se;
    logic [31:0] sr;
    logic [4:0]  sb;
    logic        av;
    logic        ac;
    logic        ss;
    logic [31:0] sr_result;
    logic        sr_write;
    logic [7:0]  se_result;
    logic        se_write;
    logic [4:0]  sb_result;
    logic        sb_write;
    logic        ss_result;
    logic        ss_write;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {sf, x, shift_or_se, sr, sb, av, ac, ss} = stimulus;
    assign actual = {
        sr_result,
        sr_write,
        se_result,
        se_write,
        sb_result,
        sb_write,
        ss_result,
        ss_write
    };

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

    initial begin
        vector_file = $fopen("build/shifter_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/shifter_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(vector_file, "%h %h\n", stimulus, expected);
            if (scan_count == 2) begin
                #1;
                if (actual !== expected) begin
                    $fatal(
                        1,
                        "shifter mismatch vector=%0d sf=%0h x=%0h shift=%0h expected=%0h actual=%0h",
                        vector_count,
                        sf,
                        x,
                        shift_or_se,
                        expected,
                        actual
                    );
                end
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display(
            "PASS %0d original ADSP-2100 shifter vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
