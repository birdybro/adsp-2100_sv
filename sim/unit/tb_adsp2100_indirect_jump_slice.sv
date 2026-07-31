`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_indirect_jump_slice;
    logic         clk;
    logic [83:0]  stimulus;
    logic [48:0]  expected_events;
    logic [100:0] expected_state;
    logic         reset;
    logic         execute;
    logic [23:0]  opcode;
    logic         pc_setup;
    logic [13:0]  pc_setup_data;
    logic         astat_setup;
    logic [7:0]   astat_setup_data;
    logic         counter_setup;
    logic [13:0]  counter_setup_data;
    logic         i_setup;
    logic [1:0]   i_setup_local;
    logic [13:0]  i_setup_data;
    logic [1:0]   i_probe_local;
    logic [13:0]  i_probe_data;
    logic         i_probe_valid;
    logic         class_valid;
    logic         action_valid;
    logic         unsupported_call_ce;
    logic         call_action;
    logic [1:0]   i_local;
    logic [2:0]   i_address;
    logic [3:0]   condition;
    logic         boundary_valid;
    logic         invalid_opcode;
    logic         integration_conflict;
    logic         invalid_condition_state;
    logic         invalid_target_state;
    logic         internal_conflict;
    logic         condition_known;
    logic         condition_true;
    logic [13:0]  indirect_address;
    logic         indirect_address_valid;
    logic         pma_indirect_drive;
    logic [13:0]  pc;
    logic         pc_write;
    logic         explicit_transfer;
    logic         pc_stack_push;
    logic         pc_stack_push_accepted;
    logic [13:0]  pc_stack_top;
    logic         pc_stack_top_valid;
    logic [4:0]   pc_stack_depth;
    logic         pc_stack_overflow;
    logic [13:0]  cntr;
    logic         cntr_valid;
    logic         counter_test;
    logic         counter_decrement;
    logic         counter_restore;
    logic         counter_empty_invalidate;
    logic         count_stack_push;
    logic         count_stack_pop;
    logic [13:0]  count_stack_top;
    logic         count_stack_top_valid;
    logic [2:0]   count_stack_depth;
    logic         count_stack_overflow;
    logic [7:0]   astat;
    logic         astat_valid;
    logic [7:0]   sstat_fragment;
    logic         pm_data_access;
    logic         dm_access;
    logic [13:0]  expected_pc;
    logic         expected_astat_valid;
    logic [7:0]   expected_astat;
    logic         expected_cntr_valid;
    logic [13:0]  expected_cntr;
    logic         expected_pc_top_valid;
    logic [13:0]  expected_pc_top;
    logic         expected_count_top_valid;
    logic [13:0]  expected_count_top;
    logic [4:0]   expected_pc_depth;
    logic [2:0]   expected_count_depth;
    logic         expected_pc_overflow;
    logic         expected_count_overflow;
    logic [7:0]   expected_sstat;
    logic         expected_i_probe_valid;
    logic [13:0]  expected_i_probe_data;
    integer       vector_file;
    integer       scan_count;
    integer       vector_count;

    assign {
        reset, execute, opcode,
        pc_setup, pc_setup_data,
        astat_setup, astat_setup_data,
        counter_setup, counter_setup_data,
        i_setup, i_setup_local, i_setup_data,
        i_probe_local
    } = stimulus;
    assign {
        expected_pc,
        expected_astat_valid, expected_astat,
        expected_cntr_valid, expected_cntr,
        expected_pc_top_valid, expected_pc_top,
        expected_count_top_valid, expected_count_top,
        expected_pc_depth, expected_count_depth,
        expected_pc_overflow, expected_count_overflow,
        expected_sstat,
        expected_i_probe_valid, expected_i_probe_data
    } = expected_state;

    adsp2100_indirect_jump_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .pc_setup_write_i(pc_setup),
        .pc_setup_data_i(pc_setup_data),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .counter_setup_write_i(counter_setup),
        .counter_setup_data_i(counter_setup_data),
        .i_setup_write_i(i_setup),
        .i_setup_local_i(i_setup_local),
        .i_setup_data_i(i_setup_data),
        .i_probe_local_i(i_probe_local),
        .i_probe_data_o(i_probe_data),
        .i_probe_valid_o(i_probe_valid),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_call_ce_o(unsupported_call_ce),
        .call_o(call_action),
        .i_local_o(i_local),
        .i_address_o(i_address),
        .condition_o(condition),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .invalid_condition_state_o(invalid_condition_state),
        .invalid_target_state_o(invalid_target_state),
        .internal_conflict_o(internal_conflict),
        .condition_known_o(condition_known),
        .condition_true_o(condition_true),
        .indirect_address_o(indirect_address),
        .indirect_address_valid_o(indirect_address_valid),
        .pma_indirect_drive_o(pma_indirect_drive),
        .pc_o(pc),
        .pc_write_o(pc_write),
        .explicit_transfer_o(explicit_transfer),
        .pc_stack_push_o(pc_stack_push),
        .pc_stack_push_accepted_o(pc_stack_push_accepted),
        .pc_stack_top_o(pc_stack_top),
        .pc_stack_top_valid_o(pc_stack_top_valid),
        .pc_stack_depth_o(pc_stack_depth),
        .pc_stack_overflow_o(pc_stack_overflow),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .counter_test_o(counter_test),
        .counter_decrement_o(counter_decrement),
        .counter_restore_o(counter_restore),
        .counter_empty_invalidate_o(counter_empty_invalidate),
        .count_stack_push_o(count_stack_push),
        .count_stack_pop_o(count_stack_pop),
        .count_stack_top_o(count_stack_top),
        .count_stack_top_valid_o(count_stack_top_valid),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .astat_o(astat),
        .astat_valid_o(astat_valid),
        .sstat_fragment_o(sstat_fragment),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_state = '0;
        vector_file = $fopen("build/indirect_jump_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 19 vectors");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_events,
                expected_state
            );
            if (scan_count == 3) begin
                #1;
                if ({
                    class_valid, action_valid, unsupported_call_ce,
                    call_action, i_local, i_address, condition,
                    boundary_valid, invalid_opcode, integration_conflict,
                    invalid_condition_state, invalid_target_state,
                    internal_conflict, condition_known, condition_true,
                    indirect_address, indirect_address_valid,
                    pma_indirect_drive, pc_write, explicit_transfer,
                    pc_stack_push, pc_stack_push_accepted,
                    counter_test, counter_decrement, counter_restore,
                    counter_empty_invalidate, count_stack_push,
                    count_stack_pop, pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(1, "event mismatch vector=%0d", vector_count);
                end
                #4 clk = 1'b1;
                #2;
                if (pc !== expected_pc
                    || astat_valid !== expected_astat_valid
                    || cntr_valid !== expected_cntr_valid
                    || pc_stack_top_valid !== expected_pc_top_valid
                    || count_stack_top_valid !== expected_count_top_valid
                    || pc_stack_depth !== expected_pc_depth
                    || count_stack_depth !== expected_count_depth
                    || pc_stack_overflow !== expected_pc_overflow
                    || count_stack_overflow !== expected_count_overflow
                    || sstat_fragment !== expected_sstat
                    || i_probe_valid !== expected_i_probe_valid) begin
                    $fatal(1, "state metadata mismatch vector=%0d", vector_count);
                end
                if (expected_astat_valid && astat !== expected_astat) begin
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
                end
                if (expected_cntr_valid && cntr !== expected_cntr) begin
                    $fatal(1, "CNTR mismatch vector=%0d", vector_count);
                end
                if (expected_pc_top_valid && pc_stack_top !== expected_pc_top) begin
                    $fatal(1, "PC-stack top mismatch vector=%0d", vector_count);
                end
                if (expected_count_top_valid
                    && count_stack_top !== expected_count_top) begin
                    $fatal(1, "count-stack top mismatch vector=%0d", vector_count);
                end
                if (expected_i_probe_valid
                    && i_probe_data !== expected_i_probe_data) begin
                    $fatal(1, "DAG2 I probe mismatch vector=%0d", vector_count);
                end
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count != 50_259) begin
            $fatal(1, "unexpected vector count=%0d", vector_count);
        end
        $display(
            "PASS Type 19 bounded model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
