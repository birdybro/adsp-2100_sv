`default_nettype none

module adsp2100_data_bus (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,

    input  logic        request_valid_i,
    input  logic [13:0] request_address_i,
    input  logic        request_address_valid_i,
    input  logic        request_write_i,
    input  logic [15:0] request_write_data_i,
    input  logic        request_write_data_valid_i,

    input  logic        dm_ack_i,
    input  logic [15:0] dmd_read_data_i,
    input  logic        dmd_read_data_valid_i,
    input  logic        bus_relinquished_i,

    output logic        request_ready_o,
    output logic        request_accepted_o,
    output logic        dmack_sample_event_o,
    output logic        dmack_accepted_o,
    output logic        wait_extension_event_o,
    output logic        completion_event_o,
    output logic        read_sample_event_o,
    output logic        transaction_active_o,
    output logic        waiting_o,

    output logic        response_valid_o,
    output logic        response_write_o,
    output logic [15:0] response_read_data_o,
    output logic        response_read_data_valid_o,

    output logic        dm_address_output_enable_o,
    output logic        dm_control_output_enable_o,
    output logic        dm_data_output_enable_o,
    output logic [13:0] dma_o,
    output logic        dma_valid_o,
    output logic        dms_n_o,
    output logic        dmrd_n_o,
    output logic        dmwr_n_o,
    output logic [15:0] dmd_write_data_o,
    output logic        dmd_write_data_valid_o,

    output logic [13:0] descriptor_address_o,
    output logic        descriptor_address_valid_o,
    output logic        descriptor_write_o,
    output logic [15:0] descriptor_write_data_o,
    output logic        descriptor_write_data_valid_o
);
    import adsp2100_pkg::*;

    logic        active_q;
    logic [13:0] address_q;
    logic        address_valid_q;
    logic        write_q;
    logic [15:0] write_data_q;
    logic        write_data_valid_q;
    logic        waiting_q;
    logic        acknowledged_q;
    logic        response_valid_q;
    logic        response_write_q;
    logic [15:0] read_data_q;
    logic        read_data_valid_q;
    logic        in_progress;
    logic        interface_active;
    logic        strobe_active;
    logic        write_drive_active;

    assign in_progress = active_q && !response_valid_q;
    assign interface_active = active_q && !bus_relinquished_i && !reset_i;
    assign request_ready_o = (
        !reset_i && !bus_relinquished_i && phase_advance_i
        && phase_i == PHASE_STATE_8
        && (!active_q || response_valid_q)
    );
    assign request_accepted_o = request_ready_o && request_valid_i;
    assign dmack_sample_event_o = (
        interface_active && in_progress && phase_advance_i
        && phase_i == PHASE_STATE_6
    );
    assign dmack_accepted_o = dmack_sample_event_o && dm_ack_i;
    assign wait_extension_event_o = dmack_sample_event_o && !dm_ack_i;
    assign completion_event_o = (
        interface_active && in_progress && phase_advance_i
        && phase_i == PHASE_STATE_7
        && acknowledged_q && !waiting_q
    );
    assign read_sample_event_o = completion_event_o && !write_q;
    assign transaction_active_o = active_q;
    assign waiting_o = in_progress && waiting_q;

    always_comb begin
        strobe_active = waiting_q || (
            phase_i == PHASE_STATE_4
            || phase_i == PHASE_STATE_5
            || phase_i == PHASE_STATE_6
            || phase_i == PHASE_STATE_7
        );
        write_drive_active = waiting_q || (
            phase_i == PHASE_STATE_5
            || phase_i == PHASE_STATE_6
            || phase_i == PHASE_STATE_7
            || phase_i == PHASE_STATE_8
        );
    end

    assign response_valid_o = response_valid_q;
    assign response_write_o = response_write_q;
    assign response_read_data_o = read_data_q;
    assign response_read_data_valid_o = read_data_valid_q;

    assign dm_address_output_enable_o = interface_active;
    assign dm_control_output_enable_o = interface_active;
    assign dm_data_output_enable_o = (
        interface_active && in_progress && write_q && write_drive_active
    );
    assign dma_o = address_q;
    assign dma_valid_o = interface_active && address_valid_q;
    assign dms_n_o = !interface_active;
    assign dmrd_n_o = !(
        interface_active && in_progress && !write_q && strobe_active
    );
    assign dmwr_n_o = !(
        interface_active && in_progress && write_q && strobe_active
    );
    assign dmd_write_data_o = write_data_q;
    assign dmd_write_data_valid_o = (
        dm_data_output_enable_o && write_data_valid_q
    );

    assign descriptor_address_o = address_q;
    assign descriptor_address_valid_o = address_valid_q;
    assign descriptor_write_o = write_q;
    assign descriptor_write_data_o = write_data_q;
    assign descriptor_write_data_valid_o = write_data_valid_q;

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            active_q <= 1'b0;
            address_q <= 14'h0000;
            address_valid_q <= 1'b0;
            write_q <= 1'b0;
            write_data_q <= 16'h0000;
            write_data_valid_q <= 1'b0;
            waiting_q <= 1'b0;
            acknowledged_q <= 1'b0;
            response_valid_q <= 1'b0;
            response_write_q <= 1'b0;
            read_data_q <= 16'h0000;
            read_data_valid_q <= 1'b0;
        end else begin
            if (dmack_sample_event_o) begin
                waiting_q <= !dm_ack_i;
                acknowledged_q <= dm_ack_i;
            end
            if (completion_event_o) begin
                waiting_q <= 1'b0;
                acknowledged_q <= 1'b0;
                response_valid_q <= 1'b1;
                response_write_q <= write_q;
                if (write_q) begin
                    read_data_q <= 16'h0000;
                    read_data_valid_q <= 1'b0;
                end else begin
                    read_data_q <= dmd_read_data_i;
                    read_data_valid_q <= dmd_read_data_valid_i;
                end
            end
            if (request_ready_o) begin
                waiting_q <= 1'b0;
                acknowledged_q <= 1'b0;
                response_valid_q <= 1'b0;
                response_write_q <= 1'b0;
                read_data_q <= 16'h0000;
                read_data_valid_q <= 1'b0;
                if (request_valid_i) begin
                    active_q <= 1'b1;
                    address_q <= request_address_i;
                    address_valid_q <= request_address_valid_i;
                    write_q <= request_write_i;
                    write_data_q <= request_write_data_i;
                    write_data_valid_q <= request_write_data_valid_i;
                end else begin
                    active_q <= 1'b0;
                    address_q <= 14'h0000;
                    address_valid_q <= 1'b0;
                    write_q <= 1'b0;
                    write_data_q <= 16'h0000;
                    write_data_valid_q <= 1'b0;
                end
            end
        end
    end

`ifndef SYNTHESIS
    always_comb begin
        assert (!(~dmrd_n_o && ~dmwr_n_o));
        assert (request_accepted_o == (request_ready_o && request_valid_i));
        assert (dmack_accepted_o == (dmack_sample_event_o && dm_ack_i));
        assert (wait_extension_event_o
            == (dmack_sample_event_o && !dm_ack_i));
        assert (read_sample_event_o == (completion_event_o && !write_q));
        assert (dms_n_o == !dm_control_output_enable_o);
        assert (dm_address_output_enable_o == dm_control_output_enable_o);
        assert (!response_read_data_valid_o
            || (response_valid_o && !response_write_o));
        if (completion_event_o) begin
            assert (acknowledged_q && !waiting_q);
        end
        if (waiting_o) begin
            assert (active_q && !response_valid_q && strobe_active);
            assert (!completion_event_o && !request_ready_o);
        end
        if (bus_relinquished_i || reset_i) begin
            assert (!dm_address_output_enable_o);
            assert (!dm_control_output_enable_o);
            assert (!dm_data_output_enable_o);
            assert (dms_n_o && dmrd_n_o && dmwr_n_o);
        end
        if (!dmrd_n_o || !dmwr_n_o) begin
            assert (interface_active && in_progress && strobe_active);
        end
        if (dm_data_output_enable_o) begin
            assert (interface_active && in_progress && write_q);
            assert (write_drive_active);
        end
    end
`endif
endmodule

`default_nettype wire
