`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_conditional_return_slice;
    logic         clk;
    logic [106:0] stimulus;
    logic [27:0]  expected_events;
    logic [114:0] expected_state;
    logic         reset;
    logic         execute;
    logic [23:0]  opcode;
    logic         pc_setup;
    logic [13:0]  pc_setup_data;
    logic         astat_setup;
    logic [7:0]   astat_setup_data;
    logic         mstat_setup;
    logic [3:0]   mstat_setup_data;
    logic         imask_setup;
    logic [3:0]   imask_setup_data;
    logic         counter_setup;
    logic [13:0]  counter_setup_data;
    logic         pc_stack_setup;
    logic [13:0]  pc_stack_setup_data;
    logic         status_stack_setup;
    logic [15:0]  status_stack_setup_data;
    logic         class_valid;
    logic         action_valid;
    logic         interrupt_return;
    logic [3:0]   condition;
    logic         boundary_valid;
    logic         invalid_opcode;
    logic         integration_conflict;
    logic         internal_conflict;
    logic         invalid_condition_state;
    logic         invalid_return_context;
    logic         condition_known;
    logic         condition_true;
    logic [13:0]  pc;
    logic         pc_write;
    logic         explicit_transfer;
    logic         pc_stack_pop;
    logic         pc_stack_pop_valid;
    logic [13:0]  pc_stack_top;
    logic         pc_stack_top_valid;
    logic [4:0]   pc_stack_depth;
    logic         pc_stack_overflow;
    logic         status_stack_pop;
    logic         status_stack_pop_valid;
    logic [15:0]  status_stack_top;
    logic         status_stack_top_valid;
    logic [2:0]   status_stack_depth;
    logic         status_stack_overflow;
    logic         status_restored;
    logic [7:0]   astat;
    logic         astat_valid;
    logic [3:0]   mstat;
    logic [3:0]   imask;
    logic [13:0]  cntr;
    logic         cntr_valid;
    logic         counter_test;
    logic         counter_decrement;
    logic         counter_restore;
    logic         count_stack_push;
    logic [13:0]  count_stack_top;
    logic         count_stack_top_valid;
    logic [2:0]   count_stack_depth;
    logic         count_stack_overflow;
    logic [7:0]   sstat;
    logic         pm_data_access;
    logic         dm_access;
    logic [13:0]  expected_pc;
    logic         expected_astat_valid;
    logic [7:0]   expected_astat;
    logic [3:0]   expected_mstat;
    logic [3:0]   expected_imask;
    logic         expected_cntr_valid;
    logic [13:0]  expected_cntr;
    logic         expected_pc_top_valid;
    logic [13:0]  expected_pc_top;
    logic [4:0]   expected_pc_depth;
    logic         expected_pc_overflow;
    logic         expected_status_top_valid;
    logic [15:0]  expected_status_top;
    logic [2:0]   expected_status_depth;
    logic         expected_status_overflow;
    logic         expected_count_top_valid;
    logic [13:0]  expected_count_top;
    logic [2:0]   expected_count_depth;
    logic         expected_count_overflow;
    logic [7:0]   expected_sstat;
    integer       vector_file;
    integer       scan_count;
    integer       vector_count;

    assign {
        reset, execute, opcode,
        pc_setup, pc_setup_data,
        astat_setup, astat_setup_data,
        mstat_setup, mstat_setup_data,
        imask_setup, imask_setup_data,
        counter_setup, counter_setup_data,
        pc_stack_setup, pc_stack_setup_data,
        status_stack_setup, status_stack_setup_data
    } = stimulus;
    assign {
        expected_pc,
        expected_astat_valid, expected_astat,
        expected_mstat, expected_imask,
        expected_cntr_valid, expected_cntr,
        expected_pc_top_valid, expected_pc_top,
        expected_pc_depth, expected_pc_overflow,
        expected_status_top_valid, expected_status_top,
        expected_status_depth, expected_status_overflow,
        expected_count_top_valid, expected_count_top,
        expected_count_depth, expected_count_overflow,
        expected_sstat
    } = expected_state;

    adsp2100_conditional_return_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .pc_setup_write_i(pc_setup),
        .pc_setup_data_i(pc_setup_data),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .imask_setup_write_i(imask_setup),
        .imask_setup_data_i(imask_setup_data),
        .counter_setup_write_i(counter_setup),
        .counter_setup_data_i(counter_setup_data),
        .pc_stack_setup_push_i(pc_stack_setup),
        .pc_stack_setup_data_i(pc_stack_setup_data),
        .status_stack_setup_push_i(status_stack_setup),
        .status_stack_setup_data_i(status_stack_setup_data),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .interrupt_return_o(interrupt_return),
        .condition_o(condition),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .invalid_condition_state_o(invalid_condition_state),
        .invalid_return_context_o(invalid_return_context),
        .condition_known_o(condition_known),
        .condition_true_o(condition_true),
        .pc_o(pc),
        .pc_write_o(pc_write),
        .explicit_transfer_o(explicit_transfer),
        .pc_stack_pop_o(pc_stack_pop),
        .pc_stack_pop_valid_o(pc_stack_pop_valid),
        .pc_stack_top_o(pc_stack_top),
        .pc_stack_top_valid_o(pc_stack_top_valid),
        .pc_stack_depth_o(pc_stack_depth),
        .pc_stack_overflow_o(pc_stack_overflow),
        .status_stack_pop_o(status_stack_pop),
        .status_stack_pop_valid_o(status_stack_pop_valid),
        .status_stack_top_o(status_stack_top),
        .status_stack_top_valid_o(status_stack_top_valid),
        .status_stack_depth_o(status_stack_depth),
        .status_stack_overflow_o(status_stack_overflow),
        .status_restored_o(status_restored),
        .astat_o(astat),
        .astat_valid_o(astat_valid),
        .mstat_o(mstat),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .counter_test_o(counter_test),
        .counter_decrement_o(counter_decrement),
        .counter_restore_o(counter_restore),
        .count_stack_push_o(count_stack_push),
        .count_stack_top_o(count_stack_top),
        .count_stack_top_valid_o(count_stack_top_valid),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .sstat_o(sstat),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_state = '0;
        vector_file = $fopen("build/conditional_return_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 20 vectors");
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
                    class_valid, action_valid, interrupt_return, condition,
                    boundary_valid, invalid_opcode, integration_conflict,
                    internal_conflict, invalid_condition_state,
                    invalid_return_context, condition_known, condition_true,
                    pc_write, explicit_transfer,
                    pc_stack_pop, pc_stack_pop_valid,
                    status_stack_pop, status_stack_pop_valid, status_restored,
                    count_stack_push,
                    counter_test, counter_decrement, counter_restore,
                    pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d actual=%07x expected=%07x stimulus=%027x",
                        vector_count,
                        {
                            class_valid, action_valid,
                            interrupt_return, condition,
                            boundary_valid, invalid_opcode,
                            integration_conflict, internal_conflict,
                            invalid_condition_state,
                            invalid_return_context,
                            condition_known, condition_true,
                            pc_write, explicit_transfer,
                            pc_stack_pop, pc_stack_pop_valid,
                            status_stack_pop, status_stack_pop_valid,
                            status_restored, count_stack_push,
                            counter_test, counter_decrement,
                            counter_restore, pm_data_access, dm_access
                        },
                        expected_events,
                        stimulus
                    );
                end
                #4 clk = 1'b1;
                #2;
                if (pc !== expected_pc
                    || astat_valid !== expected_astat_valid
                    || mstat !== expected_mstat
                    || imask !== expected_imask
                    || cntr_valid !== expected_cntr_valid
                    || pc_stack_top_valid !== expected_pc_top_valid
                    || pc_stack_depth !== expected_pc_depth
                    || pc_stack_overflow !== expected_pc_overflow
                    || status_stack_top_valid !== expected_status_top_valid
                    || status_stack_depth !== expected_status_depth
                    || status_stack_overflow !== expected_status_overflow
                    || count_stack_top_valid !== expected_count_top_valid
                    || count_stack_depth !== expected_count_depth
                    || count_stack_overflow !== expected_count_overflow
                    || sstat !== expected_sstat) begin
                    $fatal(1, "state metadata mismatch vector=%0d", vector_count);
                end
                if (expected_astat_valid && astat !== expected_astat) begin
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
                end
                if (expected_cntr_valid && cntr !== expected_cntr) begin
                    $fatal(1, "CNTR mismatch vector=%0d", vector_count);
                end
                if (expected_pc_top_valid
                    && pc_stack_top !== expected_pc_top) begin
                    $fatal(1, "PC-stack top mismatch vector=%0d", vector_count);
                end
                if (expected_status_top_valid
                    && status_stack_top !== expected_status_top) begin
                    $fatal(1, "status-stack top mismatch vector=%0d", vector_count);
                end
                if (expected_count_top_valid
                    && count_stack_top !== expected_count_top) begin
                    $fatal(1, "count-stack top mismatch vector=%0d", vector_count);
                end
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count != 50_254) begin
            $fatal(1, "unexpected vector count=%0d", vector_count);
        end
        $display(
            "PASS Type 20 bounded model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
