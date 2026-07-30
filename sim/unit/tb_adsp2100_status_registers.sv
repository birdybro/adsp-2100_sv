`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_status_registers;
    logic        clk;
    logic [66:0] stimulus;
    logic [43:0] expected;
    logic        reset;
    logic        astat_move_write_enable;
    logic [7:0]  astat_move_write_data;
    logic        mstat_move_write_enable;
    logic [3:0]  mstat_move_write_data;
    logic        icntl_move_write_enable;
    logic [4:0]  icntl_move_write_data;
    logic        imask_move_write_enable;
    logic [3:0]  imask_move_write_data;
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
    logic        interrupt_entry;
    logic [1:0]  interrupt_level;
    logic        status_restore;
    logic [7:0]  restore_astat;
    logic [3:0]  restore_mstat;
    logic [3:0]  restore_imask;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic [4:0]  icntl;
    logic [3:0]  imask;
    logic        alternate_bank;
    logic        bit_reverse;
    logic        overflow_latch;
    logic        saturate_ar;
    logic        write_conflict;
    logic        status_push;
    logic [7:0]  status_push_astat;
    logic [3:0]  status_push_mstat;
    logic [3:0]  status_push_imask;
    logic        compare_astat;
    logic        compare_mstat;
    logic        compare_icntl;
    logic        compare_imask;
    logic        expected_conflict;
    logic        expected_status_push;
    logic        compare_push_data;
    logic [7:0]  expected_astat;
    logic [3:0]  expected_mstat;
    logic [4:0]  expected_icntl;
    logic [3:0]  expected_imask;
    logic [7:0]  expected_push_astat;
    logic [3:0]  expected_push_mstat;
    logic [3:0]  expected_push_imask;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset,
        astat_move_write_enable,
        astat_move_write_data,
        mstat_move_write_enable,
        mstat_move_write_data,
        icntl_move_write_enable,
        icntl_move_write_data,
        imask_move_write_enable,
        imask_move_write_data,
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
        shifter_ss,
        interrupt_entry,
        interrupt_level,
        status_restore,
        restore_astat,
        restore_mstat,
        restore_imask
    } = stimulus;
    assign {
        compare_astat,
        compare_mstat,
        compare_icntl,
        compare_imask,
        expected_conflict,
        expected_status_push,
        compare_push_data,
        expected_astat,
        expected_mstat,
        expected_icntl,
        expected_imask,
        expected_push_astat,
        expected_push_mstat,
        expected_push_imask
    } = expected;

    adsp2100_status_registers dut (
        .clk_i(clk),
        .reset_i(reset),
        .astat_move_write_enable_i(astat_move_write_enable),
        .astat_move_write_data_i(astat_move_write_data),
        .mstat_move_write_enable_i(mstat_move_write_enable),
        .mstat_move_write_data_i(mstat_move_write_data),
        .icntl_move_write_enable_i(icntl_move_write_enable),
        .icntl_move_write_data_i(icntl_move_write_data),
        .imask_move_write_enable_i(imask_move_write_enable),
        .imask_move_write_data_i(imask_move_write_data),
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
        .interrupt_entry_i(interrupt_entry),
        .interrupt_level_i(interrupt_level),
        .status_restore_i(status_restore),
        .restore_astat_i(restore_astat),
        .restore_mstat_i(restore_mstat),
        .restore_imask_i(restore_imask),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .write_conflict_o(write_conflict),
        .status_push_o(status_push),
        .status_push_astat_o(status_push_astat),
        .status_push_mstat_o(status_push_mstat),
        .status_push_imask_o(status_push_imask)
    );

    initial begin
        clk = 1'b0;
        stimulus = 67'h00000000000000000;
        expected = 44'h00000000000;
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
                if (compare_icntl && (icntl !== expected_icntl)) begin
                    $fatal(
                        1,
                        "ICNTL mismatch vector=%0d expected=%02h actual=%02h",
                        vector_count,
                        expected_icntl,
                        icntl
                    );
                end
                if (compare_imask && (imask !== expected_imask)) begin
                    $fatal(
                        1,
                        "IMASK mismatch vector=%0d expected=%01h actual=%01h",
                        vector_count,
                        expected_imask,
                        imask
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
                if (status_push !== expected_status_push) begin
                    $fatal(
                        1,
                        "status push mismatch vector=%0d expected=%0b actual=%0b",
                        vector_count,
                        expected_status_push,
                        status_push
                    );
                end
                if (
                    compare_push_data
                    && (
                        {
                            status_push_astat,
                            status_push_mstat,
                            status_push_imask
                        }
                        !== {
                            expected_push_astat,
                            expected_push_mstat,
                            expected_push_imask
                        }
                    )
                ) begin
                    $fatal(
                        1,
                        "status push data mismatch vector=%0d expected=%04h actual=%04h",
                        vector_count,
                        {
                            expected_push_astat,
                            expected_push_mstat,
                            expected_push_imask
                        },
                        {
                            status_push_astat,
                            status_push_mstat,
                            status_push_imask
                        }
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
            "PASS %0d original ADSP-2100 status/control vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
