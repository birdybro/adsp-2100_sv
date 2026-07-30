`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_status_registers;
    logic        clk;
    logic [35:0] stimulus;
    logic [14:0] expected;
    logic        reset;
    logic        astat_move_write_enable;
    logic [7:0]  astat_move_write_data;
    logic        mstat_move_write_enable;
    logic [3:0]  mstat_move_write_data;
    logic [1:0]  mode_sr;
    logic [1:0]  mode_br;
    logic [1:0]  mode_ol;
    logic [1:0]  mode_as;
    logic        alu_status_write_enable;
    logic        alu_az;
    logic        alu_an;
    logic        alu_av;
    logic        alu_ac;
    logic        alu_as_write_enable;
    logic        alu_as;
    logic        divide_status_write_enable;
    logic        divide_aq;
    logic        mac_status_write_enable;
    logic        mac_mv;
    logic        shifter_status_write_enable;
    logic        shifter_ss;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        bit_reverse;
    logic        overflow_latch;
    logic        saturate_ar;
    logic        write_conflict;
    logic        compare_astat;
    logic        compare_mstat;
    logic        expected_conflict;
    logic [7:0]  expected_astat;
    logic [3:0]  expected_mstat;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset,
        astat_move_write_enable,
        astat_move_write_data,
        mstat_move_write_enable,
        mstat_move_write_data,
        mode_sr,
        mode_br,
        mode_ol,
        mode_as,
        alu_status_write_enable,
        alu_az,
        alu_an,
        alu_av,
        alu_ac,
        alu_as_write_enable,
        alu_as,
        divide_status_write_enable,
        divide_aq,
        mac_status_write_enable,
        mac_mv,
        shifter_status_write_enable,
        shifter_ss
    } = stimulus;
    assign {
        compare_astat,
        compare_mstat,
        expected_conflict,
        expected_astat,
        expected_mstat
    } = expected;

    adsp2100_status_registers dut (
        .clk_i(clk),
        .reset_i(reset),
        .astat_move_write_enable_i(astat_move_write_enable),
        .astat_move_write_data_i(astat_move_write_data),
        .mstat_move_write_enable_i(mstat_move_write_enable),
        .mstat_move_write_data_i(mstat_move_write_data),
        .mode_sr_i(mode_sr),
        .mode_br_i(mode_br),
        .mode_ol_i(mode_ol),
        .mode_as_i(mode_as),
        .alu_status_write_enable_i(alu_status_write_enable),
        .alu_az_i(alu_az),
        .alu_an_i(alu_an),
        .alu_av_i(alu_av),
        .alu_ac_i(alu_ac),
        .alu_as_write_enable_i(alu_as_write_enable),
        .alu_as_i(alu_as),
        .divide_status_write_enable_i(divide_status_write_enable),
        .divide_aq_i(divide_aq),
        .mac_status_write_enable_i(mac_status_write_enable),
        .mac_mv_i(mac_mv),
        .shifter_status_write_enable_i(shifter_status_write_enable),
        .shifter_ss_i(shifter_ss),
        .astat_o(astat),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .write_conflict_o(write_conflict)
    );

    initial begin
        clk = 1'b0;
        stimulus = 36'h000000000;
        expected = 15'h0000;
        vector_file = $fopen("build/status_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/status_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h\n",
                stimulus,
                expected
            );
            if (scan_count == 2) begin
                #1;
                if (write_conflict !== expected_conflict) begin
                    $fatal(
                        1,
                        "status conflict mismatch vector=%0d expected=%0b actual=%0b",
                        vector_count,
                        expected_conflict,
                        write_conflict
                    );
                end
                if (compare_astat && (astat !== expected_astat)) begin
                    $fatal(
                        1,
                        "ASTAT mismatch vector=%0d expected=%02h actual=%02h",
                        vector_count,
                        expected_astat,
                        astat
                    );
                end
                if (compare_mstat && (mstat !== expected_mstat)) begin
                    $fatal(
                        1,
                        "MSTAT mismatch vector=%0d expected=%01h actual=%01h",
                        vector_count,
                        expected_mstat,
                        mstat
                    );
                end
                if (
                    compare_mstat
                    && (
                        {
                            saturate_ar,
                            overflow_latch,
                            bit_reverse,
                            alternate_bank
                        }
                        !== expected_mstat
                    )
                ) begin
                    $fatal(
                        1,
                        "MSTAT mode output mismatch vector=%0d",
                        vector_count
                    );
                end
                #4;
                clk = 1'b1;
                #1;
                clk = 1'b0;
                #4;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display(
            "PASS %0d original ADSP-2100 ASTAT/MSTAT vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
