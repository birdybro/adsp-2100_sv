`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_internal_move_slice;
    logic        clk;
    logic [54:0] stimulus;
    logic [36:0] expected_events;
    logic [15:0] expected_source_data;
    logic [15:0] expected_source_mask;
    logic [71:0] expected_post;
    logic [71:0] expected_post_mask;

    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        setup_write;
    logic [5:0]  setup_code;
    logic [15:0] setup_data;
    logic [5:0]  probe_code;
    logic [15:0] probe_data;
    logic        class_valid;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        invalid_subencoding;
    logic        invalid_setup;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [5:0]  source_code;
    logic [5:0]  destination_code;
    logic [15:0] source_data;
    logic        source_extension_provisional;
    logic        count_stack_push;
    logic [13:0] count_stack_push_data;
    logic [2:0]  count_stack_depth;
    logic        count_stack_overflow;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic [4:0]  icntl;
    logic [3:0]  imask;
    logic [13:0] cntr;
    logic        cntr_valid;
    logic [7:0]  px;
    logic [7:0]  sstat;
    logic        pm_data_access;
    logic        dm_access;
    logic [36:0] actual_events;
    logic [71:0] actual_post;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset,
        execute,
        opcode,
        setup_write,
        setup_code,
        setup_data,
        probe_code
    } = stimulus;
    assign actual_events = {
        class_valid,
        boundary_valid,
        invalid_opcode,
        invalid_subencoding,
        invalid_setup,
        integration_conflict,
        internal_conflict,
        source_code,
        destination_code,
        source_extension_provisional,
        count_stack_push,
        count_stack_push_data,
        pm_data_access,
        dm_access
    };
    assign actual_post = {
        probe_data,
        astat,
        mstat,
        icntl,
        imask,
        cntr,
        cntr_valid,
        px,
        sstat,
        count_stack_depth,
        count_stack_overflow
    };

    adsp2100_internal_move_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .setup_write_i(setup_write),
        .setup_data_valid_i(1'b1),
        .setup_code_i(setup_code),
        .setup_data_i(setup_data),
        .probe_code_i(probe_code),
        .probe_data_o(probe_data),
        .class_valid_o(class_valid),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .invalid_subencoding_o(invalid_subencoding),
        .invalid_setup_o(invalid_setup),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .source_code_o(source_code),
        .destination_code_o(destination_code),
        .source_data_o(source_data),
        .source_extension_provisional_o(source_extension_provisional),
        .count_stack_push_o(count_stack_push),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .px_o(px),
        .sstat_o(sstat),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_source_data = '0;
        expected_source_mask = '0;
        expected_post = '0;
        expected_post_mask = '0;
        vector_file = $fopen(
            "build/internal_move_slice_vectors.txt",
            "r"
        );
        if (vector_file == 0) begin
            $fatal(
                1,
                "cannot open build/internal_move_slice_vectors.txt"
            );
        end

        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h %h %h %h\n",
                stimulus,
                expected_events,
                expected_source_data,
                expected_source_mask,
                expected_post,
                expected_post_mask
            );
            if (scan_count == 6) begin
                #1;
                if (actual_events !== expected_events) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d actual=%010x expected=%010x",
                        vector_count,
                        actual_events,
                        expected_events
                    );
                end
                if (
                    (source_data & expected_source_mask)
                    !== (expected_source_data & expected_source_mask)
                ) begin
                    $fatal(
                        1,
                        "source mismatch vector=%0d actual=%04x expected=%04x mask=%04x",
                        vector_count,
                        source_data,
                        expected_source_data,
                        expected_source_mask
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
                        "state mismatch vector=%0d actual=%018x expected=%018x mask=%018x",
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
        if (vector_count < 59_000) begin
            $fatal(1, "insufficient vectors: %0d", vector_count);
        end
        $display(
            "PASS Type 17 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
