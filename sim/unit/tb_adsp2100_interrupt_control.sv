`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_interrupt_control;
    logic clk;
    logic [20:0] stimulus;
    logic [32:0] expected_pre;
    logic [4:0] expected_post;

    logic reset;
    logic [2:0] phase;
    logic phase_advance;
    logic [3:0] irq_n;
    logic [4:0] icntl;
    logic icntl_valid;
    logic [3:0] imask;
    logic imask_valid;
    logic service_allowed;
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

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, phase, phase_advance, irq_n, icntl, icntl_valid,
        imask, imask_valid, service_allowed
    } = stimulus;
    adsp2100_interrupt_control dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .irq_n_i(irq_n),
        .icntl_i(icntl),
        .icntl_valid_i(icntl_valid),
        .imask_i(imask),
        .imask_valid_i(imask_valid),
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

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_pre = '0;
        expected_post = '0;
        vector_file = $fopen("build/interrupt_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open interrupt vectors");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file, "%h %h %h\n",
                stimulus, expected_pre, expected_post
            );
            if (scan_count == 3) begin
                #2;
                if ({
                    sample_event, sampled_requests, enabled_requests,
                    recognition_event, recognized_level, vector_address,
                    edge_pending, sample_history_valid,
                    configuration_invalid, reset_baseline_provisional
                } !== expected_pre) begin
                    $display(
                        "actual=%h expected=%h stimulus=%h",
                        {
                            sample_event, sampled_requests, enabled_requests,
                            recognition_event, recognized_level,
                            vector_address, edge_pending,
                            sample_history_valid, configuration_invalid,
                            reset_baseline_provisional
                        }, expected_pre, stimulus
                    );
                    $fatal(1, "interrupt pre-edge mismatch at %0d", vector_count);
                end
                clk = 1'b1;
                #2;
                if ({edge_pending, sample_history_valid} !== expected_post) begin
                    $display(
                        "post_actual=%h post_expected=%h stimulus=%h",
                        {edge_pending, sample_history_valid},
                        expected_post, stimulus
                    );
                    $fatal(1, "interrupt post-edge mismatch at %0d", vector_count);
                end
                clk = 1'b0;
                #1;
                vector_count = vector_count + 1;
            end
        end
        $display("PASS interrupt recognition vectors: %0d", vector_count);
        $finish;
    end
endmodule

`default_nettype wire
