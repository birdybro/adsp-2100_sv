`default_nettype none

// Original ADSP-2100 normal-operation BR/BG sequencing.
//
// br_n_i is sampled only at enabled end-of-state-three boundaries. The
// service-inhibit input preserves initial request recognition but defers
// follow-up grant/release transitions while a current DM cycle is incomplete.
// asynchronous RESET-time BR/BG path is intentionally isolated in the native
// pin wrapper; reset_br_request_o makes that handoff explicit.
module adsp2100_bus_control (
    input  logic       clk_i,
    input  logic       reset_i,
    input  logic [2:0] phase_i,
    input  logic       phase_advance_i,
    input  logic       br_n_i,
    input  logic       service_inhibit_i,

    output logic [2:0] mode_o,
    output logic       state_three_boundary_o,
    output logic       request_recognized_o,
    output logic       grant_assert_event_o,
    output logic       release_recognized_o,
    output logic       grant_release_event_o,
    output logic       resume_event_o,
    output logic       request_withdrawn_o,
    output logic       release_cancelled_o,
    output logic       instruction_issue_inhibit_o,
    output logic       bus_relinquished_o,
    output logic       bg_n_o,
    output logic       reset_br_request_o
);
    import adsp2100_pkg::*;

    typedef enum logic [2:0] {
        BUS_IDLE          = 3'd0,
        BUS_REQUEST_DELAY = 3'd1,
        BUS_GRANTED       = 3'd2,
        BUS_RELEASE_DELAY = 3'd3,
        BUS_REACQUIRE     = 3'd4
    } bus_mode_t;

    bus_mode_t mode_q;
    bus_mode_t mode_d;
    logic normal_granted;
    logic service_boundary;

    assign state_three_boundary_o = (
        !reset_i && phase_advance_i && phase_i == PHASE_STATE_3
    );
    assign request_recognized_o = (
        mode_q == BUS_IDLE && state_three_boundary_o && !br_n_i
    );
    assign service_boundary = (
        state_three_boundary_o && !service_inhibit_i
    );
    assign grant_assert_event_o = (
        mode_q == BUS_REQUEST_DELAY
        && service_boundary && !br_n_i
    );
    assign request_withdrawn_o = (
        mode_q == BUS_REQUEST_DELAY
        && service_boundary && br_n_i
    );
    assign release_recognized_o = (
        mode_q == BUS_GRANTED && service_boundary && br_n_i
    );
    assign grant_release_event_o = (
        mode_q == BUS_RELEASE_DELAY
        && service_boundary && br_n_i
    );
    assign release_cancelled_o = (
        mode_q == BUS_RELEASE_DELAY
        && service_boundary && !br_n_i
    );
    assign resume_event_o = (
        !reset_i && mode_q == BUS_REACQUIRE
        && phase_advance_i && phase_i == PHASE_STATE_8
    );

    assign normal_granted = (
        !reset_i
        && (mode_q == BUS_GRANTED || mode_q == BUS_RELEASE_DELAY)
    );
    assign instruction_issue_inhibit_o = (
        !reset_i
        && (
            (mode_q != BUS_IDLE && !resume_event_o)
            || request_recognized_o
        )
    );
    assign bus_relinquished_o = normal_granted;
    assign bg_n_o = !normal_granted;
    assign reset_br_request_o = reset_i && !br_n_i;
    assign mode_o = mode_q;

    always_comb begin
        mode_d = mode_q;
        if (reset_i) begin
            mode_d = BUS_IDLE;
        end else if (request_recognized_o) begin
            mode_d = BUS_REQUEST_DELAY;
        end else if (grant_assert_event_o) begin
            mode_d = BUS_GRANTED;
        end else if (request_withdrawn_o) begin
            mode_d = BUS_IDLE;
        end else if (release_recognized_o) begin
            mode_d = BUS_RELEASE_DELAY;
        end else if (grant_release_event_o) begin
            mode_d = BUS_REACQUIRE;
        end else if (release_cancelled_o) begin
            mode_d = BUS_GRANTED;
        end else if (resume_event_o) begin
            mode_d = BUS_IDLE;
        end
    end

    always_ff @(posedge clk_i) begin
        mode_q <= mode_d;
    end

`ifndef SYNTHESIS
    always_comb begin
        assert (!(grant_assert_event_o && grant_release_event_o));
        assert (!(request_recognized_o && release_recognized_o));
        assert (!(request_withdrawn_o && release_cancelled_o));
        assert (bg_n_o == !bus_relinquished_o);
        if (bus_relinquished_o) begin
            assert (instruction_issue_inhibit_o);
        end
        if (!phase_advance_i) begin
            assert (!state_three_boundary_o);
            assert (!request_recognized_o);
            assert (!grant_assert_event_o);
            assert (!release_recognized_o);
            assert (!grant_release_event_o);
            assert (!resume_event_o);
        end
        if (service_inhibit_i) begin
            assert (!grant_assert_event_o);
            assert (!request_withdrawn_o);
            assert (!release_recognized_o);
            assert (!grant_release_event_o);
            assert (!release_cancelled_o);
        end
        if (reset_i) begin
            assert (bg_n_o);
            assert (!bus_relinquished_o);
            assert (!instruction_issue_inhibit_o);
        end
    end
`endif
endmodule

`default_nettype wire
