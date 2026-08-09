`default_nettype none

// Bounded composition of ordinary linear PM fetch ownership and HALT control.
module adsp2100_linear_halt_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        halt_n_i,
    input  logic        dmack_i,
    input  logic [3:0]  irq_n_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,
    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [5:0]  probe_code_i,

    output logic [1:0]  halt_mode_o,
    output logic        state_three_boundary_o,
    output logic        halt_recognized_o,
    output logic        halt_stop_event_o,
    output logic        resume_event_o,
    output logic        release_blocked_o,
    output logic        instruction_issue_inhibit_o,
    output logic        phase_hold_o,
    output logic        effective_phase_advance_o,
    output logic        halted_o,
    output logic        halt_phase_conflict_o,
    output logic        trap_o,
    output logic        trap_event_o,
    output logic        trap_halt_recognized_o,
    output logic        trap_handoff_o,
    output logic        trap_resume_event_o,
    output logic        trap_release_blocked_o,
    output logic        trap_halt_conflict_o,

    output logic        issue_boundary_o,
    output logic        instruction_setup_accepted_o,
    output logic        instruction_issue_o,
    output logic        retire_event_o,
    output logic        instruction_valid_o,
    output logic        transaction_pending_o,
    output logic        unsupported_instruction_o,
    output logic        reserved_subencoding_o,
    output logic        phase_conflict_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        provisional_source_extension_o,
    output logic [13:0] pc_o,
    output logic [23:0] opcode_o,

    output logic [15:0] probe_data_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [4:0]  icntl_o,
    output logic [3:0]  imask_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic [7:0]  px_o,
    output logic [7:0]  sstat_o,
    output logic        alternate_bank_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,

    output logic        pm_request_accepted_o,
    output logic        pm_completion_event_o,
    output logic        pm_read_sample_event_o,
    output logic        pm_bus_active_o,
    output logic        pm_address_output_enable_o,
    output logic        pm_control_output_enable_o,
    output logic        pm_data_output_enable_o,
    output logic [13:0] pma_o,
    output logic        pma_valid_o,
    output logic        pmda_o,
    output logic        pmda_valid_o,
    output logic        pms_n_o,
    output logic        pmrd_n_o,
    output logic        pmwr_n_o,
    output logic [23:0] pmd_write_data_o,
    output logic        pmd_write_data_valid_o
);
    localparam logic [2:0] PHASE_STATE_8 = 3'd7;
    localparam logic [1:0] HALT_MODE_RUNNING = 2'd0;

    logic ordinary_force_fetch_issue;
    logic [1:0] halt_mode_raw;
    logic halt_resume_event_raw;
    logic halt_release_blocked_raw;
    logic halt_instruction_issue_inhibit_raw;
    logic halt_phase_hold_raw;
    logic halt_effective_phase_advance_raw;
    logic halted_raw;
    logic halt_phase_conflict_raw;
    logic core_trap_event;
    logic [27:0] interrupt_unused;
    logic trap_q;
    logic trap_handoff_q;
    logic trap_active;
    logic trap_phase_hold;
    logic trap_phase_conflict;

    assign halt_mode_o = halt_mode_raw;
    assign trap_o = trap_q;
    assign trap_handoff_o = trap_handoff_q;
    assign trap_active = trap_q || trap_handoff_q;
    assign trap_halt_recognized_o = (
        !reset_i && trap_q && phase_advance_i
        && (phase_i == PHASE_STATE_8) && !halt_n_i
    );
    assign trap_resume_event_o = (
        !reset_i && trap_handoff_q && phase_advance_i
        && (phase_i == PHASE_STATE_8) && halt_n_i && dmack_i
    );
    assign trap_release_blocked_o = (
        !reset_i && trap_handoff_q && phase_advance_i
        && (phase_i == PHASE_STATE_8) && halt_n_i && !dmack_i
    );
    assign trap_phase_hold = (
        !reset_i && trap_active && !trap_resume_event_o
    );
    assign trap_phase_conflict = (
        !reset_i && trap_active && phase_advance_i
        && (phase_i != PHASE_STATE_8)
    );
    assign trap_halt_conflict_o = (
        !reset_i && core_trap_event
        && (
            (halt_mode_raw != HALT_MODE_RUNNING)
            || halt_stop_event_o
        )
    );
    assign resume_event_o = halt_resume_event_raw || trap_resume_event_o;
    assign release_blocked_o = (
        halt_release_blocked_raw || trap_release_blocked_o
    );
    assign instruction_issue_inhibit_o = (
        halt_instruction_issue_inhibit_raw || trap_phase_hold
    );
    assign phase_hold_o = halt_phase_hold_raw || trap_phase_hold;
    assign effective_phase_advance_o = (
        halt_effective_phase_advance_raw && !trap_phase_hold
    );
    assign halted_o = halted_raw || trap_active;
    assign halt_phase_conflict_o = (
        halt_phase_conflict_raw || trap_phase_conflict
        || trap_halt_conflict_o
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            trap_q <= 1'b0;
            trap_handoff_q <= 1'b0;
        end else if (core_trap_event) begin
            trap_q <= 1'b1;
            trap_handoff_q <= 1'b0;
        end else if (trap_halt_recognized_o) begin
            trap_q <= 1'b0;
            trap_handoff_q <= 1'b1;
        end else if (trap_resume_event_o) begin
            trap_q <= 1'b0;
            trap_handoff_q <= 1'b0;
        end
    end

    adsp2100_halt_control halt_control (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .halt_n_i(halt_n_i),
        .dmack_i(dmack_i),
        .pm_data_cycle_i(1'b0),
        .service_inhibit_i(1'b0),
        .mode_o(halt_mode_raw),
        .state_three_boundary_o(state_three_boundary_o),
        .halt_recognized_o(halt_recognized_o),
        .halt_stop_event_o(halt_stop_event_o),
        .force_fetch_issue_o(ordinary_force_fetch_issue),
        .resume_event_o(halt_resume_event_raw),
        .release_blocked_o(halt_release_blocked_raw),
        .instruction_issue_inhibit_o(halt_instruction_issue_inhibit_raw),
        .phase_hold_o(halt_phase_hold_raw),
        .effective_phase_advance_o(halt_effective_phase_advance_raw),
        .halted_o(halted_raw),
        .phase_conflict_o(halt_phase_conflict_raw)
    );

    /* verilator lint_off PINCONNECTEMPTY */
    adsp2100_linear_core_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(effective_phase_advance_o),
        .interrupt_sample_advance_i(1'b0),
        .instruction_issue_inhibit_i(instruction_issue_inhibit_o),
        .bus_relinquished_i(1'b0),
        .instruction_setup_i(instruction_setup_i),
        .instruction_setup_pc_i(instruction_setup_pc_i),
        .instruction_setup_opcode_i(instruction_setup_opcode_i),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .dmd_read_data_i(16'h0000),
        .dmd_read_data_valid_i(1'b0),
        .irq_n_i(irq_n_i),
        .probe_code_i(probe_code_i),
        .issue_boundary_o(issue_boundary_o),
        .instruction_setup_accepted_o(instruction_setup_accepted_o),
        .instruction_issue_o(instruction_issue_o),
        .retire_event_o(retire_event_o),
        .trap_event_o(core_trap_event),
        .interrupt_recognition_event_o(interrupt_unused[0]),
        .interrupt_entry_event_o(interrupt_unused[1]),
        .interrupt_vector_issue_event_o(interrupt_unused[2]),
        .interrupt_vector_fetch_event_o(interrupt_unused[3]),
        .interrupt_level_o(interrupt_unused[5:4]),
        .interrupt_vector_o(interrupt_unused[19:6]),
        .interrupt_pending_o(interrupt_unused[23:20]),
        .interrupt_vectoring_o(interrupt_unused[24]),
        .interrupt_configuration_invalid_o(interrupt_unused[25]),
        .interrupt_reset_baseline_provisional_o(interrupt_unused[26]),
        .interrupt_adjacent_control_conflict_o(interrupt_unused[27]),
        .instruction_valid_o(instruction_valid_o),
        .transaction_pending_o(transaction_pending_o),
        .unsupported_instruction_o(unsupported_instruction_o),
        .reserved_subencoding_o(reserved_subencoding_o),
        .phase_conflict_o(phase_conflict_o),
        .integration_conflict_o(integration_conflict_o),
        .internal_conflict_o(internal_conflict_o),
        .provisional_source_extension_o(provisional_source_extension_o),
        .pc_o(pc_o),
        .opcode_o(opcode_o),
        .fetched_dm_request_candidate_o(),
        .fetched_dm_request_presented_o(),
        .fetched_dm_request_address_o(),
        .fetched_dm_request_address_valid_o(),
        .fetched_dm_request_write_o(),
        .fetched_dm_request_write_data_o(),
        .fetched_dm_request_write_data_valid_o(),
        .probe_data_o(probe_data_o),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .cntr_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .px_o(px_o),
        .sstat_o(sstat_o),
        .alternate_bank_o(alternate_bank_o),
        .count_stack_depth_o(count_stack_depth_o),
        .count_stack_overflow_o(count_stack_overflow_o),
        .pm_request_accepted_o(pm_request_accepted_o),
        .pm_completion_event_o(pm_completion_event_o),
        .pm_read_sample_event_o(pm_read_sample_event_o),
        .pm_bus_active_o(pm_bus_active_o),
        .pm_address_output_enable_o(pm_address_output_enable_o),
        .pm_control_output_enable_o(pm_control_output_enable_o),
        .pm_data_output_enable_o(pm_data_output_enable_o),
        .pma_o(pma_o),
        .pma_valid_o(pma_valid_o),
        .pmda_o(pmda_o),
        .pmda_valid_o(pmda_valid_o),
        .pms_n_o(pms_n_o),
        .pmrd_n_o(pmrd_n_o),
        .pmwr_n_o(pmwr_n_o),
        .pmd_write_data_o(pmd_write_data_o),
        .pmd_write_data_valid_o(pmd_write_data_valid_o)
    );
    /* verilator lint_on PINCONNECTEMPTY */

    assign trap_event_o = core_trap_event;

`ifndef SYNTHESIS
    always_comb begin
        assert (^interrupt_unused == ^interrupt_unused);
        // This wrapper owns ordinary instruction fetches only. The PM-data
        // discriminator is tied low, so the forced-fetch state is unreachable.
        assert (!ordinary_force_fetch_issue);
        assert (
            halt_effective_phase_advance_raw
            == (phase_advance_i && !halt_phase_hold_raw)
        );
        if (instruction_issue_inhibit_o) begin
            assert (!instruction_issue_o);
        end
        if (phase_hold_o) begin
            assert (!effective_phase_advance_o);
            assert (!instruction_issue_o);
            assert (!retire_event_o);
        end
        if (halt_stop_event_o && transaction_pending_o) begin
            assert (retire_event_o);
            assert (pm_completion_event_o);
        end
        if (resume_event_o && instruction_valid_o) begin
            assert (issue_boundary_o);
        end
        if (trap_event_o) begin
            assert (retire_event_o);
            assert (pm_completion_event_o);
            assert (phase_i == 3'd6 && phase_advance_i);
        end
        if (trap_halt_recognized_o) begin
            assert (trap_o && !halt_n_i);
            assert (phase_i == PHASE_STATE_8);
        end
        if (trap_resume_event_o) begin
            assert (trap_handoff_o && halt_n_i && dmack_i);
            assert (phase_i == PHASE_STATE_8);
        end
        if (trap_release_blocked_o) begin
            assert (trap_handoff_o && halt_n_i && !dmack_i);
            assert (phase_hold_o);
        end
        if (halted_o && !halt_phase_conflict_o) begin
            assert (phase_i == 3'd7);
        end
    end
`endif
endmodule

`default_nettype wire
