`default_nettype none

module adsp2100_halt_control_formal (
    input logic       clk,
    input logic       reset,
    input logic [2:0] phase,
    input logic       phase_advance,
    input logic       halt_n,
    input logic       dmack,
    input logic       pm_data_cycle
);
    import adsp2100_pkg::*;

    logic [1:0] mode;
    logic state_three_boundary;
    logic halt_recognized;
    logic halt_stop_event;
    logic force_fetch_issue;
    logic resume_event;
    logic release_blocked;
    logic instruction_issue_inhibit;
    logic phase_hold;
    logic effective_phase_advance;
    logic halted;
    logic phase_conflict;
    logic past_valid;

    adsp2100_halt_control dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .halt_n_i(halt_n),
        .dmack_i(dmack),
        .pm_data_cycle_i(pm_data_cycle),
        .mode_o(mode),
        .state_three_boundary_o(state_three_boundary),
        .halt_recognized_o(halt_recognized),
        .halt_stop_event_o(halt_stop_event),
        .force_fetch_issue_o(force_fetch_issue),
        .resume_event_o(resume_event),
        .release_blocked_o(release_blocked),
        .instruction_issue_inhibit_o(instruction_issue_inhibit),
        .phase_hold_o(phase_hold),
        .effective_phase_advance_o(effective_phase_advance),
        .halted_o(halted),
        .phase_conflict_o(phase_conflict)
    );

    initial begin
        past_valid = 1'b0;
        assume (reset);
    end

    always_comb begin
        assert (state_three_boundary == (
            !reset && phase_advance && phase == PHASE_STATE_3
        ));
        assert (phase_conflict == (
            !reset && mode == 2'd2 && phase_advance
            && phase != PHASE_STATE_8
        ));
        assert (effective_phase_advance == (phase_advance && !phase_hold));
        assert (!(halt_recognized && halt_stop_event));
        assert (!(halt_recognized && force_fetch_issue));
        assert (!(halt_stop_event && force_fetch_issue));
        assert (!(halt_stop_event && resume_event));
        if (halt_recognized) begin
            assert (mode == 2'd0 && !halt_n);
        end
        if (halt_stop_event) begin
            assert (mode == 2'd1);
            assert (phase == PHASE_STATE_7 && phase_advance);
        end
        if (force_fetch_issue) begin
            assert (mode == 2'd3);
            assert (phase == PHASE_STATE_8 && phase_advance);
            assert (!instruction_issue_inhibit);
        end
        if (resume_event) begin
            assert (mode == 2'd2);
            assert (phase == PHASE_STATE_8 && phase_advance);
            assert (halt_n && dmack && !phase_hold);
        end
        if (release_blocked) begin
            assert (mode == 2'd2);
            assert (phase == PHASE_STATE_8 && phase_advance);
            assert (halt_n && !dmack && phase_hold);
        end
        if (halted && !resume_event) begin
            assert (phase_hold && instruction_issue_inhibit);
        end
        if (!phase_advance) begin
            assert (!state_three_boundary);
            assert (!halt_recognized);
            assert (!halt_stop_event);
            assert (!force_fetch_issue);
            assert (!resume_event);
        end
        cover (halt_recognized && !pm_data_cycle);
        cover (halt_recognized && pm_data_cycle);
        cover (force_fetch_issue);
        cover (halt_stop_event);
        cover (release_blocked);
        cover (resume_event);
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mode == 2'd0);
        end else if ($past(halt_recognized)) begin
            if ($past(pm_data_cycle)) begin
                assert (mode == 2'd3);
            end else begin
                assert (mode == 2'd1);
            end
        end else if ($past(force_fetch_issue)) begin
            assert (mode == 2'd1);
        end else if ($past(halt_stop_event)) begin
            assert (mode == 2'd2);
        end else if ($past(resume_event)) begin
            assert (mode == 2'd0);
        end else begin
            assert (mode == $past(mode));
        end
    end
endmodule

`default_nettype wire
