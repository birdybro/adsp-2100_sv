`default_nettype none

module adsp2100_compute_dm_native_formal (
    input logic        clk_i,
    input logic        reset_i,
    input logic [2:0]  phase_i,
    input logic        phase_advance_i,
    input logic        bus_relinquished_i,
    input logic        execute_i,
    input logic [23:0] opcode_i,
    input logic        dm_ack_i,
    input logic [15:0] dmd_read_data_i,
    input logic        dmd_read_data_valid_i,
    input logic        astat_setup_write_i,
    input logic [7:0]  astat_setup_data_i,
    input logic        mstat_setup_write_i,
    input logic [3:0]  mstat_setup_data_i,
    input logic        dreg_setup_write_i,
    input logic [3:0]  dreg_setup_code_i,
    input logic [15:0] dreg_setup_data_i,
    input logic        af_setup_write_i,
    input logic [15:0] af_setup_data_i,
    input logic        mf_setup_write_i,
    input logic [15:0] mf_setup_data_i,
    input logic        dag_setup_write_i,
    input logic [1:0]  dag_setup_kind_i,
    input logic [2:0]  dag_setup_address_i,
    input logic [13:0] dag_setup_data_i,
    input logic        inspect_probe_i,
    input logic [3:0]  probe_dreg_code_i,
    input logic [2:0]  probe_dag_address_i
);
    import adsp2100_pkg::*;

    logic        issue_boundary_o;
    logic        phase_conflict_o;
    logic        attachment_conflict_o;
    logic        integration_conflict_o;
    logic        class_valid_o;
    logic        action_valid_o;
    logic        unsupported_subencoding_o;
    logic        destination_collision_o;
    logic        computation_enable_o;
    logic        is_mac_o;
    logic        destination_feedback_o;
    logic        dag_select_o;
    logic        write_direction_o;
    logic [4:0]  amf_o;
    logic [1:0]  yop_o;
    logic [2:0]  xop_o;
    logic [3:0]  x_source_dreg_o;
    logic [3:0]  y_source_dreg_o;
    logic [3:0]  memory_dreg_o;
    logic [2:0]  i_address_o;
    logic [2:0]  m_address_o;
    logic        boundary_valid_o;
    logic        accepted_o;
    logic        instruction_complete_o;
    logic        transaction_active_o;
    logic        stalled_o;
    logic        busy_o;
    logic        invalid_opcode_o;
    logic        internal_conflict_o;
    logic        dm_select_o;
    logic        dm_read_o;
    logic        dm_write_o;
    logic [13:0] dm_address_o;
    logic        dm_address_valid_o;
    logic [15:0] dm_write_data_o;
    logic        dm_write_data_valid_o;
    logic        compute_result_known_o;
    logic        dag_configuration_valid_o;
    logic        i_write_o;
    logic        i_write_known_o;
    logic        dreg_write_o;
    logic        dreg_write_known_o;
    logic        alu_write_o;
    logic        mac_write_o;
    logic        alu_status_write_o;
    logic        mac_status_write_o;
    logic [15:0] alu_result_o;
    logic [39:0] mac_result_o;
    logic        dm_request_accepted_o;
    logic        dmack_sample_event_o;
    logic        dmack_accepted_o;
    logic        wait_extension_event_o;
    logic        dm_completion_event_o;
    logic        dm_read_sample_event_o;
    logic        dm_bus_active_o;
    logic        dm_bus_waiting_o;
    logic        dm_address_output_enable_o;
    logic        dm_control_output_enable_o;
    logic        dm_data_output_enable_o;
    logic [13:0] dma_o;
    logic        dma_valid_o;
    logic        dms_n_o;
    logic        dmrd_n_o;
    logic        dmwr_n_o;
    logic [15:0] dmd_write_data_o;
    logic        dmd_write_data_valid_o;
    logic [15:0] probe_dreg_data_o;
    logic        probe_dreg_valid_o;
    logic [13:0] probe_i_data_o;
    logic        probe_i_valid_o;
    logic [13:0] probe_m_data_o;
    logic        probe_m_valid_o;
    logic [13:0] probe_l_data_o;
    logic        probe_l_valid_o;
    logic [15:0] af_o;
    logic        af_valid_o;
    logic [15:0] mf_o;
    logic        mf_valid_o;
    logic [39:0] mr_o;
    logic        mr_valid_o;
    logic [7:0]  astat_o;
    logic [7:0]  astat_valid_mask_o;
    logic [3:0]  mstat_o;
    logic        alternate_bank_o;
    logic        controls_present;
    logic        past_valid;
    logic        unused_observation;

    assign controls_present = |{
        execute_i, astat_setup_write_i, mstat_setup_write_i,
        dreg_setup_write_i, af_setup_write_i, mf_setup_write_i,
        dag_setup_write_i
    };
    assign unused_observation = ^{
        class_valid_o, action_valid_o, unsupported_subencoding_o,
        destination_collision_o, computation_enable_o, is_mac_o,
        destination_feedback_o, dag_select_o, write_direction_o, amf_o,
        yop_o, xop_o, x_source_dreg_o, y_source_dreg_o, memory_dreg_o,
        i_address_o, m_address_o, boundary_valid_o, busy_o,
        invalid_opcode_o, internal_conflict_o, dm_address_o,
        dm_address_valid_o, dm_write_data_o, dm_write_data_valid_o,
        compute_result_known_o, dag_configuration_valid_o,
        i_write_known_o, dreg_write_known_o, alu_result_o, mac_result_o,
        dmack_sample_event_o, dmack_accepted_o, wait_extension_event_o,
        dma_o, dma_valid_o, dmd_write_data_o, dmd_write_data_valid_o,
        probe_dreg_data_o, probe_dreg_valid_o, probe_i_data_o,
        probe_i_valid_o, probe_m_data_o, probe_m_valid_o,
        probe_l_data_o, probe_l_valid_o, af_o, af_valid_o, mf_o,
        mf_valid_o, mr_o, mr_valid_o, astat_o, astat_valid_mask_o,
        mstat_o, alternate_bank_o
    };

    adsp2100_compute_dm_native_slice dut (.*);

    initial past_valid = 1'b0;

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (issue_boundary_o == (
            !reset_i && !bus_relinquished_i && phase_advance_i
            && phase_i == PHASE_STATE_8
        ));
        assert (phase_conflict_o == (
            !reset_i && controls_present && !issue_boundary_o
        ));
        assert (!attachment_conflict_o);
        assert (integration_conflict_o == (
            phase_conflict_o || attachment_conflict_o
            || dut.core_integration_conflict
        ));
        assert (accepted_o == dm_request_accepted_o);
        assert (instruction_complete_o == (
            dm_completion_event_o && dm_select_o
        ));
        assert (dm_read_sample_event_o == (
            dm_completion_event_o && dm_read_o
        ));
        assert (dm_select_o == (dm_read_o || dm_write_o));
        assert (!(dm_read_o && dm_write_o));
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
        if (dm_bus_waiting_o && !reset_i) begin
            assert (transaction_active_o && stalled_o);
            assert (!instruction_complete_o && !i_write_o);
            assert (!dreg_write_o && !alu_write_o && !mac_write_o);
            assert (!alu_status_write_o && !mac_status_write_o);
        end
        if (bus_relinquished_i || reset_i) begin
            assert (!dm_address_output_enable_o);
            assert (!dm_control_output_enable_o);
            assert (!dm_data_output_enable_o);
        end
    end

    always_ff @(posedge clk_i) begin
        past_valid <= 1'b1;
        if (past_valid && !$past(reset_i) && !reset_i
            && $past(dm_bus_waiting_o)
            && !$past(dm_completion_event_o)) begin
            assert (dut.bus.active_q);
            assert (dut.bus.address_q == $past(dut.bus.address_q));
            assert (dut.bus.address_valid_q
                == $past(dut.bus.address_valid_q));
            assert (dut.bus.write_q == $past(dut.bus.write_q));
            assert (dut.bus.write_data_q
                == $past(dut.bus.write_data_q));
            assert (dut.bus.write_data_valid_q
                == $past(dut.bus.write_data_valid_q));
        end
        cover (accepted_o && dm_request_accepted_o);
        cover (wait_extension_event_o && dm_bus_waiting_o);
        cover (instruction_complete_o && i_write_o && alu_write_o);
        cover (instruction_complete_o && i_write_o && mac_write_o);
        cover (dm_read_sample_event_o && dreg_write_o);
        cover (dm_completion_event_o && dm_write_o);
    end
endmodule

`default_nettype wire
