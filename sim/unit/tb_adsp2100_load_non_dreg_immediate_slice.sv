`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_load_non_dreg_immediate_slice;
    logic clk;
    logic [54:0] stimulus;
    logic [53:0] expected_events;
    logic [71:0] expected_post;
    logic [71:0] expected_post_mask;
    logic reset;
    logic execute;
    logic [23:0] opcode;
    logic setup_write;
    logic [5:0] setup_code;
    logic [15:0] setup_data;
    logic [5:0] probe_code;
    logic class_valid;
    logic action_valid;
    logic invalid_subencoding;
    logic boundary_valid;
    logic invalid_opcode;
    logic invalid_setup;
    logic integration_conflict;
    logic internal_conflict;
    logic [1:0] register_group;
    logic [3:0] register_index;
    logic [5:0] register_code;
    logic [13:0] immediate_data;
    logic data_register_destination;
    logic reserved_destination;
    logic read_only_destination;
    logic [15:0] probe_data;
    logic [7:0] astat;
    logic [3:0] mstat;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic [13:0] cntr;
    logic cntr_valid;
    logic [7:0] px;
    logic [7:0] sstat;
    logic count_stack_push;
    logic [13:0] count_stack_push_data;
    logic [2:0] count_stack_depth;
    logic count_stack_overflow;
    logic pm_data_access;
    logic dm_access;
    logic [53:0] actual_events;
    logic [71:0] actual_post;
    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, execute, opcode, setup_write, setup_code, setup_data, probe_code
    } = stimulus;
    assign actual_events = {
        class_valid, action_valid, invalid_subencoding, boundary_valid,
        invalid_opcode, invalid_setup, integration_conflict, internal_conflict,
        register_group, register_index, register_code, immediate_data,
        data_register_destination, reserved_destination,
        read_only_destination, count_stack_push,
        count_stack_push_data, pm_data_access, dm_access
    };
    assign actual_post = {
        probe_data, astat, mstat, icntl, imask, cntr, cntr_valid,
        px, sstat, count_stack_depth, count_stack_overflow
    };

    adsp2100_load_non_dreg_immediate_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .setup_write_i(setup_write),
        .setup_code_i(setup_code),
        .setup_data_i(setup_data),
        .probe_code_i(probe_code),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .invalid_subencoding_o(invalid_subencoding),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .invalid_setup_o(invalid_setup),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .register_group_o(register_group),
        .register_index_o(register_index),
        .register_code_o(register_code),
        .immediate_data_o(immediate_data),
        .data_register_destination_o(data_register_destination),
        .reserved_destination_o(reserved_destination),
        .read_only_destination_o(read_only_destination),
        .probe_data_o(probe_data),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .px_o(px),
        .sstat_o(sstat),
        .count_stack_push_o(count_stack_push),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_post = '0;
        expected_post_mask = '0;
        vector_file = $fopen(
            "build/load_non_dreg_immediate_vectors.txt", "r"
        );
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 7 vector file");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h %h\n",
                stimulus,
                expected_events,
                expected_post,
                expected_post_mask
            );
            if (scan_count == 4) begin
                #1;
                if (actual_events !== expected_events) begin
                    $fatal(
                        1,
                        "Type 7 event mismatch vector=%0d actual=%014x expected=%014x",
                        vector_count,
                        actual_events,
                        expected_events
                    );
                end
                #4 clk = 1'b1;
                #1;
                if (
                    (actual_post & expected_post_mask)
                    !== (expected_post & expected_post_mask)
                ) begin
                    $fatal(
                        1,
                        "Type 7 post mismatch vector=%0d actual=%018x expected=%018x mask=%018x",
                        vector_count,
                        actual_post,
                        expected_post,
                        expected_post_mask
                    );
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50000) begin
            $fatal(1, "insufficient Type 7 vectors: %0d", vector_count);
        end
        $display(
            "PASS Type 7 state model-RTL differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
