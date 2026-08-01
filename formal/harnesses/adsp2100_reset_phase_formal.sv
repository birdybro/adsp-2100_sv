`default_nettype none

module adsp2100_reset_phase_formal (
    input logic clk,
    input logic edge_enable,
    input logic clkin_rising,
    input logic reset_pin
);
    import adsp2100_pkg::*;

    logic [2:0] phase;
    logic phase_valid;
    logic phase_advance;
    logic reset_recognized;
    logic architectural_reset;
    logic reset_active;
    logic [2:0] asserted_rising_edges;
    logic release_rising_seen;
    logic release_first_rising;
    logic release_event;
    logic duration_error;
    logic clkout;
    logic past_valid;

    adsp2100_reset_phase dut (
        .clk_i(clk),
        .edge_enable_i(edge_enable),
        .clkin_rising_i(clkin_rising),
        .reset_pin_i(reset_pin),
        .phase_o(phase),
        .phase_valid_o(phase_valid),
        .phase_advance_o(phase_advance),
        .reset_recognized_o(reset_recognized),
        .architectural_reset_o(architectural_reset),
        .reset_active_o(reset_active),
        .asserted_rising_edges_o(asserted_rising_edges),
        .release_rising_seen_o(release_rising_seen),
        .release_first_rising_o(release_first_rising),
        .release_event_o(release_event),
        .duration_error_o(duration_error),
        .clkout_o(clkout)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (reset_recognized == (
            edge_enable && clkin_rising && reset_pin
        ));
        assert (!reset_recognized || architectural_reset);
        assert (!reset_recognized || !phase_advance);
        assert (!release_event || phase_advance);
        assert (!release_event || !architectural_reset);
        assert (!release_first_rising || architectural_reset);
        assert (!duration_error || reset_active);
        assert (phase_valid || !clkout);
        if (reset_active) begin
            assert (phase == PHASE_STATE_4);
            assert (!clkout);
        end
        if (!edge_enable) begin
            assert (!phase_advance);
            assert (!reset_recognized);
            assert (!release_event);
        end
        if (release_event) begin
            assert (asserted_rising_edges == 3'd4);
            assert (release_rising_seen);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && $past(reset_recognized)) begin
            assert (phase_valid);
            assert (phase == PHASE_STATE_4);
            assert (reset_active);
            assert (asserted_rising_edges >= 3'd1);
            assert (asserted_rising_edges <= 3'd4);
        end
        if (past_valid && $past(release_event)) begin
            assert (phase_valid);
            assert (phase == PHASE_STATE_5);
            assert (!reset_active);
            assert (!release_rising_seen);
        end
        if (past_valid && $past(duration_error && !reset_recognized)) begin
            assert (duration_error);
            assert (reset_active);
            assert (phase == PHASE_STATE_4);
        end
        cover (past_valid && $past(release_event) && phase == PHASE_STATE_5);
        cover (past_valid && $past(reset_recognized) && reset_active);
        cover (duration_error);
    end
endmodule

`default_nettype wire
