`default_nettype none

module adsp2100_data_owner_bus (
    input logic clk_i, input logic reset_i,
    input logic [2:0] phase_i, input logic phase_advance_i,
    input logic fetched_valid_i, input logic [13:0] fetched_address_i,
    input logic fetched_address_valid_i, input logic fetched_write_i,
    input logic [15:0] fetched_write_data_i,
    input logic fetched_write_data_valid_i,
    input logic companion_valid_i, input logic [13:0] companion_address_i,
    input logic companion_address_valid_i, input logic companion_write_i,
    input logic [15:0] companion_write_data_i,
    input logic companion_write_data_valid_i,
    input logic dm_ack_i, input logic [15:0] dmd_read_data_i,
    input logic dmd_read_data_valid_i, input logic bus_relinquished_i,
    output logic request_ready_o, output logic request_conflict_o,
    output logic request_out_of_phase_o,
    output logic [1:0] request_accepted_o,
    output logic [1:0] dmack_sample_event_o,
    output logic [1:0] dmack_accepted_o,
    output logic [1:0] wait_extension_event_o,
    output logic [1:0] completion_event_o,
    output logic [1:0] read_sample_event_o,
    output logic [1:0] owner_o, output logic transaction_active_o,
    output logic waiting_o, output logic response_valid_o,
    output logic response_write_o, output logic [15:0] response_read_data_o,
    output logic response_read_data_valid_o,
    output logic dm_address_output_enable_o,
    output logic dm_control_output_enable_o,
    output logic dm_data_output_enable_o,
    output logic [13:0] dma_o, output logic dma_valid_o,
    output logic dms_n_o, output logic dmrd_n_o, output logic dmwr_n_o,
    output logic [15:0] dmd_write_data_o,
    output logic dmd_write_data_valid_o
);
    localparam logic [1:0] OWNER_NONE = 2'd0;
    localparam logic [1:0] OWNER_FETCHED = 2'd1;
    localparam logic [1:0] OWNER_COMPANION = 2'd2;

    logic [1:0] owner_q;
    logic [1:0] request_count;
    logic [1:0] selected_owner;
    logic selected_valid;
    logic [13:0] selected_address;
    logic selected_address_valid;
    logic selected_write;
    logic [15:0] selected_write_data;
    logic selected_write_data_valid;
    logic bus_request_ready;
    logic bus_request_accepted;
    logic bus_dmack_sample;
    logic bus_dmack_accepted;
    logic bus_wait_extension;
    logic bus_completion;
    logic bus_read_sample;
    logic [13:0] unused_descriptor_address;
    logic unused_descriptor_address_valid;
    logic unused_descriptor_write;
    logic [15:0] unused_descriptor_write_data;
    logic unused_descriptor_write_data_valid;

    always_comb begin
        request_count = {1'b0, fetched_valid_i}
            + {1'b0, companion_valid_i};
        selected_owner = OWNER_NONE;
        selected_address = 14'h0000;
        selected_address_valid = 1'b0;
        selected_write = 1'b0;
        selected_write_data = 16'h0000;
        selected_write_data_valid = 1'b0;
        if (request_count == 2'd1) begin
            if (fetched_valid_i) begin
                selected_owner = OWNER_FETCHED;
                selected_address = fetched_address_i;
                selected_address_valid = fetched_address_valid_i;
                selected_write = fetched_write_i;
                selected_write_data = fetched_write_data_i;
                selected_write_data_valid = fetched_write_data_valid_i;
            end else begin
                selected_owner = OWNER_COMPANION;
                selected_address = companion_address_i;
                selected_address_valid = companion_address_valid_i;
                selected_write = companion_write_i;
                selected_write_data = companion_write_data_i;
                selected_write_data_valid = companion_write_data_valid_i;
            end
        end
    end

    assign selected_valid = bus_request_ready && request_count == 2'd1;
    assign request_ready_o = bus_request_ready;
    assign request_conflict_o = bus_request_ready && request_count > 2'd1;
    assign request_out_of_phase_o = request_count != 2'd0
        && !bus_request_ready;
    assign owner_o = owner_q;

    always_comb begin
        request_accepted_o = 2'b00;
        dmack_sample_event_o = 2'b00;
        dmack_accepted_o = 2'b00;
        wait_extension_event_o = 2'b00;
        completion_event_o = 2'b00;
        read_sample_event_o = 2'b00;
        if (bus_request_accepted) begin
            case (selected_owner)
                OWNER_FETCHED: request_accepted_o[0] = 1'b1;
                OWNER_COMPANION: request_accepted_o[1] = 1'b1;
                default: request_accepted_o = 2'b00;
            endcase
        end
        case (owner_q)
            OWNER_FETCHED: begin
                dmack_sample_event_o[0] = bus_dmack_sample;
                dmack_accepted_o[0] = bus_dmack_accepted;
                wait_extension_event_o[0] = bus_wait_extension;
                completion_event_o[0] = bus_completion;
                read_sample_event_o[0] = bus_read_sample;
            end
            OWNER_COMPANION: begin
                dmack_sample_event_o[1] = bus_dmack_sample;
                dmack_accepted_o[1] = bus_dmack_accepted;
                wait_extension_event_o[1] = bus_wait_extension;
                completion_event_o[1] = bus_completion;
                read_sample_event_o[1] = bus_read_sample;
            end
            default: begin
                dmack_sample_event_o = 2'b00;
                dmack_accepted_o = 2'b00;
                wait_extension_event_o = 2'b00;
                completion_event_o = 2'b00;
                read_sample_event_o = 2'b00;
            end
        endcase
    end

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            owner_q <= OWNER_NONE;
        end else if (bus_request_ready) begin
            owner_q <= selected_valid ? selected_owner : OWNER_NONE;
        end
    end

    adsp2100_data_bus data_bus (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .request_valid_i(selected_valid),
        .request_address_i(selected_address),
        .request_address_valid_i(selected_address_valid),
        .request_write_i(selected_write),
        .request_write_data_i(selected_write_data),
        .request_write_data_valid_i(selected_write_data_valid),
        .dm_ack_i(dm_ack_i), .dmd_read_data_i(dmd_read_data_i),
        .dmd_read_data_valid_i(dmd_read_data_valid_i),
        .bus_relinquished_i(bus_relinquished_i),
        .request_ready_o(bus_request_ready),
        .request_accepted_o(bus_request_accepted),
        .dmack_sample_event_o(bus_dmack_sample),
        .dmack_accepted_o(bus_dmack_accepted),
        .wait_extension_event_o(bus_wait_extension),
        .completion_event_o(bus_completion),
        .read_sample_event_o(bus_read_sample),
        .transaction_active_o(transaction_active_o), .waiting_o(waiting_o),
        .response_valid_o(response_valid_o),
        .response_write_o(response_write_o),
        .response_read_data_o(response_read_data_o),
        .response_read_data_valid_o(response_read_data_valid_o),
        .dm_address_output_enable_o(dm_address_output_enable_o),
        .dm_control_output_enable_o(dm_control_output_enable_o),
        .dm_data_output_enable_o(dm_data_output_enable_o),
        .dma_o(dma_o), .dma_valid_o(dma_valid_o), .dms_n_o(dms_n_o),
        .dmrd_n_o(dmrd_n_o), .dmwr_n_o(dmwr_n_o),
        .dmd_write_data_o(dmd_write_data_o),
        .dmd_write_data_valid_o(dmd_write_data_valid_o),
        .descriptor_address_o(unused_descriptor_address),
        .descriptor_address_valid_o(unused_descriptor_address_valid),
        .descriptor_write_o(unused_descriptor_write),
        .descriptor_write_data_o(unused_descriptor_write_data),
        .descriptor_write_data_valid_o(unused_descriptor_write_data_valid)
    );

`ifndef SYNTHESIS
    always_comb begin
        assert ($onehot0(request_accepted_o));
        assert ($onehot0(dmack_sample_event_o));
        assert ($onehot0(dmack_accepted_o));
        assert ($onehot0(wait_extension_event_o));
        assert ($onehot0(completion_event_o));
        assert ($onehot0(read_sample_event_o));
        assert (!request_conflict_o || request_accepted_o == 2'b00);
        assert ((dmack_accepted_o & ~dmack_sample_event_o) == 2'b00);
        assert ((wait_extension_event_o & ~dmack_sample_event_o) == 2'b00);
        assert ((read_sample_event_o & ~completion_event_o) == 2'b00);
        if (!reset_i && transaction_active_o) begin
            assert (owner_q != OWNER_NONE);
        end
        if (waiting_o) begin
            assert (owner_q != OWNER_NONE);
        end
    end
`endif
endmodule

`default_nettype wire
