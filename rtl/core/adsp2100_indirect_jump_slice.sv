`default_nettype none

module adsp2100_indirect_jump_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        pc_setup_write_i,
    input  logic [13:0] pc_setup_data_i,
    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        counter_setup_write_i,
    input  logic [13:0] counter_setup_data_i,
    input  logic        i_setup_write_i,
    input  logic [1:0]  i_setup_local_i,
    input  logic [13:0] i_setup_data_i,
    input  logic [1:0]  i_probe_local_i,
    output logic [13:0] i_probe_data_o,
    output logic        i_probe_valid_o,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_call_ce_o,
    output logic        call_o,
    output logic [1:0]  i_local_o,
    output logic [2:0]  i_address_o,
    output logic [3:0]  condition_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        invalid_condition_state_o,
    output logic        invalid_target_state_o,
    output logic        internal_conflict_o,
    output logic        condition_known_o,
    output logic        condition_true_o,
    output logic [13:0] indirect_address_o,
    output logic        indirect_address_valid_o,
    output logic        pma_indirect_drive_o,
    output logic [13:0] pc_o,
    output logic        pc_write_o,
    output logic        explicit_transfer_o,
    output logic        pc_stack_push_o,
    output logic        pc_stack_push_accepted_o,
    output logic [13:0] pc_stack_top_o,
    output logic        pc_stack_top_valid_o,
    output logic [4:0]  pc_stack_depth_o,
    output logic        pc_stack_overflow_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic        counter_test_o,
    output logic        counter_decrement_o,
    output logic        counter_restore_o,
    output logic        counter_empty_invalidate_o,
    output logic        count_stack_push_o,
    output logic        count_stack_pop_o,
    output logic [13:0] count_stack_top_o,
    output logic        count_stack_top_valid_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,
    output logic [7:0]  astat_o,
    output logic        astat_valid_o,
    output logic [7:0]  sstat_fragment_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic [13:0] pc_q;
    logic [7:0]  astat_q;
    logic        astat_valid_q;
    logic [2:0]  setup_count;
    logic        pc_setup_enable;
    logic        astat_setup_enable;
    logic        counter_setup_enable;
    logic        i_setup_enable;
    logic        raw_condition_true;
    logic        raw_condition_known;
    logic        condition_context_valid;
    logic [13:0] sequential_pc;
    logic        selected_i_valid;
    logic [13:0] selected_i_data;
    logic        unused_counter_condition_valid;
    logic        unused_counter_expired;
    logic        not_counter_expired;
    logic        unused_counter_not_expired;
    logic [13:0] counter_count_push_data;
    logic        counter_invalid_test;
    logic        counter_empty_manual_pop;
    logic        counter_write_conflict;
    logic        unused_pc_pop_valid;
    logic        unused_pc_empty;
    logic        unused_pc_overflow_event;
    logic        unused_pc_empty_pop;
    logic        unused_count_pop_valid;
    logic        unused_count_empty;
    logic        unused_count_push_accepted;
    logic        unused_count_overflow_event;
    logic        unused_count_empty_pop;
    logic [17:0] unused_loop_top;
    logic        unused_loop_top_valid;
    logic        unused_loop_pop_valid;
    logic        unused_loop_empty;
    logic        unused_loop_overflow;
    logic [2:0]  unused_loop_depth;
    logic        unused_loop_push_accepted;
    logic        unused_loop_overflow_event;
    logic        unused_loop_empty_pop;
    logic        stack_write_conflict;
    logic [13:0] unused_m_read_data;
    logic        unused_m_read_valid;
    logic [13:0] unused_l_read_data;
    logic        unused_l_read_valid;
    logic [13:0] unused_probe_m_data;
    logic        unused_probe_m_valid;
    logic [13:0] unused_probe_l_data;
    logic        unused_probe_l_valid;
    logic        dag_invalid_setup_kind;
    logic        dag_write_conflict;

    adsp2100_indirect_jump_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_call_ce_o(unsupported_call_ce_o),
        .call_o(call_o),
        .i_local_o(i_local_o),
        .i_address_o(i_address_o),
        .condition_o(condition_o)
    );

    assign setup_count = (
        {2'b00, pc_setup_write_i}
        + {2'b00, astat_setup_write_i}
        + {2'b00, counter_setup_write_i}
        + {2'b00, i_setup_write_i}
    );
    assign integration_conflict_o = !reset_i && (
        (execute_i && (setup_count != 3'd0))
        || (setup_count > 3'd1)
    );
    assign pc_setup_enable = (
        !reset_i && !execute_i && (setup_count == 3'd1)
        && pc_setup_write_i
    );
    assign astat_setup_enable = (
        !reset_i && !execute_i && (setup_count == 3'd1)
        && astat_setup_write_i
    );
    assign counter_setup_enable = (
        !reset_i && !execute_i && (setup_count == 3'd1)
        && counter_setup_write_i
    );
    assign i_setup_enable = (
        !reset_i && !execute_i && (setup_count == 3'd1)
        && i_setup_write_i
    );

    always_comb begin
        raw_condition_known = astat_valid_q;
        if (condition_o == 4'he) begin
            raw_condition_known = cntr_valid_o;
        end else if (condition_o == 4'hf) begin
            raw_condition_known = 1'b1;
        end
    end

    assign condition_context_valid = (
        !reset_i && execute_i && action_valid_o
        && !integration_conflict_o && raw_condition_known
    );
    assign condition_known_o = condition_context_valid;
    assign invalid_target_state_o = (
        condition_context_valid && raw_condition_true && !selected_i_valid
    );
    assign boundary_valid_o = (
        condition_context_valid && !invalid_target_state_o
    );
    assign invalid_opcode_o = !reset_i && execute_i && !class_valid_o;
    assign invalid_condition_state_o = (
        !reset_i && execute_i && action_valid_o
        && !integration_conflict_o && !raw_condition_known
    );
    assign condition_true_o = boundary_valid_o && raw_condition_true;
    assign indirect_address_valid_o = condition_context_valid && selected_i_valid;
    assign indirect_address_o = indirect_address_valid_o
        ? selected_i_data : 14'h0000;
    assign pma_indirect_drive_o = condition_true_o;
    assign sequential_pc = pc_q + 14'h0001;
    assign pc_write_o = boundary_valid_o;
    assign explicit_transfer_o = condition_true_o;
    assign pc_stack_push_o = condition_true_o && call_o;
    assign counter_test_o = (
        boundary_valid_o && !call_o && (condition_o == 4'he)
    );
    assign internal_conflict_o = (
        counter_write_conflict || stack_write_conflict
        || counter_invalid_test || counter_empty_manual_pop
        || dag_invalid_setup_kind || dag_write_conflict
    );
    assign pc_o = pc_q;
    assign astat_o = astat_q;
    assign astat_valid_o = astat_valid_q;
    // The IF evaluator samples cycle-start CNTR directly. Do not feed its
    // predicate back from the counter transition block, whose outputs also
    // describe the requested post-test update.
    assign not_counter_expired = (cntr_o != 14'h0001);
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    adsp2100_condition_logic condition_logic (
        .condition_i(condition_o),
        .az_i(astat_q[0]),
        .an_i(astat_q[1]),
        .av_i(astat_q[2]),
        .ac_i(astat_q[3]),
        .as_i(astat_q[4]),
        .mv_i(astat_q[6]),
        .not_counter_expired_i(not_counter_expired),
        .condition_true_o(raw_condition_true)
    );

    adsp2100_counter counter (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .load_i(counter_setup_enable),
        .load_data_i(counter_setup_data_i),
        .ce_test_i(counter_test_o),
        .manual_pop_i(1'b0),
        .count_stack_top_data_i(count_stack_top_o),
        .count_stack_top_valid_i(count_stack_top_valid_o),
        .cntr_data_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .condition_valid_o(unused_counter_condition_valid),
        .counter_expired_o(unused_counter_expired),
        .not_counter_expired_o(unused_counter_not_expired),
        .count_stack_push_o(count_stack_push_o),
        .count_stack_push_data_o(counter_count_push_data),
        .count_stack_pop_o(count_stack_pop_o),
        .decrement_o(counter_decrement_o),
        .restore_o(counter_restore_o),
        .empty_ce_invalidate_o(counter_empty_invalidate_o),
        .invalid_ce_test_o(counter_invalid_test),
        .empty_manual_pop_o(counter_empty_manual_pop),
        .write_conflict_o(counter_write_conflict)
    );

    adsp2100_sequencer_stacks stacks (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .pc_push_i(pc_stack_push_o),
        .pc_pop_i(1'b0),
        .pc_push_data_i(sequential_pc),
        .pc_top_data_o(pc_stack_top_o),
        .pc_top_valid_o(pc_stack_top_valid_o),
        .pc_pop_valid_o(unused_pc_pop_valid),
        .pc_empty_o(unused_pc_empty),
        .pc_overflow_o(pc_stack_overflow_o),
        .pc_depth_o(pc_stack_depth_o),
        .pc_push_accepted_o(pc_stack_push_accepted_o),
        .pc_overflow_event_o(unused_pc_overflow_event),
        .pc_empty_pop_o(unused_pc_empty_pop),
        .count_push_i(count_stack_push_o),
        .count_pop_i(count_stack_pop_o),
        .count_push_data_i(counter_count_push_data),
        .count_top_data_o(count_stack_top_o),
        .count_top_valid_o(count_stack_top_valid_o),
        .count_pop_valid_o(unused_count_pop_valid),
        .count_empty_o(unused_count_empty),
        .count_overflow_o(count_stack_overflow_o),
        .count_depth_o(count_stack_depth_o),
        .count_push_accepted_o(unused_count_push_accepted),
        .count_overflow_event_o(unused_count_overflow_event),
        .count_empty_pop_o(unused_count_empty_pop),
        .loop_push_i(1'b0),
        .loop_pop_i(1'b0),
        .loop_push_data_i(18'h00000),
        .loop_top_data_o(unused_loop_top),
        .loop_top_valid_o(unused_loop_top_valid),
        .loop_pop_valid_o(unused_loop_pop_valid),
        .loop_empty_o(unused_loop_empty),
        .loop_overflow_o(unused_loop_overflow),
        .loop_depth_o(unused_loop_depth),
        .loop_push_accepted_o(unused_loop_push_accepted),
        .loop_overflow_event_o(unused_loop_overflow_event),
        .loop_empty_pop_o(unused_loop_empty_pop),
        .sstat_fragment_o(sstat_fragment_o),
        .write_conflict_o(stack_write_conflict)
    );

    adsp2100_dag_register_file dag_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .i_l_read_address_i(i_address_o),
        .m_read_address_i(3'b000),
        .i_read_data_o(selected_i_data),
        .i_read_valid_o(selected_i_valid),
        .m_read_data_o(unused_m_read_data),
        .m_read_valid_o(unused_m_read_valid),
        .l_read_data_o(unused_l_read_data),
        .l_read_valid_o(unused_l_read_valid),
        .probe_address_i({1'b1, i_probe_local_i}),
        .probe_i_data_o(i_probe_data_o),
        .probe_i_valid_o(i_probe_valid_o),
        .probe_m_data_o(unused_probe_m_data),
        .probe_m_valid_o(unused_probe_m_valid),
        .probe_l_data_o(unused_probe_l_data),
        .probe_l_valid_o(unused_probe_l_valid),
        .setup_write_i(i_setup_enable),
        .setup_kind_i(2'b00),
        .setup_address_i({1'b1, i_setup_local_i}),
        .setup_data_i(i_setup_data_i),
        .i_write_enable_i(1'b0),
        .i_write_address_i(3'b000),
        .i_write_data_i(14'h0000),
        .i_write_result_valid_i(1'b0),
        .invalid_setup_kind_o(dag_invalid_setup_kind),
        .write_conflict_o(dag_write_conflict)
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pc_q <= 14'h0004;
            astat_valid_q <= 1'b0;
        end else begin
            if (pc_setup_enable) begin
                pc_q <= pc_setup_data_i;
            end else if (boundary_valid_o) begin
                pc_q <= condition_true_o ? selected_i_data : sequential_pc;
            end
            if (astat_setup_enable) begin
                astat_q <= astat_setup_data_i;
                astat_valid_q <= 1'b1;
            end
        end
    end

    always_comb begin
        assert (!(pc_stack_push_o && !call_o));
        assert (!(counter_test_o && (call_o || condition_o != 4'he)));
        assert (!(pc_stack_push_o && counter_test_o));
        assert (pma_indirect_drive_o == condition_true_o);
        assert (!pma_indirect_drive_o || indirect_address_valid_o);
        assert (!pm_data_access_o && !dm_access_o);
        if (!boundary_valid_o) begin
            assert (!pc_write_o && !pc_stack_push_o && !counter_test_o);
        end
    end
endmodule

`default_nettype wire
