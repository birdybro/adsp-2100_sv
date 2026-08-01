`default_nettype none

module adsp2100_load_non_dreg_immediate_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    // Deterministic verification/integration preload through the complete
    // original general-register destination boundary.
    input  logic        setup_write_i,
    input  logic [5:0]  setup_code_i,
    input  logic [15:0] setup_data_i,
    input  logic [5:0]  probe_code_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        invalid_subencoding_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        invalid_setup_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic [1:0]  register_group_o,
    output logic [3:0]  register_index_o,
    output logic [5:0]  register_code_o,
    output logic [13:0] immediate_data_o,
    output logic        data_register_destination_o,
    output logic        reserved_destination_o,
    output logic        read_only_destination_o,

    output logic [15:0] probe_data_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [4:0]  icntl_o,
    output logic [3:0]  imask_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic [7:0]  px_o,
    output logic [7:0]  sstat_o,
    output logic        count_stack_push_o,
    output logic [13:0] count_stack_push_data_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic decoded_present_unused;
    logic decoded_writable_unused;
    logic decoded_invalid_subencoding;
    logic state_write;
    logic [5:0] state_write_code;
    logic [15:0] state_write_data;
    logic setup_forward;
    logic state_class_valid_unused;
    logic state_boundary_valid_unused;
    logic state_invalid_opcode_unused;
    logic state_invalid_subencoding_unused;
    logic state_integration_conflict_unused;
    logic [5:0] state_source_code_unused;
    logic [5:0] state_destination_code_unused;
    logic [15:0] state_source_data_unused;
    logic state_source_extension_unused;
    logic state_pm_access_unused;
    logic state_dm_access_unused;
    logic unused_observation;

    adsp2100_load_non_dreg_immediate_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .invalid_subencoding_o(decoded_invalid_subencoding),
        .register_group_o(register_group_o),
        .register_index_o(register_index_o),
        .register_code_o(register_code_o),
        .immediate_data_o(immediate_data_o),
        .register_present_o(decoded_present_unused),
        .register_writable_o(decoded_writable_unused),
        .data_register_destination_o(data_register_destination_o),
        .reserved_destination_o(reserved_destination_o),
        .read_only_destination_o(read_only_destination_o)
    );

    assign integration_conflict_o = (
        !reset_i && execute_i && setup_write_i
    );
    assign invalid_opcode_o = (
        !reset_i && execute_i && !class_valid_o
    );
    assign invalid_subencoding_o = (
        !reset_i && execute_i && class_valid_o
        && decoded_invalid_subencoding
    );
    assign boundary_valid_o = (
        !reset_i && execute_i && action_valid_o && !setup_write_i
    );
    assign setup_forward = (
        !reset_i && !execute_i && setup_write_i
    );
    assign state_write = boundary_valid_o || setup_forward;
    assign state_write_code = boundary_valid_o
        ? register_code_o : setup_code_i;
    assign state_write_data = boundary_valid_o
        ? {2'b00, immediate_data_o} : setup_data_i;
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    // The shared Type 17 storage boundary supplies exact-width DAG, status,
    // selected-bank SB, PX, CNTR/count-stack, and SSTAT behavior. Its own
    // instruction decoder is inactive; Type 7 supplies one known write.
    adsp2100_internal_move_slice register_state (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(1'b0),
        .opcode_i(24'h000000),
        .setup_write_i(state_write),
        .setup_data_valid_i(1'b1),
        .setup_code_i(state_write_code),
        .setup_data_i(state_write_data),
        .probe_code_i(probe_code_i),
        .probe_data_o(probe_data_o),
        .class_valid_o(state_class_valid_unused),
        .boundary_valid_o(state_boundary_valid_unused),
        .invalid_opcode_o(state_invalid_opcode_unused),
        .invalid_subencoding_o(state_invalid_subencoding_unused),
        .invalid_setup_o(invalid_setup_o),
        .integration_conflict_o(state_integration_conflict_unused),
        .internal_conflict_o(internal_conflict_o),
        .source_code_o(state_source_code_unused),
        .destination_code_o(state_destination_code_unused),
        .source_data_o(state_source_data_unused),
        .source_extension_provisional_o(state_source_extension_unused),
        .count_stack_push_o(count_stack_push_o),
        .count_stack_push_data_o(count_stack_push_data_o),
        .count_stack_depth_o(count_stack_depth_o),
        .count_stack_overflow_o(count_stack_overflow_o),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .cntr_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .px_o(px_o),
        .sstat_o(sstat_o),
        .pm_data_access_o(state_pm_access_unused),
        .dm_access_o(state_dm_access_unused)
    );

    assign unused_observation = ^{
        decoded_present_unused,
        decoded_writable_unused,
        state_class_valid_unused,
        state_boundary_valid_unused,
        state_invalid_opcode_unused,
        state_invalid_subencoding_unused,
        state_integration_conflict_unused,
        state_source_code_unused,
        state_destination_code_unused,
        state_source_data_unused,
        state_source_extension_unused,
        state_pm_access_unused,
        state_dm_access_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!pm_data_access_o && !dm_access_o);
        assert (!(boundary_valid_o && integration_conflict_o));
        if (boundary_valid_o) begin
            assert (class_valid_o && action_valid_o);
            assert (state_write);
            assert (state_write_code == register_code_o);
            assert (state_write_data == {2'b00, immediate_data_o});
            assert (register_group_o != 2'b00);
        end
        if (invalid_subencoding_o && execute_i && !reset_i) begin
            assert (!boundary_valid_o);
        end
        if (reset_i) begin
            assert (!boundary_valid_o && !invalid_opcode_o);
        end
    end
`endif
endmodule

`default_nettype wire
