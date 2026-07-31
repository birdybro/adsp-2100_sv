`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_divide_sign_slice;
    logic         clk;
    logic [77:0]  stimulus;
    logic [109:0] expected_events;
    logic [54:0]  expected_post;

    logic reset;
    logic execute;
    logic [23:0] opcode;
    logic astat_setup;
    logic [7:0] astat_setup_data;
    logic mstat_setup;
    logic [3:0] mstat_setup_data;
    logic dreg_setup;
    logic [3:0] dreg_setup_code;
    logic [15:0] dreg_setup_data;
    logic af_setup;
    logic [15:0] af_setup_data;

    logic class_valid;
    logic action_valid;
    logic unsupported_yop;
    logic [1:0] yop;
    logic [2:0] xop;
    logic [3:0] x_source;
    logic [3:0] upper_source;
    logic upper_feedback;
    logic boundary_valid;
    logic invalid_opcode;
    logic integration_conflict;
    logic internal_conflict;
    logic source_known;
    logic result_known;
    logic quotient_sign;
    logic [15:0] divisor_before;
    logic [15:0] upper_before;
    logic [15:0] ay0_before;
    logic [15:0] af_result;
    logic [15:0] ay0_result;
    logic af_write;
    logic ay0_write;
    logic aq_write;
    logic [15:0] af;
    logic af_valid;
    logic [15:0] ay0;
    logic ay0_valid;
    logic [7:0] astat;
    logic [7:0] astat_valid_mask;
    logic [3:0] mstat;
    logic alternate_bank;
    logic pm_data_access;
    logic dm_access;

    logic exp_class_valid;
    logic exp_action_valid;
    logic exp_unsupported_yop;
    logic exp_boundary_valid;
    logic exp_invalid_opcode;
    logic exp_integration_conflict;
    logic exp_internal_conflict;
    logic exp_source_known;
    logic exp_result_known;
    logic exp_quotient_sign;
    logic exp_af_write;
    logic exp_ay0_write;
    logic exp_aq_write;
    logic exp_pm_data_access;
    logic exp_dm_access;
    logic [1:0] exp_yop;
    logic [2:0] exp_xop;
    logic [3:0] exp_x_source;
    logic [3:0] exp_upper_source;
    logic exp_upper_feedback;
    logic compare_values;
    logic [15:0] exp_divisor_before;
    logic [15:0] exp_upper_before;
    logic [15:0] exp_ay0_before;
    logic [15:0] exp_af_result;
    logic [15:0] exp_ay0_result;

    logic exp_af_valid;
    logic [15:0] exp_af;
    logic exp_ay0_valid;
    logic [15:0] exp_ay0;
    logic [7:0] exp_astat_valid_mask;
    logic [7:0] exp_astat;
    logic [3:0] exp_mstat;
    logic exp_alternate_bank;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset,
        execute,
        opcode,
        astat_setup,
        astat_setup_data,
        mstat_setup,
        mstat_setup_data,
        dreg_setup,
        dreg_setup_code,
        dreg_setup_data,
        af_setup,
        af_setup_data
    } = stimulus;

    assign {
        exp_class_valid,
        exp_action_valid,
        exp_unsupported_yop,
        exp_boundary_valid,
        exp_invalid_opcode,
        exp_integration_conflict,
        exp_internal_conflict,
        exp_source_known,
        exp_result_known,
        exp_quotient_sign,
        exp_af_write,
        exp_ay0_write,
        exp_aq_write,
        exp_pm_data_access,
        exp_dm_access,
        exp_yop,
        exp_xop,
        exp_x_source,
        exp_upper_source,
        exp_upper_feedback,
        compare_values,
        exp_divisor_before,
        exp_upper_before,
        exp_ay0_before,
        exp_af_result,
        exp_ay0_result
    } = expected_events;

    assign {
        exp_af_valid,
        exp_af,
        exp_ay0_valid,
        exp_ay0,
        exp_astat_valid_mask,
        exp_astat,
        exp_mstat,
        exp_alternate_bank
    } = expected_post;

    adsp2100_divide_sign_slice dut (
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
        .af_setup_write_i(af_setup),
        .af_setup_data_i(af_setup_data),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_yop_o(unsupported_yop),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .upper_source_dreg_o(upper_source),
        .upper_source_feedback_o(upper_feedback),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .source_known_o(source_known),
        .result_known_o(result_known),
        .quotient_sign_o(quotient_sign),
        .divisor_before_o(divisor_before),
        .upper_before_o(upper_before),
        .ay0_before_o(ay0_before),
        .af_result_o(af_result),
        .ay0_result_o(ay0_result),
        .af_write_o(af_write),
        .ay0_write_o(ay0_write),
        .aq_write_o(aq_write),
        .af_o(af),
        .af_valid_o(af_valid),
        .ay0_o(ay0),
        .ay0_valid_o(ay0_valid),
        .astat_o(astat),
        .astat_valid_mask_o(astat_valid_mask),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_post = '0;
        vector_file = $fopen("build/divide_sign_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/divide_sign_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_events,
                expected_post
            );
            if (scan_count == 3) begin
                #1;
                if (
                    class_valid !== exp_class_valid
                    || action_valid !== exp_action_valid
                    || unsupported_yop !== exp_unsupported_yop
                    || boundary_valid !== exp_boundary_valid
                    || invalid_opcode !== exp_invalid_opcode
                    || integration_conflict !== exp_integration_conflict
                    || internal_conflict !== exp_internal_conflict
                    || source_known !== exp_source_known
                    || result_known !== exp_result_known
                    || af_write !== exp_af_write
                    || ay0_write !== exp_ay0_write
                    || aq_write !== exp_aq_write
                    || pm_data_access !== exp_pm_data_access
                    || dm_access !== exp_dm_access
                    || yop !== exp_yop
                    || xop !== exp_xop
                    || x_source !== exp_x_source
                    || upper_source !== exp_upper_source
                    || upper_feedback !== exp_upper_feedback
                ) begin
                    $fatal(1, "event/field mismatch vector=%0d", vector_count);
                end
                if (compare_values) begin
                    if (
                        quotient_sign !== exp_quotient_sign
                        || divisor_before !== exp_divisor_before
                        || upper_before !== exp_upper_before
                        || ay0_before !== exp_ay0_before
                        || af_result !== exp_af_result
                        || ay0_result !== exp_ay0_result
                    ) begin
                        $fatal(1, "source/result mismatch vector=%0d", vector_count);
                    end
                end

                #4 clk = 1'b1;
                #1;
                if (
                    af_valid !== exp_af_valid
                    || ay0_valid !== exp_ay0_valid
                    || astat_valid_mask !== exp_astat_valid_mask
                    || mstat !== exp_mstat
                    || alternate_bank !== exp_alternate_bank
                ) begin
                    $fatal(1, "post-state validity mismatch vector=%0d", vector_count);
                end
                if (exp_af_valid && af !== exp_af) begin
                    $fatal(1, "AF mismatch vector=%0d", vector_count);
                end
                if (exp_ay0_valid && ay0 !== exp_ay0) begin
                    $fatal(1, "AY0 mismatch vector=%0d", vector_count);
                end
                if ((astat & exp_astat_valid_mask)
                    !== (exp_astat & exp_astat_valid_mask)) begin
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
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
            "PASS Type 24 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
