`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_shifter_pm_owner_control_slice;
    logic clk;
    logic [207:0] stimulus;
    logic [163:0] expected_events;
    logic [159:0] expected_post;
    logic [163:0] actual_events;
    logic [159:0] actual_post;

    logic reset, advance, br_n;
    logic [2:0] phase;
    logic fetch_valid, fetch_address_valid;
    logic [13:0] fetch_address;
    logic type5_valid, type5_address_valid, type5_write;
    logic [13:0] type5_address;
    logic [23:0] type5_data;
    logic type5_data_valid;
    logic execute;
    logic [23:0] opcode, pmd;
    logic pmd_valid;
    logic [13:0] next_address;
    logic next_valid;
    logic astat_setup;
    logic [7:0] astat_setup_data;
    logic mstat_setup;
    logic [3:0] mstat_setup_data;
    logic dreg_setup;
    logic [3:0] dreg_setup_code;
    logic [15:0] dreg_setup_data;
    logic sb_setup;
    logic [4:0] sb_setup_data;
    logic dag_setup;
    logic [1:0] dag_setup_kind;
    logic [2:0] dag_setup_address;
    logic [13:0] dag_setup_data;
    logic px_setup;
    logic [7:0] px_setup_data;
    logic [3:0] probe_dreg_code;
    logic [2:0] probe_dag_address;

    logic issue_boundary, phase_conflict, attachment_conflict;
    logic integration_conflict, class_valid, action_valid;
    logic unsupported, accepted, data_complete, instruction_complete;
    logic transaction_active, busy, recovery_fetch, fetch_cache_fill;
    logic cache_fill_accepted, type13_presented, type13_accepted;
    logic type13_retry;
    logic [23:0] next_instruction;
    logic next_instruction_valid, from_cache, from_external;
    logic [13:0] cache_region_start;
    logic cache_region_start_valid;
    logic [4:0] cache_region_count;

    logic [2:0] bus_mode;
    logic bus_request_recognized, grant_assert, release_recognized;
    logic grant_release, resume, issue_inhibit, bg_n, bus_relinquished;
    logic request_blocked, request_conflict, request_out_of_phase;
    logic [2:0] request_accepted, completion;
    logic [1:0] owner;
    logic pm_bus_active;
    logic address_oe, control_oe, data_oe;
    logic [13:0] pma;
    logic pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;

    logic [15:0] probe_dreg_data;
    logic probe_dreg_valid;
    logic [13:0] probe_i_data, probe_m_data, probe_l_data;
    logic probe_i_valid, probe_m_valid, probe_l_valid;
    logic [7:0] px;
    logic px_valid;
    logic [31:0] sr;
    logic sr_valid;
    logic [7:0] se;
    logic se_valid;
    logic [4:0] sb;
    logic sb_valid;
    logic [7:0] astat, astat_valid_mask;
    logic [3:0] mstat;
    logic alternate_bank;
    integer vector_file, scan_count, vector_count;

    assign {
        reset, phase, advance, br_n,
        fetch_valid, fetch_address, fetch_address_valid,
        type5_valid, type5_address, type5_address_valid, type5_write,
        type5_data, type5_data_valid,
        execute, opcode, pmd, pmd_valid, next_address, next_valid,
        astat_setup, astat_setup_data, mstat_setup, mstat_setup_data,
        dreg_setup, dreg_setup_code, dreg_setup_data,
        sb_setup, sb_setup_data, dag_setup, dag_setup_kind,
        dag_setup_address, dag_setup_data, px_setup, px_setup_data,
        probe_dreg_code, probe_dag_address
    } = stimulus[205:0];

    assign actual_events = {
        48'h000000000000,
        issue_boundary, phase_conflict, attachment_conflict,
        integration_conflict, class_valid, action_valid, unsupported,
        accepted, data_complete, instruction_complete, transaction_active,
        busy, recovery_fetch, fetch_cache_fill, cache_fill_accepted,
        type13_presented, type13_accepted, type13_retry,
        next_instruction_valid,
        next_instruction_valid ? next_instruction : 24'h000000,
        from_cache, from_external,
        bus_mode, bus_request_recognized, grant_assert,
        release_recognized, grant_release, resume, issue_inhibit,
        bg_n, bus_relinquished, request_blocked, request_conflict,
        request_out_of_phase, request_accepted, completion, owner,
        pm_bus_active, address_oe, control_oe, data_oe,
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
        sr_valid, sr_valid ? sr : 32'h00000000,
        se_valid, se_valid ? se : 8'h00,
        sb_valid, sb_valid ? sb : 5'h00,
        astat_valid_mask, astat & astat_valid_mask,
        mstat, alternate_bank,
        cache_region_start_valid, cache_region_start, cache_region_count
    };

    adsp2100_shifter_pm_owner_control_slice dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(advance), .br_n_i(br_n),
        .fetch_valid_i(fetch_valid), .fetch_address_i(fetch_address),
        .fetch_address_valid_i(fetch_address_valid),
        .type5_valid_i(type5_valid), .type5_address_i(type5_address),
        .type5_address_valid_i(type5_address_valid),
        .type5_data_access_i(1'b1),
        .type5_write_i(type5_write), .type5_write_data_i(type5_data),
        .type5_write_data_valid_i(type5_data_valid),
        .execute_i(execute), .opcode_i(opcode),
        .pmd_read_data_i(pmd), .pmd_read_data_valid_i(pmd_valid),
        .next_fetch_address_i(next_address),
        .next_fetch_address_valid_i(next_valid),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .sb_setup_write_i(sb_setup), .sb_setup_data_i(sb_setup_data),
        .dag_setup_write_i(dag_setup),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .px_setup_write_i(px_setup), .px_setup_data_i(px_setup_data),
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .issue_boundary_o(issue_boundary),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .class_valid_o(class_valid), .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported), .accepted_o(accepted),
        .data_action_complete_o(data_complete),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active), .busy_o(busy),
        .recovery_fetch_o(recovery_fetch),
        .fetch_cache_fill_o(fetch_cache_fill),
        .cache_fill_accepted_o(cache_fill_accepted),
        .cache_region_start_o(cache_region_start),
        .cache_region_start_valid_o(cache_region_start_valid),
        .cache_region_count_o(cache_region_count),
        .type13_request_presented_o(type13_presented),
        .type13_request_accepted_o(type13_accepted),
        .type13_retry_pending_o(type13_retry),
        .next_instruction_o(next_instruction),
        .next_instruction_valid_o(next_instruction_valid),
        .instruction_from_cache_o(from_cache),
        .instruction_from_external_o(from_external),
        .bus_mode_o(bus_mode),
        .bus_request_recognized_o(bus_request_recognized),
        .grant_assert_event_o(grant_assert),
        .release_recognized_o(release_recognized),
        .grant_release_event_o(grant_release), .resume_event_o(resume),
        .issue_inhibit_o(issue_inhibit), .bg_n_o(bg_n),
        .bus_relinquished_o(bus_relinquished),
        .request_blocked_o(request_blocked),
        .request_conflict_o(request_conflict),
        .request_out_of_phase_o(request_out_of_phase),
        .request_accepted_o(request_accepted),
        .completion_event_o(completion), .owner_o(owner),
        .pm_bus_active_o(pm_bus_active),
        .pm_address_output_enable_o(address_oe),
        .pm_control_output_enable_o(control_oe),
        .pm_data_output_enable_o(data_oe),
        .pma_o(pma), .pma_valid_o(pma_valid), .pmda_o(pmda),
        .pmda_valid_o(pmda_valid), .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n), .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid),
        .probe_dreg_data_o(probe_dreg_data),
        .probe_dreg_valid_o(probe_dreg_valid),
        .probe_i_data_o(probe_i_data), .probe_i_valid_o(probe_i_valid),
        .probe_m_data_o(probe_m_data), .probe_m_valid_o(probe_m_valid),
        .probe_l_data_o(probe_l_data), .probe_l_valid_o(probe_l_valid),
        .px_o(px), .px_valid_o(px_valid), .sr_o(sr),
        .sr_valid_o(sr_valid), .se_o(se), .se_valid_o(se_valid),
        .sb_o(sb), .sb_valid_o(sb_valid), .astat_o(astat),
        .astat_valid_mask_o(astat_valid_mask), .mstat_o(mstat),
        .alternate_bank_o(alternate_bank)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_post = '0;
        vector_file = $fopen(
            "build/shifter_pm_owner_control_vectors.txt", "r"
        );
        if (vector_file == 0)
            $fatal(1, "cannot open Type 13/shared-PM/BR-BG vectors");
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file, "%h %h %h\n",
                stimulus, expected_events, expected_post
            );
            if (scan_count == 3) begin
                #2;
                if (actual_events !== expected_events)
                    $fatal(1, "Type 13/shared-PM pre mismatch vector=%0d expected=%041x actual=%041x stimulus=%052x",
                           vector_count, expected_events, actual_events,
                           stimulus);
                #2 clk = 1'b1;
                #1;
                if (actual_post !== expected_post)
                    $fatal(1, "Type 13/shared-PM post mismatch vector=%0d expected=%040x actual=%040x",
                           vector_count, expected_post, actual_post);
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50000) $fatal(1, "insufficient vectors");
        $display(
            "PASS Type 13/shared-PM/BR-BG differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
