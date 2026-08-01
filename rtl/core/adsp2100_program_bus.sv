`default_nettype none

module adsp2100_program_bus (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,

    input  logic        request_valid_i,
    input  logic [13:0] request_address_i,
    input  logic        request_address_valid_i,
    input  logic        request_data_access_i,
    input  logic        request_write_i,
    input  logic [23:0] request_write_data_i,
    input  logic        request_write_data_valid_i,

    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic        bus_relinquished_i,

    output logic        request_ready_o,
    output logic        request_accepted_o,
    output logic        completion_event_o,
    output logic        read_sample_event_o,
    output logic        transaction_active_o,

    output logic        response_valid_o,
    output logic        response_write_o,
    output logic [23:0] response_read_data_o,
    output logic        response_read_data_valid_o,

    output logic        pm_address_output_enable_o,
    output logic        pm_control_output_enable_o,
    output logic        pm_data_output_enable_o,
    output logic [13:0] pma_o,
    output logic        pma_valid_o,
    output logic        pmda_o,
    output logic        pmda_valid_o,
    output logic        pms_n_o,
    output logic        pmrd_n_o,
    output logic        pmwr_n_o,
    output logic [23:0] pmd_write_data_o,
    output logic        pmd_write_data_valid_o,

    output logic [13:0] descriptor_address_o,
    output logic        descriptor_address_valid_o,
    output logic        descriptor_data_access_o,
    output logic        descriptor_write_o,
    output logic [23:0] descriptor_write_data_o,
    output logic        descriptor_write_data_valid_o
);
    import adsp2100_pkg::*;

    logic        active_q;
    logic [13:0] address_q;
    logic        address_valid_q;
    logic        data_access_q;
    logic        write_q;
    logic [23:0] write_data_q;
    logic        write_data_valid_q;
    logic        response_valid_q;
    logic        response_write_q;
    logic [23:0] read_data_q;
    logic        read_data_valid_q;
    logic        strobe_active;
    logic        write_drive_active;
    logic        interface_active;

    always_comb begin
        strobe_active = (
            phase_i == PHASE_STATE_4
            || phase_i == PHASE_STATE_5
            || phase_i == PHASE_STATE_6
            || phase_i == PHASE_STATE_7
        );
        write_drive_active = (
            phase_i == PHASE_STATE_5
            || phase_i == PHASE_STATE_6
            || phase_i == PHASE_STATE_7
            || phase_i == PHASE_STATE_8
        );
    end

    assign interface_active = active_q && !bus_relinquished_i && !reset_i;
    assign request_ready_o = (
        !reset_i && !bus_relinquished_i && phase_advance_i
        && phase_i == PHASE_STATE_8
    );
    assign request_accepted_o = request_ready_o && request_valid_i;
    assign completion_event_o = (
        interface_active && phase_advance_i && phase_i == PHASE_STATE_7
    );
    assign read_sample_event_o = completion_event_o && !write_q;
    assign transaction_active_o = active_q;

    assign response_valid_o = response_valid_q;
    assign response_write_o = response_write_q;
    assign response_read_data_o = read_data_q;
    assign response_read_data_valid_o = read_data_valid_q;

    assign pm_address_output_enable_o = interface_active;
    assign pm_control_output_enable_o = interface_active;
    assign pm_data_output_enable_o = (
        interface_active && write_q && write_drive_active
    );
    assign pma_o = address_q;
    assign pma_valid_o = interface_active && address_valid_q;
    assign pmda_o = interface_active ? data_access_q : 1'b0;
    assign pmda_valid_o = interface_active;
    assign pms_n_o = !interface_active;
    assign pmrd_n_o = !(
        interface_active && !write_q && strobe_active
    );
    assign pmwr_n_o = !(
        interface_active && write_q && strobe_active
    );
    assign pmd_write_data_o = write_data_q;
    assign pmd_write_data_valid_o = (
        pm_data_output_enable_o && write_data_valid_q
    );

    assign descriptor_address_o = address_q;
    assign descriptor_address_valid_o = address_valid_q;
    assign descriptor_data_access_o = data_access_q;
    assign descriptor_write_o = write_q;
    assign descriptor_write_data_o = write_data_q;
    assign descriptor_write_data_valid_o = write_data_valid_q;

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            active_q <= 1'b0;
            address_q <= 14'h0000;
            address_valid_q <= 1'b0;
            data_access_q <= 1'b0;
            write_q <= 1'b0;
            write_data_q <= 24'h000000;
            write_data_valid_q <= 1'b0;
            response_valid_q <= 1'b0;
            response_write_q <= 1'b0;
            read_data_q <= 24'h000000;
            read_data_valid_q <= 1'b0;
        end else begin
            if (completion_event_o) begin
                response_valid_q <= 1'b1;
                response_write_q <= write_q;
                if (write_q) begin
                    read_data_q <= 24'h000000;
                    read_data_valid_q <= 1'b0;
                end else begin
                    read_data_q <= pmd_read_data_i;
                    read_data_valid_q <= pmd_read_data_valid_i;
                end
            end

            if (phase_i == PHASE_STATE_8 && phase_advance_i) begin
                if (!bus_relinquished_i) begin
                    response_valid_q <= 1'b0;
                    response_write_q <= 1'b0;
                    read_data_q <= 24'h000000;
                    read_data_valid_q <= 1'b0;
                    if (request_valid_i) begin
                        active_q <= 1'b1;
                        address_q <= request_address_i;
                        address_valid_q <= request_address_valid_i;
                        data_access_q <= request_data_access_i;
                        write_q <= request_write_i;
                        write_data_q <= request_write_data_i;
                        write_data_valid_q <= request_write_data_valid_i;
                    end else begin
                        active_q <= 1'b0;
                        address_q <= 14'h0000;
                        address_valid_q <= 1'b0;
                        data_access_q <= 1'b0;
                        write_q <= 1'b0;
                        write_data_q <= 24'h000000;
                        write_data_valid_q <= 1'b0;
                    end
                end
            end
        end
    end

`ifndef SYNTHESIS
    always_comb begin
        assert (!(~pmrd_n_o && ~pmwr_n_o));
        assert (request_accepted_o == (request_ready_o && request_valid_i));
        assert (read_sample_event_o == (completion_event_o && !write_q));
        assert (pms_n_o == !pm_control_output_enable_o);
        assert (pm_address_output_enable_o == pm_control_output_enable_o);
        assert (!response_read_data_valid_o
            || (response_valid_o && !response_write_o));
        if (bus_relinquished_i || reset_i) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
            assert (pms_n_o && pmrd_n_o && pmwr_n_o);
        end
        if (!pmrd_n_o || !pmwr_n_o) begin
            assert (strobe_active && interface_active);
        end
        if (pm_data_output_enable_o) begin
            assert (interface_active && write_q && write_drive_active);
        end
    end
`endif
endmodule

`default_nettype wire
