`default_nettype none

// Original ADSP-2100 four-pin interrupt recognition boundary.
//
// IRQ0-IRQ3 are sampled only at the enabled state-7 boundary. ICNTL[3:0]
// selects edge sensitivity, IMASK enables requests, and IRQ3 has highest
// priority. Entry sequencing and stack effects belong to the fetched owner.
module adsp2100_interrupt_control (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic [3:0]  irq_n_i,
    input  logic [4:0]  icntl_i,
    input  logic        icntl_valid_i,
    input  logic [3:0]  imask_i,
    input  logic        imask_valid_i,
    input  logic        service_allowed_i,

    output logic        sample_event_o,
    output logic [3:0]  sampled_requests_o,
    output logic [3:0]  enabled_requests_o,
    output logic        recognition_event_o,
    output logic [1:0]  recognized_level_o,
    output logic [13:0] vector_address_o,
    output logic [3:0]  edge_pending_o,
    output logic        sample_history_valid_o,
    output logic        configuration_invalid_o,
    output logic        reset_baseline_provisional_o
);
    localparam logic [2:0] PHASE_STATE_7 = 3'd6;

    logic [3:0] previous_irq_n_q;
    logic       sample_history_valid_q;
    logic [3:0] edge_pending_q;
    logic [3:0] active_requests;
    logic [3:0] detected_edges;
    logic [3:0] edge_pending_with_sample;
    logic       unused_observation;

    assign sample_event_o = (
        !reset_i && phase_advance_i && (phase_i == PHASE_STATE_7)
    );
    assign active_requests = ~irq_n_i;
    assign detected_edges = (
        sample_history_valid_q && icntl_valid_i
        ? (previous_irq_n_q & active_requests & icntl_i[3:0])
        : 4'h0
    );
    assign edge_pending_with_sample = edge_pending_q | detected_edges;
    assign sampled_requests_o = (
        sample_event_o && icntl_valid_i
        ? (
            edge_pending_with_sample
            | (active_requests & ~icntl_i[3:0])
        )
        : 4'h0
    );
    assign enabled_requests_o = (
        imask_valid_i ? (sampled_requests_o & imask_i) : 4'h0
    );
    assign recognition_event_o = (
        sample_event_o && icntl_valid_i && imask_valid_i
        && service_allowed_i && (enabled_requests_o != 4'h0)
    );

    always_comb begin
        recognized_level_o = 2'd0;
        if (recognition_event_o) begin
            if (enabled_requests_o[3]) begin
                recognized_level_o = 2'd3;
            end else if (enabled_requests_o[2]) begin
                recognized_level_o = 2'd2;
            end else if (enabled_requests_o[1]) begin
                recognized_level_o = 2'd1;
            end
        end
    end

    assign vector_address_o = {12'h000, recognized_level_o};
    assign edge_pending_o = edge_pending_q;
    assign sample_history_valid_o = sample_history_valid_q;
    assign configuration_invalid_o = (
        sample_event_o && (!icntl_valid_i || !imask_valid_i)
    );
    // OQ-025: the first post-reset comparison sample is not sourced. This
    // bounded implementation uses it only as a baseline and exposes that
    // provisional boundary rather than manufacturing a high-to-low edge.
    assign reset_baseline_provisional_o = (
        sample_event_o && !sample_history_valid_q
    );
    // ICNTL[4] controls the separate entry-mask transformation, not request
    // sensitivity. Observe it here so whole-register interfaces remain clean.
    assign unused_observation = icntl_i[4];

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            previous_irq_n_q <= 4'hf;
            sample_history_valid_q <= 1'b0;
            edge_pending_q <= 4'h0;
        end else if (sample_event_o) begin
            previous_irq_n_q <= irq_n_i;
            sample_history_valid_q <= 1'b1;
            edge_pending_q <= edge_pending_with_sample;
            if (recognition_event_o) begin
                edge_pending_q[recognized_level_o] <= 1'b0;
            end
        end
    end

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        if (recognition_event_o) begin
            assert (sample_event_o && service_allowed_i);
            assert (enabled_requests_o[recognized_level_o]);
            assert (vector_address_o == {12'h000, recognized_level_o});
        end
        if (enabled_requests_o[3]) begin
            assert (!recognition_event_o || recognized_level_o == 2'd3);
        end else if (enabled_requests_o[2]) begin
            assert (!recognition_event_o || recognized_level_o == 2'd2);
        end else if (enabled_requests_o[1]) begin
            assert (!recognition_event_o || recognized_level_o == 2'd1);
        end
        if (!sample_event_o) begin
            assert (!recognition_event_o);
            assert (sampled_requests_o == 4'h0);
        end
    end
`endif
endmodule

`default_nettype wire
