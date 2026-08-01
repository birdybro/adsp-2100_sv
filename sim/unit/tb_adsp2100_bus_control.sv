`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_bus_control;
    logic clk;
    logic [5:0] stimulus;
    logic [16:0] expected_pre;
    logic [2:0] expected_post_mode;
    logic reset;
    logic [2:0] phase;
    logic phase_advance;
    logic br_n;
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
    logic normal_bus_relinquished;
    logic normal_bg_n;
    logic reset_br_request;
    logic native_bg_n;
    logic native_bus_relinquished;
    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {reset, phase, phase_advance, br_n} = stimulus;

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
        .bus_relinquished_o(normal_bus_relinquished),
        .bg_n_o(normal_bg_n),
        .reset_br_request_o(reset_br_request)
    );

    adsp2100_reset_bus_grant native_reset_path (
        .reset_active_i(reset),
        .br_n_i(br_n),
        .normal_bg_n_i(normal_bg_n),
        .normal_bus_relinquished_i(normal_bus_relinquished),
        .bg_n_o(native_bg_n),
        .bus_relinquished_o(native_bus_relinquished)
    );

    initial begin
        clk = 1'b0;
        stimulus = 6'h23;
        expected_pre = '0;
        expected_post_mode = '0;

        // Establish the required architectural RESET before observation.
        #5 clk = 1'b1;
        #5 clk = 1'b0;

        vector_file = $fopen("build/bus_control_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open BR/BG vectors");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_pre,
                expected_post_mode
            );
            if (scan_count == 3) begin
                #1;
                if (
                    {
                        mode, state_three_boundary, request_recognized,
                        grant_assert_event, release_recognized,
                        grant_release_event, resume_event,
                        request_withdrawn, release_cancelled,
                        instruction_issue_inhibit,
                        normal_bus_relinquished, normal_bg_n,
                        reset_br_request, native_bg_n,
                        native_bus_relinquished
                    } !== expected_pre
                ) begin
                    $fatal(
                        1,
                        "BR/BG pre mismatch vector=%0d got=%h expected=%h",
                        vector_count,
                        {
                            mode, state_three_boundary, request_recognized,
                            grant_assert_event, release_recognized,
                            grant_release_event, resume_event,
                            request_withdrawn, release_cancelled,
                            instruction_issue_inhibit,
                            normal_bus_relinquished, normal_bg_n,
                            reset_br_request, native_bg_n,
                            native_bus_relinquished
                        },
                        expected_pre
                    );
                end
                #4 clk = 1'b1;
                #1;
                if (mode !== expected_post_mode) begin
                    $fatal(
                        1,
                        "BR/BG post mode mismatch vector=%0d got=%h expected=%h",
                        vector_count,
                        mode,
                        expected_post_mode
                    );
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50000) begin
            $fatal(1, "insufficient BR/BG vectors: %0d", vector_count);
        end
        $display(
            "PASS original ADSP-2100 BR/BG differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
