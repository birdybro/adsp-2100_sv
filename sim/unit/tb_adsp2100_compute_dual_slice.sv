`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_compute_dual_slice;
    logic clk;
    logic [174:0] stimulus;
    logic [160:0] expected_events;
    logic [166:0] expected_post;
    logic [160:0] observed_events;

    logic reset;
    logic execute;
    logic [23:0] opcode;
    logic transaction_complete;
    logic [15:0] dm_read_data;
    logic dm_read_data_valid;
    logic [23:0] pm_read_data;
    logic pm_read_data_valid;
    logic astat_setup;
    logic [7:0] astat_setup_data;
    logic mstat_setup;
    logic [3:0] mstat_setup_data;
    logic dreg_setup;
    logic [3:0] dreg_setup_code;
    logic [15:0] dreg_setup_data;
    logic af_setup;
    logic [15:0] af_setup_data;
    logic mf_setup;
    logic [15:0] mf_setup_data;
    logic dag_setup;
    logic [1:0] dag_setup_kind;
    logic [2:0] dag_setup_address;
    logic [13:0] dag_setup_data;
    logic px_setup;
    logic [7:0] px_setup_data;
    logic inspect_probe;
    logic [3:0] probe_dreg_code;
    logic [2:0] probe_dag_address;

    logic class_valid;
    logic action_valid;
    logic unsupported;
    logic computation_enable;
    logic is_mac;
    logic [4:0] amf;
    logic [1:0] yop;
    logic [2:0] xop;
    logic [3:0] x_source;
    logic [3:0] y_source;
    logic [3:0] pm_destination;
    logic [3:0] dm_destination;
    logic [2:0] pm_i_address;
    logic [2:0] pm_m_address;
    logic [2:0] dm_i_address;
    logic [2:0] dm_m_address;
    logic boundary_valid;
    logic accepted;
    logic instruction_complete;
    logic transaction_active;
    logic stalled;
    logic busy;
    logic invalid_opcode;
    logic integration_conflict;
    logic internal_conflict;
    logic dm_select;
    logic dm_read;
    logic [13:0] dm_address;
    logic dm_address_valid;
    logic pm_select;
    logic pm_data_access;
    logic pm_read;
    logic [13:0] pm_address;
    logic pm_address_valid;
    logic compute_result_known;
    logic dm_dag_configuration_valid;
    logic pm_dag_configuration_valid;
    logic dm_i_write;
    logic dm_i_write_known;
    logic pm_i_write;
    logic pm_i_write_known;
    logic dm_dreg_write;
    logic dm_dreg_write_known;
    logic pm_dreg_write;
    logic pm_dreg_write_known;
    logic px_write;
    logic px_write_known;
    logic alu_write;
    logic mac_write;
    logic alu_status_write;
    logic mac_status_write;
    logic [15:0] alu_result;
    logic [39:0] mac_result;
    logic compare_result;

    logic [15:0] probe_dreg_data;
    logic probe_dreg_valid;
    logic [13:0] probe_i_data;
    logic probe_i_valid;
    logic [13:0] probe_m_data;
    logic probe_m_valid;
    logic [13:0] probe_l_data;
    logic probe_l_valid;
    logic [7:0] px;
    logic px_valid;
    logic [15:0] af;
    logic af_valid;
    logic [15:0] mf;
    logic mf_valid;
    logic [39:0] mr;
    logic mr_valid;
    logic [7:0] astat;
    logic [7:0] astat_valid_mask;
    logic [3:0] mstat;
    logic alternate_bank;

    logic exp_probe_dreg_valid;
    logic [15:0] exp_probe_dreg_data;
    logic exp_probe_i_valid;
    logic [13:0] exp_probe_i_data;
    logic exp_probe_m_valid;
    logic [13:0] exp_probe_m_data;
    logic exp_probe_l_valid;
    logic [13:0] exp_probe_l_data;
    logic exp_px_valid;
    logic [7:0] exp_px;
    logic exp_af_valid;
    logic [15:0] exp_af;
    logic exp_mf_valid;
    logic [15:0] exp_mf;
    logic exp_mr_valid;
    logic [39:0] exp_mr;
    logic [7:0] exp_astat_valid_mask;
    logic [7:0] exp_astat;
    logic [3:0] exp_mstat;
    logic exp_alternate_bank;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, execute, opcode, transaction_complete,
        dm_read_data, dm_read_data_valid,
        pm_read_data, pm_read_data_valid,
        astat_setup, astat_setup_data,
        mstat_setup, mstat_setup_data,
        dreg_setup, dreg_setup_code, dreg_setup_data,
        af_setup, af_setup_data,
        mf_setup, mf_setup_data,
        dag_setup, dag_setup_kind, dag_setup_address, dag_setup_data,
        px_setup, px_setup_data,
        inspect_probe, probe_dreg_code, probe_dag_address
    } = stimulus;

    assign observed_events = {
        class_valid, action_valid, unsupported,
        computation_enable, is_mac, amf, yop, xop,
        x_source, y_source, pm_destination, dm_destination,
        pm_i_address, pm_m_address, dm_i_address, dm_m_address,
        boundary_valid, accepted, instruction_complete,
        transaction_active, stalled, busy, invalid_opcode,
        integration_conflict, internal_conflict,
        dm_select, dm_read, dm_address_valid, dm_address,
        pm_select, pm_data_access, pm_read, pm_address_valid, pm_address,
        compute_result_known,
        dm_dag_configuration_valid, pm_dag_configuration_valid,
        dm_i_write, dm_i_write_known, pm_i_write, pm_i_write_known,
        dm_dreg_write, dm_dreg_write_known,
        pm_dreg_write, pm_dreg_write_known,
        px_write, px_write_known,
        alu_write, mac_write, alu_status_write, mac_status_write,
        compare_result,
        compare_result ? alu_result : 16'h0000,
        compare_result ? mac_result : 40'h0000000000
    };
    assign compare_result = compute_result_known;

    assign {
        exp_probe_dreg_valid, exp_probe_dreg_data,
        exp_probe_i_valid, exp_probe_i_data,
        exp_probe_m_valid, exp_probe_m_data,
        exp_probe_l_valid, exp_probe_l_data,
        exp_px_valid, exp_px,
        exp_af_valid, exp_af,
        exp_mf_valid, exp_mf,
        exp_mr_valid, exp_mr,
        exp_astat_valid_mask, exp_astat,
        exp_mstat, exp_alternate_bank
    } = expected_post;

    adsp2100_compute_dual_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .transaction_complete_i(transaction_complete),
        .dm_read_data_i(dm_read_data),
        .dm_read_data_valid_i(dm_read_data_valid),
        .pm_read_data_i(pm_read_data),
        .pm_read_data_valid_i(pm_read_data_valid),
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
        .dag_setup_write_i(dag_setup),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .px_setup_write_i(px_setup),
        .px_setup_data_i(px_setup_data),
        .inspect_probe_i(inspect_probe),
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported),
        .computation_enable_o(computation_enable),
        .is_mac_o(is_mac),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .y_source_dreg_o(y_source),
        .pm_destination_dreg_o(pm_destination),
        .dm_destination_dreg_o(dm_destination),
        .pm_i_address_o(pm_i_address),
        .pm_m_address_o(pm_m_address),
        .dm_i_address_o(dm_i_address),
        .dm_m_address_o(dm_m_address),
        .boundary_valid_o(boundary_valid),
        .accepted_o(accepted),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .stalled_o(stalled),
        .busy_o(busy),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .dm_select_o(dm_select),
        .dm_read_o(dm_read),
        .dm_address_o(dm_address),
        .dm_address_valid_o(dm_address_valid),
        .pm_select_o(pm_select),
        .pm_data_access_o(pm_data_access),
        .pm_read_o(pm_read),
        .pm_address_o(pm_address),
        .pm_address_valid_o(pm_address_valid),
        .compute_result_known_o(compute_result_known),
        .dm_dag_configuration_valid_o(dm_dag_configuration_valid),
        .pm_dag_configuration_valid_o(pm_dag_configuration_valid),
        .dm_i_write_o(dm_i_write),
        .dm_i_write_known_o(dm_i_write_known),
        .pm_i_write_o(pm_i_write),
        .pm_i_write_known_o(pm_i_write_known),
        .dm_dreg_write_o(dm_dreg_write),
        .dm_dreg_write_known_o(dm_dreg_write_known),
        .pm_dreg_write_o(pm_dreg_write),
        .pm_dreg_write_known_o(pm_dreg_write_known),
        .px_write_o(px_write),
        .px_write_known_o(px_write_known),
        .alu_write_o(alu_write),
        .mac_write_o(mac_write),
        .alu_status_write_o(alu_status_write),
        .mac_status_write_o(mac_status_write),
        .alu_result_o(alu_result),
        .mac_result_o(mac_result),
        .probe_dreg_data_o(probe_dreg_data),
        .probe_dreg_valid_o(probe_dreg_valid),
        .probe_i_data_o(probe_i_data),
        .probe_i_valid_o(probe_i_valid),
        .probe_m_data_o(probe_m_data),
        .probe_m_valid_o(probe_m_valid),
        .probe_l_data_o(probe_l_data),
        .probe_l_valid_o(probe_l_valid),
        .px_o(px),
        .px_valid_o(px_valid),
        .af_o(af),
        .af_valid_o(af_valid),
        .mf_o(mf),
        .mf_valid_o(mf_valid),
        .mr_o(mr),
        .mr_valid_o(mr_valid),
        .astat_o(astat),
        .astat_valid_mask_o(astat_valid_mask),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_post = '0;
        vector_file = $fopen("build/compute_dual_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/compute_dual_vectors.txt");
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
                if (observed_events !== expected_events) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d got=%h expected=%h",
                        vector_count,
                        observed_events,
                        expected_events
                    );
                end
                clk = 1'b1;
                #1;
                clk = 1'b0;
                #1;
                if (probe_dreg_valid !== exp_probe_dreg_valid
                    || (exp_probe_dreg_valid
                        && probe_dreg_data !== exp_probe_dreg_data)
                    || probe_i_valid !== exp_probe_i_valid
                    || (exp_probe_i_valid && probe_i_data !== exp_probe_i_data)
                    || probe_m_valid !== exp_probe_m_valid
                    || (exp_probe_m_valid && probe_m_data !== exp_probe_m_data)
                    || probe_l_valid !== exp_probe_l_valid
                    || (exp_probe_l_valid && probe_l_data !== exp_probe_l_data)
                    || px_valid !== exp_px_valid
                    || (exp_px_valid && px !== exp_px)
                    || af_valid !== exp_af_valid
                    || (exp_af_valid && af !== exp_af)
                    || mf_valid !== exp_mf_valid
                    || (exp_mf_valid && mf !== exp_mf)
                    || mr_valid !== exp_mr_valid
                    || (exp_mr_valid && mr !== exp_mr)
                    || astat_valid_mask !== exp_astat_valid_mask
                    || ((astat & exp_astat_valid_mask)
                        !== (exp_astat & exp_astat_valid_mask))
                    || mstat !== exp_mstat
                    || alternate_bank !== exp_alternate_bank) begin
                    $fatal(1, "post-state mismatch vector=%0d", vector_count);
                end
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count == 0) begin
            $fatal(1, "no Type 1 vectors read");
        end
        $display("PASS Type 1 logical state: %0d clocks", vector_count);
        $finish;
    end
endmodule

`default_nettype wire
