`default_nettype none

// Bounded ordinary-fetch/native-DM wait-state composition.
//
// The raw DM descriptor is admitted only beside an accepted ordinary PM
// fetch. It is structural timing evidence, not a fetched DM-instruction
// ownership claim. A DMACK-low state-6 sample freezes the architectural PM
// owner, while physical pin phases and state-7 IRQ samples continue.
module adsp2100_linear_dm_wait_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
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
    output logic        interrupt_wait_sample_o,
    output logic        dm_companion_accepted_o,
    output logic        phase_conflict_o,
    output logic        attachment_conflict_o,
    output logic        integration_conflict_o,

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

    logic paired_dm_request;
    logic ordinary_pm_issue;
    logic dm_in_progress;
    logic pairing_conflict;
    logic completion_conflict;
    logic dm_request_ready_unused;
    logic [32:0] dm_descriptor_unused;
    logic unused_observation;

    assign architectural_phase_advance_o = (
        phase_advance_i && !dm_waiting_o
    );
    assign interrupt_wait_sample_o = (
        phase_advance_i && dm_waiting_o
        && phase_i == PHASE_STATE_7
    );
    assign ordinary_pm_issue = (
        instruction_issue_o && !interrupt_vectoring_o
    );
    assign paired_dm_request = dm_request_valid_i && ordinary_pm_issue;
    assign dm_companion_accepted_o = dm_request_accepted_o;
    assign dm_in_progress = (
        dm_transaction_active_o && !dm_response_valid_o
    );
    assign phase_conflict_o = (
        !reset_i && dm_request_valid_i
        && !(
            phase_advance_i && phase_i == PHASE_STATE_8
            && !dm_waiting_o
        )
    );
    assign pairing_conflict = (
        !reset_i && dm_request_valid_i
        && !phase_conflict_o && !ordinary_pm_issue
    );
    assign completion_conflict = (
        !reset_i && dm_in_progress
        && (dm_completion_event_o != pm_completion_event_o)
    );
    assign attachment_conflict_o = (
        pairing_conflict || completion_conflict
        || (dm_request_accepted_o != paired_dm_request)
    );
    assign integration_conflict_o = (
        phase_conflict_o || attachment_conflict_o
        || core_phase_conflict_o || core_integration_conflict_o
        || internal_conflict_o
    );

    adsp2100_linear_core_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(architectural_phase_advance_o),
        .interrupt_sample_advance_i(interrupt_wait_sample_o),
        .instruction_issue_inhibit_i(1'b0),
        .bus_relinquished_i(1'b0),
        .instruction_setup_i(instruction_setup_i),
        .instruction_setup_pc_i(instruction_setup_pc_i),
        .instruction_setup_opcode_i(instruction_setup_opcode_i),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
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

    adsp2100_data_bus dm_bus (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .request_valid_i(paired_dm_request),
        .request_address_i(dm_request_address_i),
        .request_address_valid_i(dm_request_address_valid_i),
        .request_write_i(dm_request_write_i),
        .request_write_data_i(dm_request_write_data_i),
        .request_write_data_valid_i(dm_request_write_data_valid_i),
        .dm_ack_i(dm_ack_i),
        .dmd_read_data_i(dmd_read_data_i),
        .dmd_read_data_valid_i(dmd_read_data_valid_i),
        .bus_relinquished_i(1'b0),
        .request_ready_o(dm_request_ready_unused),
        .request_accepted_o(dm_request_accepted_o),
        .dmack_sample_event_o(dmack_sample_event_o),
        .dmack_accepted_o(dmack_accepted_o),
        .wait_extension_event_o(dm_wait_extension_event_o),
        .completion_event_o(dm_completion_event_o),
        .read_sample_event_o(dm_read_sample_event_o),
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
        .dmd_write_data_valid_o(dmd_write_data_valid_o),
        .descriptor_address_o(dm_descriptor_unused[32:19]),
        .descriptor_address_valid_o(dm_descriptor_unused[18]),
        .descriptor_write_o(dm_descriptor_unused[17]),
        .descriptor_write_data_o(dm_descriptor_unused[16:1]),
        .descriptor_write_data_valid_o(dm_descriptor_unused[0])
    );

    assign unused_observation = ^{
        dm_request_ready_unused, dm_descriptor_unused
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
    end
`endif
endmodule

`default_nettype wire
