`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_data_bus;
    logic        clk;
    logic [57:0] stimulus;
    logic [46:0] expected_pre;
    logic [54:0] expected_post;
    logic        reset;
    logic [2:0]  phase;
    logic        phase_advance;
    logic        request_valid;
    logic [13:0] request_address;
    logic        request_address_valid;
    logic        request_write;
    logic [15:0] request_write_data;
    logic        request_write_data_valid;
    logic        dm_ack;
    logic [15:0] dmd_read_data;
    logic        dmd_read_data_valid;
    logic        bus_relinquished;
    logic        request_ready;
    logic        request_accepted;
    logic        dmack_sample_event;
    logic        dmack_accepted;
    logic        wait_extension_event;
    logic        completion_event;
    logic        read_sample_event;
    logic        transaction_active;
    logic        waiting;
    logic        response_valid;
    logic        response_write;
    logic [15:0] response_read_data;
    logic        response_read_data_valid;
    logic        dm_address_oe;
    logic        dm_control_oe;
    logic        dm_data_oe;
    logic [13:0] dma;
    logic        dma_valid;
    logic        dms_n;
    logic        dmrd_n;
    logic        dmwr_n;
    logic [15:0] dmd_write_data;
    logic        dmd_write_data_valid;
    logic [13:0] descriptor_address;
    logic        descriptor_address_valid;
    logic        descriptor_write;
    logic [15:0] descriptor_write_data;
    logic        descriptor_write_data_valid;
    logic        exp_request_ready;
    logic        exp_request_accepted;
    logic        exp_dmack_sample_event;
    logic        exp_dmack_accepted;
    logic        exp_wait_extension_event;
    logic        exp_completion_event;
    logic        exp_read_sample_event;
    logic        exp_pre_active;
    logic        exp_waiting;
    logic        exp_dm_address_oe;
    logic        exp_dm_control_oe;
    logic        exp_dm_data_oe;
    logic [13:0] exp_dma;
    logic        exp_dma_valid;
    logic        exp_dms_n;
    logic        exp_dmrd_n;
    logic        exp_dmwr_n;
    logic [15:0] exp_dmd_write_data;
    logic        exp_dmd_write_data_valid;
    logic        exp_post_active;
    logic [13:0] exp_descriptor_address;
    logic        exp_descriptor_address_valid;
    logic        exp_descriptor_write;
    logic [15:0] exp_descriptor_write_data;
    logic        exp_descriptor_write_data_valid;
    logic        exp_post_waiting;
    logic        exp_post_acknowledged;
    logic        exp_response_valid;
    logic        exp_response_write;
    logic [15:0] exp_response_read_data;
    logic        exp_response_read_data_valid;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset, phase, phase_advance, request_valid, request_address,
        request_address_valid, request_write, request_write_data,
        request_write_data_valid, dm_ack, dmd_read_data,
        dmd_read_data_valid, bus_relinquished
    } = stimulus;
    assign {
        exp_request_ready, exp_request_accepted,
        exp_dmack_sample_event, exp_dmack_accepted,
        exp_wait_extension_event, exp_completion_event,
        exp_read_sample_event, exp_pre_active, exp_waiting,
        exp_dm_address_oe, exp_dm_control_oe, exp_dm_data_oe,
        exp_dma, exp_dma_valid, exp_dms_n, exp_dmrd_n, exp_dmwr_n,
        exp_dmd_write_data, exp_dmd_write_data_valid
    } = expected_pre;
    assign {
        exp_post_active, exp_descriptor_address,
        exp_descriptor_address_valid, exp_descriptor_write,
        exp_descriptor_write_data, exp_descriptor_write_data_valid,
        exp_post_waiting, exp_post_acknowledged,
        exp_response_valid, exp_response_write,
        exp_response_read_data, exp_response_read_data_valid
    } = expected_post;

    adsp2100_data_bus dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .request_valid_i(request_valid),
        .request_address_i(request_address),
        .request_address_valid_i(request_address_valid),
        .request_write_i(request_write),
        .request_write_data_i(request_write_data),
        .request_write_data_valid_i(request_write_data_valid),
        .dm_ack_i(dm_ack),
        .dmd_read_data_i(dmd_read_data),
        .dmd_read_data_valid_i(dmd_read_data_valid),
        .bus_relinquished_i(bus_relinquished),
        .request_ready_o(request_ready),
        .request_accepted_o(request_accepted),
        .dmack_sample_event_o(dmack_sample_event),
        .dmack_accepted_o(dmack_accepted),
        .wait_extension_event_o(wait_extension_event),
        .completion_event_o(completion_event),
        .read_sample_event_o(read_sample_event),
        .transaction_active_o(transaction_active),
        .waiting_o(waiting),
        .response_valid_o(response_valid),
        .response_write_o(response_write),
        .response_read_data_o(response_read_data),
        .response_read_data_valid_o(response_read_data_valid),
        .dm_address_output_enable_o(dm_address_oe),
        .dm_control_output_enable_o(dm_control_oe),
        .dm_data_output_enable_o(dm_data_oe),
        .dma_o(dma),
        .dma_valid_o(dma_valid),
        .dms_n_o(dms_n),
        .dmrd_n_o(dmrd_n),
        .dmwr_n_o(dmwr_n),
        .dmd_write_data_o(dmd_write_data),
        .dmd_write_data_valid_o(dmd_write_data_valid),
        .descriptor_address_o(descriptor_address),
        .descriptor_address_valid_o(descriptor_address_valid),
        .descriptor_write_o(descriptor_write),
        .descriptor_write_data_o(descriptor_write_data),
        .descriptor_write_data_valid_o(descriptor_write_data_valid)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_pre = '0;
        expected_post = '0;
        vector_file = $fopen("build/data_bus_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open DM-bus phase vectors");
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
                    request_ready, request_accepted,
                    dmack_sample_event, dmack_accepted,
                    wait_extension_event, completion_event,
                    read_sample_event, transaction_active, waiting,
                    dm_address_oe, dm_control_oe, dm_data_oe,
                    dma_valid, dms_n, dmrd_n, dmwr_n,
                    dmd_write_data_valid
                } !== {
                    exp_request_ready, exp_request_accepted,
                    exp_dmack_sample_event, exp_dmack_accepted,
                    exp_wait_extension_event, exp_completion_event,
                    exp_read_sample_event, exp_pre_active, exp_waiting,
                    exp_dm_address_oe, exp_dm_control_oe, exp_dm_data_oe,
                    exp_dma_valid, exp_dms_n, exp_dmrd_n, exp_dmwr_n,
                    exp_dmd_write_data_valid
                }) begin
                    $fatal(
                        1,
                        "DM-bus pre-event mismatch vector=%0d actual=%012x expected=%012x stimulus=%015x",
                        vector_count,
                        {
                            request_ready, request_accepted,
                            dmack_sample_event, dmack_accepted,
                            wait_extension_event, completion_event,
                            read_sample_event, transaction_active, waiting,
                            dm_address_oe, dm_control_oe, dm_data_oe,
                            dma, dma_valid, dms_n, dmrd_n, dmwr_n,
                            dmd_write_data, dmd_write_data_valid
                        },
                        expected_pre,
                        stimulus
                    );
                end
                if (exp_dma_valid && dma !== exp_dma)
                    $fatal(1, "DMA mismatch vector=%0d", vector_count);
                if (
                    exp_dmd_write_data_valid
                    && dmd_write_data !== exp_dmd_write_data
                ) $fatal(1, "DMD write mismatch vector=%0d", vector_count);
                #2 clk = 1'b1;
                #1;
                if ({
                    transaction_active, descriptor_address_valid,
                    descriptor_write, descriptor_write_data_valid,
                    waiting, dut.acknowledged_q,
                    response_valid, response_write,
                    response_read_data_valid
                } !== {
                    exp_post_active, exp_descriptor_address_valid,
                    exp_descriptor_write, exp_descriptor_write_data_valid,
                    exp_post_waiting, exp_post_acknowledged,
                    exp_response_valid, exp_response_write,
                    exp_response_read_data_valid
                }) begin
                    $fatal(
                        1,
                        "DM-bus post-state mismatch vector=%0d actual=%014x expected=%014x",
                        vector_count,
                        {
                            transaction_active, descriptor_address,
                            descriptor_address_valid, descriptor_write,
                            descriptor_write_data,
                            descriptor_write_data_valid, waiting,
                            dut.acknowledged_q, response_valid,
                            response_write, response_read_data,
                            response_read_data_valid
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
            $fatal(1, "insufficient DM-bus vectors: %0d", vector_count);
        end
        $display(
            "PASS original ADSP-2100 DM-bus phase differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
