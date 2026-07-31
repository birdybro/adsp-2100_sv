`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_counter;
    logic        clk;
    logic [32:0] stimulus;
    logic [40:0] expected;
    logic        reset;
    logic        load;
    logic [13:0] load_data;
    logic        ce_test;
    logic        manual_pop;
    logic [13:0] count_stack_top_data;
    logic        count_stack_top_valid;
    logic [13:0] cntr_data;
    logic        cntr_valid;
    logic        condition_valid;
    logic        counter_expired;
    logic        not_counter_expired;
    logic        count_stack_push;
    logic [13:0] count_stack_push_data;
    logic        count_stack_pop;
    logic        decrement;
    logic        restore;
    logic        empty_ce_invalidate;
    logic        invalid_ce_test;
    logic        empty_manual_pop;
    logic        write_conflict;
    logic        compare_state;
    logic        expected_cntr_valid;
    logic [13:0] expected_cntr_data;
    logic        expected_condition_valid;
    logic        expected_counter_expired;
    logic        expected_not_counter_expired;
    logic        expected_count_stack_push;
    logic [13:0] expected_count_stack_push_data;
    logic        expected_count_stack_pop;
    logic        expected_decrement;
    logic        expected_restore;
    logic        expected_empty_ce_invalidate;
    logic        expected_invalid_ce_test;
    logic        expected_empty_manual_pop;
    logic        expected_write_conflict;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset,
        load,
        load_data,
        ce_test,
        manual_pop,
        count_stack_top_data,
        count_stack_top_valid
    } = stimulus;

    assign {
        compare_state,
        expected_cntr_valid,
        expected_cntr_data,
        expected_condition_valid,
        expected_counter_expired,
        expected_not_counter_expired,
        expected_count_stack_push,
        expected_count_stack_push_data,
        expected_count_stack_pop,
        expected_decrement,
        expected_restore,
        expected_empty_ce_invalidate,
        expected_invalid_ce_test,
        expected_empty_manual_pop,
        expected_write_conflict
    } = expected;

    adsp2100_counter dut (
        .clk_i(clk),
        .reset_i(reset),
        .load_i(load),
        .load_data_i(load_data),
        .ce_test_i(ce_test),
        .manual_pop_i(manual_pop),
        .count_stack_top_data_i(count_stack_top_data),
        .count_stack_top_valid_i(count_stack_top_valid),
        .cntr_data_o(cntr_data),
        .cntr_valid_o(cntr_valid),
        .condition_valid_o(condition_valid),
        .counter_expired_o(counter_expired),
        .not_counter_expired_o(not_counter_expired),
        .count_stack_push_o(count_stack_push),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_pop_o(count_stack_pop),
        .decrement_o(decrement),
        .restore_o(restore),
        .empty_ce_invalidate_o(empty_ce_invalidate),
        .invalid_ce_test_o(invalid_ce_test),
        .empty_manual_pop_o(empty_manual_pop),
        .write_conflict_o(write_conflict)
    );

    initial begin
        clk = 1'b0;
        stimulus = 33'h000000000;
        expected = 41'h00000000000;
        vector_file = $fopen("build/counter_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/counter_vectors.txt");
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
                if (
                    compare_state
                    && (cntr_valid !== expected_cntr_valid)
                ) begin
                    $fatal(
                        1,
                        "CNTR validity mismatch vector=%0d",
                        vector_count
                    );
                end
                if (
                    compare_state
                    && expected_cntr_valid
                    && (cntr_data !== expected_cntr_data)
                ) begin
                    $fatal(
                        1,
                        "CNTR data mismatch vector=%0d expected=%0h actual=%0h",
                        vector_count,
                        expected_cntr_data,
                        cntr_data
                    );
                end
                if (
                    {
                        condition_valid,
                        counter_expired,
                        not_counter_expired,
                        count_stack_push,
                        count_stack_pop,
                        decrement,
                        restore,
                        empty_ce_invalidate,
                        invalid_ce_test,
                        empty_manual_pop,
                        write_conflict
                    }
                    !==
                    {
                        expected_condition_valid,
                        expected_counter_expired,
                        expected_not_counter_expired,
                        expected_count_stack_push,
                        expected_count_stack_pop,
                        expected_decrement,
                        expected_restore,
                        expected_empty_ce_invalidate,
                        expected_invalid_ce_test,
                        expected_empty_manual_pop,
                        expected_write_conflict
                    }
                ) begin
                    $fatal(1, "CNTR control mismatch vector=%0d", vector_count);
                end
                if (
                    expected_count_stack_push
                    && (
                        count_stack_push_data
                        !== expected_count_stack_push_data
                    )
                ) begin
                    $fatal(
                        1,
                        "count-stack push mismatch vector=%0d",
                        vector_count
                    );
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
            "PASS %0d original ADSP-2100 CNTR cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
