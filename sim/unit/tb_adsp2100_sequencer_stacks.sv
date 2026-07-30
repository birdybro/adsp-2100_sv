`default_nettype none

module tb_adsp2100_sequencer_stacks;
    logic        clk;
    logic [52:0] stimulus;
    logic [81:0] expected;
    logic        reset;
    logic        pc_push;
    logic        pc_pop;
    logic [13:0] pc_push_data;
    logic        count_push;
    logic        count_pop;
    logic [13:0] count_push_data;
    logic        loop_push;
    logic        loop_pop;
    logic [17:0] loop_push_data;
    logic [13:0] pc_top_data;
    logic        pc_top_valid;
    logic        pc_pop_valid;
    logic        pc_empty;
    logic        pc_overflow;
    logic [4:0]  pc_depth;
    logic        pc_push_accepted;
    logic        pc_overflow_event;
    logic        pc_empty_pop;
    logic [13:0] count_top_data;
    logic        count_top_valid;
    logic        count_pop_valid;
    logic        count_empty;
    logic        count_overflow;
    logic [2:0]  count_depth;
    logic        count_push_accepted;
    logic        count_overflow_event;
    logic        count_empty_pop;
    logic [17:0] loop_top_data;
    logic        loop_top_valid;
    logic        loop_pop_valid;
    logic        loop_empty;
    logic        loop_overflow;
    logic [2:0]  loop_depth;
    logic        loop_push_accepted;
    logic        loop_overflow_event;
    logic        loop_empty_pop;
    logic [7:0]  sstat_fragment;
    logic        write_conflict;
    logic        compare_state;
    logic [7:0]  expected_sstat;
    logic [4:0]  expected_pc_depth;
    logic        expected_pc_top_valid;
    logic [13:0] expected_pc_top_data;
    logic        expected_pc_pop_valid;
    logic        expected_pc_push_accepted;
    logic        expected_pc_overflow_event;
    logic        expected_pc_empty_pop;
    logic [2:0]  expected_count_depth;
    logic        expected_count_top_valid;
    logic [13:0] expected_count_top_data;
    logic        expected_count_pop_valid;
    logic        expected_count_push_accepted;
    logic        expected_count_overflow_event;
    logic        expected_count_empty_pop;
    logic [2:0]  expected_loop_depth;
    logic        expected_loop_top_valid;
    logic [17:0] expected_loop_top_data;
    logic        expected_loop_pop_valid;
    logic        expected_loop_push_accepted;
    logic        expected_loop_overflow_event;
    logic        expected_loop_empty_pop;
    logic        expected_write_conflict;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset,
        pc_push,
        pc_pop,
        pc_push_data,
        count_push,
        count_pop,
        count_push_data,
        loop_push,
        loop_pop,
        loop_push_data
    } = stimulus;

    assign {
        compare_state,
        expected_sstat,
        expected_pc_depth,
        expected_pc_top_valid,
        expected_pc_top_data,
        expected_pc_pop_valid,
        expected_pc_push_accepted,
        expected_pc_overflow_event,
        expected_pc_empty_pop,
        expected_count_depth,
        expected_count_top_valid,
        expected_count_top_data,
        expected_count_pop_valid,
        expected_count_push_accepted,
        expected_count_overflow_event,
        expected_count_empty_pop,
        expected_loop_depth,
        expected_loop_top_valid,
        expected_loop_top_data,
        expected_loop_pop_valid,
        expected_loop_push_accepted,
        expected_loop_overflow_event,
        expected_loop_empty_pop,
        expected_write_conflict
    } = expected;

    adsp2100_sequencer_stacks dut (
        .clk_i(clk),
        .reset_i(reset),
        .pc_push_i(pc_push),
        .pc_pop_i(pc_pop),
        .pc_push_data_i(pc_push_data),
        .pc_top_data_o(pc_top_data),
        .pc_top_valid_o(pc_top_valid),
        .pc_pop_valid_o(pc_pop_valid),
        .pc_empty_o(pc_empty),
        .pc_overflow_o(pc_overflow),
        .pc_depth_o(pc_depth),
        .pc_push_accepted_o(pc_push_accepted),
        .pc_overflow_event_o(pc_overflow_event),
        .pc_empty_pop_o(pc_empty_pop),
        .count_push_i(count_push),
        .count_pop_i(count_pop),
        .count_push_data_i(count_push_data),
        .count_top_data_o(count_top_data),
        .count_top_valid_o(count_top_valid),
        .count_pop_valid_o(count_pop_valid),
        .count_empty_o(count_empty),
        .count_overflow_o(count_overflow),
        .count_depth_o(count_depth),
        .count_push_accepted_o(count_push_accepted),
        .count_overflow_event_o(count_overflow_event),
        .count_empty_pop_o(count_empty_pop),
        .loop_push_i(loop_push),
        .loop_pop_i(loop_pop),
        .loop_push_data_i(loop_push_data),
        .loop_top_data_o(loop_top_data),
        .loop_top_valid_o(loop_top_valid),
        .loop_pop_valid_o(loop_pop_valid),
        .loop_empty_o(loop_empty),
        .loop_overflow_o(loop_overflow),
        .loop_depth_o(loop_depth),
        .loop_push_accepted_o(loop_push_accepted),
        .loop_overflow_event_o(loop_overflow_event),
        .loop_empty_pop_o(loop_empty_pop),
        .sstat_fragment_o(sstat_fragment),
        .write_conflict_o(write_conflict)
    );

    initial begin
        clk = 1'b0;
        stimulus = 53'h00000000000000;
        expected = 82'h000000000000000000000;
        vector_file = $fopen(
            "build/sequencer_stack_vectors.txt",
            "r"
        );
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/sequencer_stack_vectors.txt");
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
                    && (
                        {
                            sstat_fragment,
                            pc_depth,
                            pc_top_valid,
                            count_depth,
                            count_top_valid,
                            loop_depth,
                            loop_top_valid
                        }
                        !==
                        {
                            expected_sstat,
                            expected_pc_depth,
                            expected_pc_top_valid,
                            expected_count_depth,
                            expected_count_top_valid,
                            expected_loop_depth,
                            expected_loop_top_valid
                        }
                    )
                ) begin
                    $fatal(1, "stack state mismatch vector=%0d", vector_count);
                end
                if (
                    compare_state
                    && (
                        {
                            loop_overflow,
                            loop_empty,
                            count_overflow,
                            count_empty,
                            pc_overflow,
                            pc_empty
                        }
                        !==
                        {
                            expected_sstat[7],
                            expected_sstat[6],
                            expected_sstat[3],
                            expected_sstat[2],
                            expected_sstat[1],
                            expected_sstat[0]
                        }
                    )
                ) begin
                    $fatal(1, "stack flag mismatch vector=%0d", vector_count);
                end
                if (
                    compare_state
                    && expected_pc_top_valid
                    && (pc_top_data !== expected_pc_top_data)
                ) begin
                    $fatal(1, "PC top mismatch vector=%0d", vector_count);
                end
                if (
                    compare_state
                    && expected_count_top_valid
                    && (count_top_data !== expected_count_top_data)
                ) begin
                    $fatal(1, "count top mismatch vector=%0d", vector_count);
                end
                if (
                    compare_state
                    && expected_loop_top_valid
                    && (loop_top_data !== expected_loop_top_data)
                ) begin
                    $fatal(1, "loop top mismatch vector=%0d", vector_count);
                end
                if (
                    {
                        pc_pop_valid,
                        pc_push_accepted,
                        pc_overflow_event,
                        pc_empty_pop,
                        count_pop_valid,
                        count_push_accepted,
                        count_overflow_event,
                        count_empty_pop,
                        loop_pop_valid,
                        loop_push_accepted,
                        loop_overflow_event,
                        loop_empty_pop,
                        write_conflict
                    }
                    !==
                    {
                        expected_pc_pop_valid,
                        expected_pc_push_accepted,
                        expected_pc_overflow_event,
                        expected_pc_empty_pop,
                        expected_count_pop_valid,
                        expected_count_push_accepted,
                        expected_count_overflow_event,
                        expected_count_empty_pop,
                        expected_loop_pop_valid,
                        expected_loop_push_accepted,
                        expected_loop_overflow_event,
                        expected_loop_empty_pop,
                        expected_write_conflict
                    }
                ) begin
                    $fatal(1, "stack event mismatch vector=%0d", vector_count);
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
            "PASS %0d original ADSP-2100 sequencer-stack vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
