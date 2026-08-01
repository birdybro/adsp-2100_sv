`default_nettype none

// Bounded composition of the shared PM owner with original normal BR/BG.
//
// A recognized request inhibits only future state-8 descriptor capture. The
// active PM transaction continues through state 7. The native RESET-time
// asynchronous BR/BG relationship remains isolated in the pin-only wrapper.
module adsp2100_program_owner_bus_control (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        br_n_i,

    input  logic        fetch_valid_i,
    input  logic [13:0] fetch_address_i,
    input  logic        fetch_address_valid_i,
    input  logic        type5_valid_i,
    input  logic [13:0] type5_address_i,
    input  logic        type5_address_valid_i,
    input  logic        type5_data_access_i,
    input  logic        type5_write_i,
    input  logic [23:0] type5_write_data_i,
    input  logic        type5_write_data_valid_i,
    input  logic        type13_valid_i,
    input  logic [13:0] type13_address_i,
    input  logic        type13_address_valid_i,
    input  logic        type13_data_access_i,
    input  logic        type13_write_i,
    input  logic [23:0] type13_write_data_i,
    input  logic        type13_write_data_valid_i,
    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,

    output logic [2:0]  bus_mode_o,
    output logic        state_three_boundary_o,
    output logic        bus_request_recognized_o,
    output logic        grant_assert_event_o,
    output logic        release_recognized_o,
    output logic        grant_release_event_o,
    output logic        resume_event_o,
    output logic        request_withdrawn_o,
    output logic        release_cancelled_o,
    output logic        issue_inhibit_o,
    output logic        normal_bus_relinquished_o,
    output logic        normal_bg_n_o,
    output logic        reset_br_request_o,
    output logic        bg_n_o,
    output logic        bus_relinquished_o,

    output logic        request_ready_o,
    output logic        request_blocked_o,
    output logic        request_conflict_o,
    output logic        request_out_of_phase_o,
    output logic [2:0]  request_accepted_o,
    output logic [2:0]  completion_event_o,
    output logic [2:0]  read_sample_event_o,
    output logic [1:0]  owner_o,
    output logic        transaction_active_o,
    output logic        response_valid_o,
    output logic        response_write_o,
    output logic [23:0] response_read_data_o,
    output logic        response_read_data_valid_o,
    output logic        pm_address_output_enable_o,
    output logic        pm_control_output_enable_o,
    output logic        pm_data_output_enable_o,
    output logic [13:0] pma_o,
    output logic        pma_valid_o,
    output logic        pmda_o,
    output logic        pmda_valid_o,
    output logic        pms_n_o,
    output logic        pmrd_n_o,
    output logic        pmwr_n_o,
    output logic [23:0] pmd_write_data_o,
    output logic        pmd_write_data_valid_o
);
    logic selector_request_ready;
    logic issue_enable;
    logic [2:0] gated_request_valid;
    logic [2:0] request_count;

    assign issue_enable = !issue_inhibit_o;
    assign gated_request_valid = {
        type13_valid_i, type5_valid_i, fetch_valid_i
    } & {3{issue_enable}};
    assign request_count = {2'b00, fetch_valid_i}
        + {2'b00, type5_valid_i} + {2'b00, type13_valid_i};
    assign request_ready_o = selector_request_ready && issue_enable;
    assign request_blocked_o = request_count != 3'd0 && !issue_enable;

    adsp2100_bus_control bus_control (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .br_n_i(br_n_i),
        .mode_o(bus_mode_o),
        .state_three_boundary_o(state_three_boundary_o),
        .request_recognized_o(bus_request_recognized_o),
        .grant_assert_event_o(grant_assert_event_o),
        .release_recognized_o(release_recognized_o),
        .grant_release_event_o(grant_release_event_o),
        .resume_event_o(resume_event_o),
        .request_withdrawn_o(request_withdrawn_o),
        .release_cancelled_o(release_cancelled_o),
        .instruction_issue_inhibit_o(issue_inhibit_o),
        .bus_relinquished_o(normal_bus_relinquished_o),
        .bg_n_o(normal_bg_n_o),
        .reset_br_request_o(reset_br_request_o)
    );

    adsp2100_reset_bus_grant reset_bus_grant (
        .reset_active_i(reset_i),
        .br_n_i(br_n_i),
        .normal_bg_n_i(normal_bg_n_o),
        .normal_bus_relinquished_i(normal_bus_relinquished_o),
        .bg_n_o(bg_n_o),
        .bus_relinquished_o(bus_relinquished_o)
    );

    adsp2100_program_owner_bus program_owner_bus (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .fetch_valid_i(gated_request_valid[0]),
        .fetch_address_i(fetch_address_i),
        .fetch_address_valid_i(fetch_address_valid_i),
        .type5_valid_i(gated_request_valid[1]),
        .type5_address_i(type5_address_i),
        .type5_address_valid_i(type5_address_valid_i),
        .type5_data_access_i(type5_data_access_i),
        .type5_write_i(type5_write_i),
        .type5_write_data_i(type5_write_data_i),
        .type5_write_data_valid_i(type5_write_data_valid_i),
        .type13_valid_i(gated_request_valid[2]),
        .type13_address_i(type13_address_i),
        .type13_address_valid_i(type13_address_valid_i),
        .type13_data_access_i(type13_data_access_i),
        .type13_write_i(type13_write_i),
        .type13_write_data_i(type13_write_data_i),
        .type13_write_data_valid_i(type13_write_data_valid_i),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .bus_relinquished_i(bus_relinquished_o),
        .request_ready_o(selector_request_ready),
        .request_conflict_o(request_conflict_o),
        .request_out_of_phase_o(request_out_of_phase_o),
        .request_accepted_o(request_accepted_o),
        .completion_event_o(completion_event_o),
        .read_sample_event_o(read_sample_event_o),
        .owner_o(owner_o),
        .transaction_active_o(transaction_active_o),
        .response_valid_o(response_valid_o),
        .response_write_o(response_write_o),
        .response_read_data_o(response_read_data_o),
        .response_read_data_valid_o(response_read_data_valid_o),
        .pm_address_output_enable_o(pm_address_output_enable_o),
        .pm_control_output_enable_o(pm_control_output_enable_o),
        .pm_data_output_enable_o(pm_data_output_enable_o),
        .pma_o(pma_o),
        .pma_valid_o(pma_valid_o),
        .pmda_o(pmda_o),
        .pmda_valid_o(pmda_valid_o),
        .pms_n_o(pms_n_o),
        .pmrd_n_o(pmrd_n_o),
        .pmwr_n_o(pmwr_n_o),
        .pmd_write_data_o(pmd_write_data_o),
        .pmd_write_data_valid_o(pmd_write_data_valid_o)
    );

`ifndef SYNTHESIS
    always_comb begin
        assert (bg_n_o == !bus_relinquished_o);
        assert (request_blocked_o
            == (request_count != 3'd0 && issue_inhibit_o));
        if (issue_inhibit_o) begin
            assert (!request_ready_o);
            assert (request_accepted_o == 3'b000);
        end
        if (bus_relinquished_o) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
        end
        if (bus_request_recognized_o && transaction_active_o) begin
            assert (pm_address_output_enable_o);
            assert (pm_control_output_enable_o);
        end
        if (resume_event_o && request_count == 3'd1) begin
            assert ($onehot(request_accepted_o));
        end
    end
`endif
endmodule

`default_nettype wire
