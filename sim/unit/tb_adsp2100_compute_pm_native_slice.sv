`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_compute_pm_native_slice;
    logic         clk;
    logic [232:0] stimulus;
    logic [140:0] expected_events;
    logic [191:0] expected_post;
    logic [140:0] actual_events;
    logic [191:0] actual_post;

    logic reset;
    logic [2:0] phase;
    logic phase_advance;
    logic bus_relinquished;
    logic execute;
    logic [23:0] opcode;
    logic [23:0] pmd_read_data;
    logic pmd_read_data_valid;
    logic [13:0] next_fetch_address;
    logic next_fetch_address_valid;
    logic force_instruction_fetch;
    logic external_fetch_fill;
    logic [13:0] external_fetch_address;
    logic external_fetch_address_valid;
    logic [23:0] external_fetch_instruction;
    logic external_fetch_instruction_valid;
    logic [3:0] irq_n;
    logic [4:0] icntl;
    logic icntl_valid;
    logic [3:0] imask;
    logic imask_valid;
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

    logic issue_boundary;
    logic phase_conflict;
    logic attachment_conflict;
    logic integration_conflict;
    logic class_valid;
    logic action_valid;
    logic unsupported_subencoding;
    logic accepted;
    logic data_action_complete;
    logic instruction_complete;
    logic transaction_active;
    logic busy;
    logic cache_instruction_selected;
    logic recovery_required;
    logic recovery_fetch;
    logic event_boundary;
    logic [23:0] next_instruction;
    logic next_instruction_valid;
    logic instruction_from_cache;
    logic instruction_from_external;
    logic cache_fill;
    logic cache_fill_from_recovery;
    logic cache_fill_accepted;
    logic [13:0] cache_region_start;
    logic cache_region_start_valid;
    logic [4:0] cache_region_count;
    logic interrupt_sample_event;
    logic interrupt_interval_block;
    logic [3:0] interrupt_enabled_requests;
    logic interrupt_recognition_event;
    logic [1:0] interrupt_recognized_level;
    logic [13:0] interrupt_vector_address;
    logic [3:0] interrupt_edge_pending;
    logic interrupt_sample_history_valid;
    logic pm_request_accepted;
    logic pm_completion_event;
    logic pm_read_sample_event;
    logic pm_bus_active;
    logic pm_address_oe;
    logic pm_control_oe;
    logic pm_data_oe;
    logic [13:0] pma;
    logic pma_valid;
    logic pmda;
    logic pmda_valid;
    logic pms_n;
    logic pmrd_n;
    logic pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
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
    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, phase, phase_advance, bus_relinquished, execute, opcode,
        pmd_read_data, pmd_read_data_valid, next_fetch_address,
        next_fetch_address_valid, force_instruction_fetch,
        external_fetch_fill, external_fetch_address,
        external_fetch_address_valid, external_fetch_instruction,
        external_fetch_instruction_valid, irq_n, icntl, icntl_valid,
        imask, imask_valid, astat_setup, astat_setup_data,
        mstat_setup, mstat_setup_data, dreg_setup, dreg_setup_code,
        dreg_setup_data, af_setup, af_setup_data, mf_setup, mf_setup_data,
        dag_setup,
        dag_setup_kind, dag_setup_address, dag_setup_data, px_setup,
        px_setup_data, probe_dreg_code, probe_dag_address
    } = stimulus;

    assign actual_events = {
        issue_boundary, phase_conflict, attachment_conflict,
        integration_conflict, class_valid, action_valid,
        unsupported_subencoding, accepted, data_action_complete,
        instruction_complete, transaction_active, busy,
        cache_instruction_selected, recovery_required, recovery_fetch,
        event_boundary, next_instruction_valid,
        next_instruction_valid ? next_instruction : 24'h000000,
        instruction_from_cache, instruction_from_external,
        cache_fill, cache_fill_from_recovery, cache_fill_accepted,
        cache_region_start_valid, cache_region_start, cache_region_count,
        interrupt_sample_event, interrupt_interval_block,
        interrupt_enabled_requests, interrupt_recognition_event,
        interrupt_recognized_level, interrupt_vector_address,
        pm_request_accepted, pm_completion_event, pm_read_sample_event,
        pm_bus_active, pm_address_oe, pm_control_oe, pm_data_oe,
        pma_valid, pma_valid ? pma : 14'h0000,
        pmda, pmda_valid, pms_n, pmrd_n, pmwr_n,
        pmd_write_data_valid,
        pmd_write_data_valid ? pmd_write_data : 24'h000000
    };

    assign actual_post = {
        probe_dreg_valid,
        probe_dreg_valid ? probe_dreg_data : 16'h0000,
        probe_i_valid, probe_i_valid ? probe_i_data : 14'h0000,
        probe_m_valid, probe_m_valid ? probe_m_data : 14'h0000,
        probe_l_valid, probe_l_valid ? probe_l_data : 14'h0000,
        px_valid, px_valid ? px : 8'h00,
        af_valid, af_valid ? af : 16'h0000,
        mf_valid, mf_valid ? mf : 16'h0000,
        mr_valid, mr_valid ? mr : 40'h0000000000,
        astat_valid_mask, astat & astat_valid_mask,
        mstat, alternate_bank,
        cache_region_start_valid, cache_region_start, cache_region_count,
        interrupt_edge_pending, interrupt_sample_history_valid
    };

    adsp2100_compute_pm_native_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .bus_relinquished_i(bus_relinquished),
        .execute_i(execute),
        .opcode_i(opcode),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .next_fetch_address_i(next_fetch_address),
        .next_fetch_address_valid_i(next_fetch_address_valid),
        .force_instruction_fetch_i(force_instruction_fetch),
        .external_fetch_fill_i(external_fetch_fill),
        .external_fetch_address_i(external_fetch_address),
        .external_fetch_address_valid_i(external_fetch_address_valid),
        .external_fetch_instruction_i(external_fetch_instruction),
        .external_fetch_instruction_valid_i(
            external_fetch_instruction_valid
        ),
        .irq_n_i(irq_n),
        .icntl_i(icntl),
        .icntl_valid_i(icntl_valid),
        .imask_i(imask),
        .imask_valid_i(imask_valid),
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
        .issue_boundary_o(issue_boundary),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .accepted_o(accepted),
        .data_action_complete_o(data_action_complete),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .busy_o(busy),
        .cache_instruction_selected_o(cache_instruction_selected),
        .recovery_required_o(recovery_required),
        .recovery_fetch_o(recovery_fetch),
        .event_boundary_o(event_boundary),
        .next_instruction_o(next_instruction),
        .next_instruction_valid_o(next_instruction_valid),
        .instruction_from_cache_o(instruction_from_cache),
        .instruction_from_external_o(instruction_from_external),
        .cache_fill_o(cache_fill),
        .cache_fill_from_recovery_o(cache_fill_from_recovery),
        .cache_fill_accepted_o(cache_fill_accepted),
        .cache_region_start_o(cache_region_start),
        .cache_region_start_valid_o(cache_region_start_valid),
        .cache_region_count_o(cache_region_count),
        .interrupt_sample_event_o(interrupt_sample_event),
        .interrupt_interval_block_o(interrupt_interval_block),
        .interrupt_enabled_requests_o(interrupt_enabled_requests),
        .interrupt_recognition_event_o(interrupt_recognition_event),
        .interrupt_recognized_level_o(interrupt_recognized_level),
        .interrupt_vector_address_o(interrupt_vector_address),
        .interrupt_edge_pending_o(interrupt_edge_pending),
        .interrupt_sample_history_valid_o(
            interrupt_sample_history_valid
        ),
        .pm_request_accepted_o(pm_request_accepted),
        .pm_completion_event_o(pm_completion_event),
        .pm_read_sample_event_o(pm_read_sample_event),
        .pm_bus_active_o(pm_bus_active),
        .pm_address_output_enable_o(pm_address_oe),
        .pm_control_output_enable_o(pm_control_oe),
        .pm_data_output_enable_o(pm_data_oe),
        .pma_o(pma),
        .pma_valid_o(pma_valid),
        .pmda_o(pmda),
        .pmda_valid_o(pmda_valid),
        .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n),
        .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid),
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
        vector_file = $fopen("build/compute_pm_native_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 5/native-PM vectors");
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
                #2;
                if (actual_events !== expected_events) begin
                    $fatal(
                        1,
                        "Type 5/native event mismatch vector=%0d expected=%030x actual=%030x stimulus=%055x",
                        vector_count,
                        expected_events,
                        actual_events,
                        stimulus
                    );
                end
                #2 clk = 1'b1;
                #1;
                if (actual_post !== expected_post) begin
                    $fatal(
                        1,
                        "Type 5/native post mismatch vector=%0d expected=%047x actual=%047x",
                        vector_count,
                        expected_post,
                        actual_post
                    );
                end
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50_000) begin
            $fatal(1, "insufficient Type 5/native vectors: %0d", vector_count);
        end
        $display(
            "PASS Type 5/cache/native-PM differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
