`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_condition_logic;
    logic [3:0] condition;
    logic       az;
    logic       an;
    logic       av;
    logic       ac;
    logic       as_flag;
    logic       mv;
    logic       not_counter_expired;
    logic       condition_true;
    logic       expected [0:2047];
    integer     vector_index;

    adsp2100_condition_logic dut (
        .condition_i(condition),
        .az_i(az),
        .an_i(an),
        .av_i(av),
        .ac_i(ac),
        .as_i(as_flag),
        .mv_i(mv),
        .not_counter_expired_i(not_counter_expired),
        .condition_true_o(condition_true)
    );

    initial begin
        $readmemb("build/condition_expected.mem", expected);
        for (vector_index = 0; vector_index < 2048; vector_index = vector_index + 1) begin
            {condition, az, an, av, ac, as_flag, mv, not_counter_expired} =
                vector_index[10:0];
            #1;
            if (condition_true !== expected[vector_index]) begin
                $fatal(
                    1,
                    "condition mismatch vector=%0d condition=%0h flags=%0h expected=%0b actual=%0b",
                    vector_index,
                    condition,
                    vector_index[6:0],
                    expected[vector_index],
                    condition_true
                );
            end
        end
        $display("PASS 2048 exhaustive original ADSP-2100 IF-condition vectors");
        $finish;
    end
endmodule

`default_nettype wire
