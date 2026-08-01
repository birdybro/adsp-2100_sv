`default_nettype none

module adsp2100_dm_write_immediate_native_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        bus_relinquished,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        dm_ack,
    input logic        mstat_setup_write,
    input logic [3:0]  mstat_setup_data,
    input logic        dag_setup_write,
    input logic [1:0]  dag_setup_kind,
    input logic [2:0]  dag_setup_address,
    input logic [13:0] dag_setup_data,
    input logic [2:0]  probe_dag_address
);
    import adsp2100_pkg::*;

    logic issue_boundary;
    logic phase_conflict;
    logic attachment_conflict;
    logic integration_conflict;
    logic class_valid;
    logic action_valid;
    logic [15:0] immediate;
    logic dag2;
    logic [1:0] i_local;
    logic [1:0] m_local;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic [2:0] l_address;
    logic boundary_valid;
    logic accepted;
    logic instruction_complete;
    logic transaction_active;
    logic stalled;
    logic busy;
    logic invalid_opcode;
    logic internal_conflict;
    logic dag_configuration_valid;
    logic i_write;
    logic i_write_known;
    logic dm_request_accepted;
    logic dmack_sample_event;
    logic dmack_accepted;
    logic wait_extension_event;
    logic dm_completion_event;
    logic dm_bus_active;
    logic dm_bus_waiting;
    logic dm_address_oe;
    logic dm_control_oe;
    logic dm_data_oe;
    logic [13:0] dma;
    logic dma_valid;
    logic dms_n;
    logic dmrd_n;
    logic dmwr_n;
    logic [15:0] dmd_write_data;
    logic dmd_write_data_valid;
    logic [13:0] probe_i_data;
    logic probe_i_valid;
    logic [13:0] probe_m_data;
    logic probe_m_valid;
    logic [13:0] probe_l_data;
    logic probe_l_valid;
    logic [3:0] mstat;
    logic controls_present;
    logic unused_observation;

    assign controls_present = (
        execute || mstat_setup_write || dag_setup_write
    );
    assign unused_observation = ^{
        class_valid, action_valid, immediate, dag2, i_local, m_local,
        i_address, m_address, l_address, boundary_valid,
        transaction_active, stalled, busy, invalid_opcode,
        internal_conflict, dag_configuration_valid, i_write_known,
        dmack_sample_event, dmack_accepted, wait_extension_event,
        dm_bus_active, dma, dma_valid, dmd_write_data,
        dmd_write_data_valid, probe_i_data, probe_i_valid,
        probe_m_data, probe_m_valid, probe_l_data, probe_l_valid,
        mstat
    };

    adsp2100_dm_write_immediate_native_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .bus_relinquished_i(bus_relinquished),
        .execute_i(execute),
        .opcode_i(opcode),
        .dm_ack_i(dm_ack),
        .mstat_setup_write_i(mstat_setup_write),
        .mstat_setup_data_i(mstat_setup_data),
        .dag_setup_write_i(dag_setup_write),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .probe_dag_address_i(probe_dag_address),
        .issue_boundary_o(issue_boundary),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .immediate_o(immediate),
        .dag2_o(dag2),
        .i_local_o(i_local),
        .m_local_o(m_local),
        .i_address_o(i_address),
        .m_address_o(m_address),
        .l_address_o(l_address),
        .boundary_valid_o(boundary_valid),
        .accepted_o(accepted),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .stalled_o(stalled),
        .busy_o(busy),
        .invalid_opcode_o(invalid_opcode),
        .internal_conflict_o(internal_conflict),
        .dag_configuration_valid_o(dag_configuration_valid),
        .i_write_o(i_write),
        .i_write_known_o(i_write_known),
        .dm_request_accepted_o(dm_request_accepted),
        .dmack_sample_event_o(dmack_sample_event),
        .dmack_accepted_o(dmack_accepted),
        .wait_extension_event_o(wait_extension_event),
        .dm_completion_event_o(dm_completion_event),
        .dm_bus_active_o(dm_bus_active),
        .dm_bus_waiting_o(dm_bus_waiting),
        .dm_address_output_enable_o(dm_address_oe),
        .dm_control_output_enable_o(dm_control_oe),
        .dm_data_output_enable_o(dm_data_oe),
        .dma_o(dma),
        .dma_valid_o(dma_valid),
        .dms_n_o(dms_n),
        .dmrd_n_o(dmrd_n),
        .dmwr_n_o(dmwr_n),
        .dmd_write_data_o(dmd_write_data),
        .dmd_write_data_valid_o(dmd_write_data_valid),
        .probe_i_data_o(probe_i_data),
        .probe_i_valid_o(probe_i_valid),
        .probe_m_data_o(probe_m_data),
        .probe_m_valid_o(probe_m_valid),
        .probe_l_data_o(probe_l_data),
        .probe_l_valid_o(probe_l_valid),
        .mstat_o(mstat)
    );

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (issue_boundary == (
            !reset && !bus_relinquished && phase_advance
            && phase == PHASE_STATE_8
        ));
        assert (phase_conflict
            == (!reset && controls_present && !issue_boundary));
        assert (!attachment_conflict);
        assert (integration_conflict
            == (phase_conflict || attachment_conflict
                || dut.core_integration_conflict));
        assert (accepted == dm_request_accepted);
        assert (instruction_complete
            == (dm_completion_event && dut.core_dm_select));
        assert (!(~dmrd_n && ~dmwr_n));
        assert (dm_address_oe == dm_control_oe);
        assert (dms_n == !dm_control_oe);
        if (accepted) begin
            assert (issue_boundary && dut.core_dm_select);
        end
        if (instruction_complete) begin
            assert (phase == PHASE_STATE_7 && phase_advance);
            assert (transaction_active && dm_bus_active && i_write);
        end
        if (dm_bus_waiting) begin
            assert (transaction_active && stalled);
            assert (!instruction_complete && !i_write);
        end
        if (bus_relinquished || reset) begin
            assert (!dm_address_oe && !dm_control_oe && !dm_data_oe);
        end
    end

    always_ff @(posedge clk) begin
        cover (accepted && dm_request_accepted);
        cover (wait_extension_event && dm_bus_waiting);
        cover (instruction_complete && i_write);
    end
endmodule

`default_nettype wire
