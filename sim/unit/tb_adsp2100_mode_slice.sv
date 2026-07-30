`default_nettype none

module tb_adsp2100_mode_slice;
    logic         clk;
    logic [128:0] stimulus;
    logic [99:0]  expected;
    logic         reset;
    logic         astat_move_enable;
    logic [7:0]   astat_move_data;
    logic         mstat_move_enable;
    logic [3:0]   mstat_move_data;
    logic [1:0]   mode_sr;
    logic [1:0]   mode_br;
    logic [1:0]   mode_ol;
    logic [1:0]   mode_as;
    logic [3:0]   dreg_read_address;
    logic [15:0]  dreg_read_data;
    logic         dreg_write_enable;
    logic [3:0]   dreg_write_address;
    logic [15:0]  dreg_write_data;
    logic         alu_execute;
    logic [4:0]   alu_amf;
    logic [15:0]  alu_x;
    logic [15:0]  alu_y;
    logic         alu_feedback;
    logic         alu_valid;
    logic [15:0]  alu_raw_result;
    logic [15:0]  alu_destination_result;
    logic [13:0]  dag_i;
    logic [13:0]  dag_m;
    logic [13:0]  dag_l;
    logic [13:0]  dag_address;
    logic [13:0]  dag_next_i;
    logic [7:0]   astat;
    logic [3:0]   mstat;
    logic         alternate_bank;
    logic         bit_reverse;
    logic         overflow_latch;
    logic         saturate_ar;
    logic         status_conflict;
    logic         register_conflict;
    logic         compare_astat;
    logic         compare_read;
    logic         compare_alu;
    logic         compare_modes;
    logic         compare_dag;
    logic         expected_status_conflict;
    logic         expected_register_conflict;
    logic [7:0]   expected_astat;
    logic [3:0]   expected_mstat;
    logic         expected_alternate_bank;
    logic         expected_bit_reverse;
    logic         expected_overflow_latch;
    logic         expected_saturate_ar;
    logic [15:0]  expected_read_data;
    logic         expected_alu_valid;
    logic [15:0]  expected_alu_raw;
    logic [15:0]  expected_alu_destination;
    logic [13:0]  expected_dag_address;
    logic [13:0]  expected_dag_next_i;
    integer       vector_file;
    integer       scan_count;
    integer       vector_count;

    assign {
        reset,
        astat_move_enable,
        astat_move_data,
        mstat_move_enable,
        mstat_move_data,
        mode_sr,
        mode_br,
        mode_ol,
        mode_as,
        dreg_read_address,
        dreg_write_enable,
        dreg_write_address,
        dreg_write_data,
        alu_execute,
        alu_amf,
        alu_x,
        alu_y,
        alu_feedback,
        dag_i,
        dag_m,
        dag_l
    } = stimulus;

    assign {
        compare_astat,
        compare_read,
        compare_alu,
        compare_modes,
        compare_dag,
        expected_status_conflict,
        expected_register_conflict,
        expected_astat,
        expected_mstat,
        expected_alternate_bank,
        expected_bit_reverse,
        expected_overflow_latch,
        expected_saturate_ar,
        expected_read_data,
        expected_alu_valid,
        expected_alu_raw,
        expected_alu_destination,
        expected_dag_address,
        expected_dag_next_i
    } = expected;

    adsp2100_mode_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .astat_move_write_enable_i(astat_move_enable),
        .astat_move_write_data_i(astat_move_data),
        .mstat_move_write_enable_i(mstat_move_enable),
        .mstat_move_write_data_i(mstat_move_data),
        .mode_sr_i(mode_sr),
        .mode_br_i(mode_br),
        .mode_ol_i(mode_ol),
        .mode_as_i(mode_as),
        .dreg_read_address_i(dreg_read_address),
        .dreg_read_data_o(dreg_read_data),
        .dreg_write_enable_i(dreg_write_enable),
        .dreg_write_address_i(dreg_write_address),
        .dreg_write_data_i(dreg_write_data),
        .alu_execute_i(alu_execute),
        .alu_amf_i(alu_amf),
        .alu_x_i(alu_x),
        .alu_y_i(alu_y),
        .alu_destination_feedback_i(alu_feedback),
        .alu_valid_o(alu_valid),
        .alu_raw_result_o(alu_raw_result),
        .alu_destination_result_o(alu_destination_result),
        .dag1_i_i(dag_i),
        .dag1_m_i(dag_m),
        .dag1_l_i(dag_l),
        .dag1_address_o(dag_address),
        .dag1_next_i_o(dag_next_i),
        .astat_o(astat),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .status_write_conflict_o(status_conflict),
        .register_write_conflict_o(register_conflict)
    );

    initial begin
        clk = 1'b0;
        stimulus = 129'h0;
        expected = 100'h0;
        vector_file = $fopen("build/mode_slice_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/mode_slice_vectors.txt");
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
                if (compare_astat && (astat !== expected_astat)) begin
                    $fatal(
                        1,
                        "ASTAT mismatch vector=%0d expected=%02h actual=%02h",
                        vector_count,
                        expected_astat,
                        astat
                    );
                end
                if (
                    compare_modes
                    && (
                        {mstat, alternate_bank, bit_reverse,
                            overflow_latch, saturate_ar}
                        !==
                        {expected_mstat, expected_alternate_bank,
                            expected_bit_reverse, expected_overflow_latch,
                            expected_saturate_ar}
                    )
                ) begin
                    $fatal(1, "mode mismatch vector=%0d", vector_count);
                end
                if (
                    compare_read
                    && (dreg_read_data !== expected_read_data)
                ) begin
                    $fatal(
                        1,
                        "DREG mismatch vector=%0d expected=%04h actual=%04h",
                        vector_count,
                        expected_read_data,
                        dreg_read_data
                    );
                end
                if (
                    compare_alu
                    && (
                        {alu_valid, alu_raw_result, alu_destination_result}
                        !==
                        {expected_alu_valid, expected_alu_raw,
                            expected_alu_destination}
                    )
                ) begin
                    $fatal(1, "ALU mismatch vector=%0d", vector_count);
                end
                if (
                    compare_dag
                    && (
                        {dag_address, dag_next_i}
                        !== {expected_dag_address, expected_dag_next_i}
                    )
                ) begin
                    $fatal(1, "DAG mismatch vector=%0d", vector_count);
                end
                if (
                    {status_conflict, register_conflict}
                    !== {
                        expected_status_conflict,
                        expected_register_conflict
                    }
                ) begin
                    $fatal(1, "conflict mismatch vector=%0d", vector_count);
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
            "PASS %0d original ADSP-2100 MSTAT-consumer vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
