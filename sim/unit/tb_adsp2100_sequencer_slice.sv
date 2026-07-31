`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_sequencer_slice;
    logic         clk;
    logic [77:0]  stimulus;
    logic [140:0] expected;

    logic        reset;
    logic [13:0] pc;
    logic        do_until;
    logic [13:0] do_end;
    logic [3:0]  do_condition;
    logic [1:0]  explicit_flow;
    logic [3:0]  explicit_condition;
    logic [13:0] explicit_target;
    logic        counter_load;
    logic [13:0] counter_load_data;
    logic        pc_manual_pop;
    logic        count_manual_pop;
    logic        loop_manual_pop;
    logic        az;
    logic        an;
    logic        av;
    logic        ac;
    logic        as_flag;
    logic        mv;

    logic [13:0] next_pc;
    logic        boundary_valid;
    logic        integration_conflict;
    logic        unsupported_call_ce;
    logic        invalid_counter_condition;
    logic        invalid_loop_context;
    logic        invalid_return_context;
    logic        unsupported_do_at_loop_end;
    logic        explicit_condition_true;
    logic        loop_termination_true;
    logic        explicit_transfer;
    logic        loop_back;
    logic        loop_exit;
    logic [13:0] cntr_data;
    logic        cntr_valid;
    logic        counter_condition_valid;
    logic        counter_expired;
    logic        not_counter_expired;
    logic        counter_test;
    logic        counter_decrement;
    logic        counter_restore;
    logic        counter_empty_invalidate;
    logic        counter_invalid_test;
    logic        counter_empty_manual_pop;
    logic [13:0] pc_top_data;
    logic [13:0] count_top_data;
    logic [17:0] loop_top_data;
    logic [2:0]  stack_top_valid;
    logic [4:0]  pc_depth;
    logic [2:0]  count_depth;
    logic [2:0]  loop_depth;
    logic [2:0]  stack_empty;
    logic [2:0]  stack_overflow;
    logic [2:0]  stack_pop_valid;
    logic [2:0]  stack_push_accepted;
    logic [2:0]  stack_overflow_event;
    logic [2:0]  stack_empty_pop;
    logic [7:0]  sstat_fragment;
    logic        pc_stack_push;
    logic        pc_stack_pop;
    logic        count_stack_push;
    logic        count_stack_pop;
    logic        loop_stack_push;
    logic        loop_stack_pop;
    logic        internal_storage_conflict;

    logic        compare_state;
    logic        expected_cntr_valid;
    logic [13:0] expected_cntr_data;
    logic        expected_pc_top_valid;
    logic [13:0] expected_pc_top_data;
    logic        expected_count_top_valid;
    logic [13:0] expected_count_top_data;
    logic        expected_loop_top_valid;
    logic [17:0] expected_loop_top_data;
    logic [4:0]  expected_pc_depth;
    logic [2:0]  expected_count_depth;
    logic [2:0]  expected_loop_depth;
    logic [2:0]  expected_stack_overflow;
    logic [7:0]  expected_sstat_fragment;
    logic [13:0] expected_next_pc;
    logic        expected_boundary_valid;
    logic        expected_integration_conflict;
    logic        expected_unsupported_call_ce;
    logic        expected_invalid_counter_condition;
    logic        expected_invalid_loop_context;
    logic        expected_invalid_return_context;
    logic        expected_unsupported_do_at_loop_end;
    logic        expected_explicit_condition_true;
    logic        expected_loop_termination_true;
    logic        expected_explicit_transfer;
    logic        expected_loop_back;
    logic        expected_loop_exit;
    logic        expected_counter_condition_valid;
    logic        expected_counter_expired;
    logic        expected_not_counter_expired;
    logic        expected_counter_test;
    logic        expected_counter_decrement;
    logic        expected_counter_restore;
    logic        expected_counter_empty_invalidate;
    logic        expected_counter_invalid_test;
    logic        expected_counter_empty_manual_pop;
    logic        expected_pc_stack_push;
    logic        expected_pc_stack_pop;
    logic        expected_count_stack_push;
    logic        expected_count_stack_pop;
    logic        expected_loop_stack_push;
    logic        expected_loop_stack_pop;
    logic [2:0]  expected_stack_pop_valid;
    logic [2:0]  expected_stack_push_accepted;
    logic [2:0]  expected_stack_overflow_event;
    logic [2:0]  expected_stack_empty_pop;
    logic        expected_internal_storage_conflict;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset,
        pc,
        do_until,
        do_end,
        do_condition,
        explicit_flow,
        explicit_condition,
        explicit_target,
        counter_load,
        counter_load_data,
        pc_manual_pop,
        count_manual_pop,
        loop_manual_pop,
        az,
        an,
        av,
        ac,
        as_flag,
        mv
    } = stimulus;

    assign {
        compare_state,
        expected_cntr_valid,
        expected_cntr_data,
        expected_pc_top_valid,
        expected_pc_top_data,
        expected_count_top_valid,
        expected_count_top_data,
        expected_loop_top_valid,
        expected_loop_top_data,
        expected_pc_depth,
        expected_count_depth,
        expected_loop_depth,
        expected_stack_overflow,
        expected_sstat_fragment,
        expected_next_pc,
        expected_boundary_valid,
        expected_integration_conflict,
        expected_unsupported_call_ce,
        expected_invalid_counter_condition,
        expected_invalid_loop_context,
        expected_invalid_return_context,
        expected_unsupported_do_at_loop_end,
        expected_explicit_condition_true,
        expected_loop_termination_true,
        expected_explicit_transfer,
        expected_loop_back,
        expected_loop_exit,
        expected_counter_condition_valid,
        expected_counter_expired,
        expected_not_counter_expired,
        expected_counter_test,
        expected_counter_decrement,
        expected_counter_restore,
        expected_counter_empty_invalidate,
        expected_counter_invalid_test,
        expected_counter_empty_manual_pop,
        expected_pc_stack_push,
        expected_pc_stack_pop,
        expected_count_stack_push,
        expected_count_stack_pop,
        expected_loop_stack_push,
        expected_loop_stack_pop,
        expected_stack_pop_valid,
        expected_stack_push_accepted,
        expected_stack_overflow_event,
        expected_stack_empty_pop,
        expected_internal_storage_conflict
    } = expected;

    adsp2100_sequencer_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .pc_i(pc),
        .do_until_i(do_until),
        .do_end_i(do_end),
        .do_condition_i(do_condition),
        .explicit_flow_i(explicit_flow),
        .explicit_condition_i(explicit_condition),
        .explicit_target_i(explicit_target),
        .counter_load_i(counter_load),
        .counter_load_data_i(counter_load_data),
        .pc_manual_pop_i(pc_manual_pop),
        .count_manual_pop_i(count_manual_pop),
        .loop_manual_pop_i(loop_manual_pop),
        .az_i(az),
        .an_i(an),
        .av_i(av),
        .ac_i(ac),
        .as_i(as_flag),
        .mv_i(mv),
        .next_pc_o(next_pc),
        .boundary_valid_o(boundary_valid),
        .integration_conflict_o(integration_conflict),
        .unsupported_call_ce_o(unsupported_call_ce),
        .invalid_counter_condition_o(invalid_counter_condition),
        .invalid_loop_context_o(invalid_loop_context),
        .invalid_return_context_o(invalid_return_context),
        .unsupported_do_at_loop_end_o(unsupported_do_at_loop_end),
        .explicit_condition_true_o(explicit_condition_true),
        .loop_termination_true_o(loop_termination_true),
        .explicit_transfer_o(explicit_transfer),
        .loop_back_o(loop_back),
        .loop_exit_o(loop_exit),
        .cntr_data_o(cntr_data),
        .cntr_valid_o(cntr_valid),
        .counter_condition_valid_o(counter_condition_valid),
        .counter_expired_o(counter_expired),
        .not_counter_expired_o(not_counter_expired),
        .counter_test_o(counter_test),
        .counter_decrement_o(counter_decrement),
        .counter_restore_o(counter_restore),
        .counter_empty_invalidate_o(counter_empty_invalidate),
        .counter_invalid_test_o(counter_invalid_test),
        .counter_empty_manual_pop_o(counter_empty_manual_pop),
        .pc_top_data_o(pc_top_data),
        .count_top_data_o(count_top_data),
        .loop_top_data_o(loop_top_data),
        .stack_top_valid_o(stack_top_valid),
        .pc_depth_o(pc_depth),
        .count_depth_o(count_depth),
        .loop_depth_o(loop_depth),
        .stack_empty_o(stack_empty),
        .stack_overflow_o(stack_overflow),
        .stack_pop_valid_o(stack_pop_valid),
        .stack_push_accepted_o(stack_push_accepted),
        .stack_overflow_event_o(stack_overflow_event),
        .stack_empty_pop_o(stack_empty_pop),
        .sstat_fragment_o(sstat_fragment),
        .pc_stack_push_o(pc_stack_push),
        .pc_stack_pop_o(pc_stack_pop),
        .count_stack_push_o(count_stack_push),
        .count_stack_pop_o(count_stack_pop),
        .loop_stack_push_o(loop_stack_push),
        .loop_stack_pop_o(loop_stack_pop),
        .internal_storage_conflict_o(internal_storage_conflict)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected = '0;
        vector_file = $fopen(
            "build/sequencer_slice_vectors.txt",
            "r"
        );
        if (vector_file == 0) begin
            $fatal(
                1,
                "cannot open build/sequencer_slice_vectors.txt"
            );
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
                if (stack_empty !== ~stack_top_valid) begin
                    $fatal(
                        1,
                        "stack empty/valid mismatch vector=%0d",
                        vector_count
                    );
                end
                if (compare_state) begin
                    if (
                        {
                            cntr_valid,
                            stack_top_valid,
                            pc_depth,
                            count_depth,
                            loop_depth,
                            stack_overflow,
                            sstat_fragment
                        }
                        !==
                        {
                            expected_cntr_valid,
                            expected_loop_top_valid,
                            expected_count_top_valid,
                            expected_pc_top_valid,
                            expected_pc_depth,
                            expected_count_depth,
                            expected_loop_depth,
                            expected_stack_overflow,
                            expected_sstat_fragment
                        }
                    ) begin
                        $fatal(
                            1,
                            "sequencer state metadata mismatch vector=%0d",
                            vector_count
                        );
                    end
                    if (
                        expected_cntr_valid
                        && (cntr_data !== expected_cntr_data)
                    ) begin
                        $fatal(
                            1,
                            "CNTR data mismatch vector=%0d",
                            vector_count
                        );
                    end
                    if (
                        expected_pc_top_valid
                        && (pc_top_data !== expected_pc_top_data)
                    ) begin
                        $fatal(
                            1,
                            "PC top mismatch vector=%0d",
                            vector_count
                        );
                    end
                    if (
                        expected_count_top_valid
                        && (
                            count_top_data
                            !== expected_count_top_data
                        )
                    ) begin
                        $fatal(
                            1,
                            "count top mismatch vector=%0d",
                            vector_count
                        );
                    end
                    if (
                        expected_loop_top_valid
                        && (
                            loop_top_data
                            !== expected_loop_top_data
                        )
                    ) begin
                        $fatal(
                            1,
                            "loop top mismatch vector=%0d",
                            vector_count
                        );
                    end
                end
                if (
                    {
                        next_pc,
                        boundary_valid,
                        integration_conflict,
                        unsupported_call_ce,
                        invalid_counter_condition,
                        invalid_loop_context,
                        invalid_return_context,
                        unsupported_do_at_loop_end,
                        explicit_condition_true,
                        loop_termination_true,
                        explicit_transfer,
                        loop_back,
                        loop_exit,
                        counter_condition_valid,
                        counter_expired,
                        not_counter_expired,
                        counter_test,
                        counter_decrement,
                        counter_restore,
                        counter_empty_invalidate,
                        counter_invalid_test,
                        counter_empty_manual_pop,
                        pc_stack_push,
                        pc_stack_pop,
                        count_stack_push,
                        count_stack_pop,
                        loop_stack_push,
                        loop_stack_pop,
                        stack_pop_valid,
                        stack_push_accepted,
                        stack_overflow_event,
                        stack_empty_pop,
                        internal_storage_conflict
                    }
                    !==
                    {
                        expected_next_pc,
                        expected_boundary_valid,
                        expected_integration_conflict,
                        expected_unsupported_call_ce,
                        expected_invalid_counter_condition,
                        expected_invalid_loop_context,
                        expected_invalid_return_context,
                        expected_unsupported_do_at_loop_end,
                        expected_explicit_condition_true,
                        expected_loop_termination_true,
                        expected_explicit_transfer,
                        expected_loop_back,
                        expected_loop_exit,
                        expected_counter_condition_valid,
                        expected_counter_expired,
                        expected_not_counter_expired,
                        expected_counter_test,
                        expected_counter_decrement,
                        expected_counter_restore,
                        expected_counter_empty_invalidate,
                        expected_counter_invalid_test,
                        expected_counter_empty_manual_pop,
                        expected_pc_stack_push,
                        expected_pc_stack_pop,
                        expected_count_stack_push,
                        expected_count_stack_pop,
                        expected_loop_stack_push,
                        expected_loop_stack_pop,
                        expected_stack_pop_valid,
                        expected_stack_push_accepted,
                        expected_stack_overflow_event,
                        expected_stack_empty_pop,
                        expected_internal_storage_conflict
                    }
                ) begin
                    $fatal(
                        1,
                        "sequencer integration mismatch vector=%0d",
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
            "PASS %0d original ADSP-2100 sequencer-slice cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
