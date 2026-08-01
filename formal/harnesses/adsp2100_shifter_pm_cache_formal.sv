`default_nettype none

module adsp2100_shifter_pm_cache_formal (
    input logic clk,
    input logic reset,
    input logic execute,
    input logic [23:0] opcode,
    input logic [23:0] pm_read_data,
    input logic pm_read_data_valid,
    input logic [13:0] next_fetch_address,
    input logic next_fetch_address_valid,
    input logic force_instruction_fetch,
    input logic external_fetch_fill,
    input logic [13:0] external_fetch_address,
    input logic external_fetch_address_valid,
    input logic [23:0] external_fetch_instruction,
    input logic external_fetch_instruction_valid,
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
    logic cache_selected;
    logic recovery_required;
    logic recovery_fetch;
    logic instruction_complete;
    logic cache_lookup_hit;
    logic [23:0] cache_lookup_instruction;
    logic cache_lookup_instruction_valid;
    logic cache_fill;
    logic cache_fill_from_recovery;
    logic external_fill_selected;
    logic cache_fill_accepted;
    logic external_fill_conflict;
    logic integration_conflict;
    logic [23:0] next_instruction;
    logic next_instruction_valid;
    logic instruction_from_cache;
    logic instruction_from_external;
    logic [4:0] cache_region_count;
    logic class_valid_unused;
    logic action_valid_unused;
    logic unsupported_unused;
    logic boundary_valid_unused;
    logic accepted_unused;
    logic data_action_complete_unused;
    logic transaction_active_unused;
    logic busy_unused;
    logic invalid_opcode_unused;
    logic internal_conflict_unused;
    logic event_boundary_unused;
    logic pm_select_unused;
    logic pm_data_access_unused;
    logic pm_read_unused;
    logic pm_write_unused;
    logic [13:0] pm_address_unused;
    logic pm_address_valid_unused;
    logic [23:0] pm_write_data_unused;
    logic pm_write_data_valid_unused;
    logic [23:0] fetched_instruction_unused;
    logic fetched_instruction_valid_unused;
    logic cache_region_restarted_unused;
    logic cache_oldest_replaced_unused;
    logic [13:0] cache_region_start_unused;
    logic cache_region_start_valid_unused;
    logic [15:0] probe_dreg_data_unused;
    logic probe_dreg_valid_unused;
    logic [13:0] probe_i_data_unused;
    logic probe_i_valid_unused;
    logic [13:0] probe_m_data_unused;
    logic probe_m_valid_unused;
    logic [13:0] probe_l_data_unused;
    logic probe_l_valid_unused;
    logic [7:0] px_unused;
    logic px_valid_unused;
    logic [31:0] sr_unused;
    logic sr_valid_unused;
    logic [7:0] se_unused;
    logic se_valid_unused;
    logic [4:0] sb_unused;
    logic sb_valid_unused;
    logic [7:0] astat_unused;
    logic [7:0] astat_valid_mask_unused;
    logic [3:0] mstat_unused;
    logic alternate_bank_unused;
    logic unused_observation;
    logic past_valid;

    adsp2100_shifter_pm_cache_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .pm_read_data_i(pm_read_data),
        .pm_read_data_valid_i(pm_read_data_valid),
        .next_fetch_address_i(next_fetch_address),
        .next_fetch_address_valid_i(next_fetch_address_valid),
        .force_instruction_fetch_i(force_instruction_fetch),
        .external_fetch_fill_i(external_fetch_fill),
        .external_fetch_address_i(external_fetch_address),
        .external_fetch_address_valid_i(external_fetch_address_valid),
        .external_fetch_instruction_i(external_fetch_instruction),
        .external_fetch_instruction_valid_i(external_fetch_instruction_valid),
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
        .class_valid_o(class_valid_unused),
        .action_valid_o(action_valid_unused),
        .unsupported_subencoding_o(unsupported_unused),
        .boundary_valid_o(boundary_valid_unused),
        .accepted_o(accepted_unused),
        .data_action_complete_o(data_action_complete_unused),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active_unused),
        .busy_o(busy_unused),
        .invalid_opcode_o(invalid_opcode_unused),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict_unused),
        .cache_instruction_selected_o(cache_selected),
        .recovery_required_o(recovery_required),
        .recovery_fetch_o(recovery_fetch),
        .event_boundary_o(event_boundary_unused),
        .pm_select_o(pm_select_unused),
        .pm_data_access_o(pm_data_access_unused),
        .pm_read_o(pm_read_unused),
        .pm_write_o(pm_write_unused),
        .pm_address_o(pm_address_unused),
        .pm_address_valid_o(pm_address_valid_unused),
        .pm_write_data_o(pm_write_data_unused),
        .pm_write_data_valid_o(pm_write_data_valid_unused),
        .fetched_instruction_o(fetched_instruction_unused),
        .fetched_instruction_valid_o(fetched_instruction_valid_unused),
        .cache_lookup_address_hit_o(cache_lookup_hit),
        .cache_lookup_instruction_o(cache_lookup_instruction),
        .cache_lookup_instruction_valid_o(cache_lookup_instruction_valid),
        .cache_fill_o(cache_fill),
        .cache_fill_from_recovery_o(cache_fill_from_recovery),
        .external_fill_selected_o(external_fill_selected),
        .cache_fill_accepted_o(cache_fill_accepted),
        .cache_region_restarted_o(cache_region_restarted_unused),
        .cache_oldest_replaced_o(cache_oldest_replaced_unused),
        .external_fill_conflict_o(external_fill_conflict),
        .cache_region_start_o(cache_region_start_unused),
        .cache_region_start_valid_o(cache_region_start_valid_unused),
        .cache_region_count_o(cache_region_count),
        .next_instruction_o(next_instruction),
        .next_instruction_valid_o(next_instruction_valid),
        .instruction_from_cache_o(instruction_from_cache),
        .instruction_from_external_o(instruction_from_external),
        .probe_dreg_data_o(probe_dreg_data_unused),
        .probe_dreg_valid_o(probe_dreg_valid_unused),
        .probe_i_data_o(probe_i_data_unused),
        .probe_i_valid_o(probe_i_valid_unused),
        .probe_m_data_o(probe_m_data_unused),
        .probe_m_valid_o(probe_m_valid_unused),
        .probe_l_data_o(probe_l_data_unused),
        .probe_l_valid_o(probe_l_valid_unused),
        .px_o(px_unused),
        .px_valid_o(px_valid_unused),
        .sr_o(sr_unused),
        .sr_valid_o(sr_valid_unused),
        .se_o(se_unused),
        .se_valid_o(se_valid_unused),
        .sb_o(sb_unused),
        .sb_valid_o(sb_valid_unused),
        .astat_o(astat_unused),
        .astat_valid_mask_o(astat_valid_mask_unused),
        .mstat_o(mstat_unused),
        .alternate_bank_o(alternate_bank_unused)
    );

    initial past_valid = 1'b0;

    assign unused_observation = ^{
        class_valid_unused, action_valid_unused, unsupported_unused,
        boundary_valid_unused, accepted_unused, data_action_complete_unused,
        transaction_active_unused, busy_unused, invalid_opcode_unused,
        internal_conflict_unused, event_boundary_unused, pm_select_unused,
        pm_data_access_unused, pm_read_unused, pm_write_unused,
        pm_address_unused, pm_address_valid_unused, pm_write_data_unused,
        pm_write_data_valid_unused, fetched_instruction_unused,
        fetched_instruction_valid_unused, cache_region_restarted_unused,
        cache_oldest_replaced_unused, cache_region_start_unused,
        cache_region_start_valid_unused, probe_dreg_data_unused,
        probe_dreg_valid_unused, probe_i_data_unused, probe_i_valid_unused,
        probe_m_data_unused, probe_m_valid_unused, probe_l_data_unused,
        probe_l_valid_unused, px_unused, px_valid_unused, sr_unused,
        sr_valid_unused, se_unused, se_valid_unused, sb_unused,
        sb_valid_unused, astat_unused, astat_valid_mask_unused,
        mstat_unused, alternate_bank_unused
    };

    always_comb begin
        assert (cache_region_count <= 5'd16);
        assert (unused_observation == unused_observation);
        assert (!cache_lookup_instruction_valid || cache_lookup_hit);
        assert (cache_fill_from_recovery == recovery_fetch);
        assert (!(cache_fill_from_recovery && external_fill_selected));
        assert (cache_fill
            == (cache_fill_from_recovery || external_fill_selected));
        assert (next_instruction_valid
            == (instruction_from_cache || instruction_from_external));
        assert (!(instruction_from_cache && instruction_from_external));
        assert (integration_conflict
            == (dut.core_integration_conflict || external_fill_conflict));
        if (cache_selected) begin
            assert (cache_lookup_instruction_valid);
            assert (instruction_from_cache);
            assert (next_instruction_valid);
            assert (next_instruction == cache_lookup_instruction);
            assert (instruction_complete);
            assert (!recovery_required);
        end
        if (instruction_from_external) begin
            assert (recovery_fetch && next_instruction_valid);
            assert (next_instruction == pm_read_data);
        end
        if (external_fill_selected) begin
            assert (!recovery_fetch);
        end
        if (cache_fill_accepted) begin
            assert (cache_fill && dut.cache_fill_address_valid);
        end
        if (reset) begin
            assert (!cache_fill && !next_instruction_valid);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (
            past_valid && !reset && !$past(reset)
            && $past(recovery_required)
        ) begin
            assert (recovery_fetch);
            assert (cache_fill_from_recovery);
        end
        if (
            past_valid
            && !reset
            && $past(cache_fill)
            && $past(dut.cache_fill_address_valid)
            && $past(dut.cache_fill_instruction_valid)
            && next_fetch_address_valid
            && next_fetch_address == $past(dut.cache_fill_address)
        ) begin
            assert (cache_lookup_instruction_valid);
            assert (cache_lookup_instruction
                == $past(dut.cache_fill_instruction));
        end
        cover (past_valid && $past(recovery_required) && recovery_fetch);
        cover (cache_selected && instruction_from_cache);
    end
endmodule

`default_nettype wire
