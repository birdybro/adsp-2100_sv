`default_nettype none

module adsp2100_shifter_pm_owner_control_formal (
    input logic clk,
    input logic reset,
    input logic [2:0] phase,
    input logic phase_advance,
    input logic br_n,
    input logic fetch_valid,
    input logic [13:0] fetch_address,
    input logic fetch_address_valid,
    input logic type5_valid,
    input logic [13:0] type5_address,
    input logic type5_address_valid,
    input logic type5_data_access,
    input logic type5_write,
    input logic [23:0] type5_write_data,
    input logic type5_write_data_valid,
    input logic execute,
    input logic [23:0] opcode,
    input logic [23:0] pmd_read_data,
    input logic pmd_read_data_valid,
    input logic [13:0] next_fetch_address,
    input logic next_fetch_address_valid,
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
    input logic [7:0] px_setup_data,
    input logic [3:0] probe_dreg_code,
    input logic [2:0] probe_dag_address
);
    logic issue_boundary, phase_conflict, attachment_conflict;
    logic integration_conflict, class_valid, action_valid, unsupported;
    logic accepted, data_complete, instruction_complete, transaction_active;
    logic busy, recovery_fetch, fetch_cache_fill, cache_fill_accepted;
    logic [13:0] cache_region_start;
    logic cache_region_start_valid;
    logic [4:0] cache_region_count;
    logic type13_presented, type13_accepted, type13_retry;
    logic [23:0] next_instruction;
    logic next_instruction_valid, from_cache, from_external;
    logic [2:0] bus_mode;
    logic bus_request_recognized, grant_assert, release_recognized;
    logic grant_release, resume, issue_inhibit, bg_n, bus_relinquished;
    logic request_blocked, request_conflict, request_out_of_phase;
    logic [2:0] request_accepted, completion;
    logic [1:0] owner;
    logic pm_bus_active, address_oe, control_oe, data_oe;
    logic [13:0] pma;
    logic pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
    logic [15:0] probe_dreg_data;
    logic probe_dreg_valid;
    logic [13:0] probe_i_data, probe_m_data, probe_l_data;
    logic probe_i_valid, probe_m_valid, probe_l_valid;
    logic [7:0] px;
    logic px_valid;
    logic [31:0] sr;
    logic sr_valid;
    logic [7:0] se;
    logic se_valid;
    logic [4:0] sb;
    logic sb_valid;
    logic [7:0] astat, astat_valid_mask;
    logic [3:0] mstat;
    logic alternate_bank;
    logic past_valid;
    logic unused_observation;

    assign unused_observation = ^{
        issue_boundary, phase_conflict, attachment_conflict,
        integration_conflict, class_valid, action_valid, unsupported,
        accepted, busy, cache_region_start, cache_region_start_valid,
        cache_region_count, next_instruction, next_instruction_valid,
        from_cache, from_external, bus_mode, bus_request_recognized,
        grant_assert, release_recognized, grant_release, resume,
        request_blocked, request_out_of_phase, pm_bus_active, pma,
        pmd_write_data, pmd_write_data_valid, probe_dreg_data,
        probe_dreg_valid, probe_i_data, probe_i_valid, probe_m_data,
        probe_m_valid, probe_l_data, probe_l_valid, px, px_valid, sr,
        sr_valid, se, se_valid, sb, sb_valid, astat, astat_valid_mask,
        mstat, alternate_bank
    };

    adsp2100_shifter_pm_owner_control_slice dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(phase_advance), .br_n_i(br_n),
        .fetch_valid_i(fetch_valid), .fetch_address_i(fetch_address),
        .fetch_address_valid_i(fetch_address_valid),
        .type5_valid_i(type5_valid), .type5_address_i(type5_address),
        .type5_address_valid_i(type5_address_valid),
        .type5_data_access_i(type5_data_access),
        .type5_write_i(type5_write),
        .type5_write_data_i(type5_write_data),
        .type5_write_data_valid_i(type5_write_data_valid),
        .execute_i(execute), .opcode_i(opcode),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .next_fetch_address_i(next_fetch_address),
        .next_fetch_address_valid_i(next_fetch_address_valid),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .sb_setup_write_i(sb_setup), .sb_setup_data_i(sb_setup_data),
        .dag_setup_write_i(dag_setup),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .px_setup_write_i(px_setup), .px_setup_data_i(px_setup_data),
        .probe_dreg_code_i(probe_dreg_code),
        .probe_dag_address_i(probe_dag_address),
        .issue_boundary_o(issue_boundary),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .class_valid_o(class_valid), .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported), .accepted_o(accepted),
        .data_action_complete_o(data_complete),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active), .busy_o(busy),
        .recovery_fetch_o(recovery_fetch),
        .fetch_cache_fill_o(fetch_cache_fill),
        .cache_fill_accepted_o(cache_fill_accepted),
        .cache_region_start_o(cache_region_start),
        .cache_region_start_valid_o(cache_region_start_valid),
        .cache_region_count_o(cache_region_count),
        .type13_request_presented_o(type13_presented),
        .type13_request_accepted_o(type13_accepted),
        .type13_retry_pending_o(type13_retry),
        .next_instruction_o(next_instruction),
        .next_instruction_valid_o(next_instruction_valid),
        .instruction_from_cache_o(from_cache),
        .instruction_from_external_o(from_external),
        .bus_mode_o(bus_mode),
        .bus_request_recognized_o(bus_request_recognized),
        .grant_assert_event_o(grant_assert),
        .release_recognized_o(release_recognized),
        .grant_release_event_o(grant_release), .resume_event_o(resume),
        .issue_inhibit_o(issue_inhibit), .bg_n_o(bg_n),
        .bus_relinquished_o(bus_relinquished),
        .request_blocked_o(request_blocked),
        .request_conflict_o(request_conflict),
        .request_out_of_phase_o(request_out_of_phase),
        .request_accepted_o(request_accepted),
        .completion_event_o(completion), .owner_o(owner),
        .pm_bus_active_o(pm_bus_active),
        .pm_address_output_enable_o(address_oe),
        .pm_control_output_enable_o(control_oe),
        .pm_data_output_enable_o(data_oe),
        .pma_o(pma), .pma_valid_o(pma_valid), .pmda_o(pmda),
        .pmda_valid_o(pmda_valid), .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n), .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(pmd_write_data),
        .pmd_write_data_valid_o(pmd_write_data_valid),
        .probe_dreg_data_o(probe_dreg_data),
        .probe_dreg_valid_o(probe_dreg_valid),
        .probe_i_data_o(probe_i_data), .probe_i_valid_o(probe_i_valid),
        .probe_m_data_o(probe_m_data), .probe_m_valid_o(probe_m_valid),
        .probe_l_data_o(probe_l_data), .probe_l_valid_o(probe_l_valid),
        .px_o(px), .px_valid_o(px_valid), .sr_o(sr),
        .sr_valid_o(sr_valid), .se_o(se), .se_valid_o(se_valid),
        .sb_o(sb), .sb_valid_o(sb_valid), .astat_o(astat),
        .astat_valid_mask_o(astat_valid_mask), .mstat_o(mstat),
        .alternate_bank_o(alternate_bank)
    );

    initial begin
        past_valid = 1'b0;
        assume (reset);
    end

    always_comb begin
        assert (unused_observation == unused_observation);
        assert ($onehot0(request_accepted));
        assert ($onehot0(completion));
        assert (type13_accepted == request_accepted[2]);
        assert (!type13_accepted || type13_presented);
        assert (!type13_retry || (transaction_active && !type13_accepted));
        assert (!(completion[2]
            && !(data_complete || instruction_complete)));
        assert (!(~pmrd_n && ~pmwr_n));
        if (request_conflict) assert (request_accepted == 3'b000);
        if (bus_relinquished) begin
            assert (!address_oe && !control_oe && !data_oe);
            assert (pms_n && pmrd_n && pmwr_n);
        end
        if (fetch_cache_fill && pma_valid && pmd_read_data_valid) begin
            assert (cache_fill_accepted);
        end
        if (issue_inhibit) assert (!type13_presented);
        if (reset && !br_n) assert (!bg_n && bus_relinquished);
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && !$past(reset) && !reset
            && $past(type13_accepted && recovery_fetch)
            && !bus_relinquished) begin
            assert (owner == 2'd3);
            assert (pmda_valid && !pmda);
        end
        cover (type13_retry);
        cover (fetch_cache_fill && cache_fill_accepted);
        cover (completion[1]);
        cover (completion[2] && data_complete);
        cover (completion[2] && instruction_complete && recovery_fetch);
        cover (bus_request_recognized && transaction_active);
        cover (resume && type13_accepted);
    end
endmodule

`default_nettype wire
