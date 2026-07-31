`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_conditional_trap_slice;
    logic        clk;
    logic [69:0] stimulus;
    logic [20:0] expected_events;
    logic [58:0] expected_state;
    logic        reset;
    logic [2:0]  phase;
    logic        phase_advance;
    logic        execute;
    logic [23:0] opcode;
    logic        halt_recognized;
    logic        pc_setup;
    logic [13:0] pc_setup_data;
    logic        astat_setup;
    logic [7:0]  astat_setup_data;
    logic        counter_setup;
    logic [13:0] counter_setup_data;
    logic        class_valid;
    logic        action_valid;
    logic [3:0]  condition;
    logic        instruction_accepted;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        invalid_condition_state;
    logic        integration_conflict;
    logic        phase_mismatch;
    logic        condition_known;
    logic        condition_true;
    logic        pending;
    logic        pending_taken;
    logic [13:0] pc;
    logic        pc_write;
    logic [7:0]  astat;
    logic        astat_valid;
    logic [13:0] cntr;
    logic        cntr_valid;
    logic        counter_test;
    logic        counter_decrement;
    logic        trap;
    logic        trap_event;
    logic        halted;
    logic        halt_handoff;
    logic        resume_event;
    logic        phase_hold;
    logic [13:0] pma_observation;
    logic        pma_observation_valid;
    logic        pm_data_access;
    logic        dm_access;
    logic [13:0] expected_pc;
    logic        expected_astat_valid;
    logic [7:0]  expected_astat;
    logic        expected_cntr_valid;
    logic [13:0] expected_cntr;
    logic        expected_pending;
    logic        expected_pending_taken;
    logic        expected_trap;
    logic        expected_halted;
    logic        expected_halt_handoff;
    logic        expected_phase_hold;
    logic [13:0] expected_pma;
    logic        expected_pma_valid;
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        reset, phase, phase_advance, execute, opcode, halt_recognized,
        pc_setup, pc_setup_data, astat_setup, astat_setup_data,
        counter_setup, counter_setup_data
    } = stimulus;
    assign {
        expected_pc, expected_astat_valid, expected_astat,
        expected_cntr_valid, expected_cntr,
        expected_pending, expected_pending_taken, expected_trap,
        expected_halted, expected_halt_handoff, expected_phase_hold,
        expected_pma, expected_pma_valid
    } = expected_state;

    adsp2100_conditional_trap_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .execute_i(execute),
        .opcode_i(opcode),
        .halt_recognized_i(halt_recognized),
        .pc_setup_write_i(pc_setup),
        .pc_setup_data_i(pc_setup_data),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .counter_setup_write_i(counter_setup),
        .counter_setup_data_i(counter_setup_data),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .condition_o(condition),
        .instruction_accepted_o(instruction_accepted),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .invalid_condition_state_o(invalid_condition_state),
        .integration_conflict_o(integration_conflict),
        .phase_mismatch_o(phase_mismatch),
        .condition_known_o(condition_known),
        .condition_true_o(condition_true),
        .pending_o(pending),
        .pending_taken_o(pending_taken),
        .pc_o(pc),
        .pc_write_o(pc_write),
        .astat_o(astat),
        .astat_valid_o(astat_valid),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .counter_test_o(counter_test),
        .counter_decrement_o(counter_decrement),
        .trap_o(trap),
        .trap_event_o(trap_event),
        .halted_o(halted),
        .halt_handoff_o(halt_handoff),
        .resume_event_o(resume_event),
        .phase_hold_o(phase_hold),
        .pma_observation_o(pma_observation),
        .pma_observation_valid_o(pma_observation_valid),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_state = '0;
        vector_file = $fopen("build/conditional_trap_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open Type 22 vectors");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_events,
                expected_state
            );
            if (scan_count == 3) begin
                #4 clk = 1'b1;
                #2;
                if ({
                    class_valid, action_valid, condition,
                    instruction_accepted, boundary_valid, invalid_opcode,
                    invalid_condition_state, integration_conflict,
                    phase_mismatch, condition_known, condition_true,
                    pc_write, trap_event, resume_event,
                    counter_test, counter_decrement,
                    pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d actual=%06x expected=%06x stimulus=%018x",
                        vector_count,
                        {
                            class_valid, action_valid, condition,
                            instruction_accepted, boundary_valid,
                            invalid_opcode, invalid_condition_state,
                            integration_conflict, phase_mismatch,
                            condition_known, condition_true, pc_write,
                            trap_event, resume_event, counter_test,
                            counter_decrement, pm_data_access, dm_access
                        },
                        expected_events,
                        stimulus
                    );
                end
                if (pc !== expected_pc
                    || astat_valid !== expected_astat_valid
                    || cntr_valid !== expected_cntr_valid
                    || pending !== expected_pending
                    || pending_taken !== expected_pending_taken
                    || trap !== expected_trap
                    || halted !== expected_halted
                    || halt_handoff !== expected_halt_handoff
                    || phase_hold !== expected_phase_hold
                    || pma_observation !== expected_pma
                    || pma_observation_valid !== expected_pma_valid) begin
                    $fatal(1, "state mismatch vector=%0d", vector_count);
                end
                if (expected_astat_valid && astat !== expected_astat) begin
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
                end
                if (expected_cntr_valid && cntr !== expected_cntr) begin
                    $fatal(1, "CNTR mismatch vector=%0d", vector_count);
                end
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count != 50_168) begin
            $fatal(1, "unexpected vector count=%0d", vector_count);
        end
        $display(
            "PASS Type 22 phase-aware model/RTL differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
