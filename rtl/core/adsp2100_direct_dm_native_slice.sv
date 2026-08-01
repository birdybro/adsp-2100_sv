`default_nettype none

module adsp2100_direct_dm_native_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        bus_relinquished_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic        dm_ack_i,
    input  logic [15:0] dmd_read_data_i,
    input  logic        dmd_read_data_valid_i,
    input  logic        setup_write_i,
    input  logic [5:0]  setup_code_i,
    input  logic [15:0] setup_data_i,
    input  logic [5:0]  probe_code_i,

    output logic        issue_boundary_o,
    output logic        phase_conflict_o,
    output logic        attachment_conflict_o,
    output logic        integration_conflict_o,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        invalid_subencoding_o,
    output logic        write_direction_o,
    output logic [13:0] direct_address_o,
    output logic [5:0]  register_code_o,
    output logic        boundary_valid_o,
    output logic        accepted_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        stalled_o,
    output logic        busy_o,
    output logic        invalid_opcode_o,
    output logic        invalid_setup_o,
    output logic        internal_conflict_o,
    output logic        source_extension_provisional_o,
    output logic        register_write_o,
    output logic        register_write_known_o,

    output logic        dm_request_accepted_o,
    output logic        dmack_sample_event_o,
    output logic        dmack_accepted_o,
    output logic        wait_extension_event_o,
    output logic        dm_completion_event_o,
    output logic        dm_read_sample_event_o,
    output logic        dm_bus_active_o,
    output logic        dm_bus_waiting_o,
    output logic        dm_address_output_enable_o,
    output logic        dm_control_output_enable_o,
    output logic        dm_data_output_enable_o,
    output logic [13:0] dma_o,
    output logic        dma_valid_o,
    output logic        dms_n_o,
    output logic        dmrd_n_o,
    output logic        dmwr_n_o,
    output logic [15:0] dmd_write_data_o,
    output logic        dmd_write_data_valid_o,

    output logic [15:0] probe_data_o,
    output logic        probe_data_valid_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [4:0]  icntl_o,
    output logic [3:0]  imask_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic [7:0]  px_o,
    output logic [7:0]  sstat_o,
    output logic        count_stack_push_o,
    output logic [13:0] count_stack_push_data_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o
);
    import adsp2100_pkg::*;

    logic controls_present;
    logic core_integration_conflict;
    logic core_dm_select;
    logic core_dm_read;
    logic core_dm_write;
    logic [13:0] core_dm_address;
    logic core_dm_address_valid;
    logic [15:0] core_dm_write_data;
    logic core_dm_write_data_valid;
    logic core_pm_access_unused;
    logic core_dm_access_unused;
    logic bus_request_ready_unused;
    logic bus_response_valid_unused;
    logic bus_response_write_unused;
    logic [15:0] bus_response_data_unused;
    logic bus_response_data_valid_unused;
    logic [13:0] descriptor_address_unused;
    logic descriptor_address_valid_unused;
    logic descriptor_write_unused;
    logic [15:0] descriptor_write_data_unused;
    logic descriptor_write_data_valid_unused;
    logic unused_observation;

    assign controls_present = execute_i || setup_write_i;
    assign issue_boundary_o = (
        !reset_i && !bus_relinquished_i && phase_advance_i
        && phase_i == PHASE_STATE_8
    );
    assign phase_conflict_o = (
        !reset_i && controls_present && !issue_boundary_o
    );
    assign attachment_conflict_o = (
        accepted_o != dm_request_accepted_o
        || (accepted_o && !(issue_boundary_o && core_dm_select))
        || instruction_complete_o
            != (dm_completion_event_o && core_dm_select)
        || dm_read_sample_event_o
            != (dm_completion_event_o && core_dm_read)
    );
    assign integration_conflict_o = (
        phase_conflict_o || attachment_conflict_o
        || core_integration_conflict
    );

    adsp2100_direct_dm_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(execute_i && issue_boundary_o),
        .opcode_i(opcode_i),
        .dm_ack_i(dm_completion_event_o),
        .dm_read_data_i(dmd_read_data_i),
        .dm_read_data_valid_i(dmd_read_data_valid_i),
        .setup_write_i(setup_write_i && issue_boundary_o),
        .setup_code_i(setup_code_i),
        .setup_data_i(setup_data_i),
        .probe_code_i(probe_code_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .invalid_subencoding_o(invalid_subencoding_o),
        .write_direction_o(write_direction_o),
        .direct_address_o(direct_address_o),
        .register_code_o(register_code_o),
        .boundary_valid_o(boundary_valid_o),
        .accepted_o(accepted_o),
        .instruction_complete_o(instruction_complete_o),
        .transaction_active_o(transaction_active_o),
        .stalled_o(stalled_o),
        .busy_o(busy_o),
        .invalid_opcode_o(invalid_opcode_o),
        .invalid_setup_o(invalid_setup_o),
        .integration_conflict_o(core_integration_conflict),
        .internal_conflict_o(internal_conflict_o),
        .dm_select_o(core_dm_select),
        .dm_read_o(core_dm_read),
        .dm_write_o(core_dm_write),
        .dm_address_o(core_dm_address),
        .dm_address_valid_o(core_dm_address_valid),
        .dm_write_data_o(core_dm_write_data),
        .dm_write_data_valid_o(core_dm_write_data_valid),
        .register_write_o(register_write_o),
        .register_write_known_o(register_write_known_o),
        .source_extension_provisional_o(
            source_extension_provisional_o
        ),
        .pm_data_access_o(core_pm_access_unused),
        .dm_access_o(core_dm_access_unused),
        .probe_data_o(probe_data_o),
        .probe_data_valid_o(probe_data_valid_o),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .cntr_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .px_o(px_o),
        .sstat_o(sstat_o),
        .count_stack_push_o(count_stack_push_o),
        .count_stack_push_data_o(count_stack_push_data_o),
        .count_stack_depth_o(count_stack_depth_o),
        .count_stack_overflow_o(count_stack_overflow_o)
    );

    adsp2100_data_bus bus (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .request_valid_i(core_dm_select),
        .request_address_i(core_dm_address),
        .request_address_valid_i(core_dm_address_valid),
        .request_write_i(core_dm_write),
        .request_write_data_i(core_dm_write_data),
        .request_write_data_valid_i(core_dm_write_data_valid),
        .dm_ack_i(dm_ack_i),
        .dmd_read_data_i(dmd_read_data_i),
        .dmd_read_data_valid_i(dmd_read_data_valid_i),
        .bus_relinquished_i(bus_relinquished_i),
        .request_ready_o(bus_request_ready_unused),
        .request_accepted_o(dm_request_accepted_o),
        .dmack_sample_event_o(dmack_sample_event_o),
        .dmack_accepted_o(dmack_accepted_o),
        .wait_extension_event_o(wait_extension_event_o),
        .completion_event_o(dm_completion_event_o),
        .read_sample_event_o(dm_read_sample_event_o),
        .transaction_active_o(dm_bus_active_o),
        .waiting_o(dm_bus_waiting_o),
        .response_valid_o(bus_response_valid_unused),
        .response_write_o(bus_response_write_unused),
        .response_read_data_o(bus_response_data_unused),
        .response_read_data_valid_o(bus_response_data_valid_unused),
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
        .descriptor_address_o(descriptor_address_unused),
        .descriptor_address_valid_o(descriptor_address_valid_unused),
        .descriptor_write_o(descriptor_write_unused),
        .descriptor_write_data_o(descriptor_write_data_unused),
        .descriptor_write_data_valid_o(
            descriptor_write_data_valid_unused
        )
    );

    assign unused_observation = ^{
        core_pm_access_unused,
        core_dm_access_unused,
        bus_request_ready_unused,
        bus_response_valid_unused,
        bus_response_write_unused,
        bus_response_data_unused,
        bus_response_data_valid_unused,
        descriptor_address_unused,
        descriptor_address_valid_unused,
        descriptor_write_unused,
        descriptor_write_data_unused,
        descriptor_write_data_valid_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!attachment_conflict_o);
        assert (!(core_dm_read && core_dm_write));
        assert (core_dm_select == (core_dm_read || core_dm_write));
        assert (accepted_o == dm_request_accepted_o);
        assert (instruction_complete_o
            == (dm_completion_event_o && core_dm_select));
        assert (dm_read_sample_event_o
            == (dm_completion_event_o && core_dm_read));
        assert (!(~dmrd_n_o && ~dmwr_n_o));
        assert (dm_address_output_enable_o
            == dm_control_output_enable_o);
        assert (dms_n_o == !dm_control_output_enable_o);
        if (accepted_o) begin
            assert (issue_boundary_o && core_dm_select);
        end
        if (instruction_complete_o) begin
            assert (phase_i == PHASE_STATE_7 && phase_advance_i);
            assert (transaction_active_o && dm_bus_active_o);
        end
        if (register_write_o) begin
            assert (dm_read_sample_event_o);
            assert (register_write_known_o == dmd_read_data_valid_i);
        end
        if (dm_bus_waiting_o && !reset_i) begin
            assert (transaction_active_o && stalled_o);
            assert (!instruction_complete_o && !register_write_o);
        end
        if (bus_relinquished_i || reset_i) begin
            assert (!dm_address_output_enable_o);
            assert (!dm_control_output_enable_o);
            assert (!dm_data_output_enable_o);
        end
    end
`endif
endmodule

`default_nettype wire
