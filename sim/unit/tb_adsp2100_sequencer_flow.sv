`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_sequencer_flow;
    logic [61:0] stimulus;
    logic [35:0] expected;
    logic [35:0] actual;
    logic [13:0] pc;
    logic [1:0]  explicit_flow;
    logic        explicit_taken;
    logic [13:0] explicit_target;
    logic        loop_active;
    logic [13:0] loop_end;
    logic [13:0] loop_start;
    logic        loop_termination_true;
    logic        loop_uses_counter;
    logic [13:0] next_pc;
    logic        pc_stack_push;
    logic [13:0] pc_stack_push_value;
    logic        pc_stack_pop;
    logic        loop_stack_pop;
    logic        count_stack_pop;
    logic        loop_counter_test;
    logic        loop_back;
    logic        loop_exit;
    logic        explicit_transfer;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        pc,
        explicit_flow,
        explicit_taken,
        explicit_target,
        loop_active,
        loop_end,
        loop_start,
        loop_termination_true,
        loop_uses_counter
    } = stimulus;
    assign actual = {
        next_pc,
        pc_stack_push,
        pc_stack_push_value,
        pc_stack_pop,
        loop_stack_pop,
        count_stack_pop,
        loop_counter_test,
        loop_back,
        loop_exit,
        explicit_transfer
    };

    adsp2100_sequencer_flow dut (
        .pc_i(pc),
        .explicit_flow_i(explicit_flow),
        .explicit_taken_i(explicit_taken),
        .explicit_target_i(explicit_target),
        .loop_active_i(loop_active),
        .loop_end_i(loop_end),
        .loop_start_i(loop_start),
        .loop_termination_true_i(loop_termination_true),
        .loop_uses_counter_i(loop_uses_counter),
        .next_pc_o(next_pc),
        .pc_stack_push_o(pc_stack_push),
        .pc_stack_push_value_o(pc_stack_push_value),
        .pc_stack_pop_o(pc_stack_pop),
        .loop_stack_pop_o(loop_stack_pop),
        .count_stack_pop_o(count_stack_pop),
        .loop_counter_test_o(loop_counter_test),
        .loop_back_o(loop_back),
        .loop_exit_o(loop_exit),
        .explicit_transfer_o(explicit_transfer)
    );

    initial begin
        vector_file = $fopen("build/sequencer_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/sequencer_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(vector_file, "%h %h\n", stimulus, expected);
            if (scan_count == 2) begin
                #1;
                if (actual !== expected) begin
                    $fatal(
                        1,
                        "sequencer mismatch vector=%0d pc=%0h flow=%0h taken=%0b target=%0h loop=%0b end=%0h start=%0h term=%0b counter=%0b expected=%0h actual=%0h",
                        vector_count,
                        pc,
                        explicit_flow,
                        explicit_taken,
                        explicit_target,
                        loop_active,
                        loop_end,
                        loop_start,
                        loop_termination_true,
                        loop_uses_counter,
                        expected,
                        actual
                    );
                end
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display(
            "PASS %0d original ADSP-2100 sequencer-flow vectors",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
