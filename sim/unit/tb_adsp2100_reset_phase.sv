`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_reset_phase;
    logic clk;
    logic [2:0] stimulus;
    logic [14:0] expected_pre;
    logic [10:0] expected_post;
    logic edge_enable;
    logic clkin_rising;
    logic reset_pin;
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
    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {edge_enable, clkin_rising, reset_pin} = stimulus;
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

    initial begin
        clk = 1'b0;
        stimulus = 3'b111;
        expected_pre = '0;
        expected_post = '0;

        // Establish the architecturally required first recognized RESET edge.
        #5 clk = 1'b1;
        #5 clk = 1'b0;

        vector_file = $fopen("build/reset_phase_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open reset/phase vectors");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_pre,
                expected_post
            );
            if (scan_count == 3) begin
                #1;
                if (
                    {
                        phase, phase_valid, phase_advance,
                        reset_recognized, architectural_reset, reset_active,
                        asserted_rising_edges, release_first_rising,
                        release_event, duration_error, clkout
                    } !== expected_pre
                ) begin
                    $fatal(
                        1,
                        "reset/phase pre mismatch vector=%0d got=%h expected=%h",
                        vector_count,
                        {
                            phase, phase_valid, phase_advance,
                            reset_recognized, architectural_reset,
                            reset_active, asserted_rising_edges,
                            release_first_rising, release_event,
                            duration_error, clkout
                        },
                        expected_pre
                    );
                end
                #4 clk = 1'b1;
                #1;
                if (
                    {
                        phase, phase_valid, reset_active,
                        asserted_rising_edges, release_rising_seen,
                        duration_error, clkout
                    } !== expected_post
                ) begin
                    $fatal(
                        1,
                        "reset/phase post mismatch vector=%0d got=%h expected=%h",
                        vector_count,
                        {
                            phase, phase_valid, reset_active,
                            asserted_rising_edges, release_rising_seen,
                            duration_error, clkout
                        },
                        expected_post
                    );
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50000) begin
            $fatal(1, "insufficient reset/phase vectors: %0d", vector_count);
        end
        $display(
            "PASS original ADSP-2100 reset/phase differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
