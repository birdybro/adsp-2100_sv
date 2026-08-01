`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_shifter_dm_native_slice;
    logic         clk;
    logic [116:0] stimulus;
    logic [103:0] expected_pre;
    logic [135:0] expected_post;
    logic         reset;
    logic [2:0]   phase;
    logic         phase_advance;
    logic         bus_relinquished;
    logic         execute;
    logic [23:0]  opcode;
    logic         dm_ack;
    logic [15:0]  dmd_read_data;
    logic         dmd_read_data_valid;
    logic         astat_setup_write;
    logic [7:0]   astat_setup_data;
    logic         mstat_setup_write;
    logic [3:0]   mstat_setup_data;
    logic         dreg_setup_write;
    logic [3:0]   dreg_setup_code;
    logic [15:0]  dreg_setup_data;
    logic         sb_setup_write;
    logic [4:0]   sb_setup_data;
    logic         dag_setup_write;
    logic [1:0]   dag_setup_kind;
    logic [2:0]   dag_setup_address;
    logic [13:0]  dag_setup_data;
    logic [3:0]   probe_dreg_code;
    logic [2:0]   probe_dag_address;

    logic         issue_boundary;
    logic         phase_conflict;
    logic         attachment_conflict;
    logic         integration_conflict;
    logic         class_valid;
    logic         action_valid;
    logic         unsupported_subencoding;
    logic         unavailable_xop;
    logic         destination_collision;
    logic         dag_select;
    logic         write_direction;
    logic [3:0]   sf;
    logic [2:0]   xop;
    logic [3:0]   shifter_source_dreg;
    logic [3:0]   memory_dreg;
    logic [2:0]   i_address;
    logic [2:0]   m_address;
    logic         boundary_valid;
    logic         accepted;
    logic         instruction_complete;
    logic         transaction_active;
    logic         stalled;
    logic         busy;
    logic         invalid_opcode;
    logic         internal_conflict;
    logic         dm_select;
    logic         dm_read;
    logic         dm_write;
    logic [13:0]  dm_address;
    logic         dm_address_valid;
    logic [15:0]  dm_write_data;
    logic         dm_write_data_valid;
    logic         shifter_result_known;
    logic         dag_configuration_valid;
    logic         i_write;
    logic         i_write_known;
    logic         dreg_write;
    logic         dreg_write_known;
    logic         sr_write;
    logic         se_write;
    logic         sb_write;
    logic         ss_write;
    logic [31:0]  sr_result;
    logic [7:0]   se_result;
    logic [4:0]   sb_result;
    logic         ss_result;
    logic         dm_request_accepted;
    logic         dmack_sample_event;
    logic         dmack_accepted;
    logic         wait_extension_event;
    logic         dm_completion_event;
    logic         dm_read_sample_event;
    logic         dm_bus_active;
    logic         dm_bus_waiting;
    logic         dm_address_oe;
    logic         dm_control_oe;
    logic         dm_data_oe;
    logic [13:0]  dma;
    logic         dma_valid;
    logic         dms_n;
    logic         dmrd_n;
    logic         dmwr_n;
    logic [15:0]  dmd_write_data;
    logic         dmd_write_data_valid;
    logic [15:0]  probe_dreg_data;
    logic         probe_dreg_valid;
    logic [13:0]  probe_i_data;
    logic         probe_i_valid;
    logic [13:0]  probe_m_data;
    logic         probe_m_valid;
    logic [13:0]  probe_l_data;
    logic         probe_l_valid;
    logic [31:0]  sr;
    logic         sr_valid;
    logic [7:0]   se;
    logic         se_valid;
    logic [4:0]   sb;
    logic         sb_valid;
    logic [7:0]   astat;
    logic [7:0]   astat_valid_mask;
    logic [3:0]   mstat;
    logic         alternate_bank;
    logic         unused_observation;

    logic         exp_issue_boundary;
    logic         exp_phase_conflict;
    logic         exp_attachment_conflict;
    logic         exp_integration_conflict;
    logic         exp_class_valid;
    logic         exp_action_valid;
    logic         exp_unsupported_subencoding;
    logic         exp_accepted;
    logic         exp_instruction_complete;
    logic         exp_transaction_active;
    logic         exp_stalled;
    logic         exp_busy;
    logic         exp_invalid_opcode;
    logic         exp_dm_select;
    logic         exp_dm_read;
    logic         exp_dm_write;
    logic         exp_core_address_valid;
    logic [13:0]  exp_core_address;
    logic         exp_core_write_data_valid;
    logic [15:0]  exp_core_write_data;
    logic         exp_shifter_result_known;
    logic         exp_dag_configuration_valid;
    logic         exp_i_write;
    logic         exp_i_write_known;
    logic         exp_dreg_write;
    logic         exp_dreg_write_known;
    logic         exp_sr_write;
    logic         exp_se_write;
    logic         exp_sb_write;
    logic         exp_ss_write;
    logic         exp_dm_request_accepted;
    logic         exp_dmack_sample_event;
    logic         exp_dmack_accepted;
    logic         exp_wait_extension_event;
    logic         exp_dm_completion_event;
    logic         exp_dm_read_sample_event;
    logic         exp_dm_bus_active;
    logic         exp_dm_bus_waiting;
    logic         exp_dm_address_oe;
    logic         exp_dm_control_oe;
    logic         exp_dm_data_oe;
    logic         exp_dma_valid;
    logic [13:0]  exp_dma;
    logic         exp_dms_n;
    logic         exp_dmrd_n;
    logic         exp_dmwr_n;
    logic         exp_dmd_write_data_valid;
    logic [15:0]  exp_dmd_write_data;

    logic         exp_probe_dreg_valid;
    logic [15:0]  exp_probe_dreg_data;
    logic         exp_probe_i_valid;
    logic [13:0]  exp_probe_i_data;
    logic         exp_probe_m_valid;
    logic [13:0]  exp_probe_m_data;
    logic         exp_probe_l_valid;
    logic [13:0]  exp_probe_l_data;
    logic         exp_sr_valid;
    logic [31:0]  exp_sr;
    logic         exp_se_valid;
    logic [7:0]   exp_se;
    logic         exp_sb_valid;
    logic [4:0]   exp_sb;
    logic [7:0]   exp_astat_valid_mask;
    logic [7:0]   exp_astat;
    logic [3:0]   exp_mstat;
    logic         exp_alternate_bank;
    logic         exp_core_pending;
    logic         exp_bus_active;
    logic         exp_bus_waiting;
    logic         exp_bus_acknowledged;
    logic         exp_bus_response_valid;
    integer       vector_file;
    integer       scan_count;
    integer       vector_count;

    assign unused_observation = ^{
        unavailable_xop, destination_collision, dag_select,
        write_direction, sf, xop, shifter_source_dreg, memory_dreg,
        i_address, m_address, internal_conflict, sr_result, se_result,
        sb_result, ss_result
    };

    always_comb begin
        assert (unused_observation == unused_observation);
    end

    assign {
        reset, phase, phase_advance, bus_relinquished, execute, opcode,
        dm_ack, dmd_read_data, dmd_read_data_valid,
        astat_setup_write, astat_setup_data,
        mstat_setup_write, mstat_setup_data,
        dreg_setup_write, dreg_setup_code, dreg_setup_data,
        sb_setup_write, sb_setup_data,
        dag_setup_write, dag_setup_kind, dag_setup_address,
        dag_setup_data, probe_dreg_code, probe_dag_address
    } = stimulus;
    assign {
        exp_issue_boundary, exp_phase_conflict,
        exp_attachment_conflict, exp_integration_conflict,
        exp_class_valid, exp_action_valid,
        exp_unsupported_subencoding, exp_accepted,
        exp_instruction_complete, exp_transaction_active,
        exp_stalled, exp_busy, exp_invalid_opcode,
        exp_dm_select, exp_dm_read, exp_dm_write,
        exp_core_address_valid, exp_core_address,
        exp_core_write_data_valid, exp_core_write_data,
        exp_shifter_result_known, exp_dag_configuration_valid,
        exp_i_write, exp_i_write_known, exp_dreg_write,
        exp_dreg_write_known, exp_sr_write, exp_se_write,
        exp_sb_write, exp_ss_write, exp_dm_request_accepted,
        exp_dmack_sample_event, exp_dmack_accepted,
        exp_wait_extension_event, exp_dm_completion_event,
        exp_dm_read_sample_event, exp_dm_bus_active,
        exp_dm_bus_waiting, exp_dm_address_oe, exp_dm_control_oe,
        exp_dm_data_oe, exp_dma_valid, exp_dma, exp_dms_n,
        exp_dmrd_n, exp_dmwr_n, exp_dmd_write_data_valid,
        exp_dmd_write_data
    } = expected_pre;
    assign {
        exp_probe_dreg_valid, exp_probe_dreg_data,
        exp_probe_i_valid, exp_probe_i_data,
        exp_probe_m_valid, exp_probe_m_data,
        exp_probe_l_valid, exp_probe_l_data,
        exp_sr_valid, exp_sr, exp_se_valid, exp_se,
        exp_sb_valid, exp_sb, exp_astat_valid_mask, exp_astat,
        exp_mstat, exp_alternate_bank, exp_core_pending,
        exp_bus_active, exp_bus_waiting, exp_bus_acknowledged,
        exp_bus_response_valid
    } = expected_post;

    adsp2100_shifter_dm_native_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .bus_relinquished_i(bus_relinquished),
        .execute_i(execute),
        .opcode_i(opcode),
        .dm_ack_i(dm_ack),
        .dmd_read_data_i(dmd_read_data),
        .dmd_read_data_valid_i(dmd_read_data_valid),
        .astat_setup_write_i(astat_setup_write),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup_write),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup_write),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .sb_setup_write_i(sb_setup_write),
        .sb_setup_data_i(sb_setup_data),
        .dag_setup_write_i(dag_setup_write),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .issue_boundary_o(issue_boundary),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .unavailable_xop_o(unavailable_xop),
        .destination_collision_o(destination_collision),
        .dag_select_o(dag_select),
        .write_direction_o(write_direction),
        .sf_o(sf),
        .xop_o(xop),
        .shifter_source_dreg_o(shifter_source_dreg),
        .memory_dreg_o(memory_dreg),
        .i_address_o(i_address),
        .m_address_o(m_address),
        .boundary_valid_o(boundary_valid),
        .accepted_o(accepted),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .stalled_o(stalled),
        .busy_o(busy),
        .invalid_opcode_o(invalid_opcode),
        .internal_conflict_o(internal_conflict),
        .dm_select_o(dm_select),
        .dm_read_o(dm_read),
        .dm_write_o(dm_write),
        .dm_address_o(dm_address),
        .dm_address_valid_o(dm_address_valid),
        .dm_write_data_o(dm_write_data),
        .dm_write_data_valid_o(dm_write_data_valid),
        .shifter_result_known_o(shifter_result_known),
        .dag_configuration_valid_o(dag_configuration_valid),
        .i_write_o(i_write),
        .i_write_known_o(i_write_known),
        .dreg_write_o(dreg_write),
        .dreg_write_known_o(dreg_write_known),
        .sr_write_o(sr_write),
        .se_write_o(se_write),
        .sb_write_o(sb_write),
        .ss_write_o(ss_write),
        .sr_result_o(sr_result),
        .se_result_o(se_result),
        .sb_result_o(sb_result),
        .ss_result_o(ss_result),
        .dm_request_accepted_o(dm_request_accepted),
        .dmack_sample_event_o(dmack_sample_event),
        .dmack_accepted_o(dmack_accepted),
        .wait_extension_event_o(wait_extension_event),
        .dm_completion_event_o(dm_completion_event),
        .dm_read_sample_event_o(dm_read_sample_event),
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
        .probe_dreg_data_o(probe_dreg_data),
        .probe_dreg_valid_o(probe_dreg_valid),
        .probe_i_data_o(probe_i_data),
        .probe_i_valid_o(probe_i_valid),
        .probe_m_data_o(probe_m_data),
        .probe_m_valid_o(probe_m_valid),
        .probe_l_data_o(probe_l_data),
        .probe_l_valid_o(probe_l_valid),
        .sr_o(sr),
        .sr_valid_o(sr_valid),
        .se_o(se),
        .se_valid_o(se_valid),
        .sb_o(sb),
        .sb_valid_o(sb_valid),
        .astat_o(astat),
        .astat_valid_mask_o(astat_valid_mask),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_pre = '0;
        expected_post = '0;
        vector_file = $fopen(
            "build/shifter_dm_native_vectors.txt", "r"
        );
        if (vector_file == 0)
            $fatal(1, "cannot open Type 12/native-DM vectors");
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
                    class_valid, action_valid,
                    unsupported_subencoding, accepted,
                    instruction_complete, transaction_active,
                    stalled, busy, invalid_opcode,
                    dm_select, dm_read, dm_write,
                    dm_address_valid, dm_write_data_valid,
                    shifter_result_known, dag_configuration_valid,
                    i_write, i_write_known, dreg_write,
                    dreg_write_known, sr_write, se_write,
                    sb_write, ss_write, dm_request_accepted,
                    dmack_sample_event, dmack_accepted,
                    wait_extension_event, dm_completion_event,
                    dm_read_sample_event, dm_bus_active,
                    dm_bus_waiting, dm_address_oe, dm_control_oe,
                    dm_data_oe, dma_valid, dms_n, dmrd_n, dmwr_n,
                    dmd_write_data_valid
                } !== {
                    exp_issue_boundary, exp_phase_conflict,
                    exp_attachment_conflict, exp_integration_conflict,
                    exp_class_valid, exp_action_valid,
                    exp_unsupported_subencoding, exp_accepted,
                    exp_instruction_complete, exp_transaction_active,
                    exp_stalled, exp_busy, exp_invalid_opcode,
                    exp_dm_select, exp_dm_read, exp_dm_write,
                    exp_core_address_valid,
                    exp_core_write_data_valid,
                    exp_shifter_result_known,
                    exp_dag_configuration_valid, exp_i_write,
                    exp_i_write_known, exp_dreg_write,
                    exp_dreg_write_known, exp_sr_write, exp_se_write,
                    exp_sb_write, exp_ss_write,
                    exp_dm_request_accepted, exp_dmack_sample_event,
                    exp_dmack_accepted, exp_wait_extension_event,
                    exp_dm_completion_event,
                    exp_dm_read_sample_event, exp_dm_bus_active,
                    exp_dm_bus_waiting, exp_dm_address_oe,
                    exp_dm_control_oe, exp_dm_data_oe, exp_dma_valid,
                    exp_dms_n, exp_dmrd_n, exp_dmwr_n,
                    exp_dmd_write_data_valid
                }) begin
                    $fatal(
                        1,
                        "Type 12/native pre-event mismatch vector=%0d stimulus=%030x",
                        vector_count,
                        stimulus
                    );
                end
                if (boundary_valid !== accepted)
                    $fatal(1, "boundary-valid mismatch vector=%0d", vector_count);
                if (exp_core_address_valid && dm_address !== exp_core_address)
                    $fatal(1, "core DMA mismatch vector=%0d", vector_count);
                if (
                    exp_core_write_data_valid
                    && dm_write_data !== exp_core_write_data
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
                    probe_dreg_valid, probe_i_valid, probe_m_valid,
                    probe_l_valid, sr_valid, se_valid, sb_valid,
                    astat_valid_mask, mstat, alternate_bank,
                    dut.core.pending_q, dut.bus.active_q,
                    dut.bus.waiting_q, dut.bus.acknowledged_q,
                    dut.bus.response_valid_q
                } !== {
                    exp_probe_dreg_valid, exp_probe_i_valid,
                    exp_probe_m_valid, exp_probe_l_valid,
                    exp_sr_valid, exp_se_valid, exp_sb_valid,
                    exp_astat_valid_mask, exp_mstat,
                    exp_alternate_bank, exp_core_pending,
                    exp_bus_active, exp_bus_waiting,
                    exp_bus_acknowledged, exp_bus_response_valid
                }) begin
                    $fatal(
                        1,
                        "Type 12/native post-state mismatch vector=%0d",
                        vector_count
                    );
                end
                if (
                    exp_probe_dreg_valid
                    && probe_dreg_data !== exp_probe_dreg_data
                ) $fatal(1, "DREG probe mismatch vector=%0d", vector_count);
                if (exp_probe_i_valid && probe_i_data !== exp_probe_i_data)
                    $fatal(1, "I probe mismatch vector=%0d", vector_count);
                if (exp_probe_m_valid && probe_m_data !== exp_probe_m_data)
                    $fatal(1, "M probe mismatch vector=%0d", vector_count);
                if (exp_probe_l_valid && probe_l_data !== exp_probe_l_data)
                    $fatal(1, "L probe mismatch vector=%0d", vector_count);
                if (exp_sr_valid && sr !== exp_sr)
                    $fatal(1, "SR mismatch vector=%0d", vector_count);
                if (exp_se_valid && se !== exp_se)
                    $fatal(1, "SE mismatch vector=%0d", vector_count);
                if (exp_sb_valid && sb !== exp_sb)
                    $fatal(1, "SB mismatch vector=%0d", vector_count);
                if ((astat & exp_astat_valid_mask)
                    !== (exp_astat & exp_astat_valid_mask))
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
                #1 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display(
            "PASS Type 12/native-DM model-RTL differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
