`default_nettype none

module adsp2100_interrupt_control_formal (
    input logic       clk,
    input logic       reset,
    input logic [2:0] phase,
    input logic       phase_advance,
    input logic [3:0] irq_n,
    input logic [4:0] icntl,
    input logic       icntl_valid,
    input logic [3:0] imask,
    input logic       imask_valid,
    input logic       service_allowed
);
    logic sample_event;
    logic [3:0] sampled_requests;
    logic [3:0] enabled_requests;
    logic recognition_event;
    logic [1:0] recognized_level;
    logic [13:0] vector_address;
    logic [3:0] edge_pending;
    logic sample_history_valid;
    logic configuration_invalid;
    logic reset_baseline_provisional;
    logic past_valid;

    adsp2100_interrupt_control dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(phase_advance), .irq_n_i(irq_n),
        .icntl_i(icntl), .icntl_valid_i(icntl_valid),
        .imask_i(imask), .imask_valid_i(imask_valid),
        .service_allowed_i(service_allowed),
        .sample_event_o(sample_event),
        .sampled_requests_o(sampled_requests),
        .enabled_requests_o(enabled_requests),
        .recognition_event_o(recognition_event),
        .recognized_level_o(recognized_level),
        .vector_address_o(vector_address),
        .edge_pending_o(edge_pending),
        .sample_history_valid_o(sample_history_valid),
        .configuration_invalid_o(configuration_invalid),
        .reset_baseline_provisional_o(reset_baseline_provisional)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (sample_event == (!reset && phase_advance && phase == 3'd6));
        assert (enabled_requests == (
            imask_valid ? (sampled_requests & imask) : 4'h0
        ));
        assert (!recognition_event || (
            sample_event && icntl_valid && imask_valid && service_allowed
        ));
        assert (vector_address == {12'h000, recognized_level});
        if (recognition_event) begin
            assert (enabled_requests[recognized_level]);
            if (enabled_requests[3]) begin
                assert (recognized_level == 2'd3);
            end else if (enabled_requests[2]) begin
                assert (recognized_level == 2'd2);
            end else if (enabled_requests[1]) begin
                assert (recognized_level == 2'd1);
            end else begin
                assert (recognized_level == 2'd0);
            end
        end
        if (!sample_event) begin
            assert (!recognition_event);
            assert (sampled_requests == 4'h0);
        end
        if (configuration_invalid) begin
            assert (sample_event && (!icntl_valid || !imask_valid));
            assert (!recognition_event);
        end
        if (reset_baseline_provisional) begin
            assert (sample_event && !sample_history_valid);
        end
        cover (recognition_event && recognized_level == 2'd0);
        cover (recognition_event && recognized_level == 2'd3);
        cover (edge_pending != 4'h0 && !service_allowed);
        cover (reset_baseline_provisional);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else begin
            if ($past(reset)) begin
                assert (edge_pending == 4'h0);
                assert (!sample_history_valid);
            end
            if (!$past(reset) && !$past(sample_event)) begin
                assert (edge_pending == $past(edge_pending));
                assert (sample_history_valid == $past(sample_history_valid));
            end
            if (
                !$past(reset) && $past(sample_event)
                && $past(recognition_event)
            ) begin
                assert (!edge_pending[$past(recognized_level)]);
            end
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
