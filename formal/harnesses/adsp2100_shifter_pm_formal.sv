`default_nettype none

module adsp2100_shifter_pm_formal (
    input logic clk,
    input logic reset,
    input logic execute,
    input logic [23:0] opcode,
    input logic [23:0] pm_read_data,
    input logic pm_read_data_valid,
    input logic [13:0] next_fetch_address,
    input logic next_fetch_address_valid,
    input logic cache_next_instruction_valid,
    input logic force_instruction_fetch,
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
    input logic px_setup,
    input logic [7:0] px_setup_data
);
    logic class_valid;
    logic action_valid;
    logic unsupported;
    logic unavailable_xop;
    logic collision;
    logic write_direction;
    logic [3:0] sf;
    logic [2:0] xop;
    logic [3:0] shifter_source;
    logic [3:0] memory_dreg;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic boundary_valid;
    logic accepted;
    logic data_action_complete;
    logic instruction_complete;
    logic transaction_active;
    logic held_transaction;
    logic busy;
    logic invalid_opcode;
    logic integration_conflict;
    logic internal_conflict;
    logic cache_instruction_selected;
    logic recovery_required;
    logic recovery_fetch;
    logic event_boundary;
    logic pm_select;
    logic pm_data_access;
    logic pm_read;
    logic pm_write;
    logic [13:0] pm_address;
    logic pm_address_valid;
    logic [23:0] pm_write_data;
    logic pm_write_data_valid;
    logic [23:0] fetched_instruction;
    logic fetched_instruction_valid;
    logic dm_access;
    logic shifter_result_known;
    logic dag_configuration_valid;
    logic i_write;
    logic i_write_known;
    logic dreg_write;
    logic dreg_write_known;
    logic px_write;
    logic px_write_known;
    logic sr_write;
    logic se_write;
    logic sb_write;
    logic ss_write;
    logic [31:0] sr_result;
    logic [7:0] se_result;
    logic [4:0] sb_result;
    logic ss_result;
    logic [7:0] px;
    logic px_valid;
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
    logic expected_issue;
    logic expected_recovery;
    logic [3:0] setup_count;
    logic past_valid;
    logic unused_observation;

    assign expected_class = ((opcode & 24'hff0000) == 24'h110000);
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
        + {3'h0, px_setup}
    );
    assign expected_issue = (
        !reset && !dut.recovery_q && execute && expected_action
        && setup_count == 4'h0
    );
    assign expected_recovery = (
        expected_issue
        && (force_instruction_fetch || !cache_next_instruction_valid)
    );
    assign unused_observation = ^{
        shifter_source, memory_dreg, i_address, m_address,
        shifter_result_known, dag_configuration_valid,
        i_write_known, dreg_write_known, px_write_known,
        sr_write, se_write, sb_write, ss_write,
        sr_result, se_result, sb_result, ss_result,
        fetched_instruction, fetched_instruction_valid,
        px, px_valid, sr, sr_valid, se, se_valid, sb, sb_valid,
        astat, astat_valid_mask, mstat, alternate_bank
    };

    adsp2100_shifter_pm_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .pm_read_data_i(pm_read_data),
        .pm_read_data_valid_i(pm_read_data_valid),
        .pm_cycle_complete_i(1'b1),
        .next_fetch_address_i(next_fetch_address),
        .next_fetch_address_valid_i(next_fetch_address_valid),
        .cache_next_instruction_valid_i(cache_next_instruction_valid),
        .force_instruction_fetch_i(force_instruction_fetch),
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
        .px_setup_write_i(px_setup),
        .px_setup_data_i(px_setup_data),
        .probe_dreg_code_i(4'h0),
        .probe_dag_address_i(3'h0),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported),
        .unavailable_xop_o(unavailable_xop),
        .destination_collision_o(collision),
        .write_direction_o(write_direction),
        .sf_o(sf),
        .xop_o(xop),
        .shifter_source_dreg_o(shifter_source),
        .memory_dreg_o(memory_dreg),
        .i_address_o(i_address),
        .m_address_o(m_address),
        .boundary_valid_o(boundary_valid),
        .accepted_o(accepted),
        .data_action_complete_o(data_action_complete),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .held_transaction_o(held_transaction),
        .busy_o(busy),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .cache_instruction_selected_o(cache_instruction_selected),
        .recovery_required_o(recovery_required),
        .recovery_fetch_o(recovery_fetch),
        .event_boundary_o(event_boundary),
        .pm_select_o(pm_select),
        .pm_data_access_o(pm_data_access),
        .pm_read_o(pm_read),
        .pm_write_o(pm_write),
        .pm_address_o(pm_address),
        .pm_address_valid_o(pm_address_valid),
        .pm_write_data_o(pm_write_data),
        .pm_write_data_valid_o(pm_write_data_valid),
        .fetched_instruction_o(fetched_instruction),
        .fetched_instruction_valid_o(fetched_instruction_valid),
        .dm_access_o(dm_access),
        .shifter_result_known_o(shifter_result_known),
        .dag_configuration_valid_o(dag_configuration_valid),
        .i_write_o(i_write),
        .i_write_known_o(i_write_known),
        .dreg_write_o(dreg_write),
        .dreg_write_known_o(dreg_write_known),
        .px_write_o(px_write),
        .px_write_known_o(px_write_known),
        .sr_write_o(sr_write),
        .se_write_o(se_write),
        .sb_write_o(sb_write),
        .ss_write_o(ss_write),
        .sr_result_o(sr_result),
        .se_result_o(se_result),
        .sb_result_o(sb_result),
        .ss_result_o(ss_result),
        .probe_dreg_data_o(),
        .probe_dreg_valid_o(),
        .probe_i_data_o(),
        .probe_i_valid_o(),
        .probe_m_data_o(),
        .probe_m_valid_o(),
        .probe_l_data_o(),
        .probe_l_valid_o(),
        .px_o(px),
        .px_valid_o(px_valid),
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
        assert (write_direction == (expected_class ? opcode[15] : 1'b0));
        assert (sf == (expected_class ? opcode[14:11] : 4'h0));
        assert (xop == (expected_class ? opcode[10:8] : 3'h0));
        assert (boundary_valid == expected_issue);
        assert (accepted == expected_issue);
        assert (data_action_complete == expected_issue);
        assert (
            invalid_opcode
            == (!reset && !dut.recovery_q && execute && !expected_action)
        );
        assert (
            integration_conflict
            == (!reset && (
                (dut.recovery_q && (execute || setup_count != 4'h0))
                || (!dut.recovery_q && (
                    (execute && setup_count != 4'h0)
                    || setup_count > 4'h1
                ))
            ))
        );
        assert (recovery_required == expected_recovery);
        assert (recovery_fetch == (!reset && dut.recovery_q));
        assert (
            instruction_complete
            == (!reset && ((expected_issue && !expected_recovery)
                || dut.recovery_q))
        );
        assert (transaction_active == (!reset && (expected_issue || dut.recovery_q)));
        assert (held_transaction == (!reset && (dut.pending_q || recovery_fetch)));
        assert (busy == expected_recovery);
        assert (event_boundary == instruction_complete);
        assert (cache_instruction_selected == (
            expected_issue && cache_next_instruction_valid
            && !force_instruction_fetch
        ));
        assert (pm_select == transaction_active);
        assert (pm_data_access == expected_issue);
        assert (pm_read == (dut.recovery_q || (expected_issue && !write_direction)));
        assert (pm_write == (expected_issue && write_direction));
        assert (!(pm_read && pm_write));
        assert (!dm_access);
        assert (i_write == expected_issue);
        assert (dreg_write == (expected_issue && !write_direction));
        assert (px_write == dreg_write);
        assert (internal_conflict == dut.dag_invalid_setup_kind);
        assert (unused_observation == unused_observation);
        if (pm_write_data_valid) begin
            assert (pm_write_data == {dut.memory_source_data, dut.px_q});
        end else begin
            assert (pm_write_data == 24'h000000);
        end
        if (!pm_address_valid) begin
            assert (pm_address == 14'h0000);
        end
        if (!fetched_instruction_valid) begin
            assert (fetched_instruction == 24'h000000);
        end
        if (recovery_fetch) begin
            assert (pm_read && !pm_write && !pm_data_access);
            assert (!data_action_complete && instruction_complete);
            assert (!i_write && !dreg_write && !px_write);
            assert (!sr_write && !se_write && !sb_write && !ss_write);
        end
        if (reset) begin
            assert (!pm_select && !accepted && !instruction_complete);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && !$past(reset) && $past(expected_recovery) && !reset) begin
            assert (recovery_fetch);
            assert (pm_address_valid == $past(next_fetch_address_valid));
            if ($past(next_fetch_address_valid)) begin
                assert (pm_address == $past(next_fetch_address));
            end
        end
        if (past_valid && $past(recovery_fetch) && !reset) begin
            assert (!recovery_fetch);
        end
        cover (past_valid && $past(expected_recovery) && recovery_fetch);
        cover (expected_issue && !expected_recovery && instruction_complete);
    end
endmodule

`default_nettype wire
