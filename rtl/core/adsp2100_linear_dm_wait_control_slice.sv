`default_nettype none

// Bounded ordinary-fetch/native-DM wait-state plus normal BR/BG composition.
//
// Fetched original Type 2/3/4/12 words generate their DM descriptor from
// shared cycle-start state. The raw descriptor remains structural timing
// scaffolding. A conservative state-8 preflight rejects a simultaneous pair
// before either the PM fetch or shared DM controller accepts it, retaining the
// fetched instruction for a later eligible retry. A DMACK-low state-6 sample
// freezes the architectural PM owner, while physical pin phases and state-7
// IRQ/state-3 BR/HALT samples continue. BR follow-up service and a pending
// HALT stop are deferred until the paired PM/DM instruction completes. Native
// grant masks both buses; HALT instead retains the driven state-8 levels.
module adsp2100_linear_dm_wait_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        br_n_i,
    input  logic        halt_n_i,
    input  logic [3:0]  irq_n_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,

    input  logic        dm_request_valid_i,
    input  logic [13:0] dm_request_address_i,
    input  logic        dm_request_address_valid_i,
    input  logic        dm_request_write_i,
    input  logic [15:0] dm_request_write_data_i,
    input  logic        dm_request_write_data_valid_i,
    input  logic        dm_ack_i,
    input  logic [15:0] dmd_read_data_i,
    input  logic        dmd_read_data_valid_i,

    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [5:0]  probe_code_i,

    output logic        architectural_phase_advance_o,
    output logic        effective_phase_advance_o,
    output logic        interrupt_wait_sample_o,
    output logic        dm_companion_accepted_o,
    output logic        phase_conflict_o,
    output logic        attachment_conflict_o,
    output logic        integration_conflict_o,

    output logic [1:0]  halt_mode_o,
    output logic        halt_state_three_boundary_o,
    output logic        halt_recognized_o,
    output logic        halt_stop_event_o,
    output logic        halt_resume_event_o,
    output logic        halt_release_blocked_o,
    output logic        halt_instruction_issue_inhibit_o,
    output logic        halt_phase_hold_o,
    output logic        halted_o,
    output logic        halt_br_conflict_o,
    output logic        halt_phase_conflict_o,

    output logic [2:0]  bus_mode_o,
    output logic        state_three_boundary_o,
    output logic        request_recognized_o,
    output logic        grant_assert_event_o,
    output logic        release_recognized_o,
    output logic        grant_release_event_o,
    output logic        resume_event_o,
    output logic        request_withdrawn_o,
    output logic        release_cancelled_o,
    output logic        instruction_issue_inhibit_o,
    output logic        normal_bus_relinquished_o,
    output logic        normal_bg_n_o,
    output logic        reset_br_request_o,
    output logic        bg_n_o,
    output logic        bus_relinquished_o,

    output logic        issue_boundary_o,
    output logic        instruction_setup_accepted_o,
    output logic        instruction_issue_o,
    output logic        retire_event_o,
    output logic        trap_event_o,
    output logic        interrupt_recognition_event_o,
    output logic        interrupt_entry_event_o,
    output logic        interrupt_vector_issue_event_o,
    output logic        interrupt_vector_fetch_event_o,
    output logic [1:0]  interrupt_level_o,
    output logic [13:0] interrupt_vector_o,
    output logic [3:0]  interrupt_pending_o,
    output logic        interrupt_vectoring_o,
    output logic        interrupt_configuration_invalid_o,
    output logic        interrupt_reset_baseline_provisional_o,
    output logic        interrupt_adjacent_control_conflict_o,
    output logic        instruction_valid_o,
    output logic        transaction_pending_o,
    output logic        unsupported_instruction_o,
    output logic        reserved_subencoding_o,
    output logic        core_phase_conflict_o,
    output logic        core_integration_conflict_o,
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
    output logic        pmd_write_data_valid_o,

    output logic        dm_request_accepted_o,
    output logic        dmack_sample_event_o,
    output logic        dmack_accepted_o,
    output logic        dm_wait_extension_event_o,
    output logic        dm_completion_event_o,
    output logic        dm_read_sample_event_o,
    output logic        dm_transaction_active_o,
    output logic        dm_waiting_o,
    output logic        dm_response_valid_o,
    output logic        dm_response_write_o,
    output logic [15:0] dm_response_read_data_o,
    output logic        dm_response_read_data_valid_o,
    output logic        dm_address_output_enable_o,
    output logic        dm_control_output_enable_o,
    output logic        dm_data_output_enable_o,
    output logic [13:0] dma_o,
    output logic        dma_valid_o,
    output logic        dms_n_o,
    output logic        dmrd_n_o,
    output logic        dmwr_n_o,
    output logic [15:0] dmd_write_data_o,
    output logic        dmd_write_data_valid_o
);
    import adsp2100_pkg::*;

    logic expected_dm_accept;
    logic ordinary_pm_issue;
    logic fetched_dm_request_candidate;
    logic fetched_dm_request_presented;
    logic [13:0] fetched_dm_request_address;
    logic fetched_dm_request_address_valid;
    logic fetched_dm_request_write;
    logic [15:0] fetched_dm_request_write_data;
    logic fetched_dm_request_write_data_valid;
    logic preflight_collision;
    logic core_issue_inhibit;
    logic fetched_owner_request_valid;
    logic companion_owner_request_valid;
    logic dm_owner_request_ready;
    logic dm_owner_request_conflict;
    logic dm_owner_request_out_of_phase;
    logic [1:0] dm_owner_request_accepted;
    logic [1:0] dm_owner_dmack_sample;
    logic [1:0] dm_owner_dmack_accepted;
    logic [1:0] dm_owner_wait_extension;
    logic [1:0] dm_owner_completion;
    logic [1:0] dm_owner_read_sample;
    logic [1:0] dm_owner;
    logic dm_in_progress;
    logic pairing_conflict;
    logic completion_conflict;
    logic halt_control_halt_n;
    logic halt_control_br_n;
    logic halt_force_fetch_issue;
    logic halt_owner_conflict;
    logic halt_trap_conflict;
    logic bus_protocol_active;
    logic bus_event_conflict;
    logic unused_observation;

    assign architectural_phase_advance_o = (
        effective_phase_advance_o && !dm_waiting_o
    );
    assign interrupt_wait_sample_o = (
        effective_phase_advance_o && dm_waiting_o
        && phase_i == PHASE_STATE_7
    );
    assign ordinary_pm_issue = (
        instruction_issue_o && !interrupt_vectoring_o
    );
    assign preflight_collision = (
        fetched_dm_request_candidate && dm_request_valid_i
        && !instruction_issue_inhibit_o
        && !halt_instruction_issue_inhibit_o
    );
    assign core_issue_inhibit = (
        instruction_issue_inhibit_o
        || halt_instruction_issue_inhibit_o
        || preflight_collision
    );
    assign fetched_owner_request_valid = (
        fetched_dm_request_presented || preflight_collision
    );
    assign companion_owner_request_valid = (
        (
            ordinary_pm_issue && dm_request_valid_i
            && !fetched_dm_request_presented
        )
        || preflight_collision
    );
    assign expected_dm_accept = (
        ordinary_pm_issue
        && (fetched_dm_request_presented ^ dm_request_valid_i)
    );
    assign dm_request_accepted_o = |dm_owner_request_accepted;
    assign dm_companion_accepted_o = dm_owner_request_accepted[1];
    assign dmack_sample_event_o = |dm_owner_dmack_sample;
    assign dmack_accepted_o = |dm_owner_dmack_accepted;
    assign dm_wait_extension_event_o = |dm_owner_wait_extension;
    assign dm_completion_event_o = |dm_owner_completion;
    assign dm_read_sample_event_o = |dm_owner_read_sample;
    assign dm_in_progress = (
        dm_transaction_active_o && !dm_response_valid_o
    );
    assign phase_conflict_o = (
        !reset_i && dm_request_valid_i
        && !(
            effective_phase_advance_o && phase_i == PHASE_STATE_8
            && !dm_waiting_o
        )
    );
    assign pairing_conflict = (
        !reset_i && dm_request_valid_i
        && !phase_conflict_o
        && (!ordinary_pm_issue || preflight_collision)
    );
    assign completion_conflict = (
        !reset_i && dm_in_progress
        && (dm_completion_event_o != pm_completion_event_o)
    );
    assign attachment_conflict_o = (
        pairing_conflict || completion_conflict
        || dm_owner_request_conflict || dm_owner_request_out_of_phase
        || (dm_request_accepted_o != expected_dm_accept)
    );
    assign integration_conflict_o = (
        phase_conflict_o || attachment_conflict_o
        || core_phase_conflict_o || core_integration_conflict_o
        || internal_conflict_o || bus_event_conflict
        || halt_br_conflict_o || halt_phase_conflict_o
        || halt_owner_conflict || halt_trap_conflict
    );
    assign bus_protocol_active = (
        bus_mode_o != 3'd0 || request_recognized_o
    );
    assign bus_event_conflict = (
        !reset_i && bus_protocol_active
        && (
            trap_event_o || interrupt_recognition_event_o
            || interrupt_entry_event_o
            || interrupt_vector_issue_event_o
            || interrupt_vector_fetch_event_o
            || interrupt_vectoring_o
        )
    );

    // HALT and normal BR/BG are each source-backed, but their simultaneous
    // priority is not. Preserve an already active owner; reject a same-edge
    // pair and report every cross-request explicitly.
    assign halt_control_halt_n = reset_i ? 1'b1 : (
        (halt_mode_o != 2'd0) ? halt_n_i
        : (halt_n_i || (bus_mode_o != 3'd0) || !br_n_i)
    );
    assign halt_control_br_n = reset_i ? br_n_i : (
        (bus_mode_o != 3'd0) ? br_n_i
        : (br_n_i || (halt_mode_o != 2'd0) || !halt_n_i)
    );
    assign halt_br_conflict_o = !reset_i && (
        (!halt_n_i && !br_n_i)
        || (!halt_n_i && bus_mode_o != 3'd0)
        || (!br_n_i && halt_mode_o != 2'd0)
    );
    assign halt_owner_conflict = (
        halt_recognized_o && !pm_bus_active_o
    );
    assign halt_trap_conflict = (
        trap_event_o
        && (halt_mode_o != 2'd0 || halt_stop_event_o)
    );

    adsp2100_halt_control halt_control (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .halt_n_i(halt_control_halt_n), .dmack_i(dm_ack_i),
        .pm_data_cycle_i(1'b0),
        .service_inhibit_i(dm_waiting_o),
        .mode_o(halt_mode_o),
        .state_three_boundary_o(halt_state_three_boundary_o),
        .halt_recognized_o(halt_recognized_o),
        .halt_stop_event_o(halt_stop_event_o),
        .force_fetch_issue_o(halt_force_fetch_issue),
        .resume_event_o(halt_resume_event_o),
        .release_blocked_o(halt_release_blocked_o),
        .instruction_issue_inhibit_o(
            halt_instruction_issue_inhibit_o
        ),
        .phase_hold_o(halt_phase_hold_o),
        .effective_phase_advance_o(effective_phase_advance_o),
        .halted_o(halted_o),
        .phase_conflict_o(halt_phase_conflict_o)
    );

    adsp2100_bus_control bus_control (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(effective_phase_advance_o),
        .br_n_i(halt_control_br_n),
        .service_inhibit_i(dm_in_progress),
        .mode_o(bus_mode_o),
        .state_three_boundary_o(state_three_boundary_o),
        .request_recognized_o(request_recognized_o),
        .grant_assert_event_o(grant_assert_event_o),
        .release_recognized_o(release_recognized_o),
        .grant_release_event_o(grant_release_event_o),
        .resume_event_o(resume_event_o),
        .request_withdrawn_o(request_withdrawn_o),
        .release_cancelled_o(release_cancelled_o),
        .instruction_issue_inhibit_o(instruction_issue_inhibit_o),
        .bus_relinquished_o(normal_bus_relinquished_o),
        .bg_n_o(normal_bg_n_o),
        .reset_br_request_o(reset_br_request_o)
    );

    adsp2100_reset_bus_grant reset_bus_grant (
        .reset_active_i(reset_i),
        .br_n_i(br_n_i),
        .normal_bg_n_i(normal_bg_n_o),
        .normal_bus_relinquished_i(normal_bus_relinquished_o),
        .bg_n_o(bg_n_o),
        .bus_relinquished_o(bus_relinquished_o)
    );

    adsp2100_linear_core_slice #(
        .FETCHED_TYPE2_ENABLED(1'b1),
        .FETCHED_TYPE3_ENABLED(1'b1),
        .FETCHED_TYPE4_ENABLED(1'b1),
        .FETCHED_TYPE12_ENABLED(1'b1)
    ) core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(architectural_phase_advance_o),
        .interrupt_sample_advance_i(interrupt_wait_sample_o),
        .instruction_issue_inhibit_i(core_issue_inhibit),
        .bus_relinquished_i(bus_relinquished_o),
        .instruction_setup_i(instruction_setup_i),
        .instruction_setup_pc_i(instruction_setup_pc_i),
        .instruction_setup_opcode_i(instruction_setup_opcode_i),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .dmd_read_data_i(dmd_read_data_i),
        .dmd_read_data_valid_i(dmd_read_data_valid_i),
        .irq_n_i(irq_n_i),
        .probe_code_i(probe_code_i),
        .issue_boundary_o(issue_boundary_o),
        .instruction_setup_accepted_o(instruction_setup_accepted_o),
        .instruction_issue_o(instruction_issue_o),
        .retire_event_o(retire_event_o),
        .trap_event_o(trap_event_o),
        .interrupt_recognition_event_o(interrupt_recognition_event_o),
        .interrupt_entry_event_o(interrupt_entry_event_o),
        .interrupt_vector_issue_event_o(interrupt_vector_issue_event_o),
        .interrupt_vector_fetch_event_o(interrupt_vector_fetch_event_o),
        .interrupt_level_o(interrupt_level_o),
        .interrupt_vector_o(interrupt_vector_o),
        .interrupt_pending_o(interrupt_pending_o),
        .interrupt_vectoring_o(interrupt_vectoring_o),
        .interrupt_configuration_invalid_o(
            interrupt_configuration_invalid_o
        ),
        .interrupt_reset_baseline_provisional_o(
            interrupt_reset_baseline_provisional_o
        ),
        .interrupt_adjacent_control_conflict_o(
            interrupt_adjacent_control_conflict_o
        ),
        .instruction_valid_o(instruction_valid_o),
        .transaction_pending_o(transaction_pending_o),
        .unsupported_instruction_o(unsupported_instruction_o),
        .reserved_subencoding_o(reserved_subencoding_o),
        .phase_conflict_o(core_phase_conflict_o),
        .integration_conflict_o(core_integration_conflict_o),
        .internal_conflict_o(internal_conflict_o),
        .provisional_source_extension_o(provisional_source_extension_o),
        .pc_o(pc_o),
        .opcode_o(opcode_o),
        .fetched_dm_request_candidate_o(
            fetched_dm_request_candidate
        ),
        .fetched_dm_request_presented_o(
            fetched_dm_request_presented
        ),
        .fetched_dm_request_address_o(fetched_dm_request_address),
        .fetched_dm_request_address_valid_o(
            fetched_dm_request_address_valid
        ),
        .fetched_dm_request_write_o(fetched_dm_request_write),
        .fetched_dm_request_write_data_o(
            fetched_dm_request_write_data
        ),
        .fetched_dm_request_write_data_valid_o(
            fetched_dm_request_write_data_valid
        ),
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

    adsp2100_data_owner_bus dm_bus (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(effective_phase_advance_o),
        .fetched_valid_i(fetched_owner_request_valid),
        .fetched_address_i(fetched_dm_request_address),
        .fetched_address_valid_i(fetched_dm_request_address_valid),
        .fetched_write_i(fetched_dm_request_write),
        .fetched_write_data_i(fetched_dm_request_write_data),
        .fetched_write_data_valid_i(
            fetched_dm_request_write_data_valid
        ),
        .companion_valid_i(companion_owner_request_valid),
        .companion_address_i(dm_request_address_i),
        .companion_address_valid_i(dm_request_address_valid_i),
        .companion_write_i(dm_request_write_i),
        .companion_write_data_i(dm_request_write_data_i),
        .companion_write_data_valid_i(dm_request_write_data_valid_i),
        .dm_ack_i(dm_ack_i),
        .dmd_read_data_i(dmd_read_data_i),
        .dmd_read_data_valid_i(dmd_read_data_valid_i),
        .bus_relinquished_i(bus_relinquished_o),
        .request_ready_o(dm_owner_request_ready),
        .request_conflict_o(dm_owner_request_conflict),
        .request_out_of_phase_o(dm_owner_request_out_of_phase),
        .request_accepted_o(dm_owner_request_accepted),
        .dmack_sample_event_o(dm_owner_dmack_sample),
        .dmack_accepted_o(dm_owner_dmack_accepted),
        .wait_extension_event_o(dm_owner_wait_extension),
        .completion_event_o(dm_owner_completion),
        .read_sample_event_o(dm_owner_read_sample),
        .owner_o(dm_owner),
        .transaction_active_o(dm_transaction_active_o),
        .waiting_o(dm_waiting_o),
        .response_valid_o(dm_response_valid_o),
        .response_write_o(dm_response_write_o),
        .response_read_data_o(dm_response_read_data_o),
        .response_read_data_valid_o(dm_response_read_data_valid_o),
        .dm_address_output_enable_o(dm_address_output_enable_o),
        .dm_control_output_enable_o(dm_control_output_enable_o),
        .dm_data_output_enable_o(dm_data_output_enable_o),
        .dma_o(dma_o),
        .dma_valid_o(dma_valid_o),
        .dms_n_o(dms_n_o),
        .dmrd_n_o(dmrd_n_o),
        .dmwr_n_o(dmwr_n_o),
        .dmd_write_data_o(dmd_write_data_o),
        .dmd_write_data_valid_o(dmd_write_data_valid_o)
    );

    assign unused_observation = ^{
        dm_owner_request_ready, dm_owner, halt_force_fetch_issue
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        if (dm_waiting_o) begin
            assert (!architectural_phase_advance_o);
            assert (!instruction_issue_o && !retire_event_o);
            assert (!pm_completion_event_o);
            assert (!interrupt_recognition_event_o);
            assert (!interrupt_entry_event_o);
            assert (!interrupt_vector_issue_event_o);
            assert (!halt_stop_event_o);
        end
        if (dm_in_progress) begin
            assert (!grant_assert_event_o);
            assert (!request_withdrawn_o);
        end
        if (core_issue_inhibit) begin
            assert (!instruction_issue_o);
        end
        if (halt_stop_event_o) begin
            assert (phase_i == PHASE_STATE_7);
            assert (pm_completion_event_o);
            assert (retire_event_o);
            if (
                opcode_o[23:21] == 3'b101
                || opcode_o[23:21] == 3'b100
                || opcode_o[23:21] == 3'b011
                || (opcode_o & 24'hfe0000) == 24'h120000
            ) begin
                assert (dm_completion_event_o);
            end
        end
        if (halted_o && !halt_resume_event_o) begin
            assert (halt_phase_hold_o);
            assert (!effective_phase_advance_o);
            assert (!architectural_phase_advance_o);
            assert (!instruction_issue_o && !retire_event_o);
        end
        if (halt_resume_event_o) begin
            assert (phase_i == PHASE_STATE_8 && dm_ack_i);
            assert (effective_phase_advance_o);
        end
        if (
            halt_br_conflict_o && halt_mode_o == 2'd0
            && bus_mode_o == 3'd0
        ) begin
            assert (!halt_recognized_o);
            assert (!request_recognized_o);
        end
        if (halt_br_conflict_o && halt_mode_o != 2'd0) begin
            assert (!request_recognized_o);
            if (!halt_n_i) begin
                assert (!halt_resume_event_o);
            end
        end
        if (halt_br_conflict_o && bus_mode_o != 3'd0) begin
            assert (!halt_recognized_o);
            if (!br_n_i) begin
                assert (!request_withdrawn_o);
            end
        end
        if (preflight_collision) begin
            assert (!pm_request_accepted_o && !instruction_issue_o);
            assert (!dm_request_accepted_o);
            assert (dm_owner_request_conflict);
        end
        if (bus_relinquished_o) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
            assert (!dm_address_output_enable_o);
            assert (!dm_control_output_enable_o);
            assert (!dm_data_output_enable_o);
        end
        if (bus_event_conflict) begin
            assert (integration_conflict_o);
        end
        if (interrupt_wait_sample_o) begin
            assert (dm_waiting_o && phase_advance_i);
            assert (phase_i == PHASE_STATE_7);
        end
        if (dm_completion_event_o) begin
            assert (pm_completion_event_o && retire_event_o);
        end
        if (dm_request_accepted_o) begin
            assert (pm_request_accepted_o && ordinary_pm_issue);
        end
        if (fetched_dm_request_presented) begin
            assert (expected_dm_accept);
            assert (dm_owner_request_accepted[0]);
            if (fetched_dm_request_write) begin
                assert (fetched_dm_request_write_data_valid);
            end
        end
        if (dm_companion_accepted_o) begin
            assert (!fetched_dm_request_presented);
            assert (dm_request_valid_i && ordinary_pm_issue);
        end
        if (
            retire_event_o
            && (
                opcode_o[23:21] == 3'b101
                || opcode_o[23:21] == 3'b100
                || opcode_o[23:21] == 3'b011
                || (opcode_o & 24'hfe0000) == 24'h120000
            )
        ) begin
            assert (dm_completion_event_o);
        end
    end
`endif
endmodule

`default_nettype wire
