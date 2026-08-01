`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_dm_write_immediate_native_slice;
    logic        clk;
    logic [59:0] stimulus;
    logic [94:0] expected_pre;
    logic [85:0] expected_post;
    logic        reset;
    logic [2:0]  phase;
    logic        phase_advance;
    logic        bus_relinquished;
    logic        execute;
    logic [23:0] opcode;
    logic        dm_ack;
    logic        mstat_setup_write;
    logic [3:0]  mstat_setup_data;
    logic        dag_setup_write;
    logic [1:0]  dag_setup_kind;
    logic [2:0]  dag_setup_address;
    logic [13:0] dag_setup_data;
    logic [2:0]  probe_dag_address;

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
    logic unused_observation;

    logic exp_issue_boundary;
    logic exp_phase_conflict;
    logic exp_attachment_conflict;
    logic exp_integration_conflict;
    logic exp_class_valid;
    logic exp_action_valid;
    logic exp_boundary_valid;
    logic exp_accepted;
    logic exp_instruction_complete;
    logic exp_transaction_active;
    logic exp_stalled;
    logic exp_busy;
    logic exp_invalid_opcode;
    logic exp_dag_configuration_valid;
    logic exp_i_write;
    logic exp_i_write_known;
    logic exp_dm_select;
    logic exp_dm_write;
    logic exp_core_address_valid;
    logic [13:0] exp_core_address;
    logic exp_core_write_data_valid;
    logic [15:0] exp_core_write_data;
    logic exp_dm_request_accepted;
    logic exp_dmack_sample_event;
    logic exp_dmack_accepted;
    logic exp_wait_extension_event;
    logic exp_dm_completion_event;
    logic exp_dm_bus_active;
    logic exp_dm_bus_waiting;
    logic exp_dm_address_oe;
    logic exp_dm_control_oe;
    logic exp_dm_data_oe;
    logic exp_dma_valid;
    logic [13:0] exp_dma;
    logic exp_dms_n;
    logic exp_dmrd_n;
    logic exp_dmwr_n;
    logic exp_dmd_write_data_valid;
    logic [15:0] exp_dmd_write_data;

    logic exp_probe_i_valid;
    logic [13:0] exp_probe_i_data;
    logic exp_probe_m_valid;
    logic [13:0] exp_probe_m_data;
    logic exp_probe_l_valid;
    logic [13:0] exp_probe_l_data;
    logic [3:0] exp_mstat;
    logic exp_core_pending;
    logic exp_bus_active;
    logic exp_bus_waiting;
    logic exp_bus_acknowledged;
    logic exp_bus_response_valid;
    logic exp_descriptor_address_valid;
    logic [13:0] exp_descriptor_address;
    logic exp_descriptor_data_valid;
    logic [15:0] exp_descriptor_data;
    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign unused_observation = ^{
        immediate, dag2, i_local, m_local, i_address, m_address,
        l_address, internal_conflict
    };

    always_comb begin
        assert (unused_observation == unused_observation);
    end

    assign {
        reset, phase, phase_advance, bus_relinquished, execute, opcode,
        dm_ack, mstat_setup_write, mstat_setup_data, dag_setup_write,
        dag_setup_kind, dag_setup_address, dag_setup_data,
        probe_dag_address
    } = stimulus;
    assign {
        exp_issue_boundary, exp_phase_conflict,
        exp_attachment_conflict, exp_integration_conflict,
        exp_class_valid, exp_action_valid, exp_boundary_valid,
        exp_accepted, exp_instruction_complete,
        exp_transaction_active, exp_stalled, exp_busy,
        exp_invalid_opcode, exp_dag_configuration_valid,
        exp_i_write, exp_i_write_known, exp_dm_select, exp_dm_write,
        exp_core_address_valid, exp_core_address,
        exp_core_write_data_valid, exp_core_write_data,
        exp_dm_request_accepted, exp_dmack_sample_event,
        exp_dmack_accepted, exp_wait_extension_event,
        exp_dm_completion_event, exp_dm_bus_active,
        exp_dm_bus_waiting, exp_dm_address_oe, exp_dm_control_oe,
        exp_dm_data_oe, exp_dma_valid, exp_dma,
        exp_dms_n, exp_dmrd_n, exp_dmwr_n,
        exp_dmd_write_data_valid, exp_dmd_write_data
    } = expected_pre;
    assign {
        exp_probe_i_valid, exp_probe_i_data,
        exp_probe_m_valid, exp_probe_m_data,
        exp_probe_l_valid, exp_probe_l_data,
        exp_mstat, exp_core_pending, exp_bus_active,
        exp_bus_waiting, exp_bus_acknowledged,
        exp_bus_response_valid, exp_descriptor_address_valid,
        exp_descriptor_address, exp_descriptor_data_valid,
        exp_descriptor_data
    } = expected_post;

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

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_pre = '0;
        expected_post = '0;
        vector_file = $fopen(
            "build/dm_write_immediate_native_vectors.txt", "r"
        );
        if (vector_file == 0)
            $fatal(1, "cannot open Type 2/native-DM vectors");
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_pre,
                expected_post
            );
            if (scan_count == 3) begin
                #2;
                if ({
                    issue_boundary, phase_conflict,
                    attachment_conflict, integration_conflict,
                    class_valid, action_valid, boundary_valid,
                    accepted, instruction_complete,
                    transaction_active, stalled, busy, invalid_opcode,
                    dag_configuration_valid, i_write, i_write_known,
                    dut.core_dm_select, dut.core_dm_write,
                    dut.core_dm_address_valid,
                    dut.core_dm_write_data_valid,
                    dm_request_accepted, dmack_sample_event,
                    dmack_accepted, wait_extension_event,
                    dm_completion_event, dm_bus_active, dm_bus_waiting,
                    dm_address_oe, dm_control_oe, dm_data_oe,
                    dma_valid, dms_n, dmrd_n, dmwr_n,
                    dmd_write_data_valid
                } !== {
                    exp_issue_boundary, exp_phase_conflict,
                    exp_attachment_conflict, exp_integration_conflict,
                    exp_class_valid, exp_action_valid,
                    exp_boundary_valid, exp_accepted,
                    exp_instruction_complete, exp_transaction_active,
                    exp_stalled, exp_busy, exp_invalid_opcode,
                    exp_dag_configuration_valid, exp_i_write,
                    exp_i_write_known, exp_dm_select, exp_dm_write,
                    exp_core_address_valid,
                    exp_core_write_data_valid,
                    exp_dm_request_accepted, exp_dmack_sample_event,
                    exp_dmack_accepted, exp_wait_extension_event,
                    exp_dm_completion_event, exp_dm_bus_active,
                    exp_dm_bus_waiting, exp_dm_address_oe,
                    exp_dm_control_oe, exp_dm_data_oe, exp_dma_valid,
                    exp_dms_n, exp_dmrd_n, exp_dmwr_n,
                    exp_dmd_write_data_valid
                }) begin
                    $fatal(
                        1,
                        "Type 2/native pre-event mismatch vector=%0d stimulus=%015x",
                        vector_count,
                        stimulus
                    );
                end
                if (
                    exp_core_address_valid
                    && dut.core_dm_address !== exp_core_address
                ) $fatal(1, "core DMA mismatch vector=%0d", vector_count);
                if (
                    exp_core_write_data_valid
                    && dut.core_dm_write_data !== exp_core_write_data
                ) $fatal(1, "core DMD mismatch vector=%0d", vector_count);
                if (exp_dma_valid && dma !== exp_dma)
                    $fatal(1, "native DMA mismatch vector=%0d", vector_count);
                if (
                    exp_dmd_write_data_valid
                    && dmd_write_data !== exp_dmd_write_data
                ) $fatal(1, "native DMD mismatch vector=%0d", vector_count);

                #2 clk = 1'b1;
                #1;
                if ({
                    probe_i_valid, probe_m_valid, probe_l_valid,
                    mstat, dut.core.pending_q, dut.bus.active_q,
                    dut.bus.waiting_q, dut.bus.acknowledged_q,
                    dut.bus.response_valid_q,
                    dut.bus.address_valid_q,
                    dut.bus.write_data_valid_q
                } !== {
                    exp_probe_i_valid, exp_probe_m_valid,
                    exp_probe_l_valid, exp_mstat, exp_core_pending,
                    exp_bus_active, exp_bus_waiting,
                    exp_bus_acknowledged, exp_bus_response_valid,
                    exp_descriptor_address_valid,
                    exp_descriptor_data_valid
                }) begin
                    $fatal(
                        1,
                        "Type 2/native post-state mismatch vector=%0d",
                        vector_count
                    );
                end
                if (exp_probe_i_valid && probe_i_data !== exp_probe_i_data)
                    $fatal(1, "I probe mismatch vector=%0d", vector_count);
                if (exp_probe_m_valid && probe_m_data !== exp_probe_m_data)
                    $fatal(1, "M probe mismatch vector=%0d", vector_count);
                if (exp_probe_l_valid && probe_l_data !== exp_probe_l_data)
                    $fatal(1, "L probe mismatch vector=%0d", vector_count);
                if (
                    exp_descriptor_address_valid
                    && dut.bus.address_q !== exp_descriptor_address
                ) $fatal(1, "descriptor DMA mismatch vector=%0d", vector_count);
                if (
                    exp_descriptor_data_valid
                    && dut.bus.write_data_q !== exp_descriptor_data
                ) $fatal(1, "descriptor DMD mismatch vector=%0d", vector_count);
                #1 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display(
            "PASS Type 2/native-DM model-RTL differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
