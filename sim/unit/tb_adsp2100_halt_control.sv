`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_halt_control;
    logic clk;
    logic [7:0] stimulus;
    logic [12:0] expected_pre;
    logic [1:0] expected_post_mode;
    logic reset;
    logic [2:0] phase;
    logic phase_advance;
    logic halt_n;
    logic dmack;
    logic pm_data_cycle;
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
    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, phase, phase_advance, halt_n, dmack, pm_data_cycle
    } = stimulus;

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
        clk = 1'b0;
        stimulus = {1'b1, 3'd7, 1'b0, 1'b1, 1'b1, 1'b0};
        expected_pre = '0;
        expected_post_mode = '0;

        // Establish the architectural reset state before pre-edge checks.
        #5 clk = 1'b1;
        #5 clk = 1'b0;

        vector_file = $fopen("build/halt_control_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open HALT-controller vectors");
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
                if ({
                    mode, state_three_boundary, halt_recognized,
                    halt_stop_event, force_fetch_issue, resume_event,
                    release_blocked, instruction_issue_inhibit,
                    phase_hold, effective_phase_advance, halted,
                    phase_conflict
                } !== expected_pre) begin
                    $fatal(
                        1,
                        "HALT pre mismatch vector=%0d got=%h expected=%h",
                        vector_count,
                        {
                            mode, state_three_boundary, halt_recognized,
                            halt_stop_event, force_fetch_issue, resume_event,
                            release_blocked, instruction_issue_inhibit,
                            phase_hold, effective_phase_advance, halted,
                            phase_conflict
                        },
                        expected_pre
                    );
                end
                #4 clk = 1'b1;
                #1;
                if (mode !== expected_post_mode) begin
                    $fatal(
                        1,
                        "HALT post mode mismatch vector=%0d got=%h expected=%h",
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
            $fatal(1, "insufficient HALT vectors: %0d", vector_count);
        end
        $display(
            "PASS original ADSP-2100 HALT differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
