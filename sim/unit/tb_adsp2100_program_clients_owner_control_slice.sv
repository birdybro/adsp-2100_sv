`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_program_clients_owner_control_slice;
    logic clk;
    logic [273:0] stimulus;
    logic [159:0] expected_events, actual_events;
    logic [127:0] expected_post, actual_post;

    logic reset, advance, br_n, halt_n, dmack;
    logic [2:0] phase;
    logic instruction_setup;
    logic [13:0] instruction_setup_pc;
    logic [23:0] instruction_setup_opcode;
    logic [3:0] irq_n;
    logic automatic_pm_flow;
    logic type5_execute;
    logic [23:0] type5_opcode;
    logic [13:0] type5_next;
    logic type5_next_valid;
    logic type13_execute;
    logic [23:0] type13_opcode;
    logic [13:0] type13_next;
    logic type13_next_valid;
    logic [23:0] pmd;
    logic pmd_valid;
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
    logic sb_setup;
    logic [4:0] sb_setup_data;
    logic dag_setup;
    logic [1:0] dag_setup_kind;
    logic [2:0] dag_setup_address;
    logic [13:0] dag_setup_data;
    logic px_setup;
    logic [7:0] px_setup_data;
    logic [5:0] linear_probe_code;
    logic [3:0] pm_probe_dreg_code;
    logic [2:0] pm_probe_dag_address;

    logic issue_boundary, client_execute_conflict, integration_conflict;
    logic automatic_pm_issue, automatic_pm_retire, automatic_pm_blocked;
    logic [1:0] halt_mode;
    logic halt_recognized, halt_stop, halt_force_fetch, halt_resume;
    logic halt_release_blocked, halt_phase_hold, effective_advance, halted;
    logic halt_br_conflict, halt_attachment_conflict;
    logic linear_fetch_presented, linear_issue, linear_retire;
    logic linear_instruction_valid;
    logic [13:0] linear_pc;
    logic [23:0] linear_opcode;
    logic [15:0] linear_probe_data;
    logic type5_presented, type5_accepted, type5_retry;
    logic type5_data_complete, type5_instruction_complete;
    logic [23:0] type5_next_instruction;
    logic type5_next_instruction_valid;
    logic [15:0] type5_probe_dreg;
    logic type5_probe_dreg_valid;
    logic [7:0] type5_px;
    logic type5_px_valid;
    logic type13_presented, type13_accepted, type13_retry;
    logic type13_data_complete, type13_instruction_complete;
    logic [23:0] type13_next_instruction;
    logic type13_next_instruction_valid;
    logic [15:0] type13_probe_dreg;
    logic type13_probe_dreg_valid;
    logic [7:0] type13_px;
    logic type13_px_valid;
    logic cache_fill, cache_fill_accepted;
    logic [13:0] cache_region_start;
    logic cache_region_start_valid;
    logic [4:0] cache_region_count;
    logic [2:0] bus_mode;
    logic issue_inhibit, bg_n, bus_relinquished;
    logic request_blocked, request_conflict, request_out_of_phase;
    logic [2:0] request_accepted, completion;
    logic [1:0] owner;
    logic pm_bus_active;
    logic address_oe, control_oe, data_oe;
    logic [13:0] pma;
    logic pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
    logic unused_observation;
    integer vector_file, scan_count, vector_count;

    assign {
        reset, phase, advance, br_n, halt_n, dmack,
        instruction_setup, instruction_setup_pc, instruction_setup_opcode,
        irq_n, automatic_pm_flow,
        type5_execute, type5_opcode, type5_next, type5_next_valid,
        type13_execute, type13_opcode, type13_next, type13_next_valid,
        pmd, pmd_valid,
        astat_setup, astat_setup_data,
        mstat_setup, mstat_setup_data,
        dreg_setup, dreg_setup_code, dreg_setup_data,
        af_setup, af_setup_data, mf_setup, mf_setup_data,
        sb_setup, sb_setup_data,
        dag_setup, dag_setup_kind, dag_setup_address, dag_setup_data,
        px_setup, px_setup_data,
        linear_probe_code, pm_probe_dreg_code, pm_probe_dag_address
    } = stimulus[273:0];

    assign actual_events = {
        11'h000,
        issue_boundary, client_execute_conflict, integration_conflict,
        automatic_pm_issue, automatic_pm_retire, automatic_pm_blocked,
        halt_mode, halt_recognized, halt_stop, halt_force_fetch,
        halt_resume, halt_release_blocked, halt_phase_hold,
        effective_advance, halted, halt_br_conflict,
        halt_attachment_conflict,
        linear_fetch_presented, linear_issue, linear_retire,
        type5_presented, type5_accepted, type5_retry,
        type5_data_complete, type5_instruction_complete,
        type5_next_instruction_valid,
        type5_next_instruction_valid
            ? type5_next_instruction : 24'h000000,
        type13_presented, type13_accepted, type13_retry,
        type13_data_complete, type13_instruction_complete,
        type13_next_instruction_valid,
        type13_next_instruction_valid
            ? type13_next_instruction : 24'h000000,
        cache_fill, cache_fill_accepted,
        bus_mode, issue_inhibit, bg_n, bus_relinquished,
        request_blocked, request_conflict, request_out_of_phase,
        request_accepted, completion, owner, pm_bus_active,
        address_oe, control_oe, data_oe,
        pma_valid, pma_valid ? pma : 14'h0000,
        pmda, pmda_valid, pms_n, pmrd_n, pmwr_n,
        pmd_write_data_valid,
        pmd_write_data_valid ? pmd_write_data : 24'h000000
    };

    assign unused_observation = ^linear_probe_data;

    always_comb begin
        assert (unused_observation == unused_observation);
    end

    assign actual_post = {
        18'h00000,
        linear_pc,
        linear_instruction_valid ? linear_opcode : 24'h000000,
        type5_probe_dreg_valid,
        type5_probe_dreg_valid ? type5_probe_dreg : 16'h0000,
        type5_px_valid, type5_px_valid ? type5_px : 8'h00,
        type13_probe_dreg_valid,
        type13_probe_dreg_valid ? type13_probe_dreg : 16'h0000,
        type13_px_valid, type13_px_valid ? type13_px : 8'h00,
        cache_region_start_valid, cache_region_start, cache_region_count
    };

    adsp2100_program_clients_owner_control_slice dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(advance), .br_n_i(br_n),
        .halt_n_i(halt_n), .dmack_i(dmack),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(instruction_setup_pc),
        .instruction_setup_opcode_i(instruction_setup_opcode),
        .irq_n_i(irq_n),
        .automatic_pm_flow_i(automatic_pm_flow),
        .type5_execute_i(type5_execute), .type5_opcode_i(type5_opcode),
        .type5_next_fetch_address_i(type5_next),
        .type5_next_fetch_address_valid_i(type5_next_valid),
        .type13_execute_i(type13_execute), .type13_opcode_i(type13_opcode),
        .type13_next_fetch_address_i(type13_next),
        .type13_next_fetch_address_valid_i(type13_next_valid),
        .pmd_read_data_i(pmd), .pmd_read_data_valid_i(pmd_valid),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .af_setup_write_i(af_setup), .af_setup_data_i(af_setup_data),
        .mf_setup_write_i(mf_setup), .mf_setup_data_i(mf_setup_data),
        .sb_setup_write_i(sb_setup), .sb_setup_data_i(sb_setup_data),
        .dag_setup_write_i(dag_setup), .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .px_setup_write_i(px_setup), .px_setup_data_i(px_setup_data),
        .linear_probe_code_i(linear_probe_code),
        .pm_probe_dreg_code_i(pm_probe_dreg_code),
        .pm_probe_dag_address_i(pm_probe_dag_address),
        .issue_boundary_o(issue_boundary),
        .client_execute_conflict_o(client_execute_conflict),
        .integration_conflict_o(integration_conflict),
        .automatic_pm_instruction_issue_o(automatic_pm_issue),
        .automatic_pm_instruction_retire_o(automatic_pm_retire),
        .automatic_pm_flow_blocked_o(automatic_pm_blocked),
        .halt_mode_o(halt_mode),
        .halt_recognized_o(halt_recognized),
        .halt_stop_event_o(halt_stop),
        .halt_force_fetch_issue_o(halt_force_fetch),
        .halt_resume_event_o(halt_resume),
        .halt_release_blocked_o(halt_release_blocked),
        .halt_phase_hold_o(halt_phase_hold),
        .effective_phase_advance_o(effective_advance),
        .halted_o(halted), .halt_br_conflict_o(halt_br_conflict),
        .halt_attachment_conflict_o(halt_attachment_conflict),
        .linear_fetch_request_presented_o(linear_fetch_presented),
        .linear_instruction_issue_o(linear_issue),
        .linear_retire_event_o(linear_retire),
        .linear_instruction_valid_o(linear_instruction_valid),
        .linear_pc_o(linear_pc), .linear_opcode_o(linear_opcode),
        .linear_probe_data_o(linear_probe_data),
        .type5_request_presented_o(type5_presented),
        .type5_request_accepted_o(type5_accepted),
        .type5_retry_pending_o(type5_retry),
        .type5_data_action_complete_o(type5_data_complete),
        .type5_instruction_complete_o(type5_instruction_complete),
        .type5_next_instruction_o(type5_next_instruction),
        .type5_next_instruction_valid_o(type5_next_instruction_valid),
        .type5_probe_dreg_data_o(type5_probe_dreg),
        .type5_probe_dreg_valid_o(type5_probe_dreg_valid),
        .type5_px_o(type5_px), .type5_px_valid_o(type5_px_valid),
        .type13_request_presented_o(type13_presented),
        .type13_request_accepted_o(type13_accepted),
        .type13_retry_pending_o(type13_retry),
        .type13_data_action_complete_o(type13_data_complete),
        .type13_instruction_complete_o(type13_instruction_complete),
        .type13_next_instruction_o(type13_next_instruction),
        .type13_next_instruction_valid_o(type13_next_instruction_valid),
        .type13_probe_dreg_data_o(type13_probe_dreg),
        .type13_probe_dreg_valid_o(type13_probe_dreg_valid),
        .type13_px_o(type13_px), .type13_px_valid_o(type13_px_valid),
        .cache_fill_o(cache_fill),
        .cache_fill_accepted_o(cache_fill_accepted),
        .cache_region_start_o(cache_region_start),
        .cache_region_start_valid_o(cache_region_start_valid),
        .cache_region_count_o(cache_region_count),
        .bus_mode_o(bus_mode), .issue_inhibit_o(issue_inhibit),
        .bg_n_o(bg_n), .bus_relinquished_o(bus_relinquished),
        .request_blocked_o(request_blocked),
        .request_conflict_o(request_conflict),
        .request_out_of_phase_o(request_out_of_phase),
        .request_accepted_o(request_accepted),
        .completion_event_o(completion), .owner_o(owner),
        .pm_bus_active_o(pm_bus_active),
        .pm_address_output_enable_o(address_oe),
        .pm_control_output_enable_o(control_oe),
        .pm_data_output_enable_o(data_oe),
        .pma_o(pma), .pma_valid_o(pma_valid),
        .pmda_o(pmda), .pmda_valid_o(pmda_valid),
        .pms_n_o(pms_n), .pmrd_n_o(pmrd_n), .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_post = '0;
        vector_file = $fopen(
            "build/program_clients_owner_control_vectors.txt", "r"
        );
        if (vector_file == 0)
            $fatal(1, "cannot open three-client/shared-cache vectors");
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file, "%h %h %h\n",
                stimulus, expected_events, expected_post
            );
            if (scan_count == 3) begin
                #2;
                if (actual_events !== expected_events)
                    $fatal(1, "three-client pre mismatch vector=%0d expected=%040x actual=%040x stimulus=%069x",
                           vector_count, expected_events, actual_events,
                           stimulus);
                #2 clk = 1'b1;
                #1;
                if (actual_post !== expected_post)
                    $fatal(1, "three-client post mismatch vector=%0d expected=%032x actual=%032x",
                           vector_count, expected_post, actual_post);
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50000) $fatal(1, "insufficient vectors");
        $display(
            "PASS three-client/shared-cache/BR-BG differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
