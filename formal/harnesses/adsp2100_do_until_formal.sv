`default_nettype none

module adsp2100_do_until_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        pc_setup,
    input logic [13:0] pc_setup_data,
    input logic        counter_setup,
    input logic [13:0] counter_setup_data
);
    logic        class_valid;
    logic        action_valid;
    logic [13:0] end_address;
    logic [3:0]  termination;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        invalid_loop_context;
    logic        unsupported_do_at_loop_end;
    logic        unsupported_nested_same_end;
    logic        internal_conflict;
    logic [13:0] pc;
    logic        pc_write;
    logic        pc_stack_push;
    logic        pc_stack_push_accepted;
    logic        pc_stack_overflow_event;
    logic [13:0] pc_stack_top;
    logic        pc_stack_top_valid;
    logic [4:0]  pc_stack_depth;
    logic        pc_stack_overflow;
    logic        loop_stack_push;
    logic        loop_stack_push_accepted;
    logic        loop_stack_overflow_event;
    logic [17:0] loop_stack_top;
    logic        loop_stack_top_valid;
    logic [2:0]  loop_stack_depth;
    logic        loop_stack_overflow;
    logic [13:0] cntr;
    logic        cntr_valid;
    logic        count_stack_push;
    logic [13:0] count_stack_top;
    logic        count_stack_top_valid;
    logic [2:0]  count_stack_depth;
    logic        count_stack_overflow;
    logic [7:0]  sstat_fragment;
    logic        pm_data_access;
    logic        dm_access;
    logic        expected_class;
    logic        expected_conflict;
    logic        execution_attempt;
    logic        past_valid;

    assign expected_class = ((opcode & 24'hfc0000) == 24'h140000);
    assign expected_conflict = !reset && (
        (execute && (pc_setup || counter_setup))
        || (pc_setup && counter_setup)
    );
    assign execution_attempt = (
        !reset && execute && expected_class && !expected_conflict
    );

    adsp2100_do_until_slice dut (
        .clk_i(clk), .reset_i(reset), .execute_i(execute), .opcode_i(opcode),
        .pc_setup_write_i(pc_setup), .pc_setup_data_i(pc_setup_data),
        .counter_setup_write_i(counter_setup),
        .counter_setup_data_i(counter_setup_data),
        .class_valid_o(class_valid), .action_valid_o(action_valid),
        .end_address_o(end_address), .termination_o(termination),
        .boundary_valid_o(boundary_valid), .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .invalid_loop_context_o(invalid_loop_context),
        .unsupported_do_at_loop_end_o(unsupported_do_at_loop_end),
        .unsupported_nested_same_end_o(unsupported_nested_same_end),
        .internal_conflict_o(internal_conflict),
        .pc_o(pc), .pc_write_o(pc_write),
        .pc_stack_push_o(pc_stack_push),
        .pc_stack_push_accepted_o(pc_stack_push_accepted),
        .pc_stack_overflow_event_o(pc_stack_overflow_event),
        .pc_stack_top_o(pc_stack_top),
        .pc_stack_top_valid_o(pc_stack_top_valid),
        .pc_stack_depth_o(pc_stack_depth),
        .pc_stack_overflow_o(pc_stack_overflow),
        .loop_stack_push_o(loop_stack_push),
        .loop_stack_push_accepted_o(loop_stack_push_accepted),
        .loop_stack_overflow_event_o(loop_stack_overflow_event),
        .loop_stack_top_o(loop_stack_top),
        .loop_stack_top_valid_o(loop_stack_top_valid),
        .loop_stack_depth_o(loop_stack_depth),
        .loop_stack_overflow_o(loop_stack_overflow),
        .cntr_o(cntr), .cntr_valid_o(cntr_valid),
        .count_stack_push_o(count_stack_push),
        .count_stack_top_o(count_stack_top),
        .count_stack_top_valid_o(count_stack_top_valid),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .sstat_fragment_o(sstat_fragment),
        .pm_data_access_o(pm_data_access), .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_class);
        assert (end_address == (expected_class ? opcode[17:4] : 14'h0000));
        assert (termination == (expected_class ? opcode[3:0] : 4'h0));
        assert (integration_conflict == expected_conflict);
        assert (invalid_opcode == (!reset && execute && !expected_class));
        assert (
            invalid_loop_context
            == (
                execution_attempt && loop_stack_top_valid
                && (
                    !pc_stack_top_valid
                    || (loop_stack_top[17:14] == 4'he && !cntr_valid)
                )
            )
        );
        assert (
            unsupported_do_at_loop_end
            == (
                execution_attempt && loop_stack_top_valid
                && pc == loop_stack_top[13:0]
            )
        );
        assert (
            unsupported_nested_same_end
            == (
                execution_attempt && loop_stack_top_valid
                && end_address == loop_stack_top[13:0]
            )
        );
        assert (
            boundary_valid
            == (
                execution_attempt && !invalid_loop_context
                && !unsupported_do_at_loop_end
                && !unsupported_nested_same_end
            )
        );
        assert (pc_write == boundary_valid);
        assert (pc_stack_push == boundary_valid);
        assert (loop_stack_push == boundary_valid);
        assert (pc_stack_push == loop_stack_push);
        assert (pc_stack_push_accepted == (boundary_valid && pc_stack_depth < 16));
        assert (loop_stack_push_accepted == (boundary_valid && loop_stack_depth < 4));
        assert (pc_stack_overflow_event == (boundary_valid && pc_stack_depth == 16));
        assert (loop_stack_overflow_event == (boundary_valid && loop_stack_depth == 4));
        assert (
            count_stack_push
            == (!reset && !execute && counter_setup && !pc_setup && cntr_valid)
        );
        assert (!internal_conflict);
        assert (!pm_data_access && !dm_access);
        assert (pc_stack_depth <= 16);
        assert (loop_stack_depth <= 4);
        assert (count_stack_depth <= 4);
        assert (pc_stack_top_valid == (pc_stack_depth != 0));
        assert (loop_stack_top_valid == (loop_stack_depth != 0));
        assert (count_stack_top_valid == (count_stack_depth != 0));
        assert (sstat_fragment[0] == !pc_stack_top_valid);
        assert (sstat_fragment[1] == pc_stack_overflow);
        assert (sstat_fragment[2] == !count_stack_top_valid);
        assert (sstat_fragment[3] == count_stack_overflow);
        assert (sstat_fragment[5:4] == 2'b00);
        assert (sstat_fragment[6] == !loop_stack_top_valid);
        assert (sstat_fragment[7] == loop_stack_overflow);
        cover (boundary_valid && termination == 4'he);
        cover (boundary_valid && termination == 4'hf);
        cover (pc_stack_push_accepted && loop_stack_push_accepted);
        cover (unsupported_nested_same_end);
        cover (unsupported_do_at_loop_end);
        cover (invalid_loop_context);
        cover (loop_stack_overflow_event);
        cover (pc_stack_top == cntr && loop_stack_top[13:0] == count_stack_top);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (pc == 14'h0004);
            assert (!cntr_valid);
            assert (pc_stack_depth == 0);
            assert (loop_stack_depth == 0);
            assert (count_stack_depth == 0);
        end else if ($past(boundary_valid)) begin
            assert (pc == ($past(pc) + 14'h0001));
        end else if ($past(!execute && pc_setup && !counter_setup)) begin
            assert (pc == $past(pc_setup_data));
        end else begin
            assert (pc == $past(pc));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
