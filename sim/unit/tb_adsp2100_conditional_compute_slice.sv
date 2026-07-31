`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_conditional_compute_slice;
    logic         clk;
    logic [99:0]  stimulus;
    logic [39:0]  expected_events;
    logic [105:0] expected_state;
    logic         reset;
    logic         execute;
    logic [23:0]  opcode;
    logic         not_counter_expired;
    logic         astat_setup;
    logic [7:0]   astat_setup_data;
    logic         mstat_setup;
    logic [3:0]   mstat_setup_data;
    logic         dreg_setup;
    logic [3:0]   dreg_setup_code;
    logic [15:0]  dreg_setup_data;
    logic         af_setup;
    logic [15:0]  af_setup_data;
    logic         mf_setup;
    logic [15:0]  mf_setup_data;
    logic [3:0]   probe_code;
    logic         class_valid;
    logic         action_valid;
    logic         unsupported_subencoding;
    logic         nop_action;
    logic         boundary_valid;
    logic         invalid_opcode;
    logic         integration_conflict;
    logic         internal_conflict;
    logic         condition_true;
    logic         is_mac;
    logic         is_alu;
    logic         destination_feedback;
    logic [4:0]   amf;
    logic [1:0]   yop;
    logic [2:0]   xop;
    logic [3:0]   condition;
    logic [3:0]   x_source_dreg;
    logic [3:0]   y_source_dreg;
    logic [15:0]  x_source_data;
    logic [15:0]  y_source_data;
    logic [15:0]  alu_result;
    logic [39:0]  mac_result;
    logic         alu_write;
    logic         mac_write;
    logic         alu_status_write;
    logic         mac_status_write;
    logic [15:0]  probe_data;
    logic [15:0]  af;
    logic [15:0]  mf;
    logic [39:0]  mr;
    logic [7:0]   astat;
    logic [3:0]   mstat;
    logic         alternate_bank;
    logic         pm_data_access;
    logic         dm_access;
    logic         compare_probe;
    logic [15:0]  expected_probe;
    logic         compare_af;
    logic [15:0]  expected_af;
    logic         compare_mf;
    logic [15:0]  expected_mf;
    logic         compare_mr;
    logic [39:0]  expected_mr;
    logic         compare_astat;
    logic [7:0]   expected_astat;
    logic [3:0]   expected_mstat;
    logic         expected_alternate_bank;
    integer       vector_file;
    integer       scan_count;
    integer       vector_count;

    assign {
        reset, execute, opcode, not_counter_expired,
        astat_setup, astat_setup_data,
        mstat_setup, mstat_setup_data,
        dreg_setup, dreg_setup_code, dreg_setup_data,
        af_setup, af_setup_data,
        mf_setup, mf_setup_data,
        probe_code
    } = stimulus;
    assign {
        compare_probe, expected_probe,
        compare_af, expected_af,
        compare_mf, expected_mf,
        compare_mr, expected_mr,
        compare_astat, expected_astat,
        expected_mstat, expected_alternate_bank
    } = expected_state;

    adsp2100_conditional_compute_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .not_counter_expired_i(not_counter_expired),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .af_setup_write_i(af_setup),
        .af_setup_data_i(af_setup_data),
        .mf_setup_write_i(mf_setup),
        .mf_setup_data_i(mf_setup_data),
        .probe_code_i(probe_code),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .nop_action_o(nop_action),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .condition_true_o(condition_true),
        .is_mac_o(is_mac),
        .is_alu_o(is_alu),
        .destination_feedback_o(destination_feedback),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .condition_o(condition),
        .x_source_dreg_o(x_source_dreg),
        .y_source_dreg_o(y_source_dreg),
        .x_source_data_o(x_source_data),
        .y_source_data_o(y_source_data),
        .alu_result_o(alu_result),
        .mac_result_o(mac_result),
        .alu_write_o(alu_write),
        .mac_write_o(mac_write),
        .alu_status_write_o(alu_status_write),
        .mac_status_write_o(mac_status_write),
        .probe_data_o(probe_data),
        .af_o(af),
        .mf_o(mf),
        .mr_o(mr),
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
        vector_file = $fopen("build/conditional_compute_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 9 vectors");
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
                    nop_action, boundary_valid, invalid_opcode,
                    integration_conflict, internal_conflict,
                    condition_true, is_mac, is_alu, destination_feedback,
                    amf, yop, xop, condition,
                    x_source_dreg, y_source_dreg,
                    alu_write, mac_write, alu_status_write, mac_status_write,
                    pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(1, "event mismatch vector=%0d", vector_count);
                end
                if (boundary_valid && condition_true && !nop_action
                    && ((^x_source_data) === 1'bx
                        || (^y_source_data) === 1'bx
                        || (is_alu && (^alu_result) === 1'bx)
                        || (is_mac && (^mac_result) === 1'bx))) begin
                    $fatal(1, "unknown action data vector=%0d", vector_count);
                end
                #4 clk = 1'b1;
                #2;
                if (mstat !== expected_mstat
                    || alternate_bank !== expected_alternate_bank) begin
                    $fatal(1, "mode mismatch vector=%0d", vector_count);
                end
                if (compare_probe && probe_data !== expected_probe) begin
                    $fatal(1, "probe mismatch vector=%0d", vector_count);
                end
                if (compare_af && af !== expected_af) begin
                    $fatal(1, "AF mismatch vector=%0d", vector_count);
                end
                if (compare_mf && mf !== expected_mf) begin
                    $fatal(1, "MF mismatch vector=%0d", vector_count);
                end
                if (compare_mr && mr !== expected_mr) begin
                    $fatal(1, "MR mismatch vector=%0d", vector_count);
                end
                if (compare_astat && astat !== expected_astat) begin
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
                end
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 280_000) begin
            $fatal(1, "insufficient vectors=%0d", vector_count);
        end
        $display(
            "PASS Type 9 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
