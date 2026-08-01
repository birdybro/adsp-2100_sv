`default_nettype none

module adsp2100_shifter_pm_halt_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        halt_n,
    input logic        dmack,
    input logic        bus_relinquished,
    input logic        execute,
    input logic [23:0] opcode,
    input logic [23:0] pmd_read_data,
    input logic        pmd_read_data_valid,
    input logic [13:0] next_fetch_address,
    input logic        next_fetch_address_valid,
    input logic        force_instruction_fetch,
    input logic        external_fetch_fill,
    input logic [13:0] external_fetch_address,
    input logic        external_fetch_address_valid,
    input logic [23:0] external_fetch_instruction,
    input logic        external_fetch_instruction_valid
);
    logic [1:0] halt_mode;
    logic halt_recognized;
    logic halt_stop_event;
    logic force_fetch_issue;
    logic resume_event;
    logic release_blocked;
    logic issue_inhibit;
    logic phase_hold;
    logic effective_advance;
    logic halted;
    logic pm_data_cycle;
    logic late_force_request;
    logic execute_suppressed;
    logic owner_conflict;
    logic halt_attachment_conflict;
    logic integration_conflict;
    logic issue_boundary;
    logic accepted;
    logic data_action_complete;
    logic instruction_complete;
    logic transaction_active;
    logic busy;
    logic cache_instruction_selected;
    logic recovery_fetch;
    logic [23:0] next_instruction;
    logic next_instruction_valid;
    logic instruction_from_cache;
    logic instruction_from_external;
    logic cache_fill;
    logic cache_fill_from_recovery;
    logic cache_fill_accepted;
    logic [13:0] cache_region_start;
    logic cache_region_start_valid;
    logic [4:0] cache_region_count;
    logic pm_request_accepted;
    logic pm_completion_event;
    logic pm_read_sample_event;
    logic pm_bus_active;
    logic pm_address_oe;
    logic pm_control_oe;
    logic pm_data_oe;
    logic [13:0] pma;
    logic pma_valid;
    logic pmda;
    logic pmda_valid;
    logic pms_n;
    logic pmrd_n;
    logic pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
    logic [15:0] probe_dreg_data;
    logic probe_dreg_valid;
    logic [13:0] probe_i_data;
    logic probe_i_valid;
    logic [13:0] probe_m_data;
    logic probe_m_valid;
    logic [13:0] probe_l_data;
    logic probe_l_valid;
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
    logic unused_observation;

    assign unused_observation = ^{
        halt_mode, halt_recognized, resume_event, release_blocked,
        issue_inhibit, halted, pm_data_cycle, execute_suppressed,
        owner_conflict, integration_conflict, issue_boundary, accepted,
        transaction_active, busy, cache_instruction_selected,
        next_instruction, next_instruction_valid, instruction_from_external,
        cache_fill, cache_fill_from_recovery, cache_fill_accepted,
        cache_region_start, cache_region_start_valid, cache_region_count,
        pm_read_sample_event, pm_bus_active, pma, pma_valid, pmda, pmda_valid,
        pmd_write_data, pmd_write_data_valid, probe_dreg_data,
        probe_dreg_valid, probe_i_data, probe_i_valid, probe_m_data,
        probe_m_valid, probe_l_data, probe_l_valid, px, px_valid, sr,
        sr_valid, se, se_valid, sb, sb_valid, astat, astat_valid_mask,
        mstat, alternate_bank
    };

    adsp2100_shifter_pm_halt_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .halt_n_i(halt_n),
        .dmack_i(dmack),
        .bus_relinquished_i(bus_relinquished),
        .execute_i(execute),
        .opcode_i(opcode),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .next_fetch_address_i(next_fetch_address),
        .next_fetch_address_valid_i(next_fetch_address_valid),
        .force_instruction_fetch_i(force_instruction_fetch),
        .external_fetch_fill_i(external_fetch_fill),
        .external_fetch_address_i(external_fetch_address),
        .external_fetch_address_valid_i(external_fetch_address_valid),
        .external_fetch_instruction_i(external_fetch_instruction),
        .external_fetch_instruction_valid_i(
            external_fetch_instruction_valid
        ),
        .astat_setup_write_i(1'b0),
        .astat_setup_data_i(8'h00),
        .mstat_setup_write_i(1'b0),
        .mstat_setup_data_i(4'h0),
        .dreg_setup_write_i(1'b0),
        .dreg_setup_code_i(4'h0),
        .dreg_setup_data_i(16'h0000),
        .sb_setup_write_i(1'b0),
        .sb_setup_data_i(5'h00),
        .dag_setup_write_i(1'b0),
        .dag_setup_kind_i(2'b00),
        .dag_setup_address_i(3'b000),
        .dag_setup_data_i(14'h0000),
        .px_setup_write_i(1'b0),
        .px_setup_data_i(8'h00),
        .probe_dreg_code_i(4'h0),
        .probe_dag_address_i(3'b000),
        .halt_mode_o(halt_mode),
        .halt_recognized_o(halt_recognized),
        .halt_stop_event_o(halt_stop_event),
        .force_fetch_issue_o(force_fetch_issue),
        .resume_event_o(resume_event),
        .release_blocked_o(release_blocked),
        .instruction_issue_inhibit_o(issue_inhibit),
        .phase_hold_o(phase_hold),
        .effective_phase_advance_o(effective_advance),
        .halted_o(halted),
        .pm_data_cycle_o(pm_data_cycle),
        .late_force_request_o(late_force_request),
        .execute_suppressed_o(execute_suppressed),
        .owner_conflict_o(owner_conflict),
        .halt_attachment_conflict_o(halt_attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .issue_boundary_o(issue_boundary),
        .accepted_o(accepted),
        .data_action_complete_o(data_action_complete),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .busy_o(busy),
        .cache_instruction_selected_o(cache_instruction_selected),
        .recovery_fetch_o(recovery_fetch),
        .next_instruction_o(next_instruction),
        .next_instruction_valid_o(next_instruction_valid),
        .instruction_from_cache_o(instruction_from_cache),
        .instruction_from_external_o(instruction_from_external),
        .cache_fill_o(cache_fill),
        .cache_fill_from_recovery_o(cache_fill_from_recovery),
        .cache_fill_accepted_o(cache_fill_accepted),
        .cache_region_start_o(cache_region_start),
        .cache_region_start_valid_o(cache_region_start_valid),
        .cache_region_count_o(cache_region_count),
        .pm_request_accepted_o(pm_request_accepted),
        .pm_completion_event_o(pm_completion_event),
        .pm_read_sample_event_o(pm_read_sample_event),
        .pm_bus_active_o(pm_bus_active),
        .pm_address_output_enable_o(pm_address_oe),
        .pm_control_output_enable_o(pm_control_oe),
        .pm_data_output_enable_o(pm_data_oe),
        .pma_o(pma),
        .pma_valid_o(pma_valid),
        .pmda_o(pmda),
        .pmda_valid_o(pmda_valid),
        .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n),
        .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid),
        .probe_dreg_data_o(probe_dreg_data),
        .probe_dreg_valid_o(probe_dreg_valid),
        .probe_i_data_o(probe_i_data),
        .probe_i_valid_o(probe_i_valid),
        .probe_m_data_o(probe_m_data),
        .probe_m_valid_o(probe_m_valid),
        .probe_l_data_o(probe_l_data),
        .probe_l_valid_o(probe_l_valid),
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

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(instruction_from_cache && instruction_from_external));
        assert (halt_attachment_conflict == (
            force_fetch_issue
            && !(pm_request_accepted && recovery_fetch)
        ));
        if (force_fetch_issue) begin
            assert (pm_request_accepted && recovery_fetch);
        end
        if (late_force_request && data_action_complete) begin
            assert (!instruction_complete);
            assert (!instruction_from_cache);
        end
        if (halt_stop_event && recovery_fetch) begin
            assert (pm_completion_event && instruction_complete);
        end
        if (phase_hold) begin
            assert (!effective_advance);
            assert (!pm_request_accepted);
            assert (!data_action_complete);
            assert (!instruction_complete);
        end
        if (bus_relinquished || reset) begin
            assert (!pm_address_oe && !pm_control_oe && !pm_data_oe);
            assert (pms_n && pmrd_n && pmwr_n);
        end
    end
endmodule

`default_nettype wire
