`default_nettype none

module adsp2100_conditional_trap_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        halt_recognized,
    input logic        pc_setup,
    input logic [13:0] pc_setup_data,
    input logic        astat_setup,
    input logic [7:0]  astat_setup_data,
    input logic        counter_setup,
    input logic [13:0] counter_setup_data
);
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
    logic        expected_class;
    logic [2:0]  setup_count;
    logic        past_valid;

    assign expected_class = ((opcode & 24'hfffff0) == 24'h080000);
    assign setup_count = (
        {2'b00, pc_setup}
        + {2'b00, astat_setup}
        + {2'b00, counter_setup}
    );

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

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_class);
        assert (condition == (expected_class ? opcode[3:0] : 4'h0));
        assert (
            integration_conflict
            == (
                !reset
                && ((execute && setup_count != 3'd0) || setup_count > 3'd1)
            )
        );
        assert (!(counter_test || counter_decrement));
        assert (!pm_data_access && !dm_access);
        assert (phase_hold == halted);
        assert (pma_observation == pc);
        assert (pma_observation_valid == halted);
        assert (!halt_handoff || halted);
        assert (!trap || halted);
        assert (!instruction_accepted || (condition_known && pending));
        assert (!condition_true || instruction_accepted);
        assert (!condition_known || instruction_accepted);
        assert (!invalid_opcode || !instruction_accepted);
        cover (trap && pending == 1'b0 && pc == 14'h1555);
        cover (halt_handoff && !trap);
        cover (resume_event && !halted);
        cover (boundary_valid && !trap_event);
        cover (invalid_condition_state);
        cover (phase_mismatch);
        cover (astat == 8'h55 && cntr == 14'h1555);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (pc == 14'h0004);
            assert (!astat_valid && !cntr_valid);
            assert (!pending && !trap && !halted && !halt_handoff);
        end else begin
            if ($past(
                pending && !halted && phase_advance && phase == 3'd6
            )) begin
                assert (pc == ($past(pc) + 14'h0001));
                assert (pc_write && boundary_valid);
                assert (!pending && !pending_taken);
                assert (trap_event == $past(pending_taken));
                if ($past(pending_taken)) begin
                    assert (trap && halted && phase_hold);
                end
            end
            if ($past(trap && halt_recognized)) begin
                assert (!trap && halted && halt_handoff);
            end
            if ($past(halt_handoff && !halt_recognized)) begin
                assert (!halted && !halt_handoff && resume_event);
            end
            if ($past(pending && !phase_advance && !halted)) begin
                assert (pending == $past(pending));
                assert (pending_taken == $past(pending_taken));
            end
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
