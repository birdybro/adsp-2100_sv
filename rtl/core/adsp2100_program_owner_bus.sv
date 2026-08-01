`default_nettype none

module adsp2100_program_owner_bus (
    input logic clk_i, input logic reset_i,
    input logic [2:0] phase_i, input logic phase_advance_i,
    input logic fetch_valid_i, input logic [13:0] fetch_address_i,
    input logic fetch_address_valid_i,
    input logic type5_valid_i, input logic [13:0] type5_address_i,
    input logic type5_address_valid_i, input logic type5_write_i,
    input logic [23:0] type5_write_data_i,
    input logic type5_write_data_valid_i,
    input logic type13_valid_i, input logic [13:0] type13_address_i,
    input logic type13_address_valid_i, input logic type13_write_i,
    input logic [23:0] type13_write_data_i,
    input logic type13_write_data_valid_i,
    input logic [23:0] pmd_read_data_i,
    input logic pmd_read_data_valid_i, input logic bus_relinquished_i,
    output logic request_ready_o, output logic request_conflict_o,
    output logic request_out_of_phase_o,
    output logic [2:0] request_accepted_o,
    output logic [2:0] completion_event_o,
    output logic [2:0] read_sample_event_o,
    output logic [1:0] owner_o, output logic transaction_active_o,
    output logic response_valid_o, output logic response_write_o,
    output logic [23:0] response_read_data_o,
    output logic response_read_data_valid_o,
    output logic pm_address_output_enable_o,
    output logic pm_control_output_enable_o,
    output logic pm_data_output_enable_o,
    output logic [13:0] pma_o, output logic pma_valid_o,
    output logic pmda_o, output logic pmda_valid_o,
    output logic pms_n_o, output logic pmrd_n_o, output logic pmwr_n_o,
    output logic [23:0] pmd_write_data_o,
    output logic pmd_write_data_valid_o
);
    import adsp2100_pkg::*;
    localparam logic [1:0] OWNER_NONE = 2'd0;
    localparam logic [1:0] OWNER_FETCH = 2'd1;
    localparam logic [1:0] OWNER_TYPE5 = 2'd2;
    localparam logic [1:0] OWNER_TYPE13 = 2'd3;

    logic [1:0] owner_q;
    logic [2:0] request_count;
    logic [1:0] selected_owner;
    logic selected_valid;
    logic [13:0] selected_address;
    logic selected_address_valid;
    logic selected_write;
    logic [23:0] selected_write_data;
    logic selected_write_data_valid;
    logic bus_request_ready;
    logic bus_request_accepted;
    logic bus_completion;
    logic bus_read_sample;
    logic [13:0] unused_descriptor_address;
    logic unused_descriptor_address_valid;
    logic unused_descriptor_data_access;
    logic unused_descriptor_write;
    logic [23:0] unused_descriptor_write_data;
    logic unused_descriptor_write_data_valid;

    always_comb begin
        request_count = {2'b00, fetch_valid_i}
            + {2'b00, type5_valid_i} + {2'b00, type13_valid_i};
        selected_owner = OWNER_NONE;
        selected_address = 14'h0000;
        selected_address_valid = 1'b0;
        selected_write = 1'b0;
        selected_write_data = 24'h000000;
        selected_write_data_valid = 1'b0;
        if (request_count == 3'd1) begin
            if (fetch_valid_i) begin
                selected_owner = OWNER_FETCH;
                selected_address = fetch_address_i;
                selected_address_valid = fetch_address_valid_i;
            end else if (type5_valid_i) begin
                selected_owner = OWNER_TYPE5;
                selected_address = type5_address_i;
                selected_address_valid = type5_address_valid_i;
                selected_write = type5_write_i;
                selected_write_data = type5_write_data_i;
                selected_write_data_valid = type5_write_data_valid_i;
            end else begin
                selected_owner = OWNER_TYPE13;
                selected_address = type13_address_i;
                selected_address_valid = type13_address_valid_i;
                selected_write = type13_write_i;
                selected_write_data = type13_write_data_i;
                selected_write_data_valid = type13_write_data_valid_i;
            end
        end
    end

    assign selected_valid = bus_request_ready && request_count == 3'd1;
    assign request_ready_o = bus_request_ready;
    assign request_conflict_o = bus_request_ready && request_count > 3'd1;
    assign request_out_of_phase_o = request_count != 3'd0 && !bus_request_ready;
    assign owner_o = owner_q;

    always_comb begin
        request_accepted_o = 3'b000;
        completion_event_o = 3'b000;
        read_sample_event_o = 3'b000;
        if (bus_request_accepted) begin
            case (selected_owner)
                OWNER_FETCH: request_accepted_o[0] = 1'b1;
                OWNER_TYPE5: request_accepted_o[1] = 1'b1;
                OWNER_TYPE13: request_accepted_o[2] = 1'b1;
                default: request_accepted_o = 3'b000;
            endcase
        end
        if (bus_completion) begin
            case (owner_q)
                OWNER_FETCH: completion_event_o[0] = 1'b1;
                OWNER_TYPE5: completion_event_o[1] = 1'b1;
                OWNER_TYPE13: completion_event_o[2] = 1'b1;
                default: completion_event_o = 3'b000;
            endcase
        end
        if (bus_read_sample) begin
            case (owner_q)
                OWNER_FETCH: read_sample_event_o[0] = 1'b1;
                OWNER_TYPE5: read_sample_event_o[1] = 1'b1;
                OWNER_TYPE13: read_sample_event_o[2] = 1'b1;
                default: read_sample_event_o = 3'b000;
            endcase
        end
    end

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            owner_q <= OWNER_NONE;
        end else if (
            phase_i == PHASE_STATE_8 && phase_advance_i
            && !bus_relinquished_i
        ) begin
            owner_q <= selected_valid ? selected_owner : OWNER_NONE;
        end
    end

    adsp2100_program_bus program_bus (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .request_valid_i(selected_valid),
        .request_address_i(selected_address),
        .request_address_valid_i(selected_address_valid),
        .request_data_access_i(selected_owner != OWNER_FETCH),
        .request_write_i(selected_write),
        .request_write_data_i(selected_write_data),
        .request_write_data_valid_i(selected_write_data_valid),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .bus_relinquished_i(bus_relinquished_i),
        .request_ready_o(bus_request_ready),
        .request_accepted_o(bus_request_accepted),
        .completion_event_o(bus_completion),
        .read_sample_event_o(bus_read_sample),
        .transaction_active_o(transaction_active_o),
        .response_valid_o(response_valid_o),
        .response_write_o(response_write_o),
        .response_read_data_o(response_read_data_o),
        .response_read_data_valid_o(response_read_data_valid_o),
        .pm_address_output_enable_o(pm_address_output_enable_o),
        .pm_control_output_enable_o(pm_control_output_enable_o),
        .pm_data_output_enable_o(pm_data_output_enable_o),
        .pma_o(pma_o), .pma_valid_o(pma_valid_o), .pmda_o(pmda_o),
        .pmda_valid_o(pmda_valid_o), .pms_n_o(pms_n_o),
        .pmrd_n_o(pmrd_n_o), .pmwr_n_o(pmwr_n_o),
        .pmd_write_data_o(pmd_write_data_o),
        .pmd_write_data_valid_o(pmd_write_data_valid_o),
        .descriptor_address_o(unused_descriptor_address),
        .descriptor_address_valid_o(unused_descriptor_address_valid),
        .descriptor_data_access_o(unused_descriptor_data_access),
        .descriptor_write_o(unused_descriptor_write),
        .descriptor_write_data_o(unused_descriptor_write_data),
        .descriptor_write_data_valid_o(unused_descriptor_write_data_valid)
    );

`ifndef SYNTHESIS
    always_comb begin
        assert ($onehot0(request_accepted_o));
        assert ($onehot0(completion_event_o));
        assert ($onehot0(read_sample_event_o));
        assert (!request_conflict_o || request_accepted_o == 3'b000);
        assert ((completion_event_o & ~({3{bus_completion}})) == 3'b000);
        if (!reset_i && transaction_active_o) begin
            assert (owner_q != OWNER_NONE);
        end
    end
`endif
endmodule

`default_nettype wire
