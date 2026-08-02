`default_nettype none

module adsp2100_linear_halt_control_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        halt_n,
    input logic        dmack,
    input logic [3:0]  irq_n,
    input logic        instruction_setup,
    input logic [13:0] instruction_setup_pc,
    input logic [23:0] instruction_setup_opcode,
    input logic [23:0] pmd_read_data,
    input logic        pmd_read_data_valid,
    input logic [5:0]  probe_code
);
    logic [1:0] halt_mode;
    logic halt_recognized;
    logic halt_stop_event;
    logic resume_event;
    logic release_blocked;
    logic instruction_issue_inhibit;
    logic phase_hold;
    logic effective_phase_advance;
    logic halted;
    logic halt_phase_conflict;
    logic trap;
    logic trap_event;
    logic trap_halt_recognized;
    logic trap_handoff;
    logic trap_resume_event;
    logic trap_release_blocked;
    logic trap_halt_conflict;
    logic issue_boundary;
    logic instruction_issue;
    logic retire_event;
    logic instruction_valid;
    logic transaction_pending;
    logic [13:0] pc;
    logic [23:0] opcode;
    logic pm_completion_event;
    logic pm_bus_active;
    logic pm_address_output_enable;
    logic pm_control_output_enable;
    logic pm_data_output_enable;
    logic [13:0] pma;
    logic pma_valid;
    logic pms_n;
    logic pmrd_n;
    logic pmwr_n;
    logic past_valid;

    adsp2100_linear_halt_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .halt_n_i(halt_n),
        .dmack_i(dmack),
        .irq_n_i(irq_n),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(instruction_setup_pc),
        .instruction_setup_opcode_i(instruction_setup_opcode),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .probe_code_i(probe_code),
        .halt_mode_o(halt_mode),
        .state_three_boundary_o(),
        .halt_recognized_o(halt_recognized),
        .halt_stop_event_o(halt_stop_event),
        .resume_event_o(resume_event),
        .release_blocked_o(release_blocked),
        .instruction_issue_inhibit_o(instruction_issue_inhibit),
        .phase_hold_o(phase_hold),
        .effective_phase_advance_o(effective_phase_advance),
        .halted_o(halted),
        .halt_phase_conflict_o(halt_phase_conflict),
        .trap_o(trap),
        .trap_event_o(trap_event),
        .trap_halt_recognized_o(trap_halt_recognized),
        .trap_handoff_o(trap_handoff),
        .trap_resume_event_o(trap_resume_event),
        .trap_release_blocked_o(trap_release_blocked),
        .trap_halt_conflict_o(trap_halt_conflict),
        .issue_boundary_o(issue_boundary),
        .instruction_setup_accepted_o(),
        .instruction_issue_o(instruction_issue),
        .retire_event_o(retire_event),
        .instruction_valid_o(instruction_valid),
        .transaction_pending_o(transaction_pending),
        .unsupported_instruction_o(),
        .reserved_subencoding_o(),
        .phase_conflict_o(),
        .integration_conflict_o(),
        .internal_conflict_o(),
        .provisional_source_extension_o(),
        .pc_o(pc),
        .opcode_o(opcode),
        .probe_data_o(),
        .astat_o(),
        .mstat_o(),
        .icntl_o(),
        .imask_o(),
        .cntr_o(),
        .cntr_valid_o(),
        .px_o(),
        .sstat_o(),
        .alternate_bank_o(),
        .count_stack_depth_o(),
        .count_stack_overflow_o(),
        .pm_request_accepted_o(),
        .pm_completion_event_o(pm_completion_event),
        .pm_read_sample_event_o(),
        .pm_bus_active_o(pm_bus_active),
        .pm_address_output_enable_o(pm_address_output_enable),
        .pm_control_output_enable_o(pm_control_output_enable),
        .pm_data_output_enable_o(pm_data_output_enable),
        .pma_o(pma),
        .pma_valid_o(pma_valid),
        .pmda_o(),
        .pmda_valid_o(),
        .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n),
        .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(),
        .pmd_write_data_valid_o()
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (halt_mode <= 2'd2);
        assert (effective_phase_advance == (phase_advance && !phase_hold));
        if (instruction_issue_inhibit) begin
            assert (!instruction_issue);
        end
        if (phase_hold) begin
            assert (halted);
            assert (!effective_phase_advance);
            assert (!retire_event);
        end
        if (halt_recognized) begin
            assert (phase == 3'd2 && phase_advance && !halt_n);
        end
        if (halt_stop_event && transaction_pending) begin
            assert (phase == 3'd6 && phase_advance);
            assert (retire_event && pm_completion_event);
        end
        if (resume_event) begin
            assert (phase == 3'd7 && phase_advance && halt_n && dmack);
            assert (issue_boundary);
        end
        if (release_blocked) begin
            assert (phase == 3'd7 && halt_n && !dmack);
            assert (phase_hold);
        end
        if (halted && !halt_phase_conflict) begin
            assert (phase == 3'd7);
        end
        if (trap_event) begin
            assert (retire_event && pm_completion_event);
            assert (phase == 3'd6 && phase_advance);
        end
        if (trap_halt_recognized) begin
            assert (trap && phase == 3'd7 && !halt_n);
        end
        if (trap_resume_event) begin
            assert (trap_handoff && phase == 3'd7 && halt_n && dmack);
        end
        if (trap_release_blocked) begin
            assert (trap_handoff && phase == 3'd7 && halt_n && !dmack);
            assert (phase_hold);
        end
        if (trap_halt_conflict) begin
            assert (trap_event);
            assert (halt_phase_conflict);
        end
        cover (halt_recognized && transaction_pending);
        cover (halt_stop_event && retire_event);
        cover (halted && pm_bus_active && pma_valid);
        cover (release_blocked);
        cover (resume_event && instruction_issue);
        cover (trap_event);
        cover (trap_halt_recognized);
        cover (trap_release_blocked);
        cover (trap_resume_event && instruction_issue);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(phase_hold) && !reset) begin
            assume (phase == 3'd7);
            assert (pc == $past(pc));
            assert (opcode == $past(opcode));
            assert (instruction_valid == $past(instruction_valid));
            assert (pm_bus_active == $past(pm_bus_active));
            assert (pm_address_output_enable ==
                    $past(pm_address_output_enable));
            assert (pm_control_output_enable ==
                    $past(pm_control_output_enable));
            assert (pm_data_output_enable ==
                    $past(pm_data_output_enable));
            assert (pma == $past(pma));
            assert (pms_n == $past(pms_n));
            assert (pmrd_n == $past(pmrd_n));
            assert (pmwr_n == $past(pmwr_n));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
