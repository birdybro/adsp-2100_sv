`default_nettype none

// Original ADSP-2100 RESET recognition and eight-state phase owner.
//
// edge_enable_i represents one CLKIN edge on the portable FPGA clock;
// clkin_rising_i labels its polarity. No generated or gated clock is used.
// A too-short RESET assertion fails closed in state 4 because behavior below
// the documented four-CLKIN-cycle minimum is not architecturally defined.
module adsp2100_reset_phase (
    input  logic       clk_i,
    input  logic       edge_enable_i,
    input  logic       clkin_rising_i,
    input  logic       reset_pin_i,

    output logic [2:0] phase_o,
    output logic       phase_valid_o,
    output logic       phase_advance_o,
    output logic       reset_recognized_o,
    output logic       architectural_reset_o,
    output logic       reset_active_o,
    output logic [2:0] asserted_rising_edges_o,
    output logic       release_rising_seen_o,
    output logic       release_first_rising_o,
    output logic       release_event_o,
    output logic       duration_error_o,
    output logic       clkout_o
);
    import adsp2100_pkg::*;

    localparam logic [2:0] MINIMUM_RESET_CYCLES = 3'd4;

    phase_state_t phase_q;
    logic phase_valid_q;
    logic reset_active_q;
    logic [2:0] asserted_rising_edges_q;
    logic release_rising_seen_q;
    logic duration_error_q;
    logic normal_advance;
    logic valid_release_sample;

    assign reset_recognized_o = (
        edge_enable_i && clkin_rising_i && reset_pin_i
    );
    assign valid_release_sample = (
        edge_enable_i && clkin_rising_i && !reset_pin_i
        && reset_active_q
        && asserted_rising_edges_q == MINIMUM_RESET_CYCLES
        && !duration_error_q
    );
    assign release_first_rising_o = (
        valid_release_sample && !release_rising_seen_q
    );
    assign release_event_o = (
        valid_release_sample && release_rising_seen_q
    );
    assign normal_advance = (
        phase_valid_q && !reset_active_q && edge_enable_i
        && !reset_recognized_o
    );
    assign phase_advance_o = normal_advance || release_event_o;
    assign architectural_reset_o = (
        reset_recognized_o || (reset_active_q && !release_event_o)
    );

    assign phase_o = phase_q;
    assign phase_valid_o = phase_valid_q;
    assign reset_active_o = reset_active_q;
    assign asserted_rising_edges_o = asserted_rising_edges_q;
    assign release_rising_seen_o = release_rising_seen_q;
    assign duration_error_o = duration_error_q;
    assign clkout_o = (
        phase_valid_q && !reset_active_q
        && (
            phase_q == PHASE_STATE_8
            || phase_q == PHASE_STATE_1
            || phase_q == PHASE_STATE_2
            || phase_q == PHASE_STATE_3
        )
    );

    always_ff @(posedge clk_i) begin
        if (reset_recognized_o) begin
            phase_q <= PHASE_STATE_4;
            phase_valid_q <= 1'b1;
            reset_active_q <= 1'b1;
            release_rising_seen_q <= 1'b0;
            duration_error_q <= 1'b0;
            if (
                reset_active_q
                && !duration_error_q
                && !release_rising_seen_q
                && asserted_rising_edges_q < MINIMUM_RESET_CYCLES
            ) begin
                asserted_rising_edges_q <= asserted_rising_edges_q + 3'd1;
            end else if (
                reset_active_q
                && !duration_error_q
                && !release_rising_seen_q
            ) begin
                asserted_rising_edges_q <= MINIMUM_RESET_CYCLES;
            end else begin
                asserted_rising_edges_q <= 3'd1;
            end
        end else if (reset_active_q) begin
            if (edge_enable_i && clkin_rising_i && !reset_pin_i) begin
                if (asserted_rising_edges_q < MINIMUM_RESET_CYCLES) begin
                    duration_error_q <= 1'b1;
                end else if (!duration_error_q) begin
                    if (!release_rising_seen_q) begin
                        release_rising_seen_q <= 1'b1;
                    end else begin
                        phase_q <= PHASE_STATE_5;
                        reset_active_q <= 1'b0;
                        release_rising_seen_q <= 1'b0;
                    end
                end
            end
        end else if (normal_advance) begin
            phase_q <= phase_state_t'(phase_q + 3'd1);
        end
    end

`ifndef SYNTHESIS
    always_comb begin
        if (reset_active_q) begin
            assert (phase_q == PHASE_STATE_4);
            assert (!clkout_o);
        end
        if (release_event_o) begin
            assert (phase_q == PHASE_STATE_4);
            assert (phase_advance_o);
            assert (!architectural_reset_o);
        end
        if (duration_error_q) begin
            assert (reset_active_q);
            assert (!release_event_o);
        end
        if (!edge_enable_i) begin
            assert (!phase_advance_o);
            assert (!reset_recognized_o);
            assert (!release_event_o);
        end
        if (reset_recognized_o) begin
            assert (!phase_advance_o);
        end
    end
`endif
endmodule

`default_nettype wire
