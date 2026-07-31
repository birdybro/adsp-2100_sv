`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_do_until_slice;
    logic        clk;
    logic [55:0] stimulus;
    logic [36:0] expected_events;
    logic [99:0] expected_state;
    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        pc_setup;
    logic [13:0] pc_setup_data;
    logic        counter_setup;
    logic [13:0] counter_setup_data;
    logic        class_valid;
    logic        action_valid;
    logic [13:0] end_address;
    logic [3:0]  termination;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        invalid_loop_context;
    logic        unsupported_do_at_loop_end;
    logic        unsupported_nested_same_end;
    logic        internal_conflict;
    logic [13:0] pc;
    logic        pc_write;
    logic        pc_stack_push;
    logic        pc_stack_push_accepted;
    logic        pc_stack_overflow_event;
    logic [13:0] pc_stack_top;
    logic        pc_stack_top_valid;
    logic [4:0]  pc_stack_depth;
    logic        pc_stack_overflow;
    logic        loop_stack_push;
    logic        loop_stack_push_accepted;
    logic        loop_stack_overflow_event;
    logic [17:0] loop_stack_top;
    logic        loop_stack_top_valid;
    logic [2:0]  loop_stack_depth;
    logic        loop_stack_overflow;
    logic [13:0] cntr;
    logic        cntr_valid;
    logic        count_stack_push;
    logic [13:0] count_stack_top;
    logic        count_stack_top_valid;
    logic [2:0]  count_stack_depth;
    logic        count_stack_overflow;
    logic [7:0]  sstat_fragment;
    logic        pm_data_access;
    logic        dm_access;
    logic [13:0] expected_pc;
    logic        expected_cntr_valid;
    logic [13:0] expected_cntr;
    logic        expected_pc_top_valid;
    logic [13:0] expected_pc_top;
    logic [4:0]  expected_pc_depth;
    logic        expected_pc_overflow;
    logic        expected_loop_top_valid;
    logic [17:0] expected_loop_top;
    logic [2:0]  expected_loop_depth;
    logic        expected_loop_overflow;
    logic        expected_count_top_valid;
    logic [13:0] expected_count_top;
    logic [2:0]  expected_count_depth;
    logic        expected_count_overflow;
    logic [7:0]  expected_sstat;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset, execute, opcode,
        pc_setup, pc_setup_data,
        counter_setup, counter_setup_data
    } = stimulus;
    assign {
        expected_pc,
        expected_cntr_valid, expected_cntr,
        expected_pc_top_valid, expected_pc_top,
        expected_pc_depth, expected_pc_overflow,
        expected_loop_top_valid, expected_loop_top,
        expected_loop_depth, expected_loop_overflow,
        expected_count_top_valid, expected_count_top,
        expected_count_depth, expected_count_overflow,
        expected_sstat
    } = expected_state;

    adsp2100_do_until_slice dut (
        .clk_i(clk), .reset_i(reset), .execute_i(execute), .opcode_i(opcode),
        .pc_setup_write_i(pc_setup), .pc_setup_data_i(pc_setup_data),
        .counter_setup_write_i(counter_setup),
        .counter_setup_data_i(counter_setup_data),
        .class_valid_o(class_valid), .action_valid_o(action_valid),
        .end_address_o(end_address), .termination_o(termination),
        .boundary_valid_o(boundary_valid), .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .invalid_loop_context_o(invalid_loop_context),
        .unsupported_do_at_loop_end_o(unsupported_do_at_loop_end),
        .unsupported_nested_same_end_o(unsupported_nested_same_end),
        .internal_conflict_o(internal_conflict),
        .pc_o(pc), .pc_write_o(pc_write),
        .pc_stack_push_o(pc_stack_push),
        .pc_stack_push_accepted_o(pc_stack_push_accepted),
        .pc_stack_overflow_event_o(pc_stack_overflow_event),
        .pc_stack_top_o(pc_stack_top),
        .pc_stack_top_valid_o(pc_stack_top_valid),
        .pc_stack_depth_o(pc_stack_depth),
        .pc_stack_overflow_o(pc_stack_overflow),
        .loop_stack_push_o(loop_stack_push),
        .loop_stack_push_accepted_o(loop_stack_push_accepted),
        .loop_stack_overflow_event_o(loop_stack_overflow_event),
        .loop_stack_top_o(loop_stack_top),
        .loop_stack_top_valid_o(loop_stack_top_valid),
        .loop_stack_depth_o(loop_stack_depth),
        .loop_stack_overflow_o(loop_stack_overflow),
        .cntr_o(cntr), .cntr_valid_o(cntr_valid),
        .count_stack_push_o(count_stack_push),
        .count_stack_top_o(count_stack_top),
        .count_stack_top_valid_o(count_stack_top_valid),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .sstat_fragment_o(sstat_fragment),
        .pm_data_access_o(pm_data_access), .dm_access_o(dm_access)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_state = '0;
        vector_file = $fopen("build/do_until_vectors.txt", "r");
        if (vector_file == 0) $fatal(1, "cannot open Type 11 vectors");
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file, "%h %h %h\n",
                stimulus, expected_events, expected_state
            );
            if (scan_count == 3) begin
                #1;
                if ({
                    class_valid, action_valid, end_address, termination,
                    boundary_valid, invalid_opcode, integration_conflict,
                    invalid_loop_context, unsupported_do_at_loop_end,
                    unsupported_nested_same_end, internal_conflict,
                    pc_write, pc_stack_push, pc_stack_push_accepted,
                    pc_stack_overflow_event, loop_stack_push,
                    loop_stack_push_accepted, loop_stack_overflow_event,
                    count_stack_push, pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(1, "event mismatch vector=%0d", vector_count);
                end
                #4 clk = 1'b1;
                #2;
                if (pc !== expected_pc
                    || cntr_valid !== expected_cntr_valid
                    || pc_stack_top_valid !== expected_pc_top_valid
                    || pc_stack_depth !== expected_pc_depth
                    || pc_stack_overflow !== expected_pc_overflow
                    || loop_stack_top_valid !== expected_loop_top_valid
                    || loop_stack_depth !== expected_loop_depth
                    || loop_stack_overflow !== expected_loop_overflow
                    || count_stack_top_valid !== expected_count_top_valid
                    || count_stack_depth !== expected_count_depth
                    || count_stack_overflow !== expected_count_overflow
                    || sstat_fragment !== expected_sstat) begin
                    $fatal(1, "state metadata mismatch vector=%0d", vector_count);
                end
                if (expected_cntr_valid && cntr !== expected_cntr)
                    $fatal(1, "CNTR mismatch vector=%0d", vector_count);
                if (expected_pc_top_valid && pc_stack_top !== expected_pc_top)
                    $fatal(1, "PC top mismatch vector=%0d", vector_count);
                if (expected_loop_top_valid && loop_stack_top !== expected_loop_top)
                    $fatal(1, "loop top mismatch vector=%0d", vector_count);
                if (expected_count_top_valid && count_stack_top !== expected_count_top)
                    $fatal(1, "count top mismatch vector=%0d", vector_count);
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count != 554_309)
            $fatal(1, "unexpected vector count=%0d", vector_count);
        $display(
            "PASS Type 11 bounded model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
