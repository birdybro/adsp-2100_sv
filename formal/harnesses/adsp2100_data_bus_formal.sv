`default_nettype none

module adsp2100_data_bus_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        request_valid,
    input logic [13:0] request_address,
    input logic        request_address_valid,
    input logic        request_write,
    input logic [15:0] request_write_data,
    input logic        request_write_data_valid,
    input logic        dm_ack,
    input logic [15:0] dmd_read_data,
    input logic        dmd_read_data_valid,
    input logic        bus_relinquished
);
    import adsp2100_pkg::*;

    logic request_ready;
    logic request_accepted;
    logic dmack_sample_event;
    logic dmack_accepted;
    logic wait_extension_event;
    logic completion_event;
    logic read_sample_event;
    logic transaction_active;
    logic waiting;
    logic response_valid;
    logic response_write;
    logic [15:0] response_read_data;
    logic response_read_data_valid;
    logic address_oe;
    logic control_oe;
    logic data_oe;
    logic [13:0] dma;
    logic dma_valid;
    logic dms_n;
    logic dmrd_n;
    logic dmwr_n;
    logic [15:0] dmd_write_data;
    logic dmd_write_data_valid;
    logic [13:0] descriptor_address;
    logic descriptor_address_valid;
    logic descriptor_write;
    logic [15:0] descriptor_write_data;
    logic descriptor_write_data_valid;
    logic strobe_phase;
    logic write_drive_phase;
    logic past_valid;
    logic unused_observation;

    assign strobe_phase = waiting || (
        phase == PHASE_STATE_4 || phase == PHASE_STATE_5
        || phase == PHASE_STATE_6 || phase == PHASE_STATE_7
    );
    assign write_drive_phase = waiting || (
        phase == PHASE_STATE_5 || phase == PHASE_STATE_6
        || phase == PHASE_STATE_7 || phase == PHASE_STATE_8
    );
    assign unused_observation = ^{
        dma, dmd_write_data, response_read_data, descriptor_address,
        descriptor_write_data
    };

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
        .dm_address_output_enable_o(address_oe),
        .dm_control_output_enable_o(control_oe),
        .dm_data_output_enable_o(data_oe),
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

    initial past_valid = 1'b0;

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (request_ready == (
            !reset && !bus_relinquished && phase_advance
            && phase == PHASE_STATE_8
            && (!transaction_active || response_valid)
        ));
        assert (request_accepted == (request_ready && request_valid));
        assert (dmack_sample_event == (
            !reset && !bus_relinquished && transaction_active
            && !response_valid && phase_advance
            && phase == PHASE_STATE_6
        ));
        assert (dmack_accepted == (dmack_sample_event && dm_ack));
        assert (wait_extension_event == (dmack_sample_event && !dm_ack));
        assert (completion_event == (
            !reset && !bus_relinquished && transaction_active
            && !response_valid && phase_advance
            && phase == PHASE_STATE_7
            && dut.acknowledged_q && !waiting
        ));
        assert (read_sample_event
            == (completion_event && !descriptor_write));
        assert (!(~dmrd_n && ~dmwr_n));
        assert (address_oe == control_oe);
        assert (dms_n == !control_oe);
        assert (dma_valid == (address_oe && descriptor_address_valid));
        assert (~dmrd_n == (
            control_oe && !response_valid && !descriptor_write
            && strobe_phase
        ));
        assert (~dmwr_n == (
            control_oe && !response_valid && descriptor_write
            && strobe_phase
        ));
        assert (data_oe == (
            control_oe && !response_valid && descriptor_write
            && write_drive_phase
        ));
        assert (dmd_write_data_valid
            == (data_oe && descriptor_write_data_valid));
        assert (!response_read_data_valid
            || (response_valid && !response_write));
        if (waiting && !bus_relinquished && !reset) begin
            assert (transaction_active && !response_valid);
            assert (!completion_event && !request_ready);
            assert (!dmrd_n || !dmwr_n);
        end
        if (bus_relinquished || reset) begin
            assert (!address_oe && !control_oe && !data_oe);
            assert (dms_n && dmrd_n && dmwr_n);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && !reset && !$past(reset)) begin
            if ($past(request_ready)) begin
                assert (transaction_active == $past(request_valid));
                assert (!response_valid && !waiting);
                assert (!dut.acknowledged_q);
                if ($past(request_valid)) begin
                    assert (descriptor_address == $past(request_address));
                    assert (descriptor_address_valid
                        == $past(request_address_valid));
                    assert (descriptor_write == $past(request_write));
                    assert (descriptor_write_data
                        == $past(request_write_data));
                    assert (descriptor_write_data_valid
                        == $past(request_write_data_valid));
                end
            end
            if ($past(dmack_sample_event)) begin
                assert (waiting == !$past(dm_ack));
                assert (dut.acknowledged_q == $past(dm_ack));
            end
            if ($past(completion_event)) begin
                assert (response_valid && !waiting);
                assert (response_write == $past(descriptor_write));
                if (!$past(descriptor_write)) begin
                    assert (response_read_data == $past(dmd_read_data));
                    assert (response_read_data_valid
                        == $past(dmd_read_data_valid));
                end
            end
            if ($past(bus_relinquished) || !$past(phase_advance)) begin
                assert (transaction_active == $past(transaction_active));
                assert (descriptor_address == $past(descriptor_address));
                assert (descriptor_address_valid
                    == $past(descriptor_address_valid));
                assert (descriptor_write == $past(descriptor_write));
                assert (descriptor_write_data
                    == $past(descriptor_write_data));
                assert (descriptor_write_data_valid
                    == $past(descriptor_write_data_valid));
                assert (waiting == $past(waiting));
                assert (response_valid == $past(response_valid));
            end
        end
        cover (past_valid && $past(wait_extension_event) && waiting);
        cover (past_valid && $past(completion_event) && response_valid);
        cover (request_accepted && transaction_active);
    end
endmodule

`default_nettype wire
