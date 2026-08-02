`default_nettype none

module adsp2100_program_clients_owner_control_formal (
    input logic clk,
    input logic reset,
    input logic [2:0] phase,
    input logic phase_advance,
    input logic br_n,
    input logic halt_n,
    input logic dmack,
    input logic instruction_setup,
    input logic [13:0] instruction_setup_pc,
    input logic [23:0] instruction_setup_opcode,
    input logic automatic_pm_flow,
    input logic type5_execute,
    input logic [23:0] type5_opcode,
    input logic [13:0] type5_next_address,
    input logic type5_next_valid,
    input logic type13_execute,
    input logic [23:0] type13_opcode,
    input logic [13:0] type13_next_address,
    input logic type13_next_valid,
    input logic [23:0] pmd_read_data,
    input logic pmd_read_data_valid
);
    logic issue_boundary, client_conflict, integration_conflict;
    logic automatic_pm_issue, automatic_pm_retire, automatic_pm_blocked;
    logic [1:0] halt_mode;
    logic halt_recognized, halt_stop, halt_force_fetch, halt_resume;
    logic halt_release_blocked, halt_phase_hold, effective_advance, halted;
    logic halt_br_conflict, halt_attachment_conflict;
    logic linear_presented, linear_issue, linear_retire;
    logic linear_instruction_valid;
    logic type5_presented, type5_accepted, type5_retry;
    logic type5_data_complete, type5_instruction_complete;
    logic type13_presented, type13_accepted, type13_retry;
    logic type13_data_complete, type13_instruction_complete;
    logic cache_fill, cache_fill_accepted;
    logic [2:0] bus_mode;
    logic issue_inhibit, bg_n, bus_relinquished;
    logic request_blocked, request_conflict, request_out_of_phase;
    logic [2:0] request_accepted, completion;
    logic [1:0] owner;
    logic pm_bus_active, address_oe, control_oe, data_oe;
    logic [13:0] pma;
    logic pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n;
    logic pmd_write_data_valid;
    logic [15:0] type5_probe_data, type13_probe_data;
    logic type5_probe_valid, type13_probe_valid;
    logic [7:0] type5_px, type13_px;
    logic type5_px_valid, type13_px_valid;
    logic unused_observation;

    assign unused_observation = ^{
        issue_boundary, integration_conflict, linear_issue, linear_retire,
        automatic_pm_issue, automatic_pm_retire, automatic_pm_blocked,
        halt_mode, halt_recognized, halt_stop, halt_force_fetch,
        halt_resume, halt_release_blocked, halt_phase_hold,
        effective_advance, halted, halt_br_conflict,
        halt_attachment_conflict,
        linear_instruction_valid, type5_retry, type5_data_complete,
        type5_instruction_complete, type13_retry, type13_data_complete,
        type13_instruction_complete, bus_mode, bg_n, request_blocked,
        request_out_of_phase, owner, pm_bus_active, pma, pma_valid,
        pmda_valid, pmd_write_data_valid
    };

    /* verilator lint_off PINCONNECTEMPTY */
    adsp2100_program_clients_owner_control_slice dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(phase_advance), .br_n_i(br_n),
        .halt_n_i(halt_n), .dmack_i(dmack),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(instruction_setup_pc),
        .instruction_setup_opcode_i(instruction_setup_opcode),
        .irq_n_i(4'hf),
        .automatic_pm_flow_i(automatic_pm_flow),
        .type5_execute_i(type5_execute), .type5_opcode_i(type5_opcode),
        .type5_next_fetch_address_i(type5_next_address),
        .type5_next_fetch_address_valid_i(type5_next_valid),
        .type13_execute_i(type13_execute), .type13_opcode_i(type13_opcode),
        .type13_next_fetch_address_i(type13_next_address),
        .type13_next_fetch_address_valid_i(type13_next_valid),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .astat_setup_write_i(1'b0), .astat_setup_data_i(8'h00),
        .mstat_setup_write_i(1'b0), .mstat_setup_data_i(4'h0),
        .dreg_setup_write_i(1'b0), .dreg_setup_code_i(4'h0),
        .dreg_setup_data_i(16'h0000),
        .af_setup_write_i(1'b0), .af_setup_data_i(16'h0000),
        .mf_setup_write_i(1'b0), .mf_setup_data_i(16'h0000),
        .sb_setup_write_i(1'b0), .sb_setup_data_i(5'h00),
        .dag_setup_write_i(1'b0), .dag_setup_kind_i(2'b00),
        .dag_setup_address_i(3'b000), .dag_setup_data_i(14'h0000),
        .px_setup_write_i(1'b0), .px_setup_data_i(8'h00),
        .linear_probe_code_i(6'h00), .pm_probe_dreg_code_i(4'h0),
        .pm_probe_dag_address_i(3'h0),
        .issue_boundary_o(issue_boundary),
        .client_execute_conflict_o(client_conflict),
        .integration_conflict_o(integration_conflict),
        .automatic_pm_instruction_issue_o(automatic_pm_issue),
        .automatic_pm_instruction_retire_o(automatic_pm_retire),
        .automatic_pm_flow_blocked_o(automatic_pm_blocked),
        .halt_mode_o(halt_mode),
        .halt_recognized_o(halt_recognized),
        .halt_stop_event_o(halt_stop),
        .halt_force_fetch_issue_o(halt_force_fetch),
        .halt_resume_event_o(halt_resume),
        .halt_release_blocked_o(halt_release_blocked),
        .halt_phase_hold_o(halt_phase_hold),
        .effective_phase_advance_o(effective_advance),
        .halted_o(halted), .halt_br_conflict_o(halt_br_conflict),
        .halt_attachment_conflict_o(halt_attachment_conflict),
        .linear_fetch_request_presented_o(linear_presented),
        .linear_instruction_issue_o(linear_issue),
        .linear_retire_event_o(linear_retire),
        .linear_instruction_valid_o(linear_instruction_valid),
        .linear_pc_o(), .linear_opcode_o(), .linear_probe_data_o(),
        .type5_request_presented_o(type5_presented),
        .type5_request_accepted_o(type5_accepted),
        .type5_retry_pending_o(type5_retry),
        .type5_data_action_complete_o(type5_data_complete),
        .type5_instruction_complete_o(type5_instruction_complete),
        .type5_next_instruction_o(), .type5_next_instruction_valid_o(),
        .type5_probe_dreg_data_o(type5_probe_data),
        .type5_probe_dreg_valid_o(type5_probe_valid),
        .type5_px_o(type5_px), .type5_px_valid_o(type5_px_valid),
        .type13_request_presented_o(type13_presented),
        .type13_request_accepted_o(type13_accepted),
        .type13_retry_pending_o(type13_retry),
        .type13_data_action_complete_o(type13_data_complete),
        .type13_instruction_complete_o(type13_instruction_complete),
        .type13_next_instruction_o(), .type13_next_instruction_valid_o(),
        .type13_probe_dreg_data_o(type13_probe_data),
        .type13_probe_dreg_valid_o(type13_probe_valid),
        .type13_px_o(type13_px), .type13_px_valid_o(type13_px_valid),
        .cache_fill_o(cache_fill),
        .cache_fill_accepted_o(cache_fill_accepted),
        .cache_region_start_o(), .cache_region_start_valid_o(),
        .cache_region_count_o(),
        .bus_mode_o(bus_mode), .issue_inhibit_o(issue_inhibit),
        .bg_n_o(bg_n), .bus_relinquished_o(bus_relinquished),
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
        .pmd_write_data_o(),
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );
    /* verilator lint_on PINCONNECTEMPTY */

    initial assume (reset);

    always_comb begin
        assert (unused_observation == unused_observation);
        assert ($onehot0(request_accepted));
        assert ($onehot0(completion));
        assert (type5_accepted == request_accepted[1]);
        assert (type13_accepted == request_accepted[2]);
        assert (type5_probe_valid == type13_probe_valid);
        assert (type5_probe_data == type13_probe_data);
        assert (type5_px_valid == type13_px_valid);
        assert (type5_px == type13_px);
        assert (!type5_accepted || type5_presented);
        assert (!type13_accepted || type13_presented);
        assert (!client_conflict || (!type5_accepted && !type13_accepted));
        assert (!automatic_pm_issue || !linear_presented);
        assert (!automatic_pm_issue || $onehot(request_accepted[2:1]));
        assert (!automatic_pm_retire || linear_retire);
        assert (!automatic_pm_blocked
            || (!linear_presented && !type5_presented && !type13_presented));
        assert (!halt_force_fetch || halt_attachment_conflict
            || $onehot(request_accepted[2:1]));
        assert (!halted || halt_resume || halt_phase_hold);
        assert (!halt_phase_hold || !effective_advance);
        assert (!halt_br_conflict || integration_conflict);
        assert (!halt_attachment_conflict || integration_conflict);
        assert (!(~pmrd_n && ~pmwr_n));
        if (request_conflict) assert (request_accepted == 3'b000);
        if (cache_fill) begin
            assert ($onehot(completion));
            assert (!pmda);
        end
        if (cache_fill && pma_valid && pmd_read_data_valid) begin
            assert (cache_fill_accepted);
        end
        if (issue_inhibit) begin
            assert (!linear_presented);
            assert (!type5_presented);
            assert (!type13_presented);
        end
        if (bus_relinquished) begin
            assert (!address_oe && !control_oe && !data_oe);
            assert (pms_n && pmrd_n && pmwr_n);
        end
    end

    always_ff @(posedge clk) begin
        cover (linear_presented && type5_presented && request_conflict);
        cover (type5_accepted);
        cover (type13_accepted);
        cover (completion[0] && cache_fill);
        cover (completion[1] && cache_fill);
        cover (completion[2] && cache_fill);
    end
endmodule

`default_nettype wire
