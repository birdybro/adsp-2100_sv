`default_nettype none

module adsp2100_direct_jump_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        pc_setup,
    input logic [13:0] pc_setup_data,
    input logic        astat_setup,
    input logic [7:0]  astat_setup_data,
    input logic        counter_setup,
    input logic [13:0] counter_setup_data
);
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_call_ce;
    logic        call_action;
    logic [13:0] address;
    logic [3:0]  condition;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        invalid_condition_state;
    logic        internal_conflict;
    logic        condition_known;
    logic        condition_true;
    logic [13:0] pc;
    logic        pc_write;
    logic        explicit_transfer;
    logic        pc_stack_push;
    logic        pc_stack_push_accepted;
    logic [13:0] pc_stack_top;
    logic        pc_stack_top_valid;
    logic [4:0]  pc_stack_depth;
    logic        pc_stack_overflow;
    logic [13:0] cntr;
    logic        cntr_valid;
    logic        counter_test;
    logic        counter_decrement;
    logic        counter_restore;
    logic        counter_empty_invalidate;
    logic        count_stack_push;
    logic        count_stack_pop;
    logic [13:0] count_stack_top;
    logic        count_stack_top_valid;
    logic [2:0]  count_stack_depth;
    logic        count_stack_overflow;
    logic [7:0]  astat;
    logic        astat_valid;
    logic [7:0]  sstat_fragment;
    logic        pm_data_access;
    logic        dm_access;
    logic        expected_class;
    logic        expected_unsupported;
    logic [1:0]  setup_count;
    logic        expected_conflict;
    logic        raw_condition_context_valid;
    logic        past_valid;

    assign expected_class = ((opcode & 24'hf80000) == 24'h180000);
    assign expected_unsupported = (
        expected_class && opcode[18] && opcode[3:0] == 4'he
    );
    assign setup_count = (
        {1'b0, pc_setup}
        + {1'b0, astat_setup}
        + {1'b0, counter_setup}
    );
    assign expected_conflict = !reset && (
        (execute && setup_count != 2'd0) || setup_count > 2'd1
    );
    assign raw_condition_context_valid = (
        (opcode[3:0] == 4'hf)
        || ((opcode[3:0] == 4'he) ? cntr_valid : astat_valid)
    );

    adsp2100_direct_jump_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .pc_setup_write_i(pc_setup),
        .pc_setup_data_i(pc_setup_data),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .counter_setup_write_i(counter_setup),
        .counter_setup_data_i(counter_setup_data),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_call_ce_o(unsupported_call_ce),
        .call_o(call_action),
        .address_o(address),
        .condition_o(condition),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .invalid_condition_state_o(invalid_condition_state),
        .internal_conflict_o(internal_conflict),
        .condition_known_o(condition_known),
        .condition_true_o(condition_true),
        .pc_o(pc),
        .pc_write_o(pc_write),
        .explicit_transfer_o(explicit_transfer),
        .pc_stack_push_o(pc_stack_push),
        .pc_stack_push_accepted_o(pc_stack_push_accepted),
        .pc_stack_top_o(pc_stack_top),
        .pc_stack_top_valid_o(pc_stack_top_valid),
        .pc_stack_depth_o(pc_stack_depth),
        .pc_stack_overflow_o(pc_stack_overflow),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .counter_test_o(counter_test),
        .counter_decrement_o(counter_decrement),
        .counter_restore_o(counter_restore),
        .counter_empty_invalidate_o(counter_empty_invalidate),
        .count_stack_push_o(count_stack_push),
        .count_stack_pop_o(count_stack_pop),
        .count_stack_top_o(count_stack_top),
        .count_stack_top_valid_o(count_stack_top_valid),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .astat_o(astat),
        .astat_valid_o(astat_valid),
        .sstat_fragment_o(sstat_fragment),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (unsupported_call_ce == expected_unsupported);
        assert (action_valid == (expected_class && !expected_unsupported));
        assert (call_action == (expected_class ? opcode[18] : 1'b0));
        assert (address == (expected_class ? opcode[17:4] : 14'h0000));
        assert (condition == (expected_class ? opcode[3:0] : 4'h0));
        assert (integration_conflict == expected_conflict);
        assert (invalid_opcode == (!reset && execute && !expected_class));
        assert (
            boundary_valid
            == (
                !reset && execute && action_valid && !expected_conflict
                && raw_condition_context_valid
            )
        );
        assert (
            invalid_condition_state
            == (
                !reset && execute && action_valid && !expected_conflict
                && !raw_condition_context_valid
            )
        );
        assert (
            condition_known
            == (
                !reset && execute && action_valid && !expected_conflict
                && raw_condition_context_valid
            )
        );
        assert (pc_write == boundary_valid);
        assert (explicit_transfer == condition_true);
        assert (pc_stack_push == (condition_true && call_action));
        assert (
            counter_test
            == (boundary_valid && !call_action && condition == 4'he)
        );
        assert (!(pc_stack_push && counter_test));
        assert (!counter_decrement || counter_test);
        assert (!counter_restore || count_stack_pop);
        assert (!counter_empty_invalidate || count_stack_pop);
        assert (!count_stack_push || counter_setup);
        assert (!internal_conflict);
        assert (!pm_data_access && !dm_access);
        assert (pc_stack_depth <= 5'd16);
        assert (count_stack_depth <= 3'd4);
        assert (pc_stack_top_valid == (pc_stack_depth != 5'd0));
        assert (count_stack_top_valid == (count_stack_depth != 3'd0));
        assert (sstat_fragment[0] == !pc_stack_top_valid);
        assert (sstat_fragment[1] == pc_stack_overflow);
        assert (sstat_fragment[2] == !count_stack_top_valid);
        assert (sstat_fragment[3] == count_stack_overflow);
        assert (sstat_fragment[5:4] == 2'b00);
        assert (sstat_fragment[7:6] == 2'b01);
        if (pc_stack_push_accepted) begin
            assert (pc_stack_push && pc_stack_depth < 5'd16);
        end
        if (!pc_stack_top_valid) assert (pc_stack_depth == 5'd0);
        if (!count_stack_top_valid) assert (count_stack_depth == 3'd0);
        cover (boundary_valid && condition_true && !call_action);
        cover (boundary_valid && !condition_true && !call_action);
        cover (pc_stack_push_accepted);
        cover (counter_decrement);
        cover (counter_restore);
        cover (counter_empty_invalidate);
        cover (unsupported_call_ce);
        cover (pc_stack_top == count_stack_top);
        cover (astat == 8'h55 && cntr == 14'h1555);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (pc == 14'h0004);
            assert (!astat_valid);
            assert (!cntr_valid);
            assert (pc_stack_depth == 5'd0);
            assert (count_stack_depth == 3'd0);
        end else if ($past(boundary_valid)) begin
            assert (
                pc
                == (
                    $past(condition_true)
                    ? $past(address)
                    : ($past(pc) + 14'h0001)
                )
            );
        end else if ($past(
            !execute && pc_setup && !astat_setup && !counter_setup
        )) begin
            assert (pc == $past(pc_setup_data));
        end else begin
            assert (pc == $past(pc));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
