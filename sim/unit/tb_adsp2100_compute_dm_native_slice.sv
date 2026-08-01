`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_compute_dm_native_slice;
    logic         clk;
    logic [145:0] stimulus;
    logic [103:0] expected_pre;
    logic [162:0] expected_post;

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
    logic         af_setup_write;
    logic [15:0]  af_setup_data;
    logic         mf_setup_write;
    logic [15:0]  mf_setup_data;
    logic         dag_setup_write;
    logic [1:0]   dag_setup_kind;
    logic [2:0]   dag_setup_address;
    logic [13:0]  dag_setup_data;
    logic         inspect_probe;
    logic [3:0]   probe_dreg_code;
    logic [2:0]   probe_dag_address;

    logic         issue_boundary;
    logic         phase_conflict;
    logic         attachment_conflict;
    logic         integration_conflict;
    logic         class_valid;
    logic         action_valid;
    logic         unsupported_subencoding;
    logic         destination_collision;
    logic         computation_enable;
    logic         is_mac;
    logic         destination_feedback;
    logic         dag_select;
    logic         write_direction;
    logic [4:0]   amf;
    logic [1:0]   yop;
    logic [2:0]   xop;
    logic [3:0]   x_source_dreg;
    logic [3:0]   y_source_dreg;
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
    logic         compute_result_known;
    logic         dag_configuration_valid;
    logic         i_write;
    logic         i_write_known;
    logic         dreg_write;
    logic         dreg_write_known;
    logic         alu_write;
    logic         mac_write;
    logic         alu_status_write;
    logic         mac_status_write;
    logic [15:0]  alu_result;
    logic [39:0]  mac_result;

    logic         dm_request_accepted;
    logic         dmack_sample_event;
    logic         dmack_accepted;
    logic         wait_extension_event;
    logic         dm_completion_event;
    logic         dm_read_sample_event;
    logic         dm_bus_active;
    logic         dm_bus_waiting;
    logic         dm_address_output_enable;
    logic         dm_control_output_enable;
    logic         dm_data_output_enable;
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
    logic [15:0]  af;
    logic         af_valid;
    logic [15:0]  mf;
    logic         mf_valid;
    logic [39:0]  mr;
    logic         mr_valid;
    logic [7:0]   astat;
    logic [7:0]   astat_valid_mask;
    logic [3:0]   mstat;
    logic         alternate_bank;
    logic         unused_observation;

    logic         exp_probe_dreg_valid;
    logic [15:0]  exp_probe_dreg_data;
    logic         exp_probe_i_valid;
    logic [13:0]  exp_probe_i_data;
    logic         exp_probe_m_valid;
    logic [13:0]  exp_probe_m_data;
    logic         exp_probe_l_valid;
    logic [13:0]  exp_probe_l_data;
    logic         exp_af_valid;
    logic [15:0]  exp_af;
    logic         exp_mf_valid;
    logic [15:0]  exp_mf;
    logic         exp_mr_valid;
    logic [39:0]  exp_mr;
    logic [7:0]   exp_astat_valid_mask;
    logic [7:0]   exp_astat;
    logic [3:0]   exp_mstat;
    logic         exp_alternate_bank;
    logic         exp_core_pending;
    logic         exp_bus_active;
    logic         exp_bus_waiting;
    logic         exp_bus_acknowledged;
    logic         exp_bus_response_valid;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, phase, phase_advance, bus_relinquished, execute, opcode,
        dm_ack, dmd_read_data, dmd_read_data_valid,
        astat_setup_write, astat_setup_data,
        mstat_setup_write, mstat_setup_data,
        dreg_setup_write, dreg_setup_code, dreg_setup_data,
        af_setup_write, af_setup_data,
        mf_setup_write, mf_setup_data,
        dag_setup_write, dag_setup_kind, dag_setup_address,
        dag_setup_data, inspect_probe, probe_dreg_code,
        probe_dag_address
    } = stimulus;

    assign {
        exp_probe_dreg_valid, exp_probe_dreg_data,
        exp_probe_i_valid, exp_probe_i_data,
        exp_probe_m_valid, exp_probe_m_data,
        exp_probe_l_valid, exp_probe_l_data,
        exp_af_valid, exp_af, exp_mf_valid, exp_mf,
        exp_mr_valid, exp_mr,
        exp_astat_valid_mask, exp_astat,
        exp_mstat, exp_alternate_bank, exp_core_pending,
        exp_bus_active, exp_bus_waiting, exp_bus_acknowledged,
        exp_bus_response_valid
    } = expected_post;

    assign unused_observation = ^{
        destination_collision, computation_enable, is_mac,
        destination_feedback, dag_select, write_direction, amf, yop, xop,
        x_source_dreg, y_source_dreg, memory_dreg, i_address, m_address,
        boundary_valid, internal_conflict, alu_result, mac_result
    };

    always_comb begin
        assert (unused_observation == unused_observation);
    end

    adsp2100_compute_dm_native_slice dut (
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
        .af_setup_write_i(af_setup_write),
        .af_setup_data_i(af_setup_data),
        .mf_setup_write_i(mf_setup_write),
        .mf_setup_data_i(mf_setup_data),
        .dag_setup_write_i(dag_setup_write),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .inspect_probe_i(inspect_probe),
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .issue_boundary_o(issue_boundary),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .destination_collision_o(destination_collision),
        .computation_enable_o(computation_enable),
        .is_mac_o(is_mac),
        .destination_feedback_o(destination_feedback),
        .dag_select_o(dag_select),
        .write_direction_o(write_direction),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source_dreg),
        .y_source_dreg_o(y_source_dreg),
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
        .compute_result_known_o(compute_result_known),
        .dag_configuration_valid_o(dag_configuration_valid),
        .i_write_o(i_write),
        .i_write_known_o(i_write_known),
        .dreg_write_o(dreg_write),
        .dreg_write_known_o(dreg_write_known),
        .alu_write_o(alu_write),
        .mac_write_o(mac_write),
        .alu_status_write_o(alu_status_write),
        .mac_status_write_o(mac_status_write),
        .alu_result_o(alu_result),
        .mac_result_o(mac_result),
        .dm_request_accepted_o(dm_request_accepted),
        .dmack_sample_event_o(dmack_sample_event),
        .dmack_accepted_o(dmack_accepted),
        .wait_extension_event_o(wait_extension_event),
        .dm_completion_event_o(dm_completion_event),
        .dm_read_sample_event_o(dm_read_sample_event),
        .dm_bus_active_o(dm_bus_active),
        .dm_bus_waiting_o(dm_bus_waiting),
        .dm_address_output_enable_o(dm_address_output_enable),
        .dm_control_output_enable_o(dm_control_output_enable),
        .dm_data_output_enable_o(dm_data_output_enable),
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
        .af_o(af),
        .af_valid_o(af_valid),
        .mf_o(mf),
        .mf_valid_o(mf_valid),
        .mr_o(mr),
        .mr_valid_o(mr_valid),
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
            "build/compute_dm_native_vectors.txt", "r"
        );
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/compute_dm_native_vectors.txt");
        end
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
                #1;
                if ({
                    issue_boundary, phase_conflict,
                    attachment_conflict, integration_conflict,
                    class_valid, action_valid, unsupported_subencoding,
                    accepted, instruction_complete, transaction_active,
                    stalled, busy, invalid_opcode,
                    dm_select, dm_read, dm_write,
                    dm_address_valid, dm_address,
                    dm_write_data_valid, dm_write_data,
                    compute_result_known, dag_configuration_valid,
                    i_write, i_write_known, dreg_write, dreg_write_known,
                    alu_write, mac_write, alu_status_write,
                    mac_status_write,
                    dm_request_accepted, dmack_sample_event,
                    dmack_accepted, wait_extension_event,
                    dm_completion_event, dm_read_sample_event,
                    dm_bus_active, dm_bus_waiting,
                    dm_address_output_enable, dm_control_output_enable,
                    dm_data_output_enable, dma_valid, dma,
                    dmd_write_data_valid, dmd_write_data,
                    dms_n, dmrd_n, dmwr_n
                } !== expected_pre) begin
                    $fatal(
                        1,
                        "pre-edge mismatch vector=%0d expected=%h actual=%h",
                        vector_count,
                        expected_pre,
                        {
                            issue_boundary, phase_conflict,
                            attachment_conflict, integration_conflict,
                            class_valid, action_valid,
                            unsupported_subencoding, accepted,
                            instruction_complete, transaction_active,
                            stalled, busy, invalid_opcode,
                            dm_select, dm_read, dm_write,
                            dm_address_valid, dm_address,
                            dm_write_data_valid, dm_write_data,
                            compute_result_known,
                            dag_configuration_valid,
                            i_write, i_write_known, dreg_write,
                            dreg_write_known, alu_write, mac_write,
                            alu_status_write, mac_status_write,
                            dm_request_accepted, dmack_sample_event,
                            dmack_accepted, wait_extension_event,
                            dm_completion_event, dm_read_sample_event,
                            dm_bus_active, dm_bus_waiting,
                            dm_address_output_enable,
                            dm_control_output_enable,
                            dm_data_output_enable, dma_valid, dma,
                            dmd_write_data_valid, dmd_write_data,
                            dms_n, dmrd_n, dmwr_n
                        }
                    );
                end

                #4 clk = 1'b1;
                #1;
                stimulus[7] = 1'b1;
                #1;
                if (probe_dreg_valid !== exp_probe_dreg_valid
                    || probe_i_valid !== exp_probe_i_valid
                    || probe_m_valid !== exp_probe_m_valid
                    || probe_l_valid !== exp_probe_l_valid
                    || af_valid !== exp_af_valid
                    || mf_valid !== exp_mf_valid
                    || mr_valid !== exp_mr_valid
                    || astat_valid_mask !== exp_astat_valid_mask
                    || mstat !== exp_mstat
                    || alternate_bank !== exp_alternate_bank
                    || dut.core.pending_q !== exp_core_pending
                    || dut.bus.active_q !== exp_bus_active
                    || dut.bus.waiting_q !== exp_bus_waiting
                    || dut.bus.acknowledged_q !== exp_bus_acknowledged
                    || dut.bus.response_valid_q
                        !== exp_bus_response_valid) begin
                    $fatal(1, "post validity mismatch vector=%0d", vector_count);
                end
                if (exp_probe_dreg_valid
                    && probe_dreg_data !== exp_probe_dreg_data)
                    $fatal(1, "DREG mismatch vector=%0d", vector_count);
                if (exp_probe_i_valid && probe_i_data !== exp_probe_i_data)
                    $fatal(1, "I mismatch vector=%0d", vector_count);
                if (exp_probe_m_valid && probe_m_data !== exp_probe_m_data)
                    $fatal(1, "M mismatch vector=%0d", vector_count);
                if (exp_probe_l_valid && probe_l_data !== exp_probe_l_data)
                    $fatal(1, "L mismatch vector=%0d", vector_count);
                if (exp_af_valid && af !== exp_af)
                    $fatal(1, "AF mismatch vector=%0d", vector_count);
                if (exp_mf_valid && mf !== exp_mf)
                    $fatal(1, "MF mismatch vector=%0d", vector_count);
                if (exp_mr_valid && mr !== exp_mr)
                    $fatal(1, "MR mismatch vector=%0d", vector_count);
                if ((astat & exp_astat_valid_mask)
                    !== (exp_astat & exp_astat_valid_mask)) begin
                    $fatal(1, "ASTAT mismatch vector=%0d", vector_count);
                end
                #3 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50_000) begin
            $fatal(1, "insufficient vectors: %0d", vector_count);
        end
        $display(
            "PASS Type 4/native-DM model-RTL differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
