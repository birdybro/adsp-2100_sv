`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_linear_owner_control_slice;
    logic clk;
    logic [195:0] stimulus;
    logic [255:0] expected_events, actual_events;
    logic [191:0] expected_post, actual_post;

    logic reset, advance, br_n, instruction_setup;
    logic [3:0] irq_n;
    logic [2:0] phase;
    logic [13:0] setup_pc;
    logic [23:0] setup_opcode;
    logic type5_valid, type5_address_valid, type5_data_access;
    logic type5_write, type5_data_valid;
    logic [13:0] type5_address;
    logic [23:0] type5_data;
    logic type13_valid, type13_address_valid, type13_data_access;
    logic type13_write, type13_data_valid;
    logic [13:0] type13_address;
    logic [23:0] type13_data;
    logic [23:0] pmd_read_data;
    logic pmd_read_data_valid;
    logic [5:0] probe_code;

    logic issue_boundary, setup_accepted, fetch_presented, fetch_accepted;
    logic fetch_retry, instruction_issue, retire_event, instruction_valid;
    logic transaction_pending, unsupported, reserved, phase_conflict;
    logic attachment_conflict, integration_conflict, internal_conflict;
    logic provisional_source_extension;
    logic [13:0] pc;
    logic [23:0] opcode;
    logic [15:0] probe_data;
    logic [7:0] astat;
    logic [3:0] mstat;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic [13:0] cntr;
    logic cntr_valid;
    logic [7:0] px, sstat;
    logic alternate_bank;
    logic [2:0] count_stack_depth;
    logic count_stack_overflow;

    logic [2:0] bus_mode;
    logic bus_request_recognized, grant_assert, release_recognized;
    logic grant_release, resume, issue_inhibit, bg_n, bus_relinquished;
    logic request_blocked, request_conflict, request_out_of_phase;
    logic [2:0] request_accepted, completion;
    logic [1:0] owner;
    logic pm_bus_active, address_oe, control_oe, data_oe;
    logic [13:0] pma;
    logic pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
    logic unused_observation;
    integer vector_file, scan_count, vector_count;

    assign {
        reset, phase, advance, br_n, irq_n,
        instruction_setup, setup_pc, setup_opcode,
        type5_valid, type5_address, type5_address_valid,
        type5_data_access, type5_write, type5_data, type5_data_valid,
        type13_valid, type13_address, type13_address_valid,
        type13_data_access, type13_write, type13_data, type13_data_valid,
        pmd_read_data, pmd_read_data_valid, probe_code
    } = stimulus[165:0];

    assign actual_events = {
        130'h0,
        issue_boundary, setup_accepted, fetch_presented, fetch_accepted,
        fetch_retry, instruction_issue, retire_event, instruction_valid,
        transaction_pending, unsupported, reserved, phase_conflict,
        attachment_conflict, integration_conflict, internal_conflict,
        provisional_source_extension, reset ? 14'h0000 : pc,
        instruction_valid,
        instruction_valid ? opcode : 24'h000000,
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
        109'h0,
        bus_mode, instruction_valid, transaction_pending, pc,
        instruction_valid, instruction_valid ? opcode : 24'h000000,
        mstat, imask,
        cntr_valid, cntr_valid ? cntr : 14'h0000,
        sstat, alternate_bank, count_stack_depth,
        count_stack_overflow, owner, pm_bus_active
    };

    assign unused_observation = ^{probe_data, astat, icntl, px};

    always_comb begin
        assert (unused_observation == unused_observation);
    end

    adsp2100_linear_owner_control_slice dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(advance), .br_n_i(br_n),
        .irq_n_i(irq_n),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(setup_pc),
        .instruction_setup_opcode_i(setup_opcode),
        .type5_valid_i(type5_valid), .type5_address_i(type5_address),
        .type5_address_valid_i(type5_address_valid),
        .type5_data_access_i(type5_data_access),
        .type5_write_i(type5_write), .type5_write_data_i(type5_data),
        .type5_write_data_valid_i(type5_data_valid),
        .type13_valid_i(type13_valid), .type13_address_i(type13_address),
        .type13_address_valid_i(type13_address_valid),
        .type13_data_access_i(type13_data_access),
        .type13_write_i(type13_write), .type13_write_data_i(type13_data),
        .type13_write_data_valid_i(type13_data_valid),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .probe_code_i(probe_code),
        .issue_boundary_o(issue_boundary),
        .instruction_setup_accepted_o(setup_accepted),
        .fetch_request_presented_o(fetch_presented),
        .fetch_request_accepted_o(fetch_accepted),
        .fetch_retry_pending_o(fetch_retry),
        .instruction_issue_o(instruction_issue),
        .retire_event_o(retire_event),
        .instruction_valid_o(instruction_valid),
        .transaction_pending_o(transaction_pending),
        .unsupported_instruction_o(unsupported),
        .reserved_subencoding_o(reserved),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .provisional_source_extension_o(provisional_source_extension),
        .pc_o(pc), .opcode_o(opcode), .probe_data_o(probe_data),
        .astat_o(astat), .mstat_o(mstat), .icntl_o(icntl),
        .imask_o(imask), .cntr_o(cntr), .cntr_valid_o(cntr_valid),
        .px_o(px), .sstat_o(sstat), .alternate_bank_o(alternate_bank),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
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
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_post = '0;
        vector_file = $fopen(
            "build/linear_owner_control_vectors.txt", "r"
        );
        if (vector_file == 0)
            $fatal(1, "cannot open linear/shared-PM/BR-BG vectors");
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file, "%h %h %h\n",
                stimulus, expected_events, expected_post
            );
            if (scan_count == 3) begin
                #2;
                if (actual_events !== expected_events)
                    $fatal(1, "linear/shared-PM pre mismatch vector=%0d expected=%064x actual=%064x stimulus=%048x",
                           vector_count, expected_events, actual_events,
                           stimulus);
                #2 clk = 1'b1;
                #1;
                if (actual_post !== expected_post)
                    $fatal(1, "linear/shared-PM post mismatch vector=%0d expected=%048x actual=%048x",
                           vector_count, expected_post, actual_post);
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50000) $fatal(1, "insufficient vectors");
        $display(
            "PASS linear/shared-PM/BR-BG differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
