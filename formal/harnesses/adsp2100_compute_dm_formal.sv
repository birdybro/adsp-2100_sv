`default_nettype none

module adsp2100_compute_dm_formal (
    input logic clk,
    input logic reset,
    input logic execute,
    input logic [23:0] opcode,
    input logic dm_ack,
    input logic [15:0] dm_read_data,
    input logic dm_read_data_valid,
    input logic astat_setup,
    input logic [7:0] astat_setup_data,
    input logic mstat_setup,
    input logic [3:0] mstat_setup_data,
    input logic dreg_setup,
    input logic [3:0] dreg_setup_code,
    input logic [15:0] dreg_setup_data,
    input logic af_setup,
    input logic [15:0] af_setup_data,
    input logic mf_setup,
    input logic [15:0] mf_setup_data,
    input logic dag_setup,
    input logic [1:0] dag_setup_kind,
    input logic [2:0] dag_setup_address,
    input logic [13:0] dag_setup_data,
    input logic inspect_probe,
    input logic [3:0] probe_dreg_code,
    input logic [2:0] probe_dag_address
);
    logic class_valid;
    logic action_valid;
    logic unsupported;
    logic collision;
    logic computation_enable;
    logic is_mac;
    logic destination_feedback;
    logic dag_select;
    logic write_direction;
    logic [4:0] amf;
    logic [1:0] yop;
    logic [2:0] xop;
    logic [3:0] x_source;
    logic [3:0] y_source;
    logic [3:0] memory_dreg;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic boundary_valid;
    logic accepted;
    logic instruction_complete;
    logic transaction_active;
    logic stalled;
    logic busy;
    logic invalid_opcode;
    logic integration_conflict;
    logic internal_conflict;
    logic dm_select;
    logic dm_read;
    logic dm_write;
    logic [13:0] dm_address;
    logic dm_address_valid;
    logic [15:0] dm_write_data;
    logic dm_write_data_valid;
    logic pm_data_access;
    logic dm_access;
    logic compute_result_known;
    logic dag_configuration_valid;
    logic i_write;
    logic i_write_known;
    logic dreg_write;
    logic dreg_write_known;
    logic alu_write;
    logic mac_write;
    logic alu_status_write;
    logic mac_status_write;
    logic [15:0] alu_result;
    logic [39:0] mac_result;
    logic [15:0] probe_dreg_data;
    logic probe_dreg_valid;
    logic [13:0] probe_i_data;
    logic probe_i_valid;
    logic [13:0] probe_m_data;
    logic probe_m_valid;
    logic [13:0] probe_l_data;
    logic probe_l_valid;
    logic [15:0] af;
    logic af_valid;
    logic [15:0] mf;
    logic mf_valid;
    logic [39:0] mr;
    logic mr_valid;
    logic [7:0] astat;
    logic [7:0] astat_valid_mask;
    logic [3:0] mstat;
    logic alternate_bank;
    logic expected_class;
    logic expected_compute;
    logic expected_collision;
    logic expected_action;
    logic [3:0] setup_count;
    logic past_valid;
    logic unused_observation;

    assign expected_class = ((opcode & 24'he00000) == 24'h600000);
    assign expected_compute = expected_class && opcode[17:13] != 5'h00;
    assign expected_collision = (
        expected_compute && !opcode[19] && !opcode[18]
        && (
            (opcode[17] && opcode[7:4] == 4'ha)
            || (
                !opcode[17] && opcode[7:4] >= 4'hb
                && opcode[7:4] <= 4'hd
            )
        )
    );
    assign expected_action = expected_class && !expected_collision;
    assign setup_count = (
        {3'h0, astat_setup} + {3'h0, mstat_setup}
        + {3'h0, dreg_setup} + {3'h0, af_setup}
        + {3'h0, mf_setup} + {3'h0, dag_setup}
    );
    assign unused_observation = ^{
        destination_feedback, dag_select, write_direction, amf, yop, xop,
        x_source, y_source, memory_dreg, i_address, m_address,
        internal_conflict, compute_result_known, dag_configuration_valid,
        i_write_known, dreg_write_known, alu_result, mac_result,
        probe_dreg_data, probe_dreg_valid, probe_i_data, probe_i_valid,
        probe_m_data, probe_m_valid, probe_l_data, probe_l_valid,
        af_valid, mf_valid, mr_valid
    };

    adsp2100_compute_dm_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .dm_ack_i(dm_ack),
        .dm_read_data_i(dm_read_data),
        .dm_read_data_valid_i(dm_read_data_valid),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .af_setup_write_i(af_setup),
        .af_setup_data_i(af_setup_data),
        .mf_setup_write_i(mf_setup),
        .mf_setup_data_i(mf_setup_data),
        .dag_setup_write_i(dag_setup),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .inspect_probe_i(inspect_probe),
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported),
        .destination_collision_o(collision),
        .computation_enable_o(computation_enable),
        .is_mac_o(is_mac),
        .destination_feedback_o(destination_feedback),
        .dag_select_o(dag_select),
        .write_direction_o(write_direction),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .y_source_dreg_o(y_source),
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
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .dm_select_o(dm_select),
        .dm_read_o(dm_read),
        .dm_write_o(dm_write),
        .dm_address_o(dm_address),
        .dm_address_valid_o(dm_address_valid),
        .dm_write_data_o(dm_write_data),
        .dm_write_data_valid_o(dm_write_data_valid),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access),
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

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (computation_enable == expected_compute);
        assert (collision == expected_collision);
        assert (action_valid == expected_action);
        assert (unsupported == (expected_class && !expected_action));
        assert (is_mac == (expected_compute && !opcode[17]));
        assert (
            boundary_valid
            == (!reset && !dut.pending_q && execute && expected_action
                && setup_count == 4'h0 && !inspect_probe)
        );
        assert (boundary_valid == accepted);
        assert (
            invalid_opcode
            == (!reset && !dut.pending_q && execute && !expected_action)
        );
        assert (
            integration_conflict
            == (!reset && (
                (dut.pending_q && (execute || setup_count != 4'h0))
                || (!dut.pending_q && (
                    (execute && (setup_count != 4'h0 || inspect_probe))
                    || setup_count > 4'h1
                ))
            ))
        );
        assert (instruction_complete == (transaction_active && dm_ack));
        assert (stalled == (transaction_active && !dm_ack));
        assert (busy == stalled);
        assert (dm_select == transaction_active);
        assert (dm_read == (transaction_active && !dut.active_write));
        assert (dm_write == (transaction_active && dut.active_write));
        assert (!(dm_read && dm_write));
        assert (dm_access == dm_select);
        assert (!pm_data_access);
        assert (i_write == instruction_complete);
        assert (dreg_write == (instruction_complete && !dut.active_write));
        assert (alu_write == alu_status_write);
        assert (mac_write == mac_status_write);
        assert (!(alu_write && mac_write));
        assert (unused_observation == unused_observation);
        if (reset) begin
            assert (!transaction_active && !accepted && !instruction_complete);
        end
        if (stalled) begin
            assert (!i_write && !dreg_write && !alu_write && !mac_write);
        end
        if (!dm_write_data_valid) begin
            assert (dm_write_data == 16'h0000);
        end
        if (!dm_address_valid) begin
            assert (dm_address == 14'h0000);
        end
        if (!compute_result_known) begin
            assert (alu_result == 16'h0000);
            assert (mac_result == 40'h0000000000);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && $past(stalled) && stalled) begin
            assert (dm_select);
            assert (dm_read == $past(dm_read));
            assert (dm_write == $past(dm_write));
            assert (dm_address_valid == $past(dm_address_valid));
            assert (dm_address == $past(dm_address));
            assert (dm_write_data_valid == $past(dm_write_data_valid));
            assert (dm_write_data == $past(dm_write_data));
            assert (af == $past(af));
            assert (mf == $past(mf));
            assert (mr == $past(mr));
            assert (astat == $past(astat));
            assert (astat_valid_mask == $past(astat_valid_mask));
            assert (mstat == $past(mstat));
            assert (alternate_bank == $past(alternate_bank));
            if (
                inspect_probe == $past(inspect_probe)
                && probe_dreg_code == $past(probe_dreg_code)
            ) begin
                assert (probe_dreg_data == $past(probe_dreg_data));
                assert (probe_dreg_valid == $past(probe_dreg_valid));
            end
            if (probe_dag_address == $past(probe_dag_address)) begin
                assert (probe_i_data == $past(probe_i_data));
                assert (probe_i_valid == $past(probe_i_valid));
                assert (probe_m_data == $past(probe_m_data));
                assert (probe_m_valid == $past(probe_m_valid));
                assert (probe_l_data == $past(probe_l_data));
                assert (probe_l_valid == $past(probe_l_valid));
            end
        end
        cover (past_valid && $past(stalled) && instruction_complete);
        cover (boundary_valid && !computation_enable && dm_read);
        cover (boundary_valid && computation_enable && dm_write);
    end
endmodule

`default_nettype wire
