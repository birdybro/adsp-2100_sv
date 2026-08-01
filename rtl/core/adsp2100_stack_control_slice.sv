`default_nettype none

module adsp2100_stack_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        astat_write_i,
    input  logic [7:0]  astat_write_data_i,
    input  logic        mstat_write_i,
    input  logic [3:0]  mstat_write_data_i,
    input  logic        imask_write_i,
    input  logic [3:0]  imask_write_data_i,
    input  logic        counter_load_i,
    input  logic [13:0] counter_load_data_i,
    input  logic        pc_push_i,
    input  logic [13:0] pc_push_data_i,
    input  logic        loop_push_i,
    input  logic [17:0] loop_push_data_i,

    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic [1:0]  status_operation_o,
    output logic        count_pop_o,
    output logic        loop_pop_o,
    output logic        pc_pop_o,
    output logic        has_effect_o,

    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [3:0]  imask_o,
    output logic        alternate_bank_o,
    output logic        bit_reverse_o,
    output logic        overflow_latch_o,
    output logic        saturate_ar_o,
    output logic [13:0] cntr_data_o,
    output logic        cntr_valid_o,
    output logic        counter_restore_o,
    output logic        counter_empty_manual_pop_o,

    output logic [13:0] pc_top_data_o,
    output logic [13:0] count_top_data_o,
    output logic [17:0] loop_top_data_o,
    output logic [15:0] status_top_data_o,
    output logic [3:0]  stack_top_valid_o,
    output logic [4:0]  pc_depth_o,
    output logic [2:0]  count_depth_o,
    output logic [2:0]  loop_depth_o,
    output logic [2:0]  status_depth_o,
    output logic [3:0]  stack_empty_o,
    output logic [3:0]  stack_overflow_o,
    output logic [3:0]  stack_pop_valid_o,
    output logic [3:0]  stack_push_accepted_o,
    output logic [3:0]  stack_overflow_event_o,
    output logic [3:0]  stack_empty_pop_o,
    output logic [7:0]  sstat_o
);
    logic       decode_valid;
    logic [1:0] decoded_status_operation;
    logic       decoded_count_pop;
    logic       decoded_loop_pop;
    logic       decoded_pc_pop;
    logic       decoded_has_effect;
    logic       setup_action;

    logic       effective_astat_write;
    logic       effective_mstat_write;
    logic       effective_imask_write;
    logic       effective_counter_load;
    logic       effective_pc_push;
    logic       effective_loop_push;

    logic [4:0] icntl_unused;
    logic       status_register_conflict;
    logic       interrupt_status_push_unused;
    logic [7:0] interrupt_push_astat_unused;
    logic [3:0] interrupt_push_mstat_unused;
    logic [3:0] interrupt_push_imask_unused;

    logic [1:0] status_stack_operation;
    logic [15:0] status_stack_push_data;
    logic [15:0] status_stack_pop_data;
    logic       status_stack_pop_valid;
    logic       status_stack_empty;
    logic       status_stack_overflow;
    logic [2:0] status_stack_depth;
    logic       status_stack_push_accepted;
    logic       status_stack_overflow_event;
    logic       status_stack_empty_pop;

    logic       counter_condition_valid_unused;
    logic       counter_expired_unused;
    logic       not_counter_expired_unused;
    logic       count_stack_push;
    logic [13:0] count_stack_push_data;
    logic       count_stack_pop;
    logic       counter_decrement_unused;
    logic       counter_empty_ce_unused;
    logic       counter_invalid_ce_unused;
    logic       counter_conflict;

    logic       pc_top_valid;
    logic       count_top_valid;
    logic       loop_top_valid;
    logic       pc_pop_valid;
    logic       count_pop_valid;
    logic       loop_pop_valid;
    logic       pc_empty;
    logic       count_empty;
    logic       loop_empty;
    logic       pc_overflow;
    logic       count_overflow;
    logic       loop_overflow;
    logic       pc_push_accepted;
    logic       count_push_accepted;
    logic       loop_push_accepted;
    logic       pc_overflow_event;
    logic       count_overflow_event;
    logic       loop_overflow_event;
    logic       pc_empty_pop;
    logic       count_empty_pop;
    logic       loop_empty_pop;
    logic [7:0] sequencer_sstat;
    logic       sequencer_stack_conflict;

    adsp2100_stack_control_decode decode (
        .opcode_i(opcode_i),
        .valid_o(decode_valid),
        .status_operation_o(decoded_status_operation),
        .count_pop_o(decoded_count_pop),
        .loop_pop_o(decoded_loop_pop),
        .pc_pop_o(decoded_pc_pop),
        .has_effect_o(decoded_has_effect)
    );

    assign setup_action = (
        astat_write_i
        || mstat_write_i
        || imask_write_i
        || counter_load_i
        || pc_push_i
        || loop_push_i
    );
    assign invalid_opcode_o = (
        execute_i
        && !decode_valid
        && !reset_i
    );
    // A verified Type 26 instruction cannot also be a setup/load/automatic
    // stack action. Until interrupt-abort integration exists, such competing
    // requests fail closed atomically rather than receiving an invented
    // priority (OQ-018).
    assign integration_conflict_o = (
        execute_i
        && setup_action
        && !reset_i
    );
    assign boundary_valid_o = (
        execute_i
        && decode_valid
        && !integration_conflict_o
        && !reset_i
    );
    assign status_operation_o = (
        boundary_valid_o ? decoded_status_operation : 2'b00
    );
    assign count_pop_o = boundary_valid_o && decoded_count_pop;
    assign loop_pop_o = boundary_valid_o && decoded_loop_pop;
    assign pc_pop_o = boundary_valid_o && decoded_pc_pop;
    assign has_effect_o = boundary_valid_o && decoded_has_effect;

    assign effective_astat_write = (
        astat_write_i && !integration_conflict_o
    );
    assign effective_mstat_write = (
        mstat_write_i && !integration_conflict_o
    );
    assign effective_imask_write = (
        imask_write_i && !integration_conflict_o
    );
    assign effective_counter_load = (
        counter_load_i && !integration_conflict_o
    );
    assign effective_pc_push = pc_push_i && !integration_conflict_o;
    assign effective_loop_push = loop_push_i && !integration_conflict_o;

    assign status_stack_operation = status_operation_o;
    assign status_stack_push_data = {astat_o, mstat_o, imask_o};

    adsp2100_status_stack status_stack (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .operation_i(status_stack_operation),
        .push_data_i(status_stack_push_data),
        .pop_data_o(status_stack_pop_data),
        .pop_valid_o(status_stack_pop_valid),
        .empty_o(status_stack_empty),
        .overflow_o(status_stack_overflow),
        .depth_o(status_stack_depth),
        .push_accepted_o(status_stack_push_accepted),
        .overflow_event_o(status_stack_overflow_event),
        .empty_pop_o(status_stack_empty_pop)
    );

    adsp2100_status_registers status_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(effective_astat_write),
        .astat_move_write_data_i(astat_write_data_i),
        .mstat_move_write_enable_i(effective_mstat_write),
        .mstat_move_write_data_i(mstat_write_data_i),
        .icntl_move_write_enable_i(1'b0),
        .icntl_move_write_data_i(5'b00000),
        .imask_move_write_enable_i(effective_imask_write),
        .imask_move_write_data_i(imask_write_data_i),
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
        .status_restore_i(status_stack_pop_valid),
        .restore_astat_i(status_stack_pop_data[15:8]),
        .restore_mstat_i(status_stack_pop_data[7:4]),
        .restore_imask_i(status_stack_pop_data[3:0]),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_unused),
        .imask_o(imask_o),
        .alternate_bank_o(alternate_bank_o),
        .bit_reverse_o(bit_reverse_o),
        .overflow_latch_o(overflow_latch_o),
        .saturate_ar_o(saturate_ar_o),
        .write_conflict_o(status_register_conflict),
        .status_push_o(interrupt_status_push_unused),
        .status_push_astat_o(interrupt_push_astat_unused),
        .status_push_mstat_o(interrupt_push_mstat_unused),
        .status_push_imask_o(interrupt_push_imask_unused)
    );

    adsp2100_counter counter (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .load_i(effective_counter_load),
        .invalidate_i(1'b0),
        .load_data_i(counter_load_data_i),
        .ce_test_i(1'b0),
        .manual_pop_i(count_pop_o),
        .count_stack_top_data_i(count_top_data_o),
        .count_stack_top_valid_i(count_top_valid),
        .cntr_data_o(cntr_data_o),
        .cntr_valid_o(cntr_valid_o),
        .condition_valid_o(counter_condition_valid_unused),
        .counter_expired_o(counter_expired_unused),
        .not_counter_expired_o(not_counter_expired_unused),
        .count_stack_push_o(count_stack_push),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_pop_o(count_stack_pop),
        .decrement_o(counter_decrement_unused),
        .restore_o(counter_restore_o),
        .empty_ce_invalidate_o(counter_empty_ce_unused),
        .invalid_ce_test_o(counter_invalid_ce_unused),
        .empty_manual_pop_o(counter_empty_manual_pop_o),
        .write_conflict_o(counter_conflict)
    );

    adsp2100_sequencer_stacks sequencer_stacks (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .pc_push_i(effective_pc_push),
        .pc_pop_i(pc_pop_o),
        .pc_push_data_i(pc_push_data_i),
        .pc_top_data_o(pc_top_data_o),
        .pc_top_valid_o(pc_top_valid),
        .pc_pop_valid_o(pc_pop_valid),
        .pc_empty_o(pc_empty),
        .pc_overflow_o(pc_overflow),
        .pc_depth_o(pc_depth_o),
        .pc_push_accepted_o(pc_push_accepted),
        .pc_overflow_event_o(pc_overflow_event),
        .pc_empty_pop_o(pc_empty_pop),
        .count_push_i(count_stack_push),
        .count_pop_i(count_stack_pop),
        .count_push_data_i(count_stack_push_data),
        .count_top_data_o(count_top_data_o),
        .count_top_valid_o(count_top_valid),
        .count_pop_valid_o(count_pop_valid),
        .count_empty_o(count_empty),
        .count_overflow_o(count_overflow),
        .count_depth_o(count_depth_o),
        .count_push_accepted_o(count_push_accepted),
        .count_overflow_event_o(count_overflow_event),
        .count_empty_pop_o(count_empty_pop),
        .loop_push_i(effective_loop_push),
        .loop_pop_i(loop_pop_o),
        .loop_push_data_i(loop_push_data_i),
        .loop_top_data_o(loop_top_data_o),
        .loop_top_valid_o(loop_top_valid),
        .loop_pop_valid_o(loop_pop_valid),
        .loop_empty_o(loop_empty),
        .loop_overflow_o(loop_overflow),
        .loop_depth_o(loop_depth_o),
        .loop_push_accepted_o(loop_push_accepted),
        .loop_overflow_event_o(loop_overflow_event),
        .loop_empty_pop_o(loop_empty_pop),
        .sstat_fragment_o(sequencer_sstat),
        .write_conflict_o(sequencer_stack_conflict)
    );

    assign status_top_data_o = status_stack_pop_data;
    assign status_depth_o = status_stack_depth;
    assign stack_top_valid_o = {
        !status_stack_empty,
        loop_top_valid,
        count_top_valid,
        pc_top_valid
    };
    assign stack_empty_o = {
        status_stack_empty,
        loop_empty,
        count_empty,
        pc_empty
    };
    assign stack_overflow_o = {
        status_stack_overflow,
        loop_overflow,
        count_overflow,
        pc_overflow
    };
    assign stack_pop_valid_o = {
        status_stack_pop_valid,
        loop_pop_valid,
        count_pop_valid,
        pc_pop_valid
    };
    assign stack_push_accepted_o = {
        status_stack_push_accepted,
        loop_push_accepted,
        count_push_accepted,
        pc_push_accepted
    };
    assign stack_overflow_event_o = {
        status_stack_overflow_event,
        loop_overflow_event,
        count_overflow_event,
        pc_overflow_event
    };
    assign stack_empty_pop_o = {
        status_stack_empty_pop,
        loop_empty_pop,
        count_empty_pop,
        pc_empty_pop
    };
    assign sstat_o = (
        sequencer_sstat
        | {
            2'b00,
            status_stack_overflow,
            status_stack_empty,
            4'b0000
        }
    );
    assign internal_conflict_o = (
        status_register_conflict
        || counter_conflict
        || sequencer_stack_conflict
    );
endmodule

`default_nettype wire
