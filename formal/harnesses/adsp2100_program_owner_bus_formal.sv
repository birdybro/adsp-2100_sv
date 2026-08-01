`default_nettype none

module adsp2100_program_owner_bus_formal (
    input logic clk, input logic reset,
    input logic [2:0] phase, input logic phase_advance,
    input logic [2:0] valid,
    input logic [13:0] fetch_address, type5_address, type13_address,
    input logic [2:0] address_valid,
    input logic type5_write, type13_write,
    input logic [23:0] type5_write_data, type13_write_data,
    input logic type5_write_data_valid, type13_write_data_valid,
    input logic [23:0] read_data, input logic read_data_valid,
    input logic bus_relinquished
);
    import adsp2100_pkg::*;
    logic ready, conflict, out_of_phase;
    logic [2:0] accepted, completion, read_sample;
    logic [1:0] owner;
    logic active, response_valid, response_write, response_data_valid;
    logic [23:0] response_data;
    logic address_oe, control_oe, data_oe;
    logic [13:0] pma;
    logic pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
    logic [2:0] request_count;
    logic past_valid;
    logic unused_observation;

    assign request_count = {2'b00, valid[0]} + {2'b00, valid[1]}
        + {2'b00, valid[2]};
    assign unused_observation = ^{
        pma, pma_valid, pmda, pmda_valid, pmd_write_data,
        pmd_write_data_valid, response_valid, response_write,
        response_data, response_data_valid
    };

    adsp2100_program_owner_bus dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(phase_advance),
        .fetch_valid_i(valid[0]), .fetch_address_i(fetch_address),
        .fetch_address_valid_i(address_valid[0]),
        .type5_valid_i(valid[1]), .type5_address_i(type5_address),
        .type5_address_valid_i(address_valid[1]),
        .type5_write_i(type5_write), .type5_write_data_i(type5_write_data),
        .type5_write_data_valid_i(type5_write_data_valid),
        .type13_valid_i(valid[2]), .type13_address_i(type13_address),
        .type13_address_valid_i(address_valid[2]),
        .type13_write_i(type13_write),
        .type13_write_data_i(type13_write_data),
        .type13_write_data_valid_i(type13_write_data_valid),
        .pmd_read_data_i(read_data), .pmd_read_data_valid_i(read_data_valid),
        .bus_relinquished_i(bus_relinquished), .request_ready_o(ready),
        .request_conflict_o(conflict),
        .request_out_of_phase_o(out_of_phase),
        .request_accepted_o(accepted), .completion_event_o(completion),
        .read_sample_event_o(read_sample), .owner_o(owner),
        .transaction_active_o(active), .response_valid_o(response_valid),
        .response_write_o(response_write),
        .response_read_data_o(response_data),
        .response_read_data_valid_o(response_data_valid),
        .pm_address_output_enable_o(address_oe),
        .pm_control_output_enable_o(control_oe),
        .pm_data_output_enable_o(data_oe), .pma_o(pma),
        .pma_valid_o(pma_valid), .pmda_o(pmda),
        .pmda_valid_o(pmda_valid), .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n), .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );

    initial begin
        past_valid = 1'b0;
        assume (reset);
    end
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (ready == (!reset && !bus_relinquished
            && phase_advance && phase == PHASE_STATE_8));
        assert (conflict == (ready && request_count > 3'd1));
        assert (out_of_phase == (request_count != 3'd0 && !ready));
        assert ($onehot0(accepted));
        assert ($onehot0(completion));
        assert ($onehot0(read_sample));
        assert ((read_sample & ~completion) == 3'b000);
        assert (!conflict || accepted == 3'b000);
        assert ((accepted != 3'b000) == (ready && request_count == 3'd1));
        if (!reset) assert (!active || owner != 2'd0);
        assert (!(~pmrd_n && ~pmwr_n));
        if (reset || bus_relinquished) begin
            assert (!address_oe && !control_oe && !data_oe);
            assert (pms_n && pmrd_n && pmwr_n);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && !reset && !$past(reset)) begin
            if ($past(phase == PHASE_STATE_8 && phase_advance
                      && !bus_relinquished)) begin
                case ($past(accepted))
                    3'b001: assert (owner == 2'd1);
                    3'b010: assert (owner == 2'd2);
                    3'b100: assert (owner == 2'd3);
                    default: assert (owner == 2'd0);
                endcase
            end else begin
                assert (owner == $past(owner));
            end
        end
        cover (accepted[0]);
        cover (accepted[1]);
        cover (accepted[2]);
        cover (conflict && accepted == 3'b000);
        cover (completion != 3'b000);
    end
endmodule

`default_nettype wire
