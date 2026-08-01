`default_nettype none

module adsp2100_direct_dm_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic        dm_ack_i,
    input  logic [15:0] dm_read_data_i,
    input  logic        dm_read_data_valid_i,

    // Deterministic verification/integration preload through the same
    // general-register destination rules used by architectural transfers.
    input  logic        setup_write_i,
    input  logic [5:0]  setup_code_i,
    input  logic [15:0] setup_data_i,
    input  logic [5:0]  probe_code_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        invalid_subencoding_o,
    output logic        write_direction_o,
    output logic [13:0] direct_address_o,
    output logic [5:0]  register_code_o,
    output logic        boundary_valid_o,
    output logic        accepted_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        stalled_o,
    output logic        busy_o,
    output logic        invalid_opcode_o,
    output logic        invalid_setup_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,

    output logic        dm_select_o,
    output logic        dm_read_o,
    output logic        dm_write_o,
    output logic [13:0] dm_address_o,
    output logic        dm_address_valid_o,
    output logic [15:0] dm_write_data_o,
    output logic        dm_write_data_valid_o,
    output logic        register_write_o,
    output logic        register_write_known_o,
    output logic        source_extension_provisional_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o,

    output logic [15:0] probe_data_o,
    output logic        probe_data_valid_o,
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
    output logic        count_stack_overflow_o
);
    logic decoded_invalid;
    logic decoded_write;
    logic [13:0] decoded_address;
    logic [1:0] decoded_group_unused;
    logic [3:0] decoded_index_unused;
    logic [5:0] decoded_code;
    logic decoded_present_unused;
    logic decoded_writable_unused;
    logic decoded_reserved_source_unused;
    logic decoded_reserved_destination_unused;
    logic decoded_read_only_unused;

    logic issue;
    logic setup_forward;
    logic state_write;
    logic [5:0] state_write_code;
    logic [15:0] state_write_data;
    logic state_write_data_valid;
    logic [5:0] state_read_code;
    logic [15:0] state_read_data;
    logic state_invalid_setup;
    logic state_integration_conflict_unused;
    logic state_internal_conflict;
    logic state_class_valid_unused;
    logic state_boundary_valid_unused;
    logic state_invalid_opcode_unused;
    logic state_invalid_subencoding_unused;
    logic [5:0] state_source_code_unused;
    logic [5:0] state_destination_code_unused;
    logic [15:0] state_source_data_unused;
    logic state_source_provisional_unused;
    logic state_pm_access_unused;
    logic state_dm_access_unused;
    logic state_cntr_valid;

    logic pending_q;
    logic pending_write_q;
    logic [13:0] pending_address_q;
    logic [5:0] pending_register_code_q;
    logic [15:0] pending_write_data_q;
    logic pending_write_data_valid_q;
    logic pending_source_provisional_q;

    logic active_write;
    logic [13:0] active_address;
    logic [5:0] active_register_code;
    logic [15:0] active_write_data;
    logic active_write_data_valid;
    logic active_source_provisional;

    logic [63:0] register_valid_q [0:1];
    logic [63:0] register_valid_next [0:1];
    logic selected_bank_valid;
    logic selected_bank;
    logic state_write_allowed;
    logic unused_observation;

    localparam logic [63:0] RESET_VALID_REGISTERS =
        64'h000e000000000000;

    function automatic logic banked_selector(input logic [5:0] code);
        banked_selector = code[5:4] == 2'b00 || code == 6'h36;
    endfunction

    function automatic logic register_known(input logic [5:0] code);
        if (banked_selector(code)) begin
            register_known = selected_bank_valid
                && register_valid_q[selected_bank][code];
        end else begin
            register_known = register_valid_q[0][code];
        end
    endfunction

    adsp2100_direct_dm_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .invalid_subencoding_o(decoded_invalid),
        .write_o(decoded_write),
        .address_o(decoded_address),
        .register_group_o(decoded_group_unused),
        .register_index_o(decoded_index_unused),
        .register_code_o(decoded_code),
        .register_present_o(decoded_present_unused),
        .register_writable_o(decoded_writable_unused),
        .reserved_source_o(decoded_reserved_source_unused),
        .reserved_destination_o(decoded_reserved_destination_unused),
        .read_only_destination_o(decoded_read_only_unused)
    );

    assign integration_conflict_o = (
        !reset_i
        && (
            (pending_q && (execute_i || setup_write_i))
            || (!pending_q && execute_i && setup_write_i)
        )
    );
    assign invalid_opcode_o = (
        !reset_i && !pending_q && execute_i && !class_valid_o
    );
    assign invalid_subencoding_o = (
        !reset_i && !pending_q && execute_i
        && class_valid_o && decoded_invalid
    );
    assign issue = (
        !reset_i && !pending_q && execute_i && action_valid_o
        && !setup_write_i
    );
    assign boundary_valid_o = issue;
    assign accepted_o = issue;
    assign setup_forward = (
        !reset_i && !pending_q && !execute_i && setup_write_i
    );

    always_comb begin
        if (pending_q) begin
            active_write = pending_write_q;
            active_address = pending_address_q;
            active_register_code = pending_register_code_q;
            active_write_data = pending_write_data_q;
            active_write_data_valid = pending_write_data_valid_q;
            active_source_provisional = pending_source_provisional_q;
        end else begin
            active_write = decoded_write;
            active_address = decoded_address;
            active_register_code = decoded_code;
            active_write_data = state_read_data;
            active_write_data_valid = register_known(decoded_code);
            active_source_provisional = (
                decoded_write
                && decoded_code[5:4] == 2'b11
                && decoded_code[3:0] <= 4'd4
            );
        end
    end

    assign transaction_active_o = !reset_i && (pending_q || issue);
    assign instruction_complete_o = transaction_active_o && dm_ack_i;
    assign stalled_o = transaction_active_o && !dm_ack_i;
    assign busy_o = stalled_o;
    assign dm_select_o = transaction_active_o;
    assign dm_read_o = transaction_active_o && !active_write;
    assign dm_write_o = transaction_active_o && active_write;
    assign dm_address_o = transaction_active_o
        ? active_address : 14'h0000;
    assign dm_address_valid_o = transaction_active_o;
    assign dm_write_data_o = (
        dm_write_o && active_write_data_valid
        ? active_write_data : 16'h0000
    );
    assign dm_write_data_valid_o = (
        dm_write_o && active_write_data_valid
    );
    assign register_write_o = instruction_complete_o && !active_write;
    assign register_write_known_o = (
        register_write_o && dm_read_data_valid_i
    );
    assign source_extension_provisional_o = (
        transaction_active_o && active_source_provisional
    );
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = transaction_active_o;
    assign write_direction_o = decoded_write;
    assign direct_address_o = decoded_address;
    assign register_code_o = decoded_code;

    assign state_read_code = issue && decoded_write
        ? decoded_code : probe_code_i;
    assign probe_data_o = state_read_data;
    assign probe_data_valid_o = register_known(state_read_code);
    assign state_write = setup_forward || register_write_o;
    assign state_write_code = register_write_o
        ? active_register_code : setup_code_i;
    assign state_write_data = register_write_o
        ? dm_read_data_i : setup_data_i;
    assign state_write_data_valid = register_write_o
        ? dm_read_data_valid_i : 1'b1;
    assign selected_bank_valid = register_valid_q[0][6'h31];
    assign selected_bank = mstat_o[0];
    assign state_write_allowed = (
        state_write
        && (!banked_selector(state_write_code) || selected_bank_valid)
    );
    assign invalid_setup_o = state_invalid_setup;
    assign internal_conflict_o = state_internal_conflict;

    // This instance owns the complete original general-register table. Type 3
    // uses its generic setup port as the shared cycle-end write boundary; the
    // Type 17 decoder itself is intentionally inactive here.
    adsp2100_internal_move_slice register_state (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .execute_i(1'b0),
        .opcode_i(24'h000000),
        .setup_write_i(state_write_allowed),
        .setup_data_valid_i(state_write_data_valid),
        .setup_code_i(state_write_code),
        .setup_data_i(state_write_data),
        .probe_code_i(state_read_code),
        .probe_data_o(state_read_data),
        .class_valid_o(state_class_valid_unused),
        .boundary_valid_o(state_boundary_valid_unused),
        .invalid_opcode_o(state_invalid_opcode_unused),
        .invalid_subencoding_o(state_invalid_subencoding_unused),
        .invalid_setup_o(state_invalid_setup),
        .integration_conflict_o(state_integration_conflict_unused),
        .internal_conflict_o(state_internal_conflict),
        .source_code_o(state_source_code_unused),
        .destination_code_o(state_destination_code_unused),
        .source_data_o(state_source_data_unused),
        .source_extension_provisional_o(
            state_source_provisional_unused
        ),
        .count_stack_push_o(count_stack_push_o),
        .count_stack_push_data_o(count_stack_push_data_o),
        .count_stack_depth_o(count_stack_depth_o),
        .count_stack_overflow_o(count_stack_overflow_o),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .cntr_o(cntr_o),
        .cntr_valid_o(state_cntr_valid),
        .px_o(px_o),
        .sstat_o(sstat_o),
        .pm_data_access_o(state_pm_access_unused),
        .dm_access_o(state_dm_access_unused)
    );

    assign cntr_valid_o = (
        state_cntr_valid && register_valid_q[0][6'h35]
    );

    always_comb begin
        register_valid_next[0] = register_valid_q[0];
        register_valid_next[1] = register_valid_q[1];
        if (setup_forward && !state_invalid_setup) begin
            if (banked_selector(setup_code_i)) begin
                if (selected_bank_valid) begin
                    register_valid_next[selected_bank][setup_code_i] = 1'b1;
                    if (setup_code_i == 6'h0c) begin
                        register_valid_next[selected_bank][6'h0d] = 1'b1;
                    end
                end
            end else begin
                register_valid_next[0][setup_code_i] = 1'b1;
            end
        end
        if (register_write_o) begin
            if (banked_selector(active_register_code)) begin
                if (selected_bank_valid) begin
                    register_valid_next[selected_bank][active_register_code]
                        = dm_read_data_valid_i;
                    if (active_register_code == 6'h0c) begin
                        register_valid_next[selected_bank][6'h0d]
                            = dm_read_data_valid_i;
                    end
                end
            end else begin
                register_valid_next[0][active_register_code]
                    = dm_read_data_valid_i;
            end
        end
    end

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pending_q <= 1'b0;
            register_valid_q[0] <= RESET_VALID_REGISTERS;
            register_valid_q[1] <= 64'h0000000000000000;
        end else begin
            register_valid_q[0] <= register_valid_next[0];
            register_valid_q[1] <= register_valid_next[1];
            if (pending_q) begin
                if (dm_ack_i) begin
                    pending_q <= 1'b0;
                end
            end else if (issue && !dm_ack_i) begin
                pending_q <= 1'b1;
                pending_write_q <= decoded_write;
                pending_address_q <= decoded_address;
                pending_register_code_q <= decoded_code;
                pending_write_data_q <= state_read_data;
                pending_write_data_valid_q
                    <= register_known(decoded_code);
                pending_source_provisional_q <= (
                    decoded_write
                    && decoded_code[5:4] == 2'b11
                    && decoded_code[3:0] <= 4'd4
                );
            end
        end
    end

    assign unused_observation = ^{
        decoded_group_unused,
        decoded_index_unused,
        decoded_present_unused,
        decoded_writable_unused,
        decoded_reserved_source_unused,
        decoded_reserved_destination_unused,
        decoded_read_only_unused,
        state_integration_conflict_unused,
        state_class_valid_unused,
        state_boundary_valid_unused,
        state_invalid_opcode_unused,
        state_invalid_subencoding_unused,
        state_source_code_unused,
        state_destination_code_unused,
        state_source_data_unused,
        state_source_provisional_unused,
        state_pm_access_unused,
        state_dm_access_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(dm_read_o && dm_write_o));
        assert (dm_select_o == (dm_read_o || dm_write_o));
        assert (dm_access_o == dm_select_o);
        assert (!pm_data_access_o);
        assert (boundary_valid_o == accepted_o);
        assert (instruction_complete_o
            == (transaction_active_o && dm_ack_i));
        assert (stalled_o == (transaction_active_o && !dm_ack_i));
        assert (register_write_o
            == (instruction_complete_o && dm_read_o));
        if (stalled_o) begin
            assert (!instruction_complete_o && !register_write_o);
        end
        if (pending_q && !reset_i) begin
            assert (!boundary_valid_o);
            assert (dm_address_o == pending_address_q);
            if (pending_write_q && pending_write_data_valid_q) begin
                assert (dm_write_data_o == pending_write_data_q);
            end
        end
        if (source_extension_provisional_o) begin
            assert (dm_write_o);
        end
        if (reset_i) begin
            assert (!transaction_active_o && !accepted_o);
        end
    end
`endif
endmodule

`default_nettype wire
