`default_nettype none

module adsp2100_shifter_dm_formal (
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
    input logic sb_setup,
    input logic [4:0] sb_setup_data,
    input logic dag_setup,
    input logic [1:0] dag_setup_kind,
    input logic [2:0] dag_setup_address,
    input logic [13:0] dag_setup_data,
    input logic [3:0] probe_dreg_code,
    input logic [2:0] probe_dag_address
);
    logic class_valid;
    logic action_valid;
    logic unsupported;
    logic unavailable_xop;
    logic collision;
    logic dag_select;
    logic write_direction;
    logic [3:0] sf;
    logic [2:0] xop;
    logic [3:0] shifter_source;
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
    logic shifter_result_known;
    logic dag_configuration_valid;
    logic i_write;
    logic i_write_known;
    logic dreg_write;
    logic dreg_write_known;
    logic sr_write;
    logic se_write;
    logic sb_write;
    logic ss_write;
    logic [31:0] sr_result;
    logic [7:0] se_result;
    logic [4:0] sb_result;
    logic ss_result;
    logic [15:0] probe_dreg_data;
    logic probe_dreg_valid;
    logic [13:0] probe_i_data;
    logic probe_i_valid;
    logic [13:0] probe_m_data;
    logic probe_m_valid;
    logic [13:0] probe_l_data;
    logic probe_l_valid;
    logic [31:0] sr;
    logic sr_valid;
    logic [7:0] se;
    logic se_valid;
    logic [4:0] sb;
    logic sb_valid;
    logic [7:0] astat;
    logic [7:0] astat_valid_mask;
    logic [3:0] mstat;
    logic alternate_bank;
    logic expected_class;
    logic raw_collision;
    logic expected_action;
    logic [3:0] setup_count;
    logic past_valid;
    logic unused_observation;

    assign expected_class = ((opcode & 24'hfe0000) == 24'h120000);
    assign raw_collision = (
        (
            opcode[14:11] <= 4'hb
            && (opcode[7:4] == 4'he || opcode[7:4] == 4'hf)
        )
        || (
            opcode[14:11] >= 4'hc
            && opcode[14:11] <= 4'he
            && opcode[7:4] == 4'h9
        )
    );
    assign expected_action = (
        expected_class
        && opcode[10:8] != 3'b001
        && (opcode[15] || !raw_collision)
    );
    assign setup_count = (
        {3'h0, astat_setup}
        + {3'h0, mstat_setup}
        + {3'h0, dreg_setup}
        + {3'h0, sb_setup}
        + {3'h0, dag_setup}
    );
    assign unused_observation = ^{
        shifter_source, memory_dreg, i_address, m_address,
        shifter_result_known, dag_configuration_valid,
        i_write_known, dreg_write_known, sr_write, se_write, sb_write,
        ss_write, sr_result, se_result, sb_result, ss_result,
        probe_dreg_data, probe_dreg_valid, probe_i_data, probe_i_valid,
        probe_m_data, probe_m_valid, probe_l_data, probe_l_valid,
        sr, sr_valid, se, se_valid, sb, sb_valid, astat,
        astat_valid_mask, mstat, alternate_bank
    };

    adsp2100_shifter_dm_slice dut (
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
        .sb_setup_write_i(sb_setup),
        .sb_setup_data_i(sb_setup_data),
        .dag_setup_write_i(dag_setup),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported),
        .unavailable_xop_o(unavailable_xop),
        .destination_collision_o(collision),
        .dag_select_o(dag_select),
        .write_direction_o(write_direction),
        .sf_o(sf),
        .xop_o(xop),
        .shifter_source_dreg_o(shifter_source),
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

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_action);
        assert (unsupported == (expected_class && !expected_action));
        assert (unavailable_xop == (expected_class && xop == 3'b001));
        assert (
            collision
            == (expected_class && !write_direction
                && xop != 3'b001 && raw_collision)
        );
        assert (dag_select == (expected_class ? opcode[16] : 1'b0));
        assert (write_direction == (expected_class ? opcode[15] : 1'b0));
        assert (sf == (expected_class ? opcode[14:11] : 4'h0));
        assert (xop == (expected_class ? opcode[10:8] : 3'h0));
        assert (
            boundary_valid
            == (!reset && !dut.pending_q && execute && expected_action
                && setup_count == 4'h0)
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
                    (execute && setup_count != 4'h0)
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
        assert (internal_conflict == dut.dag_invalid_setup_kind);
        assert (unused_observation == unused_observation);
        if (reset) begin
            assert (!transaction_active && !accepted && !instruction_complete);
        end
        if (stalled) begin
            assert (!i_write && !dreg_write);
            assert (!sr_write && !se_write && !sb_write && !ss_write);
        end
        if (!dm_write_data_valid) begin
            assert (dm_write_data == 16'h0000);
        end
        if (!dm_address_valid) begin
            assert (dm_address == 14'h0000);
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
            assert (sr == $past(sr));
            assert (sr_valid == $past(sr_valid));
            assert (se == $past(se));
            assert (se_valid == $past(se_valid));
            assert (sb == $past(sb));
            assert (sb_valid == $past(sb_valid));
            assert (astat == $past(astat));
            assert (astat_valid_mask == $past(astat_valid_mask));
            assert (mstat == $past(mstat));
            assert (alternate_bank == $past(alternate_bank));
            if (probe_dreg_code == $past(probe_dreg_code)) begin
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
    end
endmodule

`default_nettype wire
