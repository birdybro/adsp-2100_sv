`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_register_file;
    logic        clk;
    logic [75:0] stimulus;
    logic [49:0] expected;
    logic [47:0] actual_reads;
    logic        compare_reads;
    logic        expected_conflict;
    logic        alternate_bank;
    logic [3:0]  read_address_0;
    logic [3:0]  read_address_1;
    logic [3:0]  read_address_2;
    logic [15:0] read_data_0;
    logic [15:0] read_data_1;
    logic [15:0] read_data_2;
    logic [15:0] read_data_3;
    logic [47:0] unused_additional_read_data;
    logic        write_enable_0;
    logic [3:0]  write_address_0;
    logic [15:0] write_data_0;
    logic        write_enable_1;
    logic [3:0]  write_address_1;
    logic [15:0] write_data_1;
    logic        write_enable_2;
    logic [3:0]  write_address_2;
    logic [15:0] write_data_2;
    logic [15:0] af_data;
    logic [15:0] mf_data;
    logic [39:0] mr_data;
    logic [7:0]  se_data;
    logic [4:0]  sb_data;
    logic [31:0] sr_data;
    logic [116:0] computational_state;
    logic        write_conflict;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        alternate_bank,
        read_address_0,
        read_address_1,
        read_address_2,
        write_enable_0,
        write_address_0,
        write_data_0,
        write_enable_1,
        write_address_1,
        write_data_1,
        write_enable_2,
        write_address_2,
        write_data_2
    } = stimulus;
    assign {compare_reads, expected_conflict} = expected[49:48];
    assign actual_reads = {read_data_0, read_data_1, read_data_2};
    assign computational_state = {
        af_data,
        mf_data,
        mr_data,
        se_data,
        sb_data,
        sr_data
    };

    adsp2100_register_file dut (
        .clk_i(clk),
        .alternate_bank_i(alternate_bank),
        .read_address_0_i(read_address_0),
        .read_address_1_i(read_address_1),
        .read_address_2_i(read_address_2),
        .read_address_3_i(read_address_0),
        .read_address_4_i(read_address_0),
        .read_address_5_i(read_address_0),
        .read_address_6_i(read_address_0),
        .read_data_0_o(read_data_0),
        .read_data_1_o(read_data_1),
        .read_data_2_o(read_data_2),
        .read_data_3_o(read_data_3),
        .read_data_4_o(unused_additional_read_data[15:0]),
        .read_data_5_o(unused_additional_read_data[31:16]),
        .read_data_6_o(unused_additional_read_data[47:32]),
        .write_enable_0_i(write_enable_0),
        .write_address_0_i(write_address_0),
        .write_data_0_i(write_data_0),
        .write_enable_1_i(write_enable_1),
        .write_address_1_i(write_address_1),
        .write_data_1_i(write_data_1),
        .write_enable_2_i(write_enable_2),
        .write_address_2_i(write_address_2),
        .write_data_2_i(write_data_2),
        .sb_move_write_enable_i(1'b0),
        .sb_move_write_data_i(5'h00),
        .alu_write_enable_i(1'b0),
        .alu_destination_feedback_i(1'b0),
        .alu_result_i(16'h0000),
        .mac_write_enable_i(1'b0),
        .mac_destination_feedback_i(1'b0),
        .mac_result_i(40'h0000000000),
        .shifter_sr_write_enable_i(1'b0),
        .shifter_sr_result_i(32'h00000000),
        .shifter_se_write_enable_i(1'b0),
        .shifter_se_result_i(8'h00),
        .shifter_sb_write_enable_i(1'b0),
        .shifter_sb_result_i(5'h00),
        .af_o(af_data),
        .mf_o(mf_data),
        .mr_o(mr_data),
        .se_o(se_data),
        .sb_o(sb_data),
        .sr_o(sr_data),
        .write_conflict_o(write_conflict)
    );

    initial begin
        clk = 1'b0;
        stimulus = 76'h0000000000000000000;
        expected = 50'h0000000000000;
        vector_file = $fopen("build/register_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/register_vectors.txt");
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
                if (read_data_3 !== read_data_0) begin
                    $fatal(1, "fourth register read port mismatch");
                end
                if (write_conflict !== expected_conflict) begin
                    $fatal(
                        1,
                        "register conflict mismatch vector=%0d expected=%0b actual=%0b",
                        vector_count,
                        expected_conflict,
                        write_conflict
                    );
                end
                if (
                    compare_reads
                    && (actual_reads !== expected[47:0])
                ) begin
                    $fatal(
                        1,
                        "register read mismatch vector=%0d bank=%0b addresses=%0h/%0h/%0h expected=%0h actual=%0h state=%0h",
                        vector_count,
                        alternate_bank,
                        read_address_0,
                        read_address_1,
                        read_address_2,
                        expected[47:0],
                        actual_reads,
                        computational_state
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
            "PASS %0d original ADSP-2100 register-bank vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
