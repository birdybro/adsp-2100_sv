`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_stack_control_slice;
    logic         clk;
    logic [93:0]  stimulus;
    logic [27:0]  expected_events;
    logic [131:0] expected_state;

    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        astat_write;
    logic [7:0]  astat_write_data;
    logic        mstat_write;
    logic [3:0]  mstat_write_data;
    logic        imask_write;
    logic [3:0]  imask_write_data;
    logic        counter_load;
    logic [13:0] counter_load_data;
    logic        pc_push;
    logic [13:0] pc_push_data;
    logic        loop_push;
    logic [17:0] loop_push_data;

    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [1:0]  status_operation;
    logic        count_pop;
    logic        loop_pop;
    logic        pc_pop;
    logic        has_effect;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic [3:0]  imask;
    logic        alternate_bank;
    logic        bit_reverse;
    logic        overflow_latch;
    logic        saturate_ar;
    logic [13:0] cntr_data;
    logic        cntr_valid;
    logic        counter_restore;
    logic        counter_empty_manual_pop;
    logic [13:0] pc_top_data;
    logic [13:0] count_top_data;
    logic [17:0] loop_top_data;
    logic [15:0] status_top_data;
    logic [3:0]  stack_top_valid;
    logic [4:0]  pc_depth;
    logic [2:0]  count_depth;
    logic [2:0]  loop_depth;
    logic [2:0]  status_depth;
    logic [3:0]  stack_empty;
    logic [3:0]  stack_overflow;
    logic [3:0]  stack_pop_valid;
    logic [3:0]  stack_push_accepted;
    logic [3:0]  stack_overflow_event;
    logic [3:0]  stack_empty_pop;
    logic [7:0]  sstat;

    logic        compare_astat;
    logic [7:0]  expected_astat;
    logic [11:0] expected_status_state;
    logic        expected_cntr_valid;
    logic [13:0] expected_cntr_data;
    logic [95:0] expected_stack_state;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset,
        execute,
        opcode,
        astat_write,
        astat_write_data,
        mstat_write,
        mstat_write_data,
        imask_write,
        imask_write_data,
        counter_load,
        counter_load_data,
        pc_push,
        pc_push_data,
        loop_push,
        loop_push_data
    } = stimulus;

    assign {
        compare_astat,
        expected_astat,
        expected_status_state,
        expected_cntr_valid,
        expected_cntr_data,
        expected_stack_state
    } = expected_state;

    adsp2100_stack_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .astat_write_i(astat_write),
        .astat_write_data_i(astat_write_data),
        .mstat_write_i(mstat_write),
        .mstat_write_data_i(mstat_write_data),
        .imask_write_i(imask_write),
        .imask_write_data_i(imask_write_data),
        .counter_load_i(counter_load),
        .counter_load_data_i(counter_load_data),
        .pc_push_i(pc_push),
        .pc_push_data_i(pc_push_data),
        .loop_push_i(loop_push),
        .loop_push_data_i(loop_push_data),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .status_operation_o(status_operation),
        .count_pop_o(count_pop),
        .loop_pop_o(loop_pop),
        .pc_pop_o(pc_pop),
        .has_effect_o(has_effect),
        .astat_o(astat),
        .mstat_o(mstat),
        .imask_o(imask),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .cntr_data_o(cntr_data),
        .cntr_valid_o(cntr_valid),
        .counter_restore_o(counter_restore),
        .counter_empty_manual_pop_o(counter_empty_manual_pop),
        .pc_top_data_o(pc_top_data),
        .count_top_data_o(count_top_data),
        .loop_top_data_o(loop_top_data),
        .status_top_data_o(status_top_data),
        .stack_top_valid_o(stack_top_valid),
        .pc_depth_o(pc_depth),
        .count_depth_o(count_depth),
        .loop_depth_o(loop_depth),
        .status_depth_o(status_depth),
        .stack_empty_o(stack_empty),
        .stack_overflow_o(stack_overflow),
        .stack_pop_valid_o(stack_pop_valid),
        .stack_push_accepted_o(stack_push_accepted),
        .stack_overflow_event_o(stack_overflow_event),
        .stack_empty_pop_o(stack_empty_pop),
        .sstat_o(sstat)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_state = '0;
        vector_file = $fopen(
            "build/stack_control_slice_vectors.txt",
            "r"
        );
        if (vector_file == 0) begin
            $fatal(
                1,
                "cannot open build/stack_control_slice_vectors.txt"
            );
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
                if (
                    {
                        boundary_valid,
                        invalid_opcode,
                        integration_conflict,
                        internal_conflict,
                        status_operation,
                        count_pop,
                        loop_pop,
                        pc_pop,
                        has_effect,
                        counter_restore,
                        counter_empty_manual_pop,
                        stack_pop_valid,
                        stack_push_accepted,
                        stack_overflow_event,
                        stack_empty_pop
                    } !== expected_events
                ) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d actual=%07x expected=%07x",
                        vector_count,
                        {
                            boundary_valid,
                            invalid_opcode,
                            integration_conflict,
                            internal_conflict,
                            status_operation,
                            count_pop,
                            loop_pop,
                            pc_pop,
                            has_effect,
                            counter_restore,
                            counter_empty_manual_pop,
                            stack_pop_valid,
                            stack_push_accepted,
                            stack_overflow_event,
                            stack_empty_pop
                        },
                        expected_events
                    );
                end

                #4 clk = 1'b1;
                #1;
                if (
                    {
                        mstat,
                        imask,
                        {
                            saturate_ar,
                            overflow_latch,
                            bit_reverse,
                            alternate_bank
                        }
                    } !== expected_status_state
                    || cntr_valid !== expected_cntr_valid
                    || {
                        stack_top_valid[0],
                        pc_top_data,
                        stack_top_valid[1],
                        count_top_data,
                        stack_top_valid[2],
                        loop_top_data,
                        stack_top_valid[3],
                        status_top_data,
                        pc_depth,
                        count_depth,
                        loop_depth,
                        status_depth,
                        stack_overflow,
                        stack_empty,
                        sstat
                    } !== expected_stack_state
                ) begin
                    $fatal(
                        1,
                        "state mismatch vector=%0d status=%03x/%03x cntr_valid=%b/%b stacks=%024x/%024x",
                        vector_count,
                        {
                            mstat,
                            imask,
                            {
                                saturate_ar,
                                overflow_latch,
                                bit_reverse,
                                alternate_bank
                            }
                        },
                        expected_status_state,
                        cntr_valid,
                        expected_cntr_valid,
                        {
                            stack_top_valid[0],
                            pc_top_data,
                            stack_top_valid[1],
                            count_top_data,
                            stack_top_valid[2],
                            loop_top_data,
                            stack_top_valid[3],
                            status_top_data,
                            pc_depth,
                            count_depth,
                            loop_depth,
                            status_depth,
                            stack_overflow,
                            stack_empty,
                            sstat
                        },
                        expected_stack_state
                    );
                end
                if (
                    expected_cntr_valid
                    && (cntr_data !== expected_cntr_data)
                ) begin
                    $fatal(
                        1,
                        "CNTR mismatch vector=%0d actual=%04x expected=%04x",
                        vector_count,
                        cntr_data,
                        expected_cntr_data
                    );
                end
                if (compare_astat && (astat !== expected_astat)) begin
                    $fatal(
                        1,
                        "ASTAT mismatch vector=%0d actual=%02x expected=%02x",
                        vector_count,
                        astat,
                        expected_astat
                    );
                end
                if (stack_empty !== ~stack_top_valid) begin
                    $fatal(
                        1,
                        "stack empty/valid mismatch vector=%0d",
                        vector_count
                    );
                end
                if (
                    sstat !== {
                        stack_overflow[2],
                        stack_empty[2],
                        stack_overflow[3],
                        stack_empty[3],
                        stack_overflow[1],
                        stack_empty[1],
                        stack_overflow[0],
                        stack_empty[0]
                    }
                ) begin
                    $fatal(
                        1,
                        "SSTAT composition mismatch vector=%0d",
                        vector_count
                    );
                end
                #4 clk = 1'b0;
                #1;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count != 50015) begin
            $fatal(1, "unexpected vector count: %0d", vector_count);
        end
        $display(
            "PASS %0d stateful original Type 26 stack-control cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
