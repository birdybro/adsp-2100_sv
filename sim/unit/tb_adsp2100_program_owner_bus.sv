`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_program_owner_bus;
    logic clk;
    logic [132:0] stimulus;
    logic [89:0] expected_pre;
    logic [29:0] expected_post;
    logic reset; logic [2:0] phase; logic advance;
    logic [2:0] valid; logic [13:0] address [0:2];
    logic [2:0] address_valid;
    logic type5_data_access, type13_data_access;
    logic type5_write, type13_write;
    logic [23:0] type5_write_data, type13_write_data;
    logic type5_write_data_valid, type13_write_data_valid;
    logic [23:0] read_data; logic read_data_valid; logic relinquished;
    logic ready, conflict, out_of_phase;
    logic [2:0] accepted, completion, read_sample;
    logic [1:0] owner; logic active;
    logic response_valid, response_write;
    logic [23:0] response_data; logic response_data_valid;
    logic address_oe, control_oe, data_oe;
    logic [13:0] pma; logic pma_valid, pmda, pmda_valid;
    logic pms_n, pmrd_n, pmwr_n;
    logic [23:0] pmd_write_data; logic pmd_write_data_valid;
    integer vector_file, scan_count, vector_count;

    assign {reset, phase, advance,
        valid[0], address[0], address_valid[0],
        valid[1], address[1], address_valid[1], type5_data_access, type5_write,
        type5_write_data, type5_write_data_valid,
        valid[2], address[2], address_valid[2], type13_data_access, type13_write,
        type13_write_data, type13_write_data_valid,
        read_data, read_data_valid, relinquished} = stimulus;

    adsp2100_program_owner_bus dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase), .phase_advance_i(advance),
        .fetch_valid_i(valid[0]), .fetch_address_i(address[0]),
        .fetch_address_valid_i(address_valid[0]),
        .type5_valid_i(valid[1]), .type5_address_i(address[1]),
        .type5_address_valid_i(address_valid[1]),
        .type5_data_access_i(type5_data_access), .type5_write_i(type5_write),
        .type5_write_data_i(type5_write_data),
        .type5_write_data_valid_i(type5_write_data_valid),
        .type13_valid_i(valid[2]), .type13_address_i(address[2]),
        .type13_address_valid_i(address_valid[2]),
        .type13_data_access_i(type13_data_access), .type13_write_i(type13_write),
        .type13_write_data_i(type13_write_data),
        .type13_write_data_valid_i(type13_write_data_valid),
        .pmd_read_data_i(read_data), .pmd_read_data_valid_i(read_data_valid),
        .bus_relinquished_i(relinquished), .request_ready_o(ready),
        .request_conflict_o(conflict), .request_out_of_phase_o(out_of_phase),
        .request_accepted_o(accepted), .completion_event_o(completion),
        .read_sample_event_o(read_sample), .owner_o(owner),
        .transaction_active_o(active), .response_valid_o(response_valid),
        .response_write_o(response_write), .response_read_data_o(response_data),
        .response_read_data_valid_o(response_data_valid),
        .pm_address_output_enable_o(address_oe),
        .pm_control_output_enable_o(control_oe), .pm_data_output_enable_o(data_oe),
        .pma_o(pma), .pma_valid_o(pma_valid), .pmda_o(pmda),
        .pmda_valid_o(pmda_valid), .pms_n_o(pms_n), .pmrd_n_o(pmrd_n),
        .pmwr_n_o(pmwr_n), .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );

    initial begin
        clk = 0; stimulus = '0; expected_pre = '0; expected_post = '0;
        vector_file = $fopen("build/program_owner_bus_vectors.txt", "r");
        if (vector_file == 0) $fatal(1, "cannot open shared-PM-owner vectors");
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(vector_file, "%h %h %h\n",
                                 stimulus, expected_pre, expected_post);
            if (scan_count == 3) begin
                #2;
                if ({ready, conflict, out_of_phase, accepted, completion,
                     read_sample, owner, active, response_valid, response_write,
                     response_data_valid, address_oe, control_oe, data_oe,
                     pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n,
                     pmd_write_data_valid} !==
                    {expected_pre[89:73], expected_pre[48:45],
                     expected_pre[30:25], expected_pre[0]})
                    $fatal(1, "shared-PM-owner pre mismatch vector=%0d actual=%023x expected=%023x",
                           vector_count, {ready, conflict, out_of_phase, accepted,
                           completion, read_sample, owner, active, response_valid,
                           response_write, response_data, response_data_valid,
                           address_oe, control_oe, data_oe, pma, pma_valid, pmda,
                           pmda_valid, pms_n, pmrd_n, pmwr_n, pmd_write_data,
                           pmd_write_data_valid}, expected_pre);
                if (expected_pre[48] && response_data !== expected_pre[72:49])
                    $fatal(1, "shared-PM-owner response mismatch vector=%0d", vector_count);
                if (expected_pre[30] && pma !== expected_pre[44:31])
                    $fatal(1, "shared-PM-owner address mismatch vector=%0d", vector_count);
                if (expected_pre[0] && pmd_write_data !== expected_pre[24:1])
                    $fatal(1, "shared-PM-owner write-data mismatch vector=%0d", vector_count);
                #2 clk = 1; #1;
                if ({owner, active, response_valid, response_write,
                     response_data_valid} !==
                    {expected_post[29:25], expected_post[0]})
                    $fatal(1, "shared-PM-owner post mismatch vector=%0d", vector_count);
                if (expected_post[0] && response_data !== expected_post[24:1])
                    $fatal(1, "shared-PM-owner post response mismatch vector=%0d", vector_count);
                #3 clk = 0; vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50000) $fatal(1, "insufficient vectors");
        $display("PASS shared-PM-owner differential: %0d clocks", vector_count);
        $finish;
    end
endmodule

`default_nettype wire
