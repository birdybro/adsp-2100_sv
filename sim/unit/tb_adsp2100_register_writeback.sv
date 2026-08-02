`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_register_writeback;
    logic         clk;
    logic [139:0] stimulus;
    logic [134:0] expected;
    logic [132:0] actual;
    logic         compare_state;
    logic         expected_conflict;
    logic         alternate_bank;
    logic [3:0]   read_address;
    logic [15:0]  read_data;
    logic [15:0]  read_data_1;
    logic [15:0]  read_data_2;
    logic [15:0]  unused_read_data_3;
    logic [47:0]  unused_additional_read_data;
    logic         dreg_write_enable;
    logic [3:0]   dreg_write_address;
    logic [15:0]  dreg_write_data;
    logic         sb_move_write_enable;
    logic [4:0]   sb_move_write_data;
    logic         alu_write_enable;
    logic         alu_destination_feedback;
    logic [15:0]  alu_result;
    logic         mac_write_enable;
    logic         mac_destination_feedback;
    logic [39:0]  mac_result;
    logic         shifter_sr_write_enable;
    logic [31:0]  shifter_sr_result;
    logic         shifter_se_write_enable;
    logic [7:0]   shifter_se_result;
    logic         shifter_sb_write_enable;
    logic [4:0]   shifter_sb_result;
    logic [15:0]  af;
    logic [15:0]  mf;
    logic [39:0]  mr;
    logic [7:0]   se;
    logic [4:0]   sb;
    logic [31:0]  sr;
    logic         write_conflict;
    integer       vector_file;
    integer       scan_count;
    integer       vector_count;

    assign {
        alternate_bank,
        read_address,
        dreg_write_enable,
        dreg_write_address,
        dreg_write_data,
        sb_move_write_enable,
        sb_move_write_data,
        alu_write_enable,
        alu_destination_feedback,
        alu_result,
        mac_write_enable,
        mac_destination_feedback,
        mac_result,
        shifter_sr_write_enable,
        shifter_sr_result,
        shifter_se_write_enable,
        shifter_se_result,
        shifter_sb_write_enable,
        shifter_sb_result
    } = stimulus;
    assign {compare_state, expected_conflict} = expected[134:133];
    assign actual = {read_data, af, mf, mr, se, sb, sr};

    adsp2100_register_file dut (
        .clk_i(clk),
        .alternate_bank_i(alternate_bank),
        .read_address_0_i(read_address),
        .read_address_1_i(read_address),
        .read_address_2_i(read_address),
        .read_address_3_i(read_address),
        .read_address_4_i(read_address),
        .read_address_5_i(read_address),
        .read_address_6_i(read_address),
        .read_data_0_o(read_data),
        .read_data_1_o(read_data_1),
        .read_data_2_o(read_data_2),
        .read_data_3_o(unused_read_data_3),
        .read_data_4_o(unused_additional_read_data[15:0]),
        .read_data_5_o(unused_additional_read_data[31:16]),
        .read_data_6_o(unused_additional_read_data[47:32]),
        .write_enable_0_i(dreg_write_enable),
        .write_address_0_i(dreg_write_address),
        .write_data_0_i(dreg_write_data),
        .write_enable_1_i(1'b0),
        .write_address_1_i(4'h0),
        .write_data_1_i(16'h0000),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(sb_move_write_enable),
        .sb_move_write_data_i(sb_move_write_data),
        .alu_write_enable_i(alu_write_enable),
        .alu_destination_feedback_i(alu_destination_feedback),
        .alu_result_i(alu_result),
        .mac_write_enable_i(mac_write_enable),
        .mac_destination_feedback_i(mac_destination_feedback),
        .mac_result_i(mac_result),
        .shifter_sr_write_enable_i(shifter_sr_write_enable),
        .shifter_sr_result_i(shifter_sr_result),
        .shifter_se_write_enable_i(shifter_se_write_enable),
        .shifter_se_result_i(shifter_se_result),
        .shifter_sb_write_enable_i(shifter_sb_write_enable),
        .shifter_sb_result_i(shifter_sb_result),
        .af_o(af),
        .mf_o(mf),
        .mr_o(mr),
        .se_o(se),
        .sb_o(sb),
        .sr_o(sr),
        .write_conflict_o(write_conflict)
    );

    initial begin
        clk = 1'b0;
        stimulus = 140'h00000000000000000000000000000000000;
        expected = 135'h0000000000000000000000000000000000;
        vector_file = $fopen("build/register_writeback_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/register_writeback_vectors.txt");
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
                        "writeback conflict mismatch vector=%0d expected=%0b actual=%0b",
                        vector_count,
                        expected_conflict,
                        write_conflict
                    );
                end
                if (compare_state && (actual !== expected[132:0])) begin
                    $fatal(
                        1,
                        "writeback state mismatch vector=%0d bank=%0b read=%0h expected=%0h actual=%0h",
                        vector_count,
                        alternate_bank,
                        read_address,
                        expected[132:0],
                        actual
                    );
                end
                if (
                    compare_state
                    && (
                        (read_data_1 !== read_data)
                        || (read_data_2 !== read_data)
                    )
                ) begin
                    $fatal(
                        1,
                        "writeback read-port mismatch vector=%0d read0=%0h read1=%0h read2=%0h",
                        vector_count,
                        read_data,
                        read_data_1,
                        read_data_2
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
            "PASS %0d original ADSP-2100 writeback vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
