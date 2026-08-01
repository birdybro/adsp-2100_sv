`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_program_owner_bus_control;
    logic clk;
    logic [130:0] stimulus;
    logic [17:0] expected_control_pre;
    logic [89:0] expected_owner_pre;
    logic [32:0] expected_post;
    logic reset, advance, br_n;
    logic [2:0] phase, valid, address_valid;
    logic [13:0] address [0:2];
    logic type5_write, type13_write;
    logic [23:0] type5_write_data, type13_write_data;
    logic type5_write_data_valid, type13_write_data_valid;
    logic [23:0] read_data;
    logic read_data_valid;
    logic [2:0] bus_mode;
    logic state_three, bus_request_recognized, grant_assert;
    logic release_recognized, grant_release, resume;
    logic request_withdrawn, release_cancelled, issue_inhibit;
    logic normal_bus_relinquished, normal_bg_n, reset_br_request;
    logic bg_n, bus_relinquished;
    logic ready, blocked, conflict, out_of_phase;
    logic [2:0] accepted, completion, read_sample;
    logic [1:0] owner;
    logic active, response_valid, response_write, response_data_valid;
    logic [23:0] response_data;
    logic address_oe, control_oe, data_oe;
    logic [13:0] pma;
    logic pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
    integer vector_file, scan_count, vector_count;

    assign {
        reset, phase, advance, br_n,
        valid[0], address[0], address_valid[0],
        valid[1], address[1], address_valid[1], type5_write,
        type5_write_data, type5_write_data_valid,
        valid[2], address[2], address_valid[2], type13_write,
        type13_write_data, type13_write_data_valid,
        read_data, read_data_valid
    } = stimulus;

    adsp2100_program_owner_bus_control dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(advance), .br_n_i(br_n),
        .fetch_valid_i(valid[0]), .fetch_address_i(address[0]),
        .fetch_address_valid_i(address_valid[0]),
        .type5_valid_i(valid[1]), .type5_address_i(address[1]),
        .type5_address_valid_i(address_valid[1]),
        .type5_write_i(type5_write),
        .type5_write_data_i(type5_write_data),
        .type5_write_data_valid_i(type5_write_data_valid),
        .type13_valid_i(valid[2]), .type13_address_i(address[2]),
        .type13_address_valid_i(address_valid[2]),
        .type13_write_i(type13_write),
        .type13_write_data_i(type13_write_data),
        .type13_write_data_valid_i(type13_write_data_valid),
        .pmd_read_data_i(read_data),
        .pmd_read_data_valid_i(read_data_valid),
        .bus_mode_o(bus_mode), .state_three_boundary_o(state_three),
        .bus_request_recognized_o(bus_request_recognized),
        .grant_assert_event_o(grant_assert),
        .release_recognized_o(release_recognized),
        .grant_release_event_o(grant_release), .resume_event_o(resume),
        .request_withdrawn_o(request_withdrawn),
        .release_cancelled_o(release_cancelled),
        .issue_inhibit_o(issue_inhibit),
        .normal_bus_relinquished_o(normal_bus_relinquished),
        .normal_bg_n_o(normal_bg_n), .reset_br_request_o(reset_br_request),
        .bg_n_o(bg_n), .bus_relinquished_o(bus_relinquished),
        .request_ready_o(ready), .request_blocked_o(blocked),
        .request_conflict_o(conflict),
        .request_out_of_phase_o(out_of_phase),
        .request_accepted_o(accepted), .completion_event_o(completion),
        .read_sample_event_o(read_sample), .owner_o(owner),
        .transaction_active_o(active), .response_valid_o(response_valid),
        .response_write_o(response_write),
        .response_read_data_o(response_data),
        .response_read_data_valid_o(response_data_valid),
        .pm_address_output_enable_o(address_oe),
        .pm_control_output_enable_o(control_oe),
        .pm_data_output_enable_o(data_oe), .pma_o(pma),
        .pma_valid_o(pma_valid), .pmda_o(pmda),
        .pmda_valid_o(pmda_valid), .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n), .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_control_pre = '0;
        expected_owner_pre = '0;
        expected_post = '0;
        vector_file = $fopen(
            "build/program_owner_bus_control_vectors.txt", "r"
        );
        if (vector_file == 0)
            $fatal(1, "cannot open shared-PM-owner/BR-BG vectors");
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h %h\n",
                stimulus,
                expected_control_pre,
                expected_owner_pre,
                expected_post
            );
            if (scan_count == 4) begin
                #2;
                if ({
                    bus_mode, state_three, bus_request_recognized,
                    grant_assert, release_recognized, grant_release, resume,
                    request_withdrawn, release_cancelled, issue_inhibit,
                    normal_bus_relinquished, normal_bg_n, reset_br_request,
                    bg_n, bus_relinquished, blocked
                } !== expected_control_pre)
                    $fatal(1, "shared-PM-owner/BR-BG control mismatch vector=%0d",
                           vector_count);
                if ({
                    ready, conflict, out_of_phase, accepted, completion,
                    read_sample, owner, active, response_valid, response_write,
                    response_data_valid, address_oe, control_oe, data_oe,
                    pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n,
                    pmd_write_data_valid
                } !== {
                    expected_owner_pre[89:73], expected_owner_pre[48:45],
                    expected_owner_pre[30:25], expected_owner_pre[0]
                })
                    $fatal(1, "shared-PM-owner/BR-BG pre mismatch vector=%0d actual=%023x expected=%023x",
                           vector_count, {
                           ready, conflict, out_of_phase, accepted, completion,
                           read_sample, owner, active, response_valid,
                           response_write, response_data, response_data_valid,
                           address_oe, control_oe, data_oe, pma, pma_valid,
                           pmda, pmda_valid, pms_n, pmrd_n, pmwr_n,
                           pmd_write_data, pmd_write_data_valid
                           }, expected_owner_pre);
                if (expected_owner_pre[48]
                    && response_data !== expected_owner_pre[72:49])
                    $fatal(1, "shared-PM-owner/BR-BG response mismatch vector=%0d",
                           vector_count);
                if (expected_owner_pre[30]
                    && pma !== expected_owner_pre[44:31])
                    $fatal(1, "shared-PM-owner/BR-BG address mismatch vector=%0d",
                           vector_count);
                if (expected_owner_pre[0]
                    && pmd_write_data !== expected_owner_pre[24:1])
                    $fatal(1, "shared-PM-owner/BR-BG write mismatch vector=%0d",
                           vector_count);
                #2 clk = 1'b1;
                #1;
                if ({
                    bus_mode, owner, active, response_valid, response_write,
                    response_data_valid
                } !== {expected_post[32:25], expected_post[0]})
                    $fatal(1, "shared-PM-owner/BR-BG post mismatch vector=%0d",
                           vector_count);
                if (expected_post[0]
                    && response_data !== expected_post[24:1])
                    $fatal(1, "shared-PM-owner/BR-BG post response mismatch vector=%0d",
                           vector_count);
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50000) $fatal(1, "insufficient vectors");
        $display(
            "PASS shared-PM-owner/BR-BG differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
