`default_nettype none

module adsp2100_program_owner_bus_control_formal (
    input logic clk,
    input logic reset,
    input logic [2:0] phase,
    input logic phase_advance,
    input logic br_n,
    input logic [2:0] valid,
    input logic [13:0] fetch_address,
    input logic [13:0] type5_address,
    input logic [13:0] type13_address,
    input logic [2:0] address_valid,
    input logic type5_write,
    input logic type13_write,
    input logic [23:0] type5_write_data,
    input logic [23:0] type13_write_data,
    input logic type5_write_data_valid,
    input logic type13_write_data_valid,
    input logic [23:0] read_data,
    input logic read_data_valid
);
    import adsp2100_pkg::*;
    logic [2:0] bus_mode;
    logic state_three, bus_request_recognized, grant_assert;
    logic release_recognized, grant_release, resume;
    logic request_withdrawn, release_cancelled, issue_inhibit;
    logic normal_bus_relinquished, normal_bg_n, reset_br_request;
    logic bg_n, bus_relinquished;
    logic ready, blocked, conflict, out_of_phase;
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
        state_three, request_withdrawn, release_cancelled,
        normal_bus_relinquished, normal_bg_n, reset_br_request,
        out_of_phase, active, response_valid, response_write,
        response_data_valid, response_data, pma, pma_valid, pmda,
        pmda_valid, pmd_write_data, pmd_write_data_valid
    };

    adsp2100_program_owner_bus_control dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(phase_advance), .br_n_i(br_n),
        .fetch_valid_i(valid[0]), .fetch_address_i(fetch_address),
        .fetch_address_valid_i(address_valid[0]),
        .type5_valid_i(valid[1]), .type5_address_i(type5_address),
        .type5_address_valid_i(address_valid[1]),
        .type5_data_access_i(1'b1),
        .type5_write_i(type5_write),
        .type5_write_data_i(type5_write_data),
        .type5_write_data_valid_i(type5_write_data_valid),
        .type13_valid_i(valid[2]), .type13_address_i(type13_address),
        .type13_address_valid_i(address_valid[2]),
        .type13_data_access_i(1'b1),
        .type13_write_i(type13_write),
        .type13_write_data_i(type13_write_data),
        .type13_write_data_valid_i(type13_write_data_valid),
        .pmd_read_data_i(read_data),
        .pmd_read_data_valid_i(read_data_valid),
        .bus_mode_o(bus_mode), .state_three_boundary_o(state_three),
        .bus_request_recognized_o(bus_request_recognized),
        .grant_assert_event_o(grant_assert),
        .release_recognized_o(release_recognized),
        .grant_release_event_o(grant_release), .resume_event_o(resume),
        .request_withdrawn_o(request_withdrawn),
        .release_cancelled_o(release_cancelled),
        .issue_inhibit_o(issue_inhibit),
        .normal_bus_relinquished_o(normal_bus_relinquished),
        .normal_bg_n_o(normal_bg_n), .reset_br_request_o(reset_br_request),
        .bg_n_o(bg_n), .bus_relinquished_o(bus_relinquished),
        .request_ready_o(ready), .request_blocked_o(blocked),
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
        assert (bus_mode <= 3'd4);
        assert (bg_n == !bus_relinquished);
        assert (blocked == (request_count != 3'd0 && issue_inhibit));
        assert ($onehot0(accepted));
        assert ($onehot0(completion));
        assert ($onehot0(read_sample));
        assert ((read_sample & ~completion) == 3'b000);
        assert (!conflict || accepted == 3'b000);
        assert (!(~pmrd_n && ~pmwr_n));
        if (issue_inhibit) begin
            assert (!ready);
            assert (accepted == 3'b000);
        end
        if (bus_relinquished) begin
            assert (!address_oe && !control_oe && !data_oe);
            assert (pms_n && pmrd_n && pmwr_n);
        end
        if (grant_assert || grant_release || bus_request_recognized
            || release_recognized) begin
            assert (phase == PHASE_STATE_3 && phase_advance);
        end
        if (resume) begin
            assert (phase == PHASE_STATE_8 && phase_advance);
            assert (!issue_inhibit && ready);
            if (request_count == 3'd1) assert ($onehot(accepted));
        end
        if (reset && !br_n) begin
            assert (!bg_n && bus_relinquished);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && !reset && !$past(reset)
            && $past(bus_relinquished)) begin
            assert (owner == $past(owner));
        end
        cover (bus_request_recognized && active);
        cover (grant_assert);
        cover (release_recognized);
        cover (grant_release);
        cover (resume && accepted != 3'b000);
        cover (blocked);
        cover (reset && !br_n && !bg_n);
    end
endmodule

`default_nettype wire
