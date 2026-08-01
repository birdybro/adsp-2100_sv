`default_nettype none

module adsp2100_compute_dm_native_slice (
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

    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        dreg_setup_write_i,
    input  logic [3:0]  dreg_setup_code_i,
    input  logic [15:0] dreg_setup_data_i,
    input  logic        af_setup_write_i,
    input  logic [15:0] af_setup_data_i,
    input  logic        mf_setup_write_i,
    input  logic [15:0] mf_setup_data_i,
    input  logic        dag_setup_write_i,
    input  logic [1:0]  dag_setup_kind_i,
    input  logic [2:0]  dag_setup_address_i,
    input  logic [13:0] dag_setup_data_i,
    input  logic        inspect_probe_i,
    input  logic [3:0]  probe_dreg_code_i,
    input  logic [2:0]  probe_dag_address_i,

    output logic        issue_boundary_o,
    output logic        phase_conflict_o,
    output logic        attachment_conflict_o,
    output logic        integration_conflict_o,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        destination_collision_o,
    output logic        computation_enable_o,
    output logic        is_mac_o,
    output logic        destination_feedback_o,
    output logic        dag_select_o,
    output logic        write_direction_o,
    output logic [4:0]  amf_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  y_source_dreg_o,
    output logic [3:0]  memory_dreg_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,
    output logic        boundary_valid_o,
    output logic        accepted_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        stalled_o,
    output logic        busy_o,
    output logic        invalid_opcode_o,
    output logic        internal_conflict_o,

    output logic        dm_select_o,
    output logic        dm_read_o,
    output logic        dm_write_o,
    output logic [13:0] dm_address_o,
    output logic        dm_address_valid_o,
    output logic [15:0] dm_write_data_o,
    output logic        dm_write_data_valid_o,
    output logic        compute_result_known_o,
    output logic        dag_configuration_valid_o,
    output logic        i_write_o,
    output logic        i_write_known_o,
    output logic        dreg_write_o,
    output logic        dreg_write_known_o,
    output logic        alu_write_o,
    output logic        mac_write_o,
    output logic        alu_status_write_o,
    output logic        mac_status_write_o,
    output logic [15:0] alu_result_o,
    output logic [39:0] mac_result_o,

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

    output logic [15:0] probe_dreg_data_o,
    output logic        probe_dreg_valid_o,
    output logic [13:0] probe_i_data_o,
    output logic        probe_i_valid_o,
    output logic [13:0] probe_m_data_o,
    output logic        probe_m_valid_o,
    output logic [13:0] probe_l_data_o,
    output logic        probe_l_valid_o,
    output logic [15:0] af_o,
    output logic        af_valid_o,
    output logic [15:0] mf_o,
    output logic        mf_valid_o,
    output logic [39:0] mr_o,
    output logic        mr_valid_o,
    output logic [7:0]  astat_o,
    output logic [7:0]  astat_valid_mask_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o
);
    import adsp2100_pkg::*;

    logic controls_present;
    logic core_integration_conflict;
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

    assign controls_present = (
        execute_i || astat_setup_write_i || mstat_setup_write_i
        || dreg_setup_write_i || af_setup_write_i || mf_setup_write_i
        || dag_setup_write_i
    );
    assign issue_boundary_o = (
        !reset_i && !bus_relinquished_i && phase_advance_i
        && phase_i == PHASE_STATE_8
    );
    assign phase_conflict_o = (
        !reset_i && controls_present && !issue_boundary_o
    );
    assign attachment_conflict_o = (
        accepted_o != dm_request_accepted_o
        || (accepted_o && !(issue_boundary_o && dm_select_o))
        || instruction_complete_o
            != (dm_completion_event_o && dm_select_o)
        || dm_read_sample_event_o
            != (dm_completion_event_o && dm_read_o)
    );
    assign integration_conflict_o = (
        phase_conflict_o || attachment_conflict_o
        || core_integration_conflict
    );
    assign unused_observation = ^{
        core_pm_access_unused, core_dm_access_unused,
        bus_request_ready_unused, bus_response_valid_unused,
        bus_response_write_unused, bus_response_data_unused,
        bus_response_data_valid_unused, descriptor_address_unused,
        descriptor_address_valid_unused, descriptor_write_unused,
        descriptor_write_data_unused, descriptor_write_data_valid_unused
    };

    adsp2100_compute_dm_slice core (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(execute_i && issue_boundary_o),
        .opcode_i(opcode_i),
        .dm_ack_i(dm_completion_event_o),
        .dm_read_data_i(dmd_read_data_i),
        .dm_read_data_valid_i(dmd_read_data_valid_i),
        .astat_setup_write_i(astat_setup_write_i && issue_boundary_o),
        .astat_setup_data_i(astat_setup_data_i),
        .mstat_setup_write_i(mstat_setup_write_i && issue_boundary_o),
        .mstat_setup_data_i(mstat_setup_data_i),
        .dreg_setup_write_i(dreg_setup_write_i && issue_boundary_o),
        .dreg_setup_code_i(dreg_setup_code_i),
        .dreg_setup_data_i(dreg_setup_data_i),
        .af_setup_write_i(af_setup_write_i && issue_boundary_o),
        .af_setup_data_i(af_setup_data_i),
        .mf_setup_write_i(mf_setup_write_i && issue_boundary_o),
        .mf_setup_data_i(mf_setup_data_i),
        .dag_setup_write_i(dag_setup_write_i && issue_boundary_o),
        .dag_setup_kind_i(dag_setup_kind_i),
        .dag_setup_address_i(dag_setup_address_i),
        .dag_setup_data_i(dag_setup_data_i),
        .inspect_probe_i(inspect_probe_i),
        .probe_dreg_code_i(probe_dreg_code_i),
        .probe_dag_address_i(probe_dag_address_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .destination_collision_o(destination_collision_o),
        .computation_enable_o(computation_enable_o),
        .is_mac_o(is_mac_o),
        .destination_feedback_o(destination_feedback_o),
        .dag_select_o(dag_select_o),
        .write_direction_o(write_direction_o),
        .amf_o(amf_o),
        .yop_o(yop_o),
        .xop_o(xop_o),
        .x_source_dreg_o(x_source_dreg_o),
        .y_source_dreg_o(y_source_dreg_o),
        .memory_dreg_o(memory_dreg_o),
        .i_address_o(i_address_o),
        .m_address_o(m_address_o),
        .boundary_valid_o(boundary_valid_o),
        .accepted_o(accepted_o),
        .instruction_complete_o(instruction_complete_o),
        .transaction_active_o(transaction_active_o),
        .stalled_o(stalled_o),
        .busy_o(busy_o),
        .invalid_opcode_o(invalid_opcode_o),
        .integration_conflict_o(core_integration_conflict),
        .internal_conflict_o(internal_conflict_o),
        .dm_select_o(dm_select_o),
        .dm_read_o(dm_read_o),
        .dm_write_o(dm_write_o),
        .dm_address_o(dm_address_o),
        .dm_address_valid_o(dm_address_valid_o),
        .dm_write_data_o(dm_write_data_o),
        .dm_write_data_valid_o(dm_write_data_valid_o),
        .pm_data_access_o(core_pm_access_unused),
        .dm_access_o(core_dm_access_unused),
        .compute_result_known_o(compute_result_known_o),
        .dag_configuration_valid_o(dag_configuration_valid_o),
        .i_write_o(i_write_o),
        .i_write_known_o(i_write_known_o),
        .dreg_write_o(dreg_write_o),
        .dreg_write_known_o(dreg_write_known_o),
        .alu_write_o(alu_write_o),
        .mac_write_o(mac_write_o),
        .alu_status_write_o(alu_status_write_o),
        .mac_status_write_o(mac_status_write_o),
        .alu_result_o(alu_result_o),
        .mac_result_o(mac_result_o),
        .probe_dreg_data_o(probe_dreg_data_o),
        .probe_dreg_valid_o(probe_dreg_valid_o),
        .probe_i_data_o(probe_i_data_o),
        .probe_i_valid_o(probe_i_valid_o),
        .probe_m_data_o(probe_m_data_o),
        .probe_m_valid_o(probe_m_valid_o),
        .probe_l_data_o(probe_l_data_o),
        .probe_l_valid_o(probe_l_valid_o),
        .af_o(af_o),
        .af_valid_o(af_valid_o),
        .mf_o(mf_o),
        .mf_valid_o(mf_valid_o),
        .mr_o(mr_o),
        .mr_valid_o(mr_valid_o),
        .astat_o(astat_o),
        .astat_valid_mask_o(astat_valid_mask_o),
        .mstat_o(mstat_o),
        .alternate_bank_o(alternate_bank_o)
    );

    adsp2100_data_bus bus (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .request_valid_i(dm_select_o),
        .request_address_i(dm_address_o),
        .request_address_valid_i(dm_address_valid_o),
        .request_write_i(dm_write_o),
        .request_write_data_i(dm_write_data_o),
        .request_write_data_valid_i(dm_write_data_valid_o),
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

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!attachment_conflict_o);
        assert (!(dm_read_o && dm_write_o));
        assert (dm_select_o == (dm_read_o || dm_write_o));
        assert (accepted_o == dm_request_accepted_o);
        assert (instruction_complete_o
            == (dm_completion_event_o && dm_select_o));
        assert (dm_read_sample_event_o
            == (dm_completion_event_o && dm_read_o));
        assert (!(~dmrd_n_o && ~dmwr_n_o));
        assert (dm_address_output_enable_o
            == dm_control_output_enable_o);
        assert (dms_n_o == !dm_control_output_enable_o);
        if (accepted_o) begin
            assert (issue_boundary_o && dm_select_o);
        end
        if (instruction_complete_o) begin
            assert (phase_i == PHASE_STATE_7 && phase_advance_i);
            assert (transaction_active_o && dm_bus_active_o);
            assert (i_write_o);
        end
        if (dreg_write_o) begin
            assert (dm_read_sample_event_o);
            assert (dreg_write_known_o == dmd_read_data_valid_i);
        end
        // Reset is synchronous for both composed state machines. During the
        // reset clock's pre-edge observation, the bus may still expose its
        // old waiting state while the logical client already masks its
        // transaction outputs with reset_i.
        if (dm_bus_waiting_o && !reset_i) begin
            assert (transaction_active_o && stalled_o);
            assert (!instruction_complete_o && !i_write_o);
            assert (!dreg_write_o && !alu_write_o && !mac_write_o);
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
