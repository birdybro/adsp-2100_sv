`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_compute_pm_slice;
    logic clk;
    logic [173:0] stimulus;
    logic [187:0] expected_events;
    logic [166:0] expected_post;

    logic reset;
    logic execute;
    logic [23:0] opcode;
    logic [23:0] pm_read_data;
    logic pm_read_data_valid;
    logic pm_cycle_complete;
    logic [13:0] next_fetch_address;
    logic next_fetch_address_valid;
    logic cache_next_instruction_valid;
    logic force_instruction_fetch;
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
    logic [3:0] probe_dreg_code;
    logic [2:0] probe_dag_address;

    logic class_valid;
    logic action_valid;
    logic unsupported;
    logic collision;
    logic computation_enable;
    logic is_mac;
    logic destination_feedback;
    logic write_direction;
    logic [4:0] amf;
    logic [1:0] yop;
    logic [2:0] xop;
    logic [3:0] x_source;
    logic [3:0] y_source;
    logic [3:0] memory_dreg;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic boundary_valid;
    logic accepted;
    logic data_action_complete;
    logic instruction_complete;
    logic transaction_active;
    logic held_transaction;
    logic busy;
    logic invalid_opcode;
    logic integration_conflict;
    logic internal_conflict;
    logic cache_instruction_selected;
    logic recovery_required;
    logic recovery_fetch;
    logic event_boundary;
    logic pm_select;
    logic pm_data_access;
    logic pm_read;
    logic pm_write;
    logic [13:0] pm_address;
    logic pm_address_valid;
    logic [23:0] pm_write_data;
    logic pm_write_data_valid;
    logic [23:0] fetched_instruction;
    logic fetched_instruction_valid;
    logic dm_access;
    logic compute_result_known;
    logic dag_configuration_valid;
    logic i_write;
    logic i_write_known;
    logic dreg_write;
    logic dreg_write_known;
    logic px_write;
    logic px_write_known;
    logic alu_write;
    logic mac_write;
    logic alu_status_write;
    logic mac_status_write;
    logic [15:0] alu_result;
    logic [39:0] mac_result;
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

    logic [187:0] actual_events;
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
        reset, execute, opcode, pm_read_data, pm_read_data_valid,
        pm_cycle_complete, next_fetch_address, next_fetch_address_valid,
        cache_next_instruction_valid, force_instruction_fetch,
        astat_setup, astat_setup_data, mstat_setup, mstat_setup_data,
        dreg_setup, dreg_setup_code, dreg_setup_data,
        af_setup, af_setup_data, mf_setup, mf_setup_data,
        dag_setup, dag_setup_kind, dag_setup_address, dag_setup_data,
        px_setup, px_setup_data, probe_dreg_code, probe_dag_address
    } = stimulus;

    assign actual_events = {
        class_valid, action_valid, unsupported, collision,
        computation_enable, is_mac, destination_feedback, write_direction,
        amf, yop, xop, x_source, y_source, memory_dreg,
        i_address, m_address,
        boundary_valid, accepted, data_action_complete,
        instruction_complete, transaction_active, held_transaction, busy,
        invalid_opcode, integration_conflict, internal_conflict,
        cache_instruction_selected, recovery_required, recovery_fetch,
        event_boundary,
        pm_select, pm_data_access, pm_read, pm_write,
        pm_address_valid, pm_address,
        pm_write_data_valid, pm_write_data,
        fetched_instruction_valid, fetched_instruction, dm_access,
        compute_result_known, dag_configuration_valid,
        i_write, i_write_known, dreg_write, dreg_write_known,
        px_write, px_write_known,
        alu_write, mac_write, alu_status_write, mac_status_write,
        alu_result, mac_result
    };

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

    adsp2100_compute_pm_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .pm_read_data_i(pm_read_data),
        .pm_read_data_valid_i(pm_read_data_valid),
        .pm_cycle_complete_i(pm_cycle_complete),
        .next_fetch_address_i(next_fetch_address),
        .next_fetch_address_valid_i(next_fetch_address_valid),
        .cache_next_instruction_valid_i(cache_next_instruction_valid),
        .force_instruction_fetch_i(force_instruction_fetch),
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
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported),
        .destination_collision_o(collision),
        .computation_enable_o(computation_enable),
        .is_mac_o(is_mac),
        .destination_feedback_o(destination_feedback),
        .write_direction_o(write_direction),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .y_source_dreg_o(y_source),
        .memory_dreg_o(memory_dreg),
        .i_address_o(i_address),
        .m_address_o(m_address),
        .boundary_valid_o(boundary_valid),
        .accepted_o(accepted),
        .data_action_complete_o(data_action_complete),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .held_transaction_o(held_transaction),
        .busy_o(busy),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .cache_instruction_selected_o(cache_instruction_selected),
        .recovery_required_o(recovery_required),
        .recovery_fetch_o(recovery_fetch),
        .event_boundary_o(event_boundary),
        .pm_select_o(pm_select),
        .pm_data_access_o(pm_data_access),
        .pm_read_o(pm_read),
        .pm_write_o(pm_write),
        .pm_address_o(pm_address),
        .pm_address_valid_o(pm_address_valid),
        .pm_write_data_o(pm_write_data),
        .pm_write_data_valid_o(pm_write_data_valid),
        .fetched_instruction_o(fetched_instruction),
        .fetched_instruction_valid_o(fetched_instruction_valid),
        .dm_access_o(dm_access),
        .compute_result_known_o(compute_result_known),
        .dag_configuration_valid_o(dag_configuration_valid),
        .i_write_o(i_write),
        .i_write_known_o(i_write_known),
        .dreg_write_o(dreg_write),
        .dreg_write_known_o(dreg_write_known),
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
        vector_file = $fopen("build/compute_pm_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/compute_pm_vectors.txt");
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
                if (actual_events !== expected_events) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d expected=%h actual=%h",
                        vector_count,
                        expected_events,
                        actual_events
                    );
                end
                #4 clk = 1'b1;
                #1;
                if (probe_dreg_valid !== exp_probe_dreg_valid
                    || probe_i_valid !== exp_probe_i_valid
                    || probe_m_valid !== exp_probe_m_valid
                    || probe_l_valid !== exp_probe_l_valid
                    || px_valid !== exp_px_valid
                    || af_valid !== exp_af_valid
                    || mf_valid !== exp_mf_valid
                    || mr_valid !== exp_mr_valid
                    || astat_valid_mask !== exp_astat_valid_mask
                    || mstat !== exp_mstat
                    || alternate_bank !== exp_alternate_bank) begin
                    $fatal(1, "post validity mismatch vector=%0d", vector_count);
                end
                if (exp_probe_dreg_valid
                    && probe_dreg_data !== exp_probe_dreg_data)
                    $fatal(1, "DREG mismatch vector=%0d", vector_count);
                if (exp_probe_i_valid && probe_i_data !== exp_probe_i_data)
                    $fatal(1, "I mismatch vector=%0d", vector_count);
                if (exp_probe_m_valid && probe_m_data !== exp_probe_m_data)
                    $fatal(1, "M mismatch vector=%0d", vector_count);
                if (exp_probe_l_valid && probe_l_data !== exp_probe_l_data)
                    $fatal(1, "L mismatch vector=%0d", vector_count);
                if (exp_px_valid && px !== exp_px)
                    $fatal(1, "PX mismatch vector=%0d", vector_count);
                if (exp_af_valid && af !== exp_af)
                    $fatal(1, "AF mismatch vector=%0d", vector_count);
                if (exp_mf_valid && mf !== exp_mf)
                    $fatal(1, "MF mismatch vector=%0d", vector_count);
                if (exp_mr_valid && mr !== exp_mr)
                    $fatal(1, "MR mismatch vector=%0d", vector_count);
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
            "PASS Type 5 state/cache-boundary model-RTL differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
