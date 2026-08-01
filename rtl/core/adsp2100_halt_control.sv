`default_nettype none

// Original ADSP-2100 HALT sequencing for an ordinary PM-instruction cycle.
//
// halt_n_i is sampled at enabled end-of-state-three boundaries. The current
// external instruction fetch completes at state seven, then phase advancement
// is held in state eight until HALT is released with DMACK high. PM-data forced
// fetch, bus-grant/wait latching, TRAP handoff, and analog synchronization are
// intentionally outside this bounded controller.
module adsp2100_halt_control (
    input  logic       clk_i,
    input  logic       reset_i,
    input  logic [2:0] phase_i,
    input  logic       phase_advance_i,
    input  logic       halt_n_i,
    input  logic       dmack_i,

    output logic [1:0] mode_o,
    output logic       state_three_boundary_o,
    output logic       halt_recognized_o,
    output logic       halt_stop_event_o,
    output logic       resume_event_o,
    output logic       release_blocked_o,
    output logic       instruction_issue_inhibit_o,
    output logic       phase_hold_o,
    output logic       effective_phase_advance_o,
    output logic       halted_o,
    output logic       phase_conflict_o
);
    import adsp2100_pkg::*;

    typedef enum logic [1:0] {
        HALT_RUNNING      = 2'd0,
        HALT_STOP_PENDING = 2'd1,
        HALT_STOPPED      = 2'd2
    } halt_mode_t;

    halt_mode_t mode_q;
    halt_mode_t mode_d;
    logic resume_boundary;

    assign state_three_boundary_o = (
        !reset_i && phase_advance_i && phase_i == PHASE_STATE_3
    );
    assign halt_recognized_o = (
        mode_q == HALT_RUNNING
        && state_three_boundary_o && !halt_n_i
    );
    assign halt_stop_event_o = (
        !reset_i && mode_q == HALT_STOP_PENDING
        && phase_advance_i && phase_i == PHASE_STATE_7
    );
    assign resume_boundary = (
        !reset_i && mode_q == HALT_STOPPED
        && phase_advance_i && phase_i == PHASE_STATE_8
        && halt_n_i
    );
    assign resume_event_o = resume_boundary && dmack_i;
    assign release_blocked_o = resume_boundary && !dmack_i;
    assign phase_hold_o = (
        !reset_i && mode_q == HALT_STOPPED && !resume_event_o
    );
    assign effective_phase_advance_o = phase_advance_i && !phase_hold_o;
    assign instruction_issue_inhibit_o = (
        !reset_i
        && (
            halt_recognized_o
            || mode_q == HALT_STOP_PENDING
            || (mode_q == HALT_STOPPED && !resume_event_o)
        )
    );
    assign halted_o = !reset_i && mode_q == HALT_STOPPED;
    assign phase_conflict_o = (
        !reset_i && mode_q == HALT_STOPPED
        && phase_advance_i && phase_i != PHASE_STATE_8
    );
    assign mode_o = mode_q;

    always_comb begin
        mode_d = mode_q;
        if (reset_i) begin
            mode_d = HALT_RUNNING;
        end else if (halt_recognized_o) begin
            mode_d = HALT_STOP_PENDING;
        end else if (halt_stop_event_o) begin
            mode_d = HALT_STOPPED;
        end else if (resume_event_o) begin
            mode_d = HALT_RUNNING;
        end
    end

    always_ff @(posedge clk_i) begin
        mode_q <= mode_d;
    end

`ifndef SYNTHESIS
    always_comb begin
        assert (!(halt_recognized_o && halt_stop_event_o));
        assert (!(halt_stop_event_o && resume_event_o));
        assert (!(resume_event_o && release_blocked_o));
        assert (effective_phase_advance_o == (
            phase_advance_i && !phase_hold_o
        ));
        if (instruction_issue_inhibit_o) begin
            assert (!resume_event_o);
        end
        if (halted_o && !resume_event_o) begin
            assert (phase_hold_o);
        end
        if (resume_event_o) begin
            assert (halt_n_i && dmack_i);
            assert (phase_i == PHASE_STATE_8 && phase_advance_i);
        end
        if (release_blocked_o) begin
            assert (halt_n_i && !dmack_i);
            assert (phase_hold_o);
        end
        if (!phase_advance_i) begin
            assert (!state_three_boundary_o);
            assert (!halt_recognized_o);
            assert (!halt_stop_event_o);
            assert (!resume_event_o);
        end
        if (reset_i) begin
            assert (!instruction_issue_inhibit_o);
            assert (!phase_hold_o);
            assert (!halted_o);
        end
    end
`endif
endmodule

`default_nettype wire
