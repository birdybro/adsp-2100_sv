`default_nettype none

module adsp2100_linear_core_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        bus_relinquished,
    input logic        instruction_setup,
    input logic [13:0] instruction_setup_pc,
    input logic [23:0] instruction_setup_opcode,
    input logic [23:0] pmd_read_data,
    input logic        pmd_read_data_valid,
    input logic [5:0]  probe_code
);
    logic issue_boundary;
    logic instruction_setup_accepted;
    logic instruction_issue;
    logic retire_event;
    logic instruction_valid;
    logic transaction_pending;
    logic unsupported_instruction;
    logic reserved_subencoding;
    logic phase_conflict;
    logic integration_conflict;
    logic internal_conflict;
    logic [13:0] pc;
    logic [23:0] opcode;
    logic [3:0] mstat;
    logic [3:0] imask;
    logic [7:0] sstat;
    logic pm_request_accepted;
    logic pm_completion_event;
    logic pm_read_sample_event;
    logic pm_bus_active;
    logic pm_address_output_enable;
    logic pm_control_output_enable;
    logic pm_data_output_enable;
    logic [13:0] pma;
    logic pma_valid;
    logic pmda;
    logic pmda_valid;
    logic pms_n;
    logic pmrd_n;
    logic pmwr_n;
    logic pmd_write_data_valid;
    logic past_valid;

    adsp2100_linear_core_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .phase_i(phase),
        .phase_advance_i(phase_advance),
        .bus_relinquished_i(bus_relinquished),
        .instruction_setup_i(instruction_setup),
        .instruction_setup_pc_i(instruction_setup_pc),
        .instruction_setup_opcode_i(instruction_setup_opcode),
        .pmd_read_data_i(pmd_read_data),
        .pmd_read_data_valid_i(pmd_read_data_valid),
        .probe_code_i(probe_code),
        .issue_boundary_o(issue_boundary),
        .instruction_setup_accepted_o(instruction_setup_accepted),
        .instruction_issue_o(instruction_issue),
        .retire_event_o(retire_event),
        .instruction_valid_o(instruction_valid),
        .transaction_pending_o(transaction_pending),
        .unsupported_instruction_o(unsupported_instruction),
        .reserved_subencoding_o(reserved_subencoding),
        .phase_conflict_o(phase_conflict),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .pc_o(pc),
        .opcode_o(opcode),
        .probe_data_o(),
        .astat_o(),
        .mstat_o(mstat),
        .icntl_o(),
        .imask_o(imask),
        .cntr_o(),
        .cntr_valid_o(),
        .px_o(),
        .sstat_o(sstat),
        .alternate_bank_o(),
        .count_stack_depth_o(),
        .count_stack_overflow_o(),
        .pm_request_accepted_o(pm_request_accepted),
        .pm_completion_event_o(pm_completion_event),
        .pm_read_sample_event_o(pm_read_sample_event),
        .pm_bus_active_o(pm_bus_active),
        .pm_address_output_enable_o(pm_address_output_enable),
        .pm_control_output_enable_o(pm_control_output_enable),
        .pm_data_output_enable_o(pm_data_output_enable),
        .pma_o(pma),
        .pma_valid_o(pma_valid),
        .pmda_o(pmda),
        .pmda_valid_o(pmda_valid),
        .pms_n_o(pms_n),
        .pmrd_n_o(pmrd_n),
        .pmwr_n_o(pmwr_n),
        .pmd_write_data_o(),
        .pmd_write_data_valid_o(pmd_write_data_valid)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (instruction_issue == pm_request_accepted);
        assert (!internal_conflict);
        assert (!pm_data_output_enable);
        assert (!pmd_write_data_valid);
        assert (!(~pmrd_n && ~pmwr_n));
        assert (pms_n == !pm_control_output_enable);
        assert (pm_address_output_enable == pm_control_output_enable);
        assert (!pmda || !pmda_valid);
        if (instruction_issue) begin
            assert (issue_boundary);
            assert (instruction_valid);
            assert (!transaction_pending);
            assert (!unsupported_instruction && !reserved_subencoding);
        end
        if (retire_event) begin
            assert (phase == 3'd6 && phase_advance);
            assert (transaction_pending);
            assert (pm_completion_event && pm_read_sample_event);
        end
        if (pma_valid && transaction_pending) begin
            assert (pma == pc + 14'h0001);
        end
        if (unsupported_instruction || reserved_subencoding) begin
            assert (!instruction_issue);
        end
        if (bus_relinquished || reset) begin
            assert (!pm_address_output_enable);
            assert (!pm_control_output_enable);
            assert (!pm_data_output_enable);
        end
        cover (instruction_issue);
        cover (retire_event && pmd_read_data_valid);
        cover (reserved_subencoding);
        cover (unsupported_instruction);
        cover (phase_conflict);
        cover (integration_conflict);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (pc == 14'h0004);
            assert (!instruction_valid);
            assert (!transaction_pending);
            assert (mstat == 4'h0);
            assert (imask == 4'h0);
            assert (sstat == 8'h55);
            assert (!pm_bus_active);
        end else if (!reset) begin
            if ($past(instruction_setup_accepted)) begin
                assert (pc == $past(instruction_setup_pc));
                assert (opcode == $past(instruction_setup_opcode));
                assert (instruction_valid);
                assert (!transaction_pending);
            end
            if ($past(instruction_issue)) begin
                assert (transaction_pending);
            end
            if ($past(retire_event)) begin
                assert (pc == $past(pc) + 14'h0001);
                assert (!transaction_pending);
                assert (instruction_valid == $past(pmd_read_data_valid));
                if ($past(pmd_read_data_valid)) begin
                    assert (opcode == $past(pmd_read_data));
                end
            end else if (
                $past(transaction_pending)
                && !$past(instruction_setup_accepted)
            ) begin
                assert (pc == $past(pc));
                assert (opcode == $past(opcode));
                assert (instruction_valid == $past(instruction_valid));
                assert (transaction_pending);
            end
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
