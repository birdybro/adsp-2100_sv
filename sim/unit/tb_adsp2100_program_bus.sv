`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_program_bus;
    logic        clk;
    logic [73:0] stimulus;
    logic [52:0] expected_pre;
    logic [69:0] expected_post;
    logic        reset;
    logic [2:0]  phase;
    logic        phase_advance;
    logic        request_valid;
    logic [13:0] request_address;
    logic        request_address_valid;
    logic        request_data_access;
    logic        request_write;
    logic [23:0] request_write_data;
    logic        request_write_data_valid;
    logic [23:0] pmd_read_data;
    logic        pmd_read_data_valid;
    logic        bus_relinquished;
    logic        request_ready;
    logic        request_accepted;
    logic        completion_event;
    logic        read_sample_event;
    logic        transaction_active;
    logic        response_valid;
    logic        response_write;
    logic [23:0] response_read_data;
    logic        response_read_data_valid;
    logic        pm_address_oe;
    logic        pm_control_oe;
    logic        pm_data_oe;
    logic [13:0] pma;
    logic        pma_valid;
    logic        pmda;
    logic        pmda_valid;
    logic        pms_n;
    logic        pmrd_n;
    logic        pmwr_n;
    logic [23:0] pmd_write_data;
    logic        pmd_write_data_valid;
    logic [13:0] descriptor_address;
    logic        descriptor_address_valid;
    logic        descriptor_data_access;
    logic        descriptor_write;
    logic [23:0] descriptor_write_data;
    logic        descriptor_write_data_valid;
    logic        exp_request_ready;
    logic        exp_request_accepted;
    logic        exp_completion_event;
    logic        exp_read_sample_event;
    logic        exp_pre_active;
    logic        exp_pm_address_oe;
    logic        exp_pm_control_oe;
    logic        exp_pm_data_oe;
    logic [13:0] exp_pma;
    logic        exp_pma_valid;
    logic        exp_pmda;
    logic        exp_pmda_valid;
    logic        exp_pms_n;
    logic        exp_pmrd_n;
    logic        exp_pmwr_n;
    logic [23:0] exp_pmd_write_data;
    logic        exp_pmd_write_data_valid;
    logic        exp_post_active;
    logic [13:0] exp_descriptor_address;
    logic        exp_descriptor_address_valid;
    logic        exp_descriptor_data_access;
    logic        exp_descriptor_write;
    logic [23:0] exp_descriptor_write_data;
    logic        exp_descriptor_write_data_valid;
    logic        exp_response_valid;
    logic        exp_response_write;
    logic [23:0] exp_response_read_data;
    logic        exp_response_read_data_valid;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset, phase, phase_advance, request_valid, request_address,
        request_address_valid, request_data_access, request_write,
        request_write_data, request_write_data_valid, pmd_read_data,
        pmd_read_data_valid, bus_relinquished
    } = stimulus;
    assign {
        exp_request_ready, exp_request_accepted, exp_completion_event,
        exp_read_sample_event, exp_pre_active,
        exp_pm_address_oe, exp_pm_control_oe, exp_pm_data_oe,
        exp_pma, exp_pma_valid, exp_pmda, exp_pmda_valid,
        exp_pms_n, exp_pmrd_n, exp_pmwr_n,
        exp_pmd_write_data, exp_pmd_write_data_valid
    } = expected_pre;
    assign {
        exp_post_active,
        exp_descriptor_address, exp_descriptor_address_valid,
        exp_descriptor_data_access, exp_descriptor_write,
        exp_descriptor_write_data, exp_descriptor_write_data_valid,
        exp_response_valid, exp_response_write,
        exp_response_read_data, exp_response_read_data_valid
    } = expected_post;

    adsp2100_program_bus dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .request_valid_i(request_valid),
        .request_address_i(request_address),
        .request_address_valid_i(request_address_valid),
        .request_data_access_i(request_data_access),
        .request_write_i(request_write),
        .request_write_data_i(request_write_data),
        .request_write_data_valid_i(request_write_data_valid),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .bus_relinquished_i(bus_relinquished),
        .request_ready_o(request_ready),
        .request_accepted_o(request_accepted),
        .completion_event_o(completion_event),
        .read_sample_event_o(read_sample_event),
        .transaction_active_o(transaction_active),
        .response_valid_o(response_valid),
        .response_write_o(response_write),
        .response_read_data_o(response_read_data),
        .response_read_data_valid_o(response_read_data_valid),
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
        .descriptor_address_o(descriptor_address),
        .descriptor_address_valid_o(descriptor_address_valid),
        .descriptor_data_access_o(descriptor_data_access),
        .descriptor_write_o(descriptor_write),
        .descriptor_write_data_o(descriptor_write_data),
        .descriptor_write_data_valid_o(descriptor_write_data_valid)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_pre = '0;
        expected_post = '0;
        vector_file = $fopen("build/program_bus_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open PM-bus phase vectors");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_pre,
                expected_post
            );
            if (scan_count == 3) begin
                #2;
                if ({
                    request_ready, request_accepted, completion_event,
                    read_sample_event, transaction_active,
                    pm_address_oe, pm_control_oe, pm_data_oe,
                    pma_valid, pmda, pmda_valid,
                    pms_n, pmrd_n, pmwr_n,
                    pmd_write_data_valid
                } !== {
                    exp_request_ready, exp_request_accepted,
                    exp_completion_event, exp_read_sample_event,
                    exp_pre_active, exp_pm_address_oe, exp_pm_control_oe,
                    exp_pm_data_oe, exp_pma_valid, exp_pmda,
                    exp_pmda_valid, exp_pms_n, exp_pmrd_n, exp_pmwr_n,
                    exp_pmd_write_data_valid
                }) begin
                    $fatal(
                        1,
                        "PM-bus pre-event mismatch vector=%0d actual=%014x expected=%014x stimulus=%019x",
                        vector_count,
                        {
                            request_ready, request_accepted,
                            completion_event, read_sample_event,
                            transaction_active, pm_address_oe,
                            pm_control_oe, pm_data_oe, pma, pma_valid,
                            pmda, pmda_valid, pms_n, pmrd_n, pmwr_n,
                            pmd_write_data, pmd_write_data_valid
                        },
                        expected_pre,
                        stimulus
                    );
                end
                if (exp_pma_valid && pma !== exp_pma)
                    $fatal(1, "PMA mismatch vector=%0d", vector_count);
                if (
                    exp_pmd_write_data_valid
                    && pmd_write_data !== exp_pmd_write_data
                ) $fatal(1, "PMD write mismatch vector=%0d", vector_count);
                #2 clk = 1'b1;
                #1;
                if ({
                    transaction_active,
                    descriptor_address_valid,
                    descriptor_data_access, descriptor_write,
                    descriptor_write_data_valid,
                    response_valid, response_write,
                    response_read_data_valid
                } !== {
                    exp_post_active, exp_descriptor_address_valid,
                    exp_descriptor_data_access, exp_descriptor_write,
                    exp_descriptor_write_data_valid, exp_response_valid,
                    exp_response_write, exp_response_read_data_valid
                }) begin
                    $fatal(
                        1,
                        "PM-bus post-state mismatch vector=%0d actual=%018x expected=%018x",
                        vector_count,
                        {
                            transaction_active,
                            descriptor_address, descriptor_address_valid,
                            descriptor_data_access, descriptor_write,
                            descriptor_write_data,
                            descriptor_write_data_valid,
                            response_valid, response_write,
                            response_read_data, response_read_data_valid
                        },
                        expected_post
                    );
                end
                if (
                    exp_descriptor_address_valid
                    && descriptor_address !== exp_descriptor_address
                ) $fatal(1, "descriptor address mismatch vector=%0d", vector_count);
                if (
                    exp_descriptor_write_data_valid
                    && descriptor_write_data !== exp_descriptor_write_data
                ) $fatal(1, "descriptor data mismatch vector=%0d", vector_count);
                if (
                    exp_response_read_data_valid
                    && response_read_data !== exp_response_read_data
                ) $fatal(1, "response data mismatch vector=%0d", vector_count);
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50_000) begin
            $fatal(1, "insufficient PM-bus vectors: %0d", vector_count);
        end
        $display(
            "PASS original ADSP-2100 PM-bus phase differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
