`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_shift_move_slice;
    logic        clk;
    logic [70:0] stimulus;
    logic [35:0] expected_events;
    logic [86:0] expected_state;
    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        astat_setup;
    logic [7:0]  astat_setup_data;
    logic        mstat_setup;
    logic [3:0]  mstat_setup_data;
    logic        dreg_setup;
    logic [3:0]  dreg_setup_code;
    logic [15:0] dreg_setup_data;
    logic        sb_setup;
    logic [4:0]  sb_setup_data;
    logic [3:0]  probe_code;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        unverified_unused_x;
    logic        unavailable_xop;
    logic        destination_collision;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [3:0]  sf;
    logic [2:0]  xop;
    logic [3:0]  shifter_source_dreg;
    logic [3:0]  move_destination_dreg;
    logic [3:0]  move_source_dreg;
    logic [15:0] shifter_source_data;
    logic [15:0] move_source_data;
    logic [31:0] sr_result;
    logic [7:0]  se_result;
    logic [4:0]  sb_result;
    logic        ss_result;
    logic        move_write;
    logic        sr_write;
    logic        se_write;
    logic        sb_write;
    logic        ss_write;
    logic [15:0] probe_data;
    logic [31:0] sr;
    logic [7:0]  se;
    logic [4:0]  sb;
    logic [7:0]  astat;
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
    logic        compare_sb;
    logic [4:0]  expected_sb;
    logic        compare_astat;
    logic [7:0]  expected_astat;
    logic [3:0]  expected_mstat;
    logic        expected_alternate_bank;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset, execute, opcode,
        astat_setup, astat_setup_data,
        mstat_setup, mstat_setup_data,
        dreg_setup, dreg_setup_code, dreg_setup_data,
        sb_setup, sb_setup_data, probe_code
    } = stimulus;
    assign {
        compare_probe, expected_probe, compare_sr, expected_sr,
        compare_se, expected_se, compare_sb, expected_sb,
        compare_astat, expected_astat, expected_mstat,
        expected_alternate_bank
    } = expected_state;

    adsp2100_shift_move_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .sb_setup_write_i(sb_setup),
        .sb_setup_data_i(sb_setup_data),
        .probe_code_i(probe_code),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .unverified_unused_x_o(unverified_unused_x),
        .unavailable_xop_o(unavailable_xop),
        .destination_collision_o(destination_collision),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .sf_o(sf),
        .xop_o(xop),
        .shifter_source_dreg_o(shifter_source_dreg),
        .move_destination_dreg_o(move_destination_dreg),
        .move_source_dreg_o(move_source_dreg),
        .shifter_source_data_o(shifter_source_data),
        .move_source_data_o(move_source_data),
        .sr_result_o(sr_result),
        .se_result_o(se_result),
        .sb_result_o(sb_result),
        .ss_result_o(ss_result),
        .move_write_o(move_write),
        .sr_write_o(sr_write),
        .se_write_o(se_write),
        .sb_write_o(sb_write),
        .ss_write_o(ss_write),
        .probe_data_o(probe_data),
        .sr_o(sr),
        .se_o(se),
        .sb_o(sb),
        .astat_o(astat),
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
        vector_file = $fopen("build/shift_move_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 14 vectors");
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
                    unverified_unused_x, unavailable_xop,
                    destination_collision, boundary_valid, invalid_opcode,
                    integration_conflict, internal_conflict, sf, xop,
                    shifter_source_dreg, move_destination_dreg,
                    move_source_dreg, move_write, sr_write, se_write,
                    sb_write, ss_write, pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(1, "event mismatch vector=%0d", vector_count);
                end
                if (boundary_valid
                    && ((^shifter_source_data) === 1'bx
                        || (^move_source_data) === 1'bx
                        || (^sr_result) === 1'bx
                        || (^se_result) === 1'bx
                        || (^sb_result) === 1'bx
                        || ss_result === 1'bx)) begin
                    $fatal(1, "unknown action data vector=%0d", vector_count);
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
                if (compare_sb && sb !== expected_sb) begin
                    $fatal(1, "SB mismatch vector=%0d", vector_count);
                end
                if (compare_astat && astat !== expected_astat) begin
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 80_000) begin
            $fatal(1, "insufficient vectors=%0d", vector_count);
        end
        $display(
            "PASS Type 14 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
