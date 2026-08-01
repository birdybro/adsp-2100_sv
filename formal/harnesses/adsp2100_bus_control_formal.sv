`default_nettype none

module adsp2100_bus_control_formal (
    input logic       clk,
    input logic       reset,
    input logic [2:0] phase,
    input logic       phase_advance,
    input logic       br_n
);
    import adsp2100_pkg::*;

    logic [2:0] mode;
    logic state_three_boundary;
    logic request_recognized;
    logic grant_assert_event;
    logic release_recognized;
    logic grant_release_event;
    logic resume_event;
    logic request_withdrawn;
    logic release_cancelled;
    logic instruction_issue_inhibit;
    logic bus_relinquished;
    logic bg_n;
    logic reset_br_request;
    logic native_bg_n;
    logic native_bus_relinquished;
    logic past_valid;

    adsp2100_bus_control dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .br_n_i(br_n),
        .mode_o(mode),
        .state_three_boundary_o(state_three_boundary),
        .request_recognized_o(request_recognized),
        .grant_assert_event_o(grant_assert_event),
        .release_recognized_o(release_recognized),
        .grant_release_event_o(grant_release_event),
        .resume_event_o(resume_event),
        .request_withdrawn_o(request_withdrawn),
        .release_cancelled_o(release_cancelled),
        .instruction_issue_inhibit_o(instruction_issue_inhibit),
        .bus_relinquished_o(bus_relinquished),
        .bg_n_o(bg_n),
        .reset_br_request_o(reset_br_request)
    );

    adsp2100_reset_bus_grant native_reset_path (
        .reset_active_i(reset),
        .br_n_i(br_n),
        .normal_bg_n_i(bg_n),
        .normal_bus_relinquished_i(bus_relinquished),
        .bg_n_o(native_bg_n),
        .bus_relinquished_o(native_bus_relinquished)
    );

    initial begin
        past_valid = 1'b0;
        assume (reset);
    end

    always_comb begin
        assert (state_three_boundary == (
            !reset && phase_advance && phase == PHASE_STATE_3
        ));
        assert (bg_n == !bus_relinquished);
        assert (!bus_relinquished || instruction_issue_inhibit);
        assert (reset_br_request == (reset && !br_n));
        if (reset) begin
            assert (native_bg_n == br_n);
            assert (native_bus_relinquished == !br_n);
        end else begin
            assert (native_bg_n == bg_n);
            assert (native_bus_relinquished == bus_relinquished);
        end
        if (!phase_advance) begin
            assert (!state_three_boundary);
            assert (!request_recognized);
            assert (!grant_assert_event);
            assert (!release_recognized);
            assert (!grant_release_event);
            assert (!resume_event);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (!past_valid) begin
            assume (reset);
        end else begin
            assert (mode <= 3'd4);
            if ($past(reset)) begin
                assert (mode == 3'd0);
            end
            if ($past(request_recognized)) begin
                assert (mode == 3'd1);
            end
            if ($past(grant_assert_event)) begin
                assert (mode == 3'd2);
            end
            if ($past(release_recognized)) begin
                assert (mode == 3'd3);
            end
            if ($past(grant_release_event)) begin
                assert (mode == 3'd4);
            end
            if ($past(release_cancelled)) begin
                assert (mode == 3'd2);
            end
            if ($past(request_withdrawn || resume_event)) begin
                assert (mode == 3'd0);
            end
        end
        cover (past_valid && $past(grant_assert_event) && !bg_n);
        cover (past_valid && $past(grant_release_event) && mode == 3'd4);
        cover (past_valid && $past(resume_event) && mode == 3'd0);
        cover (reset && !br_n && native_bus_relinquished);
    end
endmodule

`default_nettype wire
