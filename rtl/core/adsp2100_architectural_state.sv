`default_nettype none

// Shared original-ADSP-2100 architectural state boundary.
//
// This boundary exposes the complete general-register selector used by Type
// 17 and deterministic setup together with execution-facing DREG,
// computational-unit, DAG-I, status, and mode actions. Memory transactions
// and sequencer/interrupt actions remain separate clients of this owner.
module adsp2100_architectural_state (
    input  logic        clk_i,
    input  logic        reset_i,

    input  logic        move_write_i,
    input  logic        move_data_valid_i,
    input  logic [5:0]  move_code_i,
    input  logic [15:0] move_data_i,

    input  logic [5:0]  read_code_i,
    output logic [15:0] read_data_o,
    input  logic [5:0]  probe_code_i,
    output logic [15:0] probe_data_o,

    // Parallel execution actions. These ports expose the already-verified
    // register, DAG, and status primitives through this single state owner.
    // All reads observe cycle-start state; accepted writes become visible
    // after the active edge.
    input  logic [3:0]  dreg_read_address_i,
    output logic [15:0] dreg_read_data_o,
    input  logic        dreg_write_enable_1_i,
    input  logic [3:0]  dreg_write_address_1_i,
    input  logic [15:0] dreg_write_data_1_i,
    input  logic        dreg_write_enable_2_i,
    input  logic [3:0]  dreg_write_address_2_i,
    input  logic [15:0] dreg_write_data_2_i,

    input  logic        alu_write_enable_i,
    input  logic        alu_destination_feedback_i,
    input  logic [15:0] alu_result_i,
    input  logic        mac_write_enable_i,
    input  logic        mac_destination_feedback_i,
    input  logic [39:0] mac_result_i,
    input  logic        shifter_sr_write_enable_i,
    input  logic [31:0] shifter_sr_result_i,
    input  logic        shifter_se_write_enable_i,
    input  logic [7:0]  shifter_se_result_i,
    input  logic        shifter_sb_write_enable_i,
    input  logic [4:0]  shifter_sb_result_i,

    input  logic        dag_i_write_enable_i,
    input  logic [2:0]  dag_i_write_address_i,
    input  logic [13:0] dag_i_write_data_i,
    input  logic        dag_i_write_result_valid_i,

    input  logic [1:0]  mode_sr_i,
    input  logic [1:0]  mode_br_i,
    input  logic [1:0]  mode_ol_i,
    input  logic [1:0]  mode_as_i,
    input  logic        alu_status_write_enable_i,
    input  logic        alu_az_i,
    input  logic        alu_an_i,
    input  logic        alu_av_i,
    input  logic        alu_ac_i,
    input  logic        alu_as_write_enable_i,
    input  logic        alu_as_i,
    input  logic        divide_status_write_enable_i,
    input  logic        divide_aq_i,
    input  logic        mac_status_write_enable_i,
    input  logic        mac_mv_i,
    input  logic        shifter_status_write_enable_i,
    input  logic        shifter_ss_i,

    output logic        invalid_move_write_o,
    output logic        internal_conflict_o,
    output logic        count_stack_push_o,
    output logic [13:0] count_stack_push_data_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [4:0]  icntl_o,
    output logic [3:0]  imask_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic [7:0]  px_o,
    output logic [7:0]  sstat_o,
    output logic        alternate_bank_o,
    output logic        bit_reverse_o,
    output logic        overflow_latch_o,
    output logic        saturate_ar_o,
    output logic [15:0] af_o,
    output logic [15:0] mf_o,
    output logic [39:0] mr_o,
    output logic [7:0]  se_o,
    output logic [4:0]  sb_o,
    output logic [31:0] sr_o
);
    logic       move_present;
    logic       move_writable;
    logic       state_write;
    logic [1:0] write_group;
    logic [3:0] write_index;

    logic [15:0] read_dreg_data;
    logic [15:0] probe_dreg_data;
    logic        register_conflict;

    logic [2:0]  read_dag_address;
    logic [13:0] read_i_data;
    logic        unused_read_i_valid;
    logic [13:0] read_m_data;
    logic        unused_read_m_valid;
    logic [13:0] read_l_data;
    logic        unused_read_l_valid;
    logic [2:0]  probe_dag_address;
    logic [13:0] probe_i_data;
    logic        unused_probe_i_valid;
    logic [13:0] probe_m_data;
    logic        unused_probe_m_valid;
    logic [13:0] probe_l_data;
    logic        unused_probe_l_valid;
    logic [1:0]  dag_write_kind;
    logic [2:0]  dag_write_address;
    logic        unused_dag_invalid_setup;
    logic        dag_conflict;

    logic        status_conflict;
    logic        unused_status_push;
    logic [7:0]  unused_status_push_astat;
    logic [3:0]  unused_status_push_mstat;
    logic [3:0]  unused_status_push_imask;

    logic [13:0] count_stack_top;
    logic        count_stack_top_valid;
    logic        count_stack_pop;
    logic [13:0] counter_push_data;
    logic [7:0]  sequencer_sstat;
    logic        sequencer_stack_conflict;
    logic        status_stack_empty;
    logic        status_stack_overflow;
    logic [15:0] unused_status_pop_data;
    logic        unused_status_pop_valid;
    logic [2:0]  unused_status_depth;
    logic        unused_status_push_accepted;
    logic        unused_status_overflow_event;
    logic        unused_status_empty_pop;
    logic        counter_conflict;
    logic        unused_counter_condition_valid;
    logic        unused_counter_expired;
    logic        unused_not_counter_expired;
    logic        unused_counter_decrement;
    logic        unused_counter_restore;
    logic        unused_empty_ce_invalidate;
    logic        unused_invalid_ce_test;
    logic        unused_empty_manual_pop;
    logic [13:0] unused_pc_top;
    logic        unused_pc_top_valid;
    logic        unused_pc_pop_valid;
    logic        unused_pc_empty;
    logic        unused_pc_overflow;
    logic [4:0]  unused_pc_depth;
    logic        unused_pc_push_accepted;
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
    logic [7:0]  px_q;

    function automatic logic selector_present (
        input logic [1:0] group,
        input logic [3:0] index
    );
        case (group)
            2'b00: selector_present = 1'b1;
            2'b01,
            2'b10: selector_present = index < 4'd12;
            2'b11: selector_present = index < 4'd8;
            default: selector_present = 1'b0;
        endcase
    endfunction

    function automatic logic [1:0] dag_kind (
        input logic [3:0] index
    );
        if (index < 4'd4) begin
            dag_kind = 2'b00;
        end else if (index < 4'd8) begin
            dag_kind = 2'b01;
        end else begin
            dag_kind = 2'b10;
        end
    endfunction

    assign move_present = selector_present(
        move_code_i[5:4], move_code_i[3:0]
    );
    assign move_writable = move_present && (move_code_i != 6'h32);
    assign invalid_move_write_o = (
        !reset_i && move_write_i && !move_writable
    );
    assign state_write = !reset_i && move_write_i && move_writable;
    assign write_group = move_code_i[5:4];
    assign write_index = move_code_i[3:0];
    assign read_dag_address = {
        read_code_i[5:4] == 2'b10,
        read_code_i[1:0]
    };
    assign probe_dag_address = {
        probe_code_i[5:4] == 2'b10,
        probe_code_i[1:0]
    };
    assign dag_write_address = {
        write_group == 2'b10,
        write_index[1:0]
    };
    assign dag_write_kind = dag_kind(write_index);

    // OQ-016 provisional behavior remains isolated at this selector boundary.
    // Narrow status/control reads are zero-extended; M is sign-extended.
    always_comb begin
        read_data_o = 16'h0000;
        unique case (read_code_i[5:4])
            2'b00: read_data_o = read_dreg_data;
            2'b01,
            2'b10: begin
                if (read_code_i[3:0] < 4'd4) begin
                    read_data_o = {2'b00, read_i_data};
                end else if (read_code_i[3:0] < 4'd8) begin
                    read_data_o = {{2{read_m_data[13]}}, read_m_data};
                end else if (read_code_i[3:0] < 4'd12) begin
                    read_data_o = {2'b00, read_l_data};
                end
            end
            2'b11: begin
                unique case (read_code_i[3:0])
                    4'd0: read_data_o = {8'h00, astat_o};
                    4'd1: read_data_o = {12'h000, mstat_o};
                    4'd2: read_data_o = {8'h00, sstat_o};
                    4'd3: read_data_o = {12'h000, imask_o};
                    4'd4: read_data_o = {11'h000, icntl_o};
                    4'd5: read_data_o = {2'b00, cntr_o};
                    4'd6: read_data_o = {{11{sb_o[4]}}, sb_o};
                    4'd7: read_data_o = {8'h00, px_q};
                    default: read_data_o = 16'h0000;
                endcase
            end
            default: read_data_o = 16'h0000;
        endcase
    end

    always_comb begin
        probe_data_o = 16'h0000;
        unique case (probe_code_i[5:4])
            2'b00: probe_data_o = probe_dreg_data;
            2'b01,
            2'b10: begin
                if (probe_code_i[3:0] < 4'd4) begin
                    probe_data_o = {2'b00, probe_i_data};
                end else if (probe_code_i[3:0] < 4'd8) begin
                    probe_data_o = {{2{probe_m_data[13]}}, probe_m_data};
                end else if (probe_code_i[3:0] < 4'd12) begin
                    probe_data_o = {2'b00, probe_l_data};
                end
            end
            2'b11: begin
                unique case (probe_code_i[3:0])
                    4'd0: probe_data_o = {8'h00, astat_o};
                    4'd1: probe_data_o = {12'h000, mstat_o};
                    4'd2: probe_data_o = {8'h00, sstat_o};
                    4'd3: probe_data_o = {12'h000, imask_o};
                    4'd4: probe_data_o = {11'h000, icntl_o};
                    4'd5: probe_data_o = {2'b00, cntr_o};
                    4'd6: probe_data_o = {{11{sb_o[4]}}, sb_o};
                    4'd7: probe_data_o = {8'h00, px_q};
                    default: probe_data_o = 16'h0000;
                endcase
            end
            default: probe_data_o = 16'h0000;
        endcase
    end

    assign px_o = px_q;
    assign count_stack_push_data_o = count_stack_push_o
        ? counter_push_data : 14'h0000;
    assign internal_conflict_o = (
        register_conflict || dag_conflict || status_conflict
        || counter_conflict || sequencer_stack_conflict
    );

    adsp2100_register_file computational_registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(read_code_i[3:0]),
        .read_address_1_i(probe_code_i[3:0]),
        .read_address_2_i(dreg_read_address_i),
        .read_data_0_o(read_dreg_data),
        .read_data_1_o(probe_dreg_data),
        .read_data_2_o(dreg_read_data_o),
        .write_enable_0_i(state_write && (write_group == 2'b00)),
        .write_address_0_i(write_index),
        .write_data_0_i(move_data_i),
        .write_enable_1_i(!reset_i && dreg_write_enable_1_i),
        .write_address_1_i(dreg_write_address_1_i),
        .write_data_1_i(dreg_write_data_1_i),
        .write_enable_2_i(!reset_i && dreg_write_enable_2_i),
        .write_address_2_i(dreg_write_address_2_i),
        .write_data_2_i(dreg_write_data_2_i),
        .sb_move_write_enable_i(state_write && (move_code_i == 6'h36)),
        .sb_move_write_data_i(move_data_i[4:0]),
        .alu_write_enable_i(!reset_i && alu_write_enable_i),
        .alu_destination_feedback_i(alu_destination_feedback_i),
        .alu_result_i(alu_result_i),
        .mac_write_enable_i(!reset_i && mac_write_enable_i),
        .mac_destination_feedback_i(mac_destination_feedback_i),
        .mac_result_i(mac_result_i),
        .shifter_sr_write_enable_i(
            !reset_i && shifter_sr_write_enable_i
        ),
        .shifter_sr_result_i(shifter_sr_result_i),
        .shifter_se_write_enable_i(
            !reset_i && shifter_se_write_enable_i
        ),
        .shifter_se_result_i(shifter_se_result_i),
        .shifter_sb_write_enable_i(
            !reset_i && shifter_sb_write_enable_i
        ),
        .shifter_sb_result_i(shifter_sb_result_i),
        .af_o(af_o),
        .mf_o(mf_o),
        .mr_o(mr_o),
        .se_o(se_o),
        .sb_o(sb_o),
        .sr_o(sr_o),
        .write_conflict_o(register_conflict)
    );

    adsp2100_dag_register_file dag_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .i_l_read_address_i(read_dag_address),
        .m_read_address_i(read_dag_address),
        .i_read_data_o(read_i_data),
        .i_read_valid_o(unused_read_i_valid),
        .m_read_data_o(read_m_data),
        .m_read_valid_o(unused_read_m_valid),
        .l_read_data_o(read_l_data),
        .l_read_valid_o(unused_read_l_valid),
        .probe_address_i(probe_dag_address),
        .probe_i_data_o(probe_i_data),
        .probe_i_valid_o(unused_probe_i_valid),
        .probe_m_data_o(probe_m_data),
        .probe_m_valid_o(unused_probe_m_valid),
        .probe_l_data_o(probe_l_data),
        .probe_l_valid_o(unused_probe_l_valid),
        .setup_write_i(
            state_write && ((write_group == 2'b01) || (write_group == 2'b10))
        ),
        .setup_kind_i(dag_write_kind),
        .setup_address_i(dag_write_address),
        .setup_data_i(move_data_i[13:0]),
        .i_write_enable_i(!reset_i && dag_i_write_enable_i),
        .i_write_address_i(dag_i_write_address_i),
        .i_write_data_i(dag_i_write_data_i),
        .i_write_result_valid_i(dag_i_write_result_valid_i),
        .invalid_setup_kind_o(unused_dag_invalid_setup),
        .write_conflict_o(dag_conflict)
    );

    adsp2100_status_registers status_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(state_write && (move_code_i == 6'h30)),
        .astat_move_write_data_i(move_data_i[7:0]),
        .mstat_move_write_enable_i(state_write && (move_code_i == 6'h31)),
        .mstat_move_write_data_i(move_data_i[3:0]),
        .icntl_move_write_enable_i(state_write && (move_code_i == 6'h34)),
        .icntl_move_write_data_i(move_data_i[4:0]),
        .imask_move_write_enable_i(state_write && (move_code_i == 6'h33)),
        .imask_move_write_data_i(move_data_i[3:0]),
        .mode_sr_i(reset_i ? 2'b00 : mode_sr_i),
        .mode_br_i(reset_i ? 2'b00 : mode_br_i),
        .mode_ol_i(reset_i ? 2'b00 : mode_ol_i),
        .mode_as_i(reset_i ? 2'b00 : mode_as_i),
        .alu_status_write_enable_i(
            !reset_i && alu_status_write_enable_i
        ),
        .alu_az_i(alu_az_i),
        .alu_an_i(alu_an_i),
        .alu_av_i(alu_av_i),
        .alu_ac_i(alu_ac_i),
        .alu_as_write_enable_i(alu_as_write_enable_i),
        .alu_as_i(alu_as_i),
        .divide_status_write_enable_i(
            !reset_i && divide_status_write_enable_i
        ),
        .divide_aq_i(divide_aq_i),
        .mac_status_write_enable_i(
            !reset_i && mac_status_write_enable_i
        ),
        .mac_mv_i(mac_mv_i),
        .shifter_status_write_enable_i(
            !reset_i && shifter_status_write_enable_i
        ),
        .shifter_ss_i(shifter_ss_i),
        .interrupt_entry_i(1'b0),
        .interrupt_level_i(2'b00),
        .status_restore_i(1'b0),
        .restore_astat_i(8'h00),
        .restore_mstat_i(4'h0),
        .restore_imask_i(4'h0),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .alternate_bank_o(alternate_bank_o),
        .bit_reverse_o(bit_reverse_o),
        .overflow_latch_o(overflow_latch_o),
        .saturate_ar_o(saturate_ar_o),
        .write_conflict_o(status_conflict),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );

    adsp2100_counter counter (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .load_i(state_write && move_data_valid_i && (move_code_i == 6'h35)),
        .invalidate_i(
            state_write && !move_data_valid_i && (move_code_i == 6'h35)
        ),
        .load_data_i(move_data_i[13:0]),
        .ce_test_i(1'b0),
        .manual_pop_i(1'b0),
        .count_stack_top_data_i(count_stack_top),
        .count_stack_top_valid_i(count_stack_top_valid),
        .cntr_data_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .condition_valid_o(unused_counter_condition_valid),
        .counter_expired_o(unused_counter_expired),
        .not_counter_expired_o(unused_not_counter_expired),
        .count_stack_push_o(count_stack_push_o),
        .count_stack_push_data_o(counter_push_data),
        .count_stack_pop_o(count_stack_pop),
        .decrement_o(unused_counter_decrement),
        .restore_o(unused_counter_restore),
        .empty_ce_invalidate_o(unused_empty_ce_invalidate),
        .invalid_ce_test_o(unused_invalid_ce_test),
        .empty_manual_pop_o(unused_empty_manual_pop),
        .write_conflict_o(counter_conflict)
    );

    adsp2100_sequencer_stacks sequencer_stacks (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .pc_push_i(1'b0),
        .pc_pop_i(1'b0),
        .pc_push_data_i(14'h0000),
        .pc_top_data_o(unused_pc_top),
        .pc_top_valid_o(unused_pc_top_valid),
        .pc_pop_valid_o(unused_pc_pop_valid),
        .pc_empty_o(unused_pc_empty),
        .pc_overflow_o(unused_pc_overflow),
        .pc_depth_o(unused_pc_depth),
        .pc_push_accepted_o(unused_pc_push_accepted),
        .pc_overflow_event_o(unused_pc_overflow_event),
        .pc_empty_pop_o(unused_pc_empty_pop),
        .count_push_i(count_stack_push_o),
        .count_pop_i(count_stack_pop),
        .count_push_data_i(count_stack_push_data_o),
        .count_top_data_o(count_stack_top),
        .count_top_valid_o(count_stack_top_valid),
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
        .sstat_fragment_o(sequencer_sstat),
        .write_conflict_o(sequencer_stack_conflict)
    );

    adsp2100_status_stack status_stack (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .operation_i(2'b00),
        .push_data_i(16'h0000),
        .pop_data_o(unused_status_pop_data),
        .pop_valid_o(unused_status_pop_valid),
        .empty_o(status_stack_empty),
        .overflow_o(status_stack_overflow),
        .depth_o(unused_status_depth),
        .push_accepted_o(unused_status_push_accepted),
        .overflow_event_o(unused_status_overflow_event),
        .empty_pop_o(unused_status_empty_pop)
    );

    assign sstat_o = sequencer_sstat | {
        2'b00, status_stack_overflow, status_stack_empty, 4'b0000
    };

    // PX has no documented reset value. Only its validity-independent data
    // storage is updated by an accepted architectural move.
    always_ff @(posedge clk_i) begin
        if (state_write && (move_code_i == 6'h37)) begin
            px_q <= move_data_i[7:0];
        end
    end
endmodule

`default_nettype wire
