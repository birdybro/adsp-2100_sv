`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_mr_saturation_slice;
    logic        clk;
    logic [80:0] stimulus;
    logic [8:0]  expected_events;
    logic [53:0] expected_state;

    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        astat_write;
    logic [7:0]  astat_write_data;
    logic        mstat_write;
    logic [3:0]  mstat_write_data;
    logic        mr_setup_write;
    logic [39:0] mr_setup_write_data;

    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic        condition_mv;
    logic        selected_bank_alternate;
    logic        mr_write;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic [39:0] mr;

    logic        compare_condition;
    logic        compare_selected;
    logic        expected_boundary_valid;
    logic        expected_invalid_opcode;
    logic        expected_integration_conflict;
    logic        expected_internal_conflict;
    logic        expected_condition;
    logic        expected_selected;
    logic        expected_mr_write;
    logic        compare_astat;
    logic [7:0]  expected_astat;
    logic [3:0]  expected_mstat;
    logic        compare_mr;
    logic [39:0] expected_mr;

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
        mr_setup_write,
        mr_setup_write_data
    } = stimulus;

    assign {
        compare_condition,
        compare_selected,
        expected_boundary_valid,
        expected_invalid_opcode,
        expected_integration_conflict,
        expected_internal_conflict,
        expected_condition,
        expected_selected,
        expected_mr_write
    } = expected_events;

    assign {
        compare_astat,
        expected_astat,
        expected_mstat,
        compare_mr,
        expected_mr
    } = expected_state;

    adsp2100_mr_saturation_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .astat_write_i(astat_write),
        .astat_write_data_i(astat_write_data),
        .mstat_write_i(mstat_write),
        .mstat_write_data_i(mstat_write_data),
        .mr_setup_write_i(mr_setup_write),
        .mr_setup_write_data_i(mr_setup_write_data),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .condition_mv_o(condition_mv),
        .selected_bank_alternate_o(selected_bank_alternate),
        .mr_write_o(mr_write),
        .astat_o(astat),
        .mstat_o(mstat),
        .mr_o(mr)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_state = '0;
        vector_file = $fopen(
            "build/mr_saturation_slice_vectors.txt",
            "r"
        );
        if (vector_file == 0) begin
            $fatal(
                1,
                "cannot open build/mr_saturation_slice_vectors.txt"
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
                    boundary_valid !== expected_boundary_valid
                    || invalid_opcode !== expected_invalid_opcode
                    || integration_conflict
                        !== expected_integration_conflict
                    || internal_conflict !== expected_internal_conflict
                    || mr_write !== expected_mr_write
                ) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d actual=%03x expected=%03x",
                        vector_count,
                        {
                            compare_condition,
                            compare_selected,
                            boundary_valid,
                            invalid_opcode,
                            integration_conflict,
                            internal_conflict,
                            condition_mv,
                            selected_bank_alternate,
                            mr_write
                        },
                        expected_events
                    );
                end
                if (
                    compare_condition
                    && condition_mv !== expected_condition
                ) begin
                    $fatal(
                        1,
                        "MV mismatch vector=%0d actual=%b expected=%b",
                        vector_count,
                        condition_mv,
                        expected_condition
                    );
                end
                if (
                    compare_selected
                    && selected_bank_alternate !== expected_selected
                ) begin
                    $fatal(
                        1,
                        "bank mismatch vector=%0d actual=%b expected=%b",
                        vector_count,
                        selected_bank_alternate,
                        expected_selected
                    );
                end

                #4 clk = 1'b1;
                #1;
                if (mstat !== expected_mstat) begin
                    $fatal(
                        1,
                        "MSTAT mismatch vector=%0d actual=%x expected=%x",
                        vector_count,
                        mstat,
                        expected_mstat
                    );
                end
                if (compare_astat && astat !== expected_astat) begin
                    $fatal(
                        1,
                        "ASTAT mismatch vector=%0d actual=%02x expected=%02x",
                        vector_count,
                        astat,
                        expected_astat
                    );
                end
                if (compare_mr && mr !== expected_mr) begin
                    $fatal(
                        1,
                        "MR mismatch vector=%0d actual=%010x expected=%010x",
                        vector_count,
                        mr,
                        expected_mr
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
            "PASS Type 25 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
