`default_nettype none

module adsp2100_conditional_return_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        pc_setup_write_i,
    input  logic [13:0] pc_setup_data_i,
    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        imask_setup_write_i,
    input  logic [3:0]  imask_setup_data_i,
    input  logic        counter_setup_write_i,
    input  logic [13:0] counter_setup_data_i,
    input  logic        pc_stack_setup_push_i,
    input  logic [13:0] pc_stack_setup_data_i,
    input  logic        status_stack_setup_push_i,
    input  logic [15:0] status_stack_setup_data_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        interrupt_return_o,
    output logic [3:0]  condition_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        invalid_condition_state_o,
    output logic        invalid_return_context_o,
    output logic        condition_known_o,
    output logic        condition_true_o,
    output logic [13:0] pc_o,
    output logic        pc_write_o,
    output logic        explicit_transfer_o,
    output logic        pc_stack_pop_o,
    output logic        pc_stack_pop_valid_o,
    output logic [13:0] pc_stack_top_o,
    output logic        pc_stack_top_valid_o,
    output logic [4:0]  pc_stack_depth_o,
    output logic        pc_stack_overflow_o,
    output logic        status_stack_pop_o,
    output logic        status_stack_pop_valid_o,
    output logic [15:0] status_stack_top_o,
    output logic        status_stack_top_valid_o,
    output logic [2:0]  status_stack_depth_o,
    output logic        status_stack_overflow_o,
    output logic        status_restored_o,
    output logic [7:0]  astat_o,
    output logic        astat_valid_o,
    output logic [3:0]  mstat_o,
    output logic [3:0]  imask_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic        counter_test_o,
    output logic        counter_decrement_o,
    output logic        counter_restore_o,
    output logic        count_stack_push_o,
    output logic [13:0] count_stack_top_o,
    output logic        count_stack_top_valid_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,
    output logic [7:0]  sstat_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    localparam logic [1:0] STATUS_NO_CHANGE = 2'b00;
    localparam logic [1:0] STATUS_PUSH = 2'b10;
    localparam logic [1:0] STATUS_POP = 2'b11;

    logic [13:0] pc_q;
    logic        astat_valid_q;
    logic [3:0]  setup_count;
    logic        pc_setup_enable;
    logic        astat_setup_enable;
    logic        mstat_setup_enable;
    logic        imask_setup_enable;
    logic        counter_setup_enable;
    logic        pc_stack_setup_enable;
    logic        status_stack_setup_enable;
    logic        raw_condition_true;
    logic        raw_condition_known;
    logic        condition_context_valid;
    logic        return_context_valid;
    logic [13:0] sequential_pc;
    logic        not_counter_expired;

    logic [1:0]  status_stack_operation;
    logic [15:0] status_stack_pop_data;
    logic        status_stack_empty;
    logic        status_stack_push_accepted;
    logic        status_stack_overflow_event;
    logic        status_stack_empty_pop;

    logic [4:0]  icntl_unused;
    logic        alternate_bank_unused;
    logic        bit_reverse_unused;
    logic        overflow_latch_unused;
    logic        saturate_ar_unused;
    logic        status_register_conflict;
    logic        status_push_unused;
    logic [7:0]  status_push_astat_unused;
    logic [3:0]  status_push_mstat_unused;
    logic [3:0]  status_push_imask_unused;

    logic        counter_condition_valid_unused;
    logic        counter_expired_unused;
    logic        counter_not_expired_unused;
    logic [13:0] count_stack_push_data;
    logic        count_stack_pop_unused;
    logic        counter_decrement_unused;
    logic        counter_restore_unused;
    logic        counter_empty_ce_unused;
    logic        counter_invalid_ce_unused;
    logic        counter_empty_manual_unused;
    logic        counter_conflict;

    logic        pc_stack_empty;
    logic        pc_stack_push_accepted;
    logic        pc_stack_overflow_event;
    logic        pc_stack_empty_pop;
    logic        count_stack_empty;
    logic        count_stack_pop_valid_unused;
    logic        count_stack_push_accepted;
    logic        count_stack_overflow_event;
    logic        count_stack_empty_pop;
    logic [17:0] loop_stack_top_unused;
    logic        loop_stack_top_valid_unused;
    logic        loop_stack_pop_valid_unused;
    logic        loop_stack_empty;
    logic        loop_stack_overflow;
    logic [2:0]  loop_stack_depth_unused;
    logic        loop_stack_push_accepted_unused;
    logic        loop_stack_overflow_event_unused;
    logic        loop_stack_empty_pop_unused;
    logic [7:0]  sequencer_sstat;
    logic        sequencer_stack_conflict;

    adsp2100_conditional_return_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .interrupt_return_o(interrupt_return_o),
        .condition_o(condition_o)
    );

    assign setup_count = (
        {3'b000, pc_setup_write_i}
        + {3'b000, astat_setup_write_i}
        + {3'b000, mstat_setup_write_i}
        + {3'b000, imask_setup_write_i}
        + {3'b000, counter_setup_write_i}
        + {3'b000, pc_stack_setup_push_i}
        + {3'b000, status_stack_setup_push_i}
    );
    assign integration_conflict_o = !reset_i && (
        (execute_i && setup_count != 4'd0) || setup_count > 4'd1
    );
    assign pc_setup_enable = (
        !reset_i && !execute_i && setup_count == 4'd1 && pc_setup_write_i
    );
    assign astat_setup_enable = (
        !reset_i && !execute_i && setup_count == 4'd1 && astat_setup_write_i
    );
    assign mstat_setup_enable = (
        !reset_i && !execute_i && setup_count == 4'd1 && mstat_setup_write_i
    );
    assign imask_setup_enable = (
        !reset_i && !execute_i && setup_count == 4'd1 && imask_setup_write_i
    );
    assign counter_setup_enable = (
        !reset_i && !execute_i && setup_count == 4'd1 && counter_setup_write_i
    );
    assign pc_stack_setup_enable = (
        !reset_i && !execute_i && setup_count == 4'd1
        && pc_stack_setup_push_i
    );
    assign status_stack_setup_enable = (
        !reset_i && !execute_i && setup_count == 4'd1
        && status_stack_setup_push_i
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
    assign return_context_valid = (
        pc_stack_top_valid_o
        && (!interrupt_return_o || status_stack_top_valid_o)
    );
    assign invalid_return_context_o = (
        condition_context_valid && raw_condition_true && !return_context_valid
    );
    assign boundary_valid_o = (
        condition_context_valid && !invalid_return_context_o
    );
    assign invalid_opcode_o = !reset_i && execute_i && !class_valid_o;
    assign invalid_condition_state_o = (
        !reset_i && execute_i && action_valid_o
        && !integration_conflict_o && !raw_condition_known
    );
    assign condition_known_o = condition_context_valid;
    assign condition_true_o = boundary_valid_o && raw_condition_true;
    assign sequential_pc = pc_q + 14'h0001;
    assign pc_write_o = boundary_valid_o;
    assign explicit_transfer_o = condition_true_o;
    assign pc_stack_pop_o = condition_true_o;
    assign status_stack_pop_o = condition_true_o && interrupt_return_o;
    assign status_restored_o = status_stack_pop_valid_o;
    assign counter_test_o = 1'b0;
    assign counter_decrement_o = 1'b0;
    assign counter_restore_o = 1'b0;
    assign not_counter_expired = (cntr_o != 14'h0001);
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    adsp2100_condition_logic condition_logic (
        .condition_i(condition_o),
        .az_i(astat_o[0]),
        .an_i(astat_o[1]),
        .av_i(astat_o[2]),
        .ac_i(astat_o[3]),
        .as_i(astat_o[4]),
        .mv_i(astat_o[6]),
        .not_counter_expired_i(not_counter_expired),
        .condition_true_o(raw_condition_true)
    );

    assign status_stack_operation = status_stack_setup_enable
        ? STATUS_PUSH
        : (status_stack_pop_o ? STATUS_POP : STATUS_NO_CHANGE);

    adsp2100_status_stack status_stack (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .operation_i(status_stack_operation),
        .push_data_i(status_stack_setup_data_i),
        .pop_data_o(status_stack_pop_data),
        .pop_valid_o(status_stack_pop_valid_o),
        .empty_o(status_stack_empty),
        .overflow_o(status_stack_overflow_o),
        .depth_o(status_stack_depth_o),
        .push_accepted_o(status_stack_push_accepted),
        .overflow_event_o(status_stack_overflow_event),
        .empty_pop_o(status_stack_empty_pop)
    );
    assign status_stack_top_o = status_stack_pop_data;
    assign status_stack_top_valid_o = !status_stack_empty;

    adsp2100_status_registers status_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(astat_setup_enable),
        .astat_move_write_data_i(astat_setup_data_i),
        .mstat_move_write_enable_i(mstat_setup_enable),
        .mstat_move_write_data_i(mstat_setup_data_i),
        .icntl_move_write_enable_i(1'b0),
        .icntl_move_write_data_i(5'b00000),
        .imask_move_write_enable_i(imask_setup_enable),
        .imask_move_write_data_i(imask_setup_data_i),
        .mode_sr_i(2'b00),
        .mode_br_i(2'b00),
        .mode_ol_i(2'b00),
        .mode_as_i(2'b00),
        .alu_status_write_enable_i(1'b0),
        .alu_az_i(1'b0),
        .alu_an_i(1'b0),
        .alu_av_i(1'b0),
        .alu_ac_i(1'b0),
        .alu_as_write_enable_i(1'b0),
        .alu_as_i(1'b0),
        .divide_status_write_enable_i(1'b0),
        .divide_aq_i(1'b0),
        .mac_status_write_enable_i(1'b0),
        .mac_mv_i(1'b0),
        .shifter_status_write_enable_i(1'b0),
        .shifter_ss_i(1'b0),
        .interrupt_entry_i(1'b0),
        .interrupt_level_i(2'b00),
        .status_restore_i(status_stack_pop_valid_o),
        .restore_astat_i(status_stack_pop_data[15:8]),
        .restore_mstat_i(status_stack_pop_data[7:4]),
        .restore_imask_i(status_stack_pop_data[3:0]),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_unused),
        .imask_o(imask_o),
        .alternate_bank_o(alternate_bank_unused),
        .bit_reverse_o(bit_reverse_unused),
        .overflow_latch_o(overflow_latch_unused),
        .saturate_ar_o(saturate_ar_unused),
        .write_conflict_o(status_register_conflict),
        .status_push_o(status_push_unused),
        .status_push_astat_o(status_push_astat_unused),
        .status_push_mstat_o(status_push_mstat_unused),
        .status_push_imask_o(status_push_imask_unused)
    );

    adsp2100_counter counter (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .load_i(counter_setup_enable),
        .invalidate_i(1'b0),
        .load_data_i(counter_setup_data_i),
        .ce_test_i(1'b0),
        .manual_pop_i(1'b0),
        .count_stack_top_data_i(count_stack_top_o),
        .count_stack_top_valid_i(count_stack_top_valid_o),
        .cntr_data_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .condition_valid_o(counter_condition_valid_unused),
        .counter_expired_o(counter_expired_unused),
        .not_counter_expired_o(counter_not_expired_unused),
        .count_stack_push_o(count_stack_push_o),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_pop_o(count_stack_pop_unused),
        .decrement_o(counter_decrement_unused),
        .restore_o(counter_restore_unused),
        .empty_ce_invalidate_o(counter_empty_ce_unused),
        .invalid_ce_test_o(counter_invalid_ce_unused),
        .empty_manual_pop_o(counter_empty_manual_unused),
        .write_conflict_o(counter_conflict)
    );

    adsp2100_sequencer_stacks sequencer_stacks (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .pc_push_i(pc_stack_setup_enable),
        .pc_pop_i(pc_stack_pop_o),
        .pc_push_data_i(pc_stack_setup_data_i),
        .pc_top_data_o(pc_stack_top_o),
        .pc_top_valid_o(pc_stack_top_valid_o),
        .pc_pop_valid_o(pc_stack_pop_valid_o),
        .pc_empty_o(pc_stack_empty),
        .pc_overflow_o(pc_stack_overflow_o),
        .pc_depth_o(pc_stack_depth_o),
        .pc_push_accepted_o(pc_stack_push_accepted),
        .pc_overflow_event_o(pc_stack_overflow_event),
        .pc_empty_pop_o(pc_stack_empty_pop),
        .count_push_i(count_stack_push_o),
        .count_pop_i(1'b0),
        .count_push_data_i(count_stack_push_data),
        .count_top_data_o(count_stack_top_o),
        .count_top_valid_o(count_stack_top_valid_o),
        .count_pop_valid_o(count_stack_pop_valid_unused),
        .count_empty_o(count_stack_empty),
        .count_overflow_o(count_stack_overflow_o),
        .count_depth_o(count_stack_depth_o),
        .count_push_accepted_o(count_stack_push_accepted),
        .count_overflow_event_o(count_stack_overflow_event),
        .count_empty_pop_o(count_stack_empty_pop),
        .loop_push_i(1'b0),
        .loop_pop_i(1'b0),
        .loop_push_data_i(18'h00000),
        .loop_top_data_o(loop_stack_top_unused),
        .loop_top_valid_o(loop_stack_top_valid_unused),
        .loop_pop_valid_o(loop_stack_pop_valid_unused),
        .loop_empty_o(loop_stack_empty),
        .loop_overflow_o(loop_stack_overflow),
        .loop_depth_o(loop_stack_depth_unused),
        .loop_push_accepted_o(loop_stack_push_accepted_unused),
        .loop_overflow_event_o(loop_stack_overflow_event_unused),
        .loop_empty_pop_o(loop_stack_empty_pop_unused),
        .sstat_fragment_o(sequencer_sstat),
        .write_conflict_o(sequencer_stack_conflict)
    );

    assign sstat_o = (
        sequencer_sstat
        | {2'b00, status_stack_overflow_o, status_stack_empty, 4'b0000}
    );
    assign internal_conflict_o = (
        status_register_conflict || counter_conflict
        || sequencer_stack_conflict
    );
    assign pc_o = pc_q;
    assign astat_valid_o = astat_valid_q;

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pc_q <= 14'h0004;
            astat_valid_q <= 1'b0;
        end else begin
            if (pc_setup_enable) begin
                pc_q <= pc_setup_data_i;
            end else if (boundary_valid_o) begin
                pc_q <= condition_true_o ? pc_stack_top_o : sequential_pc;
            end
            if (astat_setup_enable || status_stack_pop_valid_o) begin
                astat_valid_q <= 1'b1;
            end
        end
    end

    always_comb begin
        assert (action_valid_o == class_valid_o);
        assert (pc_stack_pop_o == explicit_transfer_o);
        assert (!status_stack_pop_o || (pc_stack_pop_o && interrupt_return_o));
        assert (status_restored_o == status_stack_pop_valid_o);
        assert (pc_stack_top_valid_o == !pc_stack_empty);
        assert (count_stack_top_valid_o == !count_stack_empty);
        assert (status_stack_top_valid_o == !status_stack_empty);
        assert (!status_stack_push_accepted || status_stack_setup_enable);
        assert (!status_stack_overflow_event || status_stack_setup_enable);
        assert (!pc_stack_push_accepted || pc_stack_setup_enable);
        assert (!pc_stack_overflow_event || pc_stack_setup_enable);
        assert (!count_stack_push_accepted || count_stack_push_o);
        assert (!count_stack_overflow_event || count_stack_push_o);
        assert (!(status_stack_empty_pop || pc_stack_empty_pop));
        assert (!count_stack_empty_pop);
        assert (sequencer_sstat[6] == loop_stack_empty);
        assert (sequencer_sstat[7] == loop_stack_overflow);
        assert (!(counter_test_o || counter_decrement_o || counter_restore_o));
        assert (!(counter_decrement_unused || counter_restore_unused));
        assert (!pm_data_access_o && !dm_access_o);
        if (!boundary_valid_o) begin
            assert (!pc_write_o && !pc_stack_pop_o && !status_stack_pop_o);
        end
    end
endmodule

`default_nettype wire
