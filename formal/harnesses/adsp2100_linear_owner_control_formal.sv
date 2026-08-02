`default_nettype none

module adsp2100_linear_owner_control_formal (
    input logic clk,
    input logic reset,
    input logic [2:0] phase,
    input logic phase_advance,
    input logic br_n,
    input logic [3:0] irq_n,
    input logic instruction_setup,
    input logic [13:0] setup_pc,
    input logic [23:0] setup_opcode,
    input logic type5_valid,
    input logic [13:0] type5_address,
    input logic type5_address_valid,
    input logic type5_data_access,
    input logic type5_write,
    input logic [23:0] type5_write_data,
    input logic type5_write_data_valid,
    input logic type13_valid,
    input logic [13:0] type13_address,
    input logic type13_address_valid,
    input logic type13_data_access,
    input logic type13_write,
    input logic [23:0] type13_write_data,
    input logic type13_write_data_valid,
    input logic [23:0] pmd_read_data,
    input logic pmd_read_data_valid,
    input logic [5:0] probe_code
);
    logic issue_boundary, setup_accepted, fetch_presented, fetch_accepted;
    logic fetch_retry, instruction_issue, retire_event, instruction_valid;
    logic transaction_pending, unsupported, reserved, phase_conflict;
    logic attachment_conflict, integration_conflict, internal_conflict;
    logic provisional_source_extension;
    logic [13:0] pc;
    logic [23:0] opcode;
    logic [15:0] probe_data;
    logic [7:0] astat;
    logic [3:0] mstat;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic [13:0] cntr;
    logic cntr_valid;
    logic [7:0] px, sstat;
    logic alternate_bank;
    logic [2:0] count_stack_depth;
    logic count_stack_overflow;
    logic [2:0] bus_mode;
    logic request_recognized, grant_assert, release_recognized;
    logic grant_release, resume, issue_inhibit, bg_n, bus_relinquished;
    logic request_blocked, request_conflict, request_out_of_phase;
    logic [2:0] request_accepted, completion;
    logic [1:0] owner;
    logic pm_bus_active, address_oe, control_oe, data_oe;
    logic [13:0] pma;
    logic pma_valid, pmda, pmda_valid, pms_n, pmrd_n, pmwr_n;
    logic [23:0] pmd_write_data;
    logic pmd_write_data_valid;
    logic past_valid;
    logic unused_observation;

    assign unused_observation = ^{
        issue_boundary, setup_accepted, instruction_issue,
        instruction_valid, unsupported, reserved, phase_conflict,
        attachment_conflict, integration_conflict, internal_conflict,
        provisional_source_extension, pc, opcode, probe_data, astat,
        mstat, icntl, imask, cntr, cntr_valid, px, sstat,
        alternate_bank, count_stack_depth, count_stack_overflow,
        bus_mode, request_recognized, grant_assert, release_recognized,
        grant_release, resume, request_blocked, request_out_of_phase,
        pm_bus_active, pma, pma_valid, pmd_write_data,
        pmd_write_data_valid
    };

    adsp2100_linear_owner_control_slice dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(phase_advance), .br_n_i(br_n),
        .irq_n_i(irq_n),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(setup_pc),
        .instruction_setup_opcode_i(setup_opcode),
        .type5_valid_i(type5_valid), .type5_address_i(type5_address),
        .type5_address_valid_i(type5_address_valid),
        .type5_data_access_i(type5_data_access),
        .type5_write_i(type5_write),
        .type5_write_data_i(type5_write_data),
        .type5_write_data_valid_i(type5_write_data_valid),
        .type13_valid_i(type13_valid), .type13_address_i(type13_address),
        .type13_address_valid_i(type13_address_valid),
        .type13_data_access_i(type13_data_access),
        .type13_write_i(type13_write),
        .type13_write_data_i(type13_write_data),
        .type13_write_data_valid_i(type13_write_data_valid),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .probe_code_i(probe_code),
        .issue_boundary_o(issue_boundary),
        .instruction_setup_accepted_o(setup_accepted),
        .fetch_request_presented_o(fetch_presented),
        .fetch_request_accepted_o(fetch_accepted),
        .fetch_retry_pending_o(fetch_retry),
        .instruction_issue_o(instruction_issue),
        .retire_event_o(retire_event),
        .instruction_valid_o(instruction_valid),
        .transaction_pending_o(transaction_pending),
        .unsupported_instruction_o(unsupported),
        .reserved_subencoding_o(reserved),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .provisional_source_extension_o(provisional_source_extension),
        .pc_o(pc), .opcode_o(opcode), .probe_data_o(probe_data),
        .astat_o(astat), .mstat_o(mstat), .icntl_o(icntl),
        .imask_o(imask), .cntr_o(cntr), .cntr_valid_o(cntr_valid),
        .px_o(px), .sstat_o(sstat), .alternate_bank_o(alternate_bank),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .bus_mode_o(bus_mode),
        .bus_request_recognized_o(request_recognized),
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
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );

    initial begin
        past_valid = 1'b0;
        assume (reset);
    end

    always_comb begin
        assert (unused_observation == unused_observation);
        assert ($onehot0(request_accepted));
        assert ($onehot0(completion));
        assert (fetch_accepted == request_accepted[0]);
        assert (!fetch_accepted || fetch_presented);
        assert (!fetch_retry
            || (fetch_presented && !fetch_accepted
                && instruction_valid && !transaction_pending));
        assert (!(completion[0] && !retire_event));
        assert (!(~pmrd_n && ~pmwr_n));
        if (request_conflict) assert (request_accepted == 3'b000);
        if (issue_inhibit) assert (!fetch_presented);
        if (bus_relinquished) begin
            assert (!address_oe && !control_oe && !data_oe);
            assert (pms_n && pmrd_n && pmwr_n);
        end
        if (reset && !br_n) assert (!bg_n && bus_relinquished);
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && !$past(reset) && !reset
            && $past(fetch_accepted) && !bus_relinquished) begin
            assert (owner == 2'd1);
            assert (pmda_valid && !pmda);
        end
        cover (fetch_retry);
        cover (completion[0] && retire_event);
        cover (request_accepted[1]);
        cover (request_accepted[2]);
        cover (request_recognized && transaction_pending);
        cover (resume && fetch_accepted);
    end
endmodule

`default_nettype wire
