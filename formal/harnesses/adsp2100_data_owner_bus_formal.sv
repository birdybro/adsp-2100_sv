`default_nettype none

module adsp2100_data_owner_bus_formal (
    input logic clk, input logic reset,
    input logic [2:0] phase, input logic phase_advance,
    input logic [1:0] valid,
    input logic [13:0] fetched_address, companion_address,
    input logic [1:0] address_valid, input logic [1:0] write,
    input logic [15:0] fetched_write_data, companion_write_data,
    input logic [1:0] write_data_valid, input logic dm_ack,
    input logic [15:0] read_data, input logic read_data_valid,
    input logic bus_relinquished
);
    import adsp2100_pkg::*;
    logic ready, conflict, out_of_phase;
    logic [1:0] accepted, dmack_sample, dmack_accepted;
    logic [1:0] wait_extension, completion, read_sample;
    logic [1:0] owner;
    logic active, waiting, response_valid, response_write;
    logic [15:0] response_data;
    logic response_data_valid, address_oe, control_oe, data_oe;
    logic [13:0] dma;
    logic dma_valid, dms_n, dmrd_n, dmwr_n;
    logic [15:0] dmd_write_data;
    logic dmd_write_data_valid;
    logic [1:0] request_count;
    logic past_valid;
    logic unused_observation;

    assign request_count = {1'b0, valid[0]} + {1'b0, valid[1]};
    assign unused_observation = ^{
        dma, dma_valid, dmd_write_data, dmd_write_data_valid,
        response_write, response_data, response_data_valid
    };

    adsp2100_data_owner_bus dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(phase_advance),
        .fetched_valid_i(valid[0]), .fetched_address_i(fetched_address),
        .fetched_address_valid_i(address_valid[0]),
        .fetched_write_i(write[0]),
        .fetched_write_data_i(fetched_write_data),
        .fetched_write_data_valid_i(write_data_valid[0]),
        .companion_valid_i(valid[1]),
        .companion_address_i(companion_address),
        .companion_address_valid_i(address_valid[1]),
        .companion_write_i(write[1]),
        .companion_write_data_i(companion_write_data),
        .companion_write_data_valid_i(write_data_valid[1]),
        .dm_ack_i(dm_ack), .dmd_read_data_i(read_data),
        .dmd_read_data_valid_i(read_data_valid),
        .bus_relinquished_i(bus_relinquished),
        .request_ready_o(ready), .request_conflict_o(conflict),
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
        past_valid = 1'b0;
        assume (reset);
    end

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (ready == (!reset && !bus_relinquished && phase_advance
            && phase == PHASE_STATE_8 && (!active || response_valid)));
        assert (conflict == (ready && request_count > 2'd1));
        assert (out_of_phase == (request_count != 2'd0 && !ready));
        assert ($onehot0(accepted));
        assert ($onehot0(dmack_sample));
        assert ($onehot0(dmack_accepted));
        assert ($onehot0(wait_extension));
        assert ($onehot0(completion));
        assert ($onehot0(read_sample));
        assert ((dmack_accepted & ~dmack_sample) == 2'b00);
        assert ((wait_extension & ~dmack_sample) == 2'b00);
        assert ((read_sample & ~completion) == 2'b00);
        assert (!conflict || accepted == 2'b00);
        assert ((accepted != 2'b00) == (ready && request_count == 2'd1));
        if (!reset) assert (!active || owner != 2'd0);
        if (waiting) begin
            assert (owner != 2'd0);
            assert (!ready && completion == 2'b00);
        end
        assert (!(~dmrd_n && ~dmwr_n));
        if (reset || bus_relinquished) begin
            assert (!address_oe && !control_oe && !data_oe);
            assert (dms_n && dmrd_n && dmwr_n);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && !reset && !$past(reset)) begin
            if ($past(ready)) begin
                case ($past(accepted))
                    2'b01: assert (owner == 2'd1);
                    2'b10: assert (owner == 2'd2);
                    default: assert (owner == 2'd0);
                endcase
            end else begin
                assert (owner == $past(owner));
            end
            if ($past(waiting)) assert (owner == $past(owner));
        end
        cover (accepted[0]);
        cover (accepted[1]);
        cover (conflict && accepted == 2'b00);
        cover (wait_extension != 2'b00);
        cover (completion != 2'b00);
    end
endmodule

`default_nettype wire
