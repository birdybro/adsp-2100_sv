`default_nettype none

module adsp2100_linear_bus_control_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        br_n,
    input logic [3:0]  irq_n,
    input logic        instruction_setup,
    input logic [13:0] instruction_setup_pc,
    input logic [23:0] instruction_setup_opcode,
    input logic [23:0] pmd_read_data,
    input logic        pmd_read_data_valid,
    input logic [5:0]  probe_code
);
    logic [2:0] bus_mode;
    logic request_recognized;
    logic grant_assert_event;
    logic release_recognized;
    logic grant_release_event;
    logic resume_event;
    logic instruction_issue_inhibit;
    logic normal_bus_relinquished;
    logic normal_bg_n;
    logic bg_n;
    logic bus_relinquished;
    logic issue_boundary;
    logic instruction_issue;
    logic retire_event;
    logic instruction_valid;
    logic transaction_pending;
    logic unsupported_instruction;
    logic reserved_subencoding;
    logic [13:0] pc;
    logic [23:0] opcode;
    logic pm_completion_event;
    logic pm_read_sample_event;
    logic pm_address_output_enable;
    logic pm_control_output_enable;
    logic pm_data_output_enable;
    logic past_valid;

    adsp2100_linear_bus_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .br_n_i(br_n),
        .irq_n_i(irq_n),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(instruction_setup_pc),
        .instruction_setup_opcode_i(instruction_setup_opcode),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .probe_code_i(probe_code),
        .bus_mode_o(bus_mode),
        .state_three_boundary_o(),
        .request_recognized_o(request_recognized),
        .grant_assert_event_o(grant_assert_event),
        .release_recognized_o(release_recognized),
        .grant_release_event_o(grant_release_event),
        .resume_event_o(resume_event),
        .request_withdrawn_o(),
        .release_cancelled_o(),
        .instruction_issue_inhibit_o(instruction_issue_inhibit),
        .normal_bus_relinquished_o(normal_bus_relinquished),
        .normal_bg_n_o(normal_bg_n),
        .reset_br_request_o(),
        .bg_n_o(bg_n),
        .bus_relinquished_o(bus_relinquished),
        .issue_boundary_o(issue_boundary),
        .instruction_setup_accepted_o(),
        .instruction_issue_o(instruction_issue),
        .retire_event_o(retire_event),
        .instruction_valid_o(instruction_valid),
        .transaction_pending_o(transaction_pending),
        .unsupported_instruction_o(unsupported_instruction),
        .reserved_subencoding_o(reserved_subencoding),
        .phase_conflict_o(),
        .integration_conflict_o(),
        .internal_conflict_o(),
        .provisional_source_extension_o(),
        .pc_o(pc),
        .opcode_o(opcode),
        .probe_data_o(),
        .astat_o(),
        .mstat_o(),
        .icntl_o(),
        .imask_o(),
        .cntr_o(),
        .cntr_valid_o(),
        .px_o(),
        .sstat_o(),
        .alternate_bank_o(),
        .count_stack_depth_o(),
        .count_stack_overflow_o(),
        .pm_request_accepted_o(),
        .pm_completion_event_o(pm_completion_event),
        .pm_read_sample_event_o(pm_read_sample_event),
        .pm_bus_active_o(),
        .pm_address_output_enable_o(pm_address_output_enable),
        .pm_control_output_enable_o(pm_control_output_enable),
        .pm_data_output_enable_o(pm_data_output_enable),
        .pma_o(),
        .pma_valid_o(),
        .pmda_o(),
        .pmda_valid_o(),
        .pms_n_o(),
        .pmrd_n_o(),
        .pmwr_n_o(),
        .pmd_write_data_o(),
        .pmd_write_data_valid_o()
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (bus_mode <= 3'd4);
        assert (bg_n == !bus_relinquished);
        assert (normal_bg_n == !normal_bus_relinquished);
        if (instruction_issue_inhibit) begin
            assert (!instruction_issue);
        end
        if (request_recognized && transaction_pending) begin
            assert (pm_address_output_enable);
            assert (pm_control_output_enable);
        end
        if (bus_relinquished) begin
            assert (!pm_address_output_enable);
            assert (!pm_control_output_enable);
            assert (!pm_data_output_enable);
        end
        if (normal_bus_relinquished) begin
            assert (!transaction_pending);
        end
        if (grant_assert_event || grant_release_event) begin
            assert (phase == 3'd2 && phase_advance);
        end
        if (resume_event) begin
            assert (phase == 3'd7 && phase_advance);
            assert (!instruction_issue_inhibit);
            assert (issue_boundary);
        end
        if (retire_event) begin
            assert (pm_completion_event && pm_read_sample_event);
        end
        cover (request_recognized && transaction_pending);
        cover (grant_assert_event);
        cover (release_recognized);
        cover (grant_release_event);
        cover (resume_event && instruction_issue);
        cover (reset && !br_n && !bg_n);
        cover (unsupported_instruction || reserved_subencoding);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(normal_bus_relinquished) && !reset) begin
            assert (pc == $past(pc));
            assert (opcode == $past(opcode));
            assert (instruction_valid == $past(instruction_valid));
            assert (!transaction_pending);
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
