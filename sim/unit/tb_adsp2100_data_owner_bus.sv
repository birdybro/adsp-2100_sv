`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_data_owner_bus;
    logic clk;
    logic [91:0] stimulus;
    logic [75:0] expected_pre;
    logic [56:0] expected_post;
    logic reset; logic [2:0] phase; logic advance;
    logic [1:0] valid; logic [13:0] address [0:1];
    logic [1:0] address_valid, write;
    logic [15:0] write_data [0:1]; logic [1:0] write_data_valid;
    logic dm_ack; logic [15:0] read_data; logic read_data_valid;
    logic relinquished;
    logic ready, conflict, out_of_phase;
    logic [1:0] accepted, dmack_sample, dmack_accepted;
    logic [1:0] wait_extension, completion, read_sample;
    logic [1:0] owner; logic active, waiting;
    logic response_valid, response_write;
    logic [15:0] response_data; logic response_data_valid;
    logic address_oe, control_oe, data_oe;
    logic [13:0] dma; logic dma_valid, dms_n, dmrd_n, dmwr_n;
    logic [15:0] dmd_write_data; logic dmd_write_data_valid;
    logic exp_ready, exp_conflict, exp_out_of_phase;
    logic [1:0] exp_accepted, exp_dmack_sample, exp_dmack_accepted;
    logic [1:0] exp_wait_extension, exp_completion, exp_read_sample;
    logic [1:0] exp_owner; logic exp_active, exp_waiting;
    logic exp_address_oe, exp_control_oe, exp_data_oe;
    logic [13:0] exp_dma; logic exp_dma_valid;
    logic exp_dms_n, exp_dmrd_n, exp_dmwr_n;
    logic [15:0] exp_dmd_write_data; logic exp_dmd_write_data_valid;
    logic exp_response_valid, exp_response_write;
    logic [15:0] exp_response_data; logic exp_response_data_valid;
    logic [1:0] exp_post_owner; logic exp_post_active;
    logic [13:0] exp_descriptor_address;
    logic exp_descriptor_address_valid, exp_descriptor_write;
    logic [15:0] exp_descriptor_write_data;
    logic exp_descriptor_write_data_valid, exp_post_waiting;
    logic exp_post_acknowledged, exp_post_response_valid;
    logic exp_post_response_write;
    logic [15:0] exp_post_response_data;
    logic exp_post_response_data_valid;
    integer vector_file, scan_count, vector_count;

    assign {
        reset, phase, advance,
        valid[0], address[0], address_valid[0], write[0],
        write_data[0], write_data_valid[0],
        valid[1], address[1], address_valid[1], write[1],
        write_data[1], write_data_valid[1],
        dm_ack, read_data, read_data_valid, relinquished
    } = stimulus;
    assign {
        exp_ready, exp_conflict, exp_out_of_phase, exp_accepted,
        exp_dmack_sample, exp_dmack_accepted, exp_wait_extension,
        exp_completion, exp_read_sample, exp_owner, exp_active, exp_waiting,
        exp_address_oe, exp_control_oe, exp_data_oe, exp_dma, exp_dma_valid,
        exp_dms_n, exp_dmrd_n, exp_dmwr_n, exp_dmd_write_data,
        exp_dmd_write_data_valid, exp_response_valid, exp_response_write,
        exp_response_data, exp_response_data_valid
    } = expected_pre;
    assign {
        exp_post_owner, exp_post_active, exp_descriptor_address,
        exp_descriptor_address_valid, exp_descriptor_write,
        exp_descriptor_write_data, exp_descriptor_write_data_valid,
        exp_post_waiting, exp_post_acknowledged, exp_post_response_valid,
        exp_post_response_write, exp_post_response_data,
        exp_post_response_data_valid
    } = expected_post;

    adsp2100_data_owner_bus dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(advance),
        .fetched_valid_i(valid[0]), .fetched_address_i(address[0]),
        .fetched_address_valid_i(address_valid[0]),
        .fetched_write_i(write[0]), .fetched_write_data_i(write_data[0]),
        .fetched_write_data_valid_i(write_data_valid[0]),
        .companion_valid_i(valid[1]), .companion_address_i(address[1]),
        .companion_address_valid_i(address_valid[1]),
        .companion_write_i(write[1]),
        .companion_write_data_i(write_data[1]),
        .companion_write_data_valid_i(write_data_valid[1]),
        .dm_ack_i(dm_ack), .dmd_read_data_i(read_data),
        .dmd_read_data_valid_i(read_data_valid),
        .bus_relinquished_i(relinquished), .request_ready_o(ready),
        .request_conflict_o(conflict),
        .request_out_of_phase_o(out_of_phase),
        .request_accepted_o(accepted),
        .dmack_sample_event_o(dmack_sample),
        .dmack_accepted_o(dmack_accepted),
        .wait_extension_event_o(wait_extension),
        .completion_event_o(completion), .read_sample_event_o(read_sample),
        .owner_o(owner), .transaction_active_o(active), .waiting_o(waiting),
        .response_valid_o(response_valid),
        .response_write_o(response_write),
        .response_read_data_o(response_data),
        .response_read_data_valid_o(response_data_valid),
        .dm_address_output_enable_o(address_oe),
        .dm_control_output_enable_o(control_oe),
        .dm_data_output_enable_o(data_oe), .dma_o(dma),
        .dma_valid_o(dma_valid), .dms_n_o(dms_n), .dmrd_n_o(dmrd_n),
        .dmwr_n_o(dmwr_n), .dmd_write_data_o(dmd_write_data),
        .dmd_write_data_valid_o(dmd_write_data_valid)
    );

    initial begin
        clk = 1'b0; stimulus = '0; expected_pre = '0; expected_post = '0;
        vector_file = $fopen("build/data_owner_bus_vectors.txt", "r");
        if (vector_file == 0) $fatal(1, "cannot open shared-DM-owner vectors");
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(vector_file, "%h %h %h\n",
                                 stimulus, expected_pre, expected_post);
            if (scan_count == 3) begin
                #2;
                if ({
                    ready, conflict, out_of_phase, accepted, dmack_sample,
                    dmack_accepted, wait_extension, completion, read_sample,
                    owner, active, waiting, address_oe, control_oe, data_oe,
                    dma_valid, dms_n, dmrd_n, dmwr_n, dmd_write_data_valid,
                    response_valid, response_write, response_data_valid
                } !== {
                    exp_ready, exp_conflict, exp_out_of_phase, exp_accepted,
                    exp_dmack_sample, exp_dmack_accepted, exp_wait_extension,
                    exp_completion, exp_read_sample, exp_owner, exp_active,
                    exp_waiting, exp_address_oe, exp_control_oe, exp_data_oe,
                    exp_dma_valid, exp_dms_n, exp_dmrd_n, exp_dmwr_n,
                    exp_dmd_write_data_valid, exp_response_valid,
                    exp_response_write, exp_response_data_valid
                }) $fatal(1, "shared-DM-owner pre-event mismatch vector=%0d actual=%019x expected=%019x stimulus=%023x",
                           vector_count, {ready, conflict, out_of_phase,
                           accepted, dmack_sample, dmack_accepted,
                           wait_extension, completion, read_sample, owner,
                           active, waiting, address_oe, control_oe, data_oe,
                           dma, dma_valid, dms_n, dmrd_n, dmwr_n,
                           dmd_write_data, dmd_write_data_valid,
                           response_valid, response_write, response_data,
                           response_data_valid}, expected_pre, stimulus);
                if (exp_dma_valid && dma !== exp_dma)
                    $fatal(1, "shared-DM-owner DMA mismatch vector=%0d", vector_count);
                if (exp_dmd_write_data_valid
                    && dmd_write_data !== exp_dmd_write_data)
                    $fatal(1, "shared-DM-owner DMD write mismatch vector=%0d", vector_count);
                if (exp_response_data_valid
                    && response_data !== exp_response_data)
                    $fatal(1, "shared-DM-owner response mismatch vector=%0d", vector_count);
                #2 clk = 1'b1; #1;
                if ({
                    owner, active, dut.data_bus.address_valid_q,
                    dut.data_bus.write_q, dut.data_bus.write_data_valid_q,
                    waiting, dut.data_bus.acknowledged_q, response_valid,
                    response_write, response_data_valid
                } !== {
                    exp_post_owner, exp_post_active,
                    exp_descriptor_address_valid, exp_descriptor_write,
                    exp_descriptor_write_data_valid, exp_post_waiting,
                    exp_post_acknowledged, exp_post_response_valid,
                    exp_post_response_write, exp_post_response_data_valid
                }) $fatal(1, "shared-DM-owner post-state mismatch vector=%0d actual=%015x expected=%015x",
                           vector_count, {owner, active,
                           dut.data_bus.address_q, dut.data_bus.address_valid_q,
                           dut.data_bus.write_q, dut.data_bus.write_data_q,
                           dut.data_bus.write_data_valid_q, waiting,
                           dut.data_bus.acknowledged_q, response_valid,
                           response_write, response_data, response_data_valid},
                           expected_post);
                if (exp_descriptor_address_valid
                    && dut.data_bus.address_q !== exp_descriptor_address)
                    $fatal(1, "shared-DM-owner descriptor address mismatch vector=%0d", vector_count);
                if (exp_descriptor_write_data_valid
                    && dut.data_bus.write_data_q !== exp_descriptor_write_data)
                    $fatal(1, "shared-DM-owner descriptor data mismatch vector=%0d", vector_count);
                if (exp_post_response_data_valid
                    && response_data !== exp_post_response_data)
                    $fatal(1, "shared-DM-owner post response mismatch vector=%0d", vector_count);
                #3 clk = 1'b0; vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50_000) $fatal(1, "insufficient shared-DM-owner vectors");
        $display("PASS shared-DM-owner differential: %0d clocks", vector_count);
        $finish;
    end
endmodule

`default_nettype wire
