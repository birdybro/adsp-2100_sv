`default_nettype none

module adsp2100_program_bus_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        request_valid,
    input logic [13:0] request_address,
    input logic        request_address_valid,
    input logic        request_data_access,
    input logic        request_write,
    input logic [23:0] request_write_data,
    input logic        request_write_data_valid,
    input logic [23:0] pmd_read_data,
    input logic        pmd_read_data_valid,
    input logic        bus_relinquished
);
    import adsp2100_pkg::*;

    logic request_ready;
    logic request_accepted;
    logic completion_event;
    logic read_sample_event;
    logic transaction_active;
    logic response_valid;
    logic response_write;
    logic [23:0] response_read_data;
    logic response_read_data_valid;
    logic address_oe;
    logic control_oe;
    logic data_oe;
    logic [13:0] pma;
    logic pma_valid;
    logic pmda;
    logic pmda_valid;
    logic pms_n;
    logic pmrd_n;
    logic pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
    logic [13:0] descriptor_address;
    logic descriptor_address_valid;
    logic descriptor_data_access;
    logic descriptor_write;
    logic [23:0] descriptor_write_data;
    logic descriptor_write_data_valid;
    logic strobe_phase;
    logic write_drive_phase;
    logic past_valid;
    logic unused_observation;

    assign strobe_phase = (
        phase == PHASE_STATE_4 || phase == PHASE_STATE_5
        || phase == PHASE_STATE_6 || phase == PHASE_STATE_7
    );
    assign write_drive_phase = (
        phase == PHASE_STATE_5 || phase == PHASE_STATE_6
        || phase == PHASE_STATE_7 || phase == PHASE_STATE_8
    );
    assign unused_observation = ^{
        pma, pmd_write_data, response_read_data, descriptor_address,
        descriptor_write_data
    };

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
        .pm_address_output_enable_o(address_oe),
        .pm_control_output_enable_o(control_oe),
        .pm_data_output_enable_o(data_oe),
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

    initial past_valid = 1'b0;

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (request_ready == (
            !reset && !bus_relinquished && phase_advance
            && phase == PHASE_STATE_8
        ));
        assert (request_accepted == (request_ready && request_valid));
        assert (completion_event == (
            !reset && !bus_relinquished && transaction_active
            && phase_advance && phase == PHASE_STATE_7
        ));
        assert (read_sample_event
            == (completion_event && !descriptor_write));
        assert (!(~pmrd_n && ~pmwr_n));
        assert (address_oe == control_oe);
        assert (pms_n == !control_oe);
        assert (pma_valid == (address_oe && descriptor_address_valid));
        assert (pmda_valid == control_oe);
        assert (pmda == (control_oe && descriptor_data_access));
        assert (~pmrd_n == (
            control_oe && !descriptor_write && strobe_phase
        ));
        assert (~pmwr_n == (
            control_oe && descriptor_write && strobe_phase
        ));
        assert (data_oe == (
            control_oe && descriptor_write && write_drive_phase
        ));
        assert (pmd_write_data_valid
            == (data_oe && descriptor_write_data_valid));
        assert (!response_read_data_valid
            || (response_valid && !response_write));
        if (bus_relinquished || reset) begin
            assert (!address_oe && !control_oe && !data_oe);
            assert (pms_n && pmrd_n && pmwr_n);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && !reset && !$past(reset)) begin
            if (
                $past(phase == PHASE_STATE_8 && phase_advance
                    && !bus_relinquished)
            ) begin
                assert (transaction_active == $past(request_valid));
                assert (!response_valid);
                if ($past(request_valid)) begin
                    assert (descriptor_address == $past(request_address));
                    assert (descriptor_address_valid
                        == $past(request_address_valid));
                    assert (descriptor_data_access
                        == $past(request_data_access));
                    assert (descriptor_write == $past(request_write));
                    assert (descriptor_write_data
                        == $past(request_write_data));
                    assert (descriptor_write_data_valid
                        == $past(request_write_data_valid));
                end
            end
            if ($past(completion_event)) begin
                assert (response_valid);
                assert (response_write == $past(descriptor_write));
                if (!$past(descriptor_write)) begin
                    assert (response_read_data == $past(pmd_read_data));
                    assert (response_read_data_valid
                        == $past(pmd_read_data_valid));
                end
            end
            if ($past(bus_relinquished) || !$past(phase_advance)) begin
                assert (transaction_active == $past(transaction_active));
                assert (descriptor_address == $past(descriptor_address));
                assert (descriptor_address_valid
                    == $past(descriptor_address_valid));
                assert (descriptor_data_access
                    == $past(descriptor_data_access));
                assert (descriptor_write == $past(descriptor_write));
                assert (descriptor_write_data
                    == $past(descriptor_write_data));
                assert (descriptor_write_data_valid
                    == $past(descriptor_write_data_valid));
            end
        end
        cover (past_valid && $past(completion_event) && response_valid);
        cover (request_accepted && transaction_active);
        cover (bus_relinquished && transaction_active && !control_oe);
    end
endmodule

`default_nettype wire
