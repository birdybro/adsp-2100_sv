`default_nettype none

module adsp2100_shifter_pm_native_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
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
    input logic        external_fetch_instruction_valid,
    input logic        astat_setup_write,
    input logic [7:0]  astat_setup_data,
    input logic        mstat_setup_write,
    input logic [3:0]  mstat_setup_data,
    input logic        dreg_setup_write,
    input logic [3:0]  dreg_setup_code,
    input logic [15:0] dreg_setup_data,
    input logic        sb_setup_write,
    input logic [4:0]  sb_setup_data,
    input logic        dag_setup_write,
    input logic [1:0]  dag_setup_kind,
    input logic [2:0]  dag_setup_address,
    input logic [13:0] dag_setup_data,
    input logic        px_setup_write,
    input logic [7:0]  px_setup_data,
    input logic [3:0]  probe_dreg_code,
    input logic [2:0]  probe_dag_address
);
    import adsp2100_pkg::*;

    logic issue_boundary;
    logic phase_conflict;
    logic attachment_conflict;
    logic integration_conflict;
    logic class_valid;
    logic action_valid;
    logic unsupported_subencoding;
    logic accepted;
    logic data_action_complete;
    logic instruction_complete;
    logic transaction_active;
    logic busy;
    logic cache_instruction_selected;
    logic recovery_required;
    logic recovery_fetch;
    logic event_boundary;
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
    logic controls_present;
    logic unused_observation;

    assign controls_present = (
        execute || external_fetch_fill || astat_setup_write
        || mstat_setup_write || dreg_setup_write || sb_setup_write
        || dag_setup_write || px_setup_write
    );
    assign unused_observation = ^{
        class_valid, action_valid, unsupported_subencoding, busy,
        cache_instruction_selected, recovery_required, next_instruction,
        next_instruction_valid, instruction_from_cache,
        instruction_from_external, cache_fill, cache_fill_from_recovery,
        cache_fill_accepted, cache_region_start,
        cache_region_start_valid, cache_region_count, pm_bus_active,
        pma, pma_valid, pmda, pmda_valid, pmd_write_data,
        pmd_write_data_valid, probe_dreg_data, probe_dreg_valid,
        probe_i_data, probe_i_valid, probe_m_data, probe_m_valid,
        probe_l_data, probe_l_valid, px, px_valid, sr, sr_valid,
        se, se_valid, sb, sb_valid, astat, astat_valid_mask, mstat,
        alternate_bank
    };

    adsp2100_shifter_pm_native_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
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
        .px_setup_write_i(px_setup_write),
        .px_setup_data_i(px_setup_data),
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .issue_boundary_o(issue_boundary),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .accepted_o(accepted),
        .data_action_complete_o(data_action_complete),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .busy_o(busy),
        .cache_instruction_selected_o(cache_instruction_selected),
        .recovery_required_o(recovery_required),
        .recovery_fetch_o(recovery_fetch),
        .event_boundary_o(event_boundary),
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
        assert (accepted
            == (pm_request_accepted && dut.core_pm_data_access));
        assert (data_action_complete
            == (pm_completion_event && dut.core_pm_data_access));
        assert (event_boundary == instruction_complete);
        assert (!(~pmrd_n && ~pmwr_n));
        assert (pm_address_oe == pm_control_oe);
        assert (pms_n == !pm_control_oe);
        if (accepted) begin
            assert (issue_boundary && pm_request_accepted);
        end
        if (data_action_complete) begin
            assert (phase == PHASE_STATE_7 && phase_advance);
            assert (transaction_active);
        end
        if (recovery_fetch) begin
            assert (dut.core_pm_select && !dut.core_pm_data_access);
        end
        if (bus_relinquished || reset) begin
            assert (!pm_address_oe && !pm_control_oe && !pm_data_oe);
        end
    end

    always_ff @(posedge clk) begin
        cover (accepted && pm_request_accepted);
        cover (data_action_complete && pm_read_sample_event);
        cover (recovery_fetch && pm_request_accepted);
        cover (recovery_fetch && instruction_complete);
    end
endmodule

`default_nettype wire
