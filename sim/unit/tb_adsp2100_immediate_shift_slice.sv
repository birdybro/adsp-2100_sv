`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_immediate_shift_slice;
    logic        clk;
    logic [55:0] stimulus;
    logic [28:0] expected_events;
    logic [71:0] expected_state;
    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        mstat_setup;
    logic [3:0]  mstat_setup_data;
    logic        dreg_setup;
    logic [3:0]  dreg_setup_code;
    logic [15:0] dreg_setup_data;
    logic [3:0]  probe_code;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [3:0]  sf;
    logic [2:0]  xop;
    logic [7:0]  exponent;
    logic [3:0]  source_dreg;
    logic [15:0] source_data;
    logic [31:0] sr_result;
    logic        sr_write;
    logic [15:0] probe_data;
    logic [31:0] sr;
    logic [7:0]  se;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        pm_data_access;
    logic        dm_access;
    logic        compare_probe;
    logic [15:0] expected_probe;
    logic        compare_sr;
    logic [31:0] expected_sr;
    logic        compare_se;
    logic [15:0] expected_se;
    logic [3:0]  expected_mstat;
    logic        expected_alternate_bank;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset, execute, opcode, mstat_setup, mstat_setup_data,
        dreg_setup, dreg_setup_code, dreg_setup_data, probe_code
    } = stimulus;
    assign {
        compare_probe, expected_probe, compare_sr, expected_sr,
        compare_se, expected_se, expected_mstat,
        expected_alternate_bank
    } = expected_state;

    adsp2100_immediate_shift_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .probe_code_i(probe_code),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .sf_o(sf),
        .xop_o(xop),
        .exponent_o(exponent),
        .source_dreg_o(source_dreg),
        .source_data_o(source_data),
        .sr_result_o(sr_result),
        .sr_write_o(sr_write),
        .probe_data_o(probe_data),
        .sr_o(sr),
        .se_o(se),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_state = '0;
        vector_file = $fopen("build/immediate_shift_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 15 vectors");
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
                    class_valid, action_valid, unsupported_subencoding,
                    boundary_valid, invalid_opcode, integration_conflict,
                    internal_conflict, sf, xop, exponent, source_dreg,
                    sr_write, pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(1, "event mismatch vector=%0d", vector_count);
                end
                if (boundary_valid
                    && ((^source_data) === 1'bx || (^sr_result) === 1'bx)) begin
                    $fatal(1, "unknown shifter data vector=%0d", vector_count);
                end
                #4 clk = 1'b1;
                #1;
                if (mstat !== expected_mstat
                    || alternate_bank !== expected_alternate_bank) begin
                    $fatal(1, "mode mismatch vector=%0d", vector_count);
                end
                if (compare_probe && probe_data !== expected_probe) begin
                    $fatal(1, "probe mismatch vector=%0d", vector_count);
                end
                if (compare_sr && sr !== expected_sr) begin
                    $fatal(1, "SR mismatch vector=%0d", vector_count);
                end
                if (compare_se && {{8{se[7]}}, se} !== expected_se) begin
                    $fatal(1, "SE mismatch vector=%0d", vector_count);
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 58_000) begin
            $fatal(1, "insufficient vectors=%0d", vector_count);
        end
        $display(
            "PASS Type 15 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
