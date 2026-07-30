`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_alu;
    logic [41:0] stimulus;
    logic [38:0] expected;
    logic [38:0] actual;
    logic [4:0]  amf;
    logic [15:0] x;
    logic [15:0] y;
    logic        carry;
    logic        previous_av;
    logic        sticky_av;
    logic        saturate_ar;
    logic        destination_is_ar;
    logic        valid;
    logic [15:0] raw_result;
    logic [15:0] destination_result;
    logic        az;
    logic        an;
    logic        av;
    logic        ac;
    logic        as_value;
    logic        as_write;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        amf, x, y, carry, previous_av, sticky_av, saturate_ar, destination_is_ar
    } = stimulus;
    assign actual = {
        valid, raw_result, destination_result, az, an, av, ac, as_value, as_write
    };

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

    initial begin
        vector_file = $fopen("build/alu_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/alu_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(vector_file, "%h %h\n", stimulus, expected);
            if (scan_count == 2) begin
                #1;
                if (actual !== expected) begin
                    $fatal(
                        1,
                        "ALU mismatch vector=%0d amf=%0h x=%0h y=%0h expected=%0h actual=%0h",
                        vector_count,
                        amf,
                        x,
                        y,
                        expected,
                        actual
                    );
                end
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display("PASS %0d original ADSP-2100 ALU vectors", vector_count);
        $finish;
    end
endmodule

`default_nettype wire
