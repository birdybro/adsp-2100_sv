`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_mac;
    logic [77:0]  stimulus;
    logic [137:0] expected;
    logic [137:0] actual;
    logic [4:0]   amf;
    logic [15:0]  x;
    logic [15:0]  y;
    logic [39:0]  mr;
    logic         saturation_mv;
    logic         valid;
    logic [39:0]  unrounded_result;
    logic [39:0]  result;
    logic [15:0]  mf_result;
    logic         mv;
    logic [39:0]  saturated_mr;
    integer       vector_file;
    integer       scan_count;
    integer       vector_count;

    assign {amf, x, y, mr, saturation_mv} = stimulus;
    assign actual = {
        valid,
        unrounded_result,
        result,
        mf_result,
        mv,
        saturated_mr
    };

    adsp2100_mac dut (
        .amf_i(amf),
        .x_i(x),
        .y_i(y),
        .mr_i(mr),
        .saturation_mv_i(saturation_mv),
        .valid_o(valid),
        .unrounded_result_o(unrounded_result),
        .result_o(result),
        .mf_result_o(mf_result),
        .mv_o(mv),
        .saturated_mr_o(saturated_mr)
    );

    initial begin
        vector_file = $fopen("build/mac_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/mac_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(vector_file, "%h %h\n", stimulus, expected);
            if (scan_count == 2) begin
                #1;
                if (actual !== expected) begin
                    $fatal(
                        1,
                        "MAC mismatch vector=%0d amf=%0h x=%0h y=%0h mr=%0h expected=%0h actual=%0h",
                        vector_count,
                        amf,
                        x,
                        y,
                        mr,
                        expected,
                        actual
                    );
                end
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display("PASS %0d original ADSP-2100 MAC vectors", vector_count);
        $finish;
    end
endmodule

`default_nettype wire
