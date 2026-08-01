`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_direct_dm_slice;
    logic clk;
    logic [72:0] stimulus;
    logic [88:0] expected_events;
    logic [72:0] expected_post;
    logic [72:0] expected_post_mask;

    logic reset;
    logic execute;
    logic [23:0] opcode;
    logic ack;
    logic [15:0] read_data;
    logic read_data_valid;
    logic setup_write;
    logic [5:0] setup_code;
    logic [15:0] setup_data;
    logic [5:0] probe_code;

    logic class_valid;
    logic action_valid;
    logic invalid_subencoding;
    logic write_direction;
    logic [13:0] direct_address;
    logic [5:0] register_code;
    logic boundary_valid;
    logic accepted;
    logic instruction_complete;
    logic transaction_active;
    logic stalled;
    logic busy;
    logic invalid_opcode;
    logic invalid_setup;
    logic integration_conflict;
    logic internal_conflict;
    logic dm_select;
    logic dm_read;
    logic dm_write;
    logic [13:0] dm_address;
    logic dm_address_valid;
    logic [15:0] dm_write_data;
    logic dm_write_data_valid;
    logic register_write;
    logic register_write_known;
    logic source_extension_provisional;
    logic pm_data_access;
    logic dm_access;
    logic [15:0] probe_data;
    logic probe_data_valid;
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
    logic [88:0] actual_events;
    logic [72:0] actual_post;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, execute, opcode, ack, read_data, read_data_valid,
        setup_write, setup_code, setup_data, probe_code
    } = stimulus;
    assign actual_events = {
        class_valid, action_valid, invalid_subencoding,
        write_direction, direct_address, register_code,
        boundary_valid, accepted, instruction_complete,
        transaction_active, stalled, busy, invalid_opcode, invalid_setup,
        integration_conflict, internal_conflict,
        dm_select, dm_read, dm_write, dm_address_valid, dm_address,
        dm_write_data_valid, dm_write_data,
        register_write, register_write_known,
        source_extension_provisional, pm_data_access, dm_access,
        count_stack_push, count_stack_push_data
    };
    assign actual_post = {
        probe_data, probe_data_valid, astat, mstat, icntl, imask,
        cntr, cntr_valid, px, sstat, count_stack_depth,
        count_stack_overflow
    };

    adsp2100_direct_dm_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .dm_ack_i(ack),
        .dm_read_data_i(read_data),
        .dm_read_data_valid_i(read_data_valid),
        .setup_write_i(setup_write),
        .setup_code_i(setup_code),
        .setup_data_i(setup_data),
        .probe_code_i(probe_code),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .invalid_subencoding_o(invalid_subencoding),
        .write_direction_o(write_direction),
        .direct_address_o(direct_address),
        .register_code_o(register_code),
        .boundary_valid_o(boundary_valid),
        .accepted_o(accepted),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .stalled_o(stalled),
        .busy_o(busy),
        .invalid_opcode_o(invalid_opcode),
        .invalid_setup_o(invalid_setup),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .dm_select_o(dm_select),
        .dm_read_o(dm_read),
        .dm_write_o(dm_write),
        .dm_address_o(dm_address),
        .dm_address_valid_o(dm_address_valid),
        .dm_write_data_o(dm_write_data),
        .dm_write_data_valid_o(dm_write_data_valid),
        .register_write_o(register_write),
        .register_write_known_o(register_write_known),
        .source_extension_provisional_o(source_extension_provisional),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access),
        .probe_data_o(probe_data),
        .probe_data_valid_o(probe_data_valid),
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
        .count_stack_overflow_o(count_stack_overflow)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_post = '0;
        expected_post_mask = '0;
        vector_file = $fopen("build/direct_dm_slice_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/direct_dm_slice_vectors.txt");
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
                        "event mismatch vector=%0d actual=%023x expected=%023x",
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
                        "post mismatch vector=%0d actual=%019x expected=%019x mask=%019x",
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
        if (vector_count < 50_000) begin
            $fatal(1, "insufficient vectors: %0d", vector_count);
        end
        $display(
            "PASS Type 3 state/transaction model-RTL differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
