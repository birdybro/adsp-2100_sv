`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_load_dreg_immediate_slice;
    logic        clk;
    logic [55:0] stimulus;
    logic [25:0] expected_events;
    logic [21:0] expected_state;
    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        mstat_setup;
    logic [3:0]  mstat_setup_data;
    logic        dreg_setup;
    logic [3:0]  dreg_setup_code;
    logic [15:0] dreg_setup_data;
    logic [3:0]  probe_code;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [3:0]  destination;
    logic [15:0] immediate;
    logic [15:0] probe_data;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        pm_data_access;
    logic        dm_access;
    logic        compare_probe;
    logic [15:0] expected_probe;
    logic [3:0]  expected_mstat;
    logic        expected_alternate_bank;
    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, execute, opcode, mstat_setup, mstat_setup_data,
        dreg_setup, dreg_setup_code, dreg_setup_data, probe_code
    } = stimulus;
    assign {
        compare_probe, expected_probe, expected_mstat,
        expected_alternate_bank
    } = expected_state;

    adsp2100_load_dreg_immediate_slice dut (
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
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .destination_dreg_o(destination),
        .immediate_data_o(immediate),
        .probe_data_o(probe_data),
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
        vector_file = $fopen("build/load_dreg_immediate_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 6 vectors");
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
                    boundary_valid, invalid_opcode,
                    integration_conflict, internal_conflict,
                    destination, immediate,
                    pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(1, "event mismatch vector=%0d", vector_count);
                end
                #4 clk = 1'b1;
                #1;
                if (
                    mstat !== expected_mstat
                    || alternate_bank !== expected_alternate_bank
                ) begin
                    $fatal(1, "mode mismatch vector=%0d", vector_count);
                end
                if (compare_probe && probe_data !== expected_probe) begin
                    $fatal(
                        1,
                        "probe mismatch vector=%0d actual=%04x expected=%04x",
                        vector_count,
                        probe_data,
                        expected_probe
                    );
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50_000) begin
            $fatal(1, "insufficient vectors=%0d", vector_count);
        end
        $display(
            "PASS Type 6 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
