`default_nettype none

module tb_adsp2100_status_stack;
    logic        clk;
    logic [18:0] stimulus;
    logic [26:0] expected;
    logic        reset;
    logic [1:0]  operation;
    logic [15:0] push_data;
    logic [15:0] pop_data;
    logic        pop_valid;
    logic        empty;
    logic        overflow;
    logic [2:0]  depth;
    logic        push_accepted;
    logic        overflow_event;
    logic        empty_pop;
    logic        compare_state;
    logic        expected_empty;
    logic        expected_overflow;
    logic [2:0]  expected_depth;
    logic        expected_pop_valid;
    logic        compare_pop_data;
    logic [15:0] expected_pop_data;
    logic        expected_push_accepted;
    logic        expected_overflow_event;
    logic        expected_empty_pop;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset,
        operation,
        push_data
    } = stimulus;
    assign {
        compare_state,
        expected_empty,
        expected_overflow,
        expected_depth,
        expected_pop_valid,
        compare_pop_data,
        expected_pop_data,
        expected_push_accepted,
        expected_overflow_event,
        expected_empty_pop
    } = expected;

    adsp2100_status_stack dut (
        .clk_i(clk),
        .reset_i(reset),
        .operation_i(operation),
        .push_data_i(push_data),
        .pop_data_o(pop_data),
        .pop_valid_o(pop_valid),
        .empty_o(empty),
        .overflow_o(overflow),
        .depth_o(depth),
        .push_accepted_o(push_accepted),
        .overflow_event_o(overflow_event),
        .empty_pop_o(empty_pop)
    );

    initial begin
        clk = 1'b0;
        stimulus = 19'h00000;
        expected = 27'h0000000;
        vector_file = $fopen("build/status_stack_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/status_stack_vectors.txt");
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
                        {empty, overflow, depth}
                        !== {
                            expected_empty,
                            expected_overflow,
                            expected_depth
                        }
                    )
                ) begin
                    $fatal(
                        1,
                        "state mismatch vector=%0d expected=%05b actual=%05b",
                        vector_count,
                        {
                            expected_empty,
                            expected_overflow,
                            expected_depth
                        },
                        {empty, overflow, depth}
                    );
                end
                if (pop_valid !== expected_pop_valid) begin
                    $fatal(
                        1,
                        "pop valid mismatch vector=%0d expected=%0b actual=%0b",
                        vector_count,
                        expected_pop_valid,
                        pop_valid
                    );
                end
                if (compare_pop_data && (pop_data !== expected_pop_data)) begin
                    $fatal(
                        1,
                        "pop data mismatch vector=%0d expected=%04h actual=%04h",
                        vector_count,
                        expected_pop_data,
                        pop_data
                    );
                end
                if (
                    {
                        push_accepted,
                        overflow_event,
                        empty_pop
                    }
                    !== {
                        expected_push_accepted,
                        expected_overflow_event,
                        expected_empty_pop
                    }
                ) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d expected=%03b actual=%03b",
                        vector_count,
                        {
                            expected_push_accepted,
                            expected_overflow_event,
                            expected_empty_pop
                        },
                        {
                            push_accepted,
                            overflow_event,
                            empty_pop
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
            "PASS %0d original ADSP-2100 status-stack vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
