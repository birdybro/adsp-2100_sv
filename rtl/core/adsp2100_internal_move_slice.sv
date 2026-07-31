`default_nettype none

module adsp2100_internal_move_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    // Deterministic verification/integration preload. This uses the same
    // destination narrowing and side effects as an architectural MOVE.
    input  logic        setup_write_i,
    input  logic [5:0]  setup_code_i,
    input  logic [15:0] setup_data_i,

    input  logic [5:0]  probe_code_i,
    output logic [15:0] probe_data_o,

    output logic        class_valid_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        invalid_subencoding_o,
    output logic        invalid_setup_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic [5:0]  source_code_o,
    output logic [5:0]  destination_code_o,
    output logic [15:0] source_data_o,
    output logic        source_extension_provisional_o,
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
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic       decoded_move_valid;
    logic       decoded_invalid_subencoding;
    logic [1:0] unused_destination_group;
    logic [1:0] source_group;
    logic [3:0] unused_destination_index;
    logic [3:0] source_index;
    logic       unused_destination_present;
    logic       unused_destination_writable;
    logic       unused_source_selector_valid;

    logic       setup_present;
    logic       setup_writable;
    logic       setup_valid;
    logic       state_write;
    logic [5:0] write_code;
    logic [15:0] write_data;
    logic [1:0] write_group;
    logic [3:0] write_index;

    logic [15:0] source_dreg_data;
    logic [15:0] probe_dreg_data;
    logic [15:0] unused_dreg_data;
    logic [15:0] unused_af;
    logic [15:0] unused_mf;
    logic [39:0] unused_mr;
    logic [7:0]  unused_se;
    logic [4:0]  selected_sb;
    logic [31:0] unused_sr;
    logic        register_conflict;
    logic        alternate_bank;

    logic [2:0]  source_dag_address;
    logic [13:0] source_i_data;
    logic        unused_source_i_valid;
    logic [13:0] source_m_data;
    logic        unused_source_m_valid;
    logic [13:0] source_l_data;
    logic        unused_source_l_valid;
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
    logic        unused_bit_reverse;
    logic        unused_overflow_latch;
    logic        unused_saturate_ar;
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

    adsp2100_internal_move_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .move_valid_o(decoded_move_valid),
        .invalid_subencoding_o(decoded_invalid_subencoding),
        .destination_group_o(unused_destination_group),
        .source_group_o(source_group),
        .destination_index_o(unused_destination_index),
        .source_index_o(source_index),
        .destination_code_o(destination_code_o),
        .source_code_o(source_code_o),
        .destination_present_o(unused_destination_present),
        .destination_writable_o(unused_destination_writable),
        .source_valid_o(unused_source_selector_valid)
    );

    assign setup_present = selector_present(
        setup_code_i[5:4],
        setup_code_i[3:0]
    );
    assign setup_writable = (
        setup_present
        && !(setup_code_i == 6'h32)
    );
    assign setup_valid = setup_write_i && setup_writable;
    assign invalid_setup_o = (
        !reset_i
        && setup_write_i
        && !setup_writable
    );
    assign integration_conflict_o = (
        !reset_i
        && execute_i
        && setup_write_i
    );
    assign invalid_opcode_o = (
        !reset_i
        && execute_i
        && !class_valid_o
    );
    assign invalid_subencoding_o = (
        !reset_i
        && execute_i
        && class_valid_o
        && decoded_invalid_subencoding
    );
    assign boundary_valid_o = (
        !reset_i
        && execute_i
        && decoded_move_valid
        && !setup_write_i
    );
    assign state_write = boundary_valid_o || (
        !reset_i
        && !execute_i
        && setup_valid
    );
    assign write_code = boundary_valid_o
        ? destination_code_o
        : setup_code_i;
    assign write_data = boundary_valid_o
        ? source_data_o
        : setup_data_i;
    assign write_group = write_code[5:4];
    assign write_index = write_code[3:0];

    assign source_dag_address = {
        source_group == 2'b10,
        source_index[1:0]
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

    // OQ-016 provisional behavior is deliberately isolated here. Current
    // MAME zero-extends these values, but the original-device manual does not
    // define the unused upper DMD bits. Every such read raises the companion
    // observable flag.
    always_comb begin
        source_data_o = 16'h0000;
        unique case (source_group)
            2'b00: source_data_o = source_dreg_data;
            2'b01,
            2'b10: begin
                if (source_index < 4'd4) begin
                    source_data_o = {2'b00, source_i_data};
                end else if (source_index < 4'd8) begin
                    source_data_o = {
                        {2{source_m_data[13]}},
                        source_m_data
                    };
                end else begin
                    source_data_o = {2'b00, source_l_data};
                end
            end
            2'b11: begin
                unique case (source_index)
                    4'd0: source_data_o = {8'h00, astat_o};
                    4'd1: source_data_o = {12'h000, mstat_o};
                    4'd2: source_data_o = {8'h00, sstat_o};
                    4'd3: source_data_o = {12'h000, imask_o};
                    4'd4: source_data_o = {11'h000, icntl_o};
                    4'd5: source_data_o = {2'b00, cntr_o};
                    4'd6: source_data_o = {
                        {11{selected_sb[4]}},
                        selected_sb
                    };
                    4'd7: source_data_o = {8'h00, px_q};
                    default: source_data_o = 16'h0000;
                endcase
            end
            default: source_data_o = 16'h0000;
        endcase
    end
    assign source_extension_provisional_o = (
        boundary_valid_o
        && (source_group == 2'b11)
        && (source_index <= 4'd4)
    );

    always_comb begin
        probe_data_o = 16'h0000;
        unique case (probe_code_i[5:4])
            2'b00: probe_data_o = probe_dreg_data;
            2'b01,
            2'b10: begin
                if (probe_code_i[3:0] < 4'd4) begin
                    probe_data_o = {2'b00, probe_i_data};
                end else if (probe_code_i[3:0] < 4'd8) begin
                    probe_data_o = {
                        {2{probe_m_data[13]}},
                        probe_m_data
                    };
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
                    4'd6: probe_data_o = {
                        {11{selected_sb[4]}},
                        selected_sb
                    };
                    4'd7: probe_data_o = {8'h00, px_q};
                    default: probe_data_o = 16'h0000;
                endcase
            end
            default: probe_data_o = 16'h0000;
        endcase
    end

    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;
    assign px_o = px_q;
    assign count_stack_push_data_o = count_stack_push_o
        ? counter_push_data
        : 14'h0000;
    assign internal_conflict_o = (
        register_conflict
        || dag_conflict
        || status_conflict
        || counter_conflict
        || sequencer_stack_conflict
    );

    adsp2100_register_file computational_registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank),
        .read_address_0_i(source_index),
        .read_address_1_i(probe_code_i[3:0]),
        .read_address_2_i(4'h0),
        .read_data_0_o(source_dreg_data),
        .read_data_1_o(probe_dreg_data),
        .read_data_2_o(unused_dreg_data),
        .write_enable_0_i(state_write && (write_group == 2'b00)),
        .write_address_0_i(write_index),
        .write_data_0_i(write_data),
        .write_enable_1_i(1'b0),
        .write_address_1_i(4'h0),
        .write_data_1_i(16'h0000),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(
            state_write
            && (write_code == 6'h36)
        ),
        .sb_move_write_data_i(write_data[4:0]),
        .alu_write_enable_i(1'b0),
        .alu_destination_feedback_i(1'b0),
        .alu_result_i(16'h0000),
        .mac_write_enable_i(1'b0),
        .mac_destination_feedback_i(1'b0),
        .mac_result_i(40'h0000000000),
        .shifter_sr_write_enable_i(1'b0),
        .shifter_sr_result_i(32'h00000000),
        .shifter_se_write_enable_i(1'b0),
        .shifter_se_result_i(8'h00),
        .shifter_sb_write_enable_i(1'b0),
        .shifter_sb_result_i(5'h00),
        .af_o(unused_af),
        .mf_o(unused_mf),
        .mr_o(unused_mr),
        .se_o(unused_se),
        .sb_o(selected_sb),
        .sr_o(unused_sr),
        .write_conflict_o(register_conflict)
    );

    adsp2100_dag_register_file dag_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .i_l_read_address_i(source_dag_address),
        .m_read_address_i(source_dag_address),
        .i_read_data_o(source_i_data),
        .i_read_valid_o(unused_source_i_valid),
        .m_read_data_o(source_m_data),
        .m_read_valid_o(unused_source_m_valid),
        .l_read_data_o(source_l_data),
        .l_read_valid_o(unused_source_l_valid),
        .probe_address_i(probe_dag_address),
        .probe_i_data_o(probe_i_data),
        .probe_i_valid_o(unused_probe_i_valid),
        .probe_m_data_o(probe_m_data),
        .probe_m_valid_o(unused_probe_m_valid),
        .probe_l_data_o(probe_l_data),
        .probe_l_valid_o(unused_probe_l_valid),
        .setup_write_i(
            state_write
            && ((write_group == 2'b01) || (write_group == 2'b10))
        ),
        .setup_kind_i(dag_write_kind),
        .setup_address_i(dag_write_address),
        .setup_data_i(write_data[13:0]),
        .i_write_enable_i(1'b0),
        .i_write_address_i(3'b000),
        .i_write_data_i(14'h0000),
        .i_write_result_valid_i(1'b0),
        .invalid_setup_kind_o(unused_dag_invalid_setup),
        .write_conflict_o(dag_conflict)
    );

    adsp2100_status_registers status_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(state_write && (write_code == 6'h30)),
        .astat_move_write_data_i(write_data[7:0]),
        .mstat_move_write_enable_i(state_write && (write_code == 6'h31)),
        .mstat_move_write_data_i(write_data[3:0]),
        .icntl_move_write_enable_i(state_write && (write_code == 6'h34)),
        .icntl_move_write_data_i(write_data[4:0]),
        .imask_move_write_enable_i(state_write && (write_code == 6'h33)),
        .imask_move_write_data_i(write_data[3:0]),
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
        .status_restore_i(1'b0),
        .restore_astat_i(8'h00),
        .restore_mstat_i(4'h0),
        .restore_imask_i(4'h0),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(unused_bit_reverse),
        .overflow_latch_o(unused_overflow_latch),
        .saturate_ar_o(unused_saturate_ar),
        .write_conflict_o(status_conflict),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );

    adsp2100_counter counter (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .load_i(state_write && (write_code == 6'h35)),
        .load_data_i(write_data[13:0]),
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

    assign sstat_o = (
        sequencer_sstat
        | {
            2'b00,
            status_stack_overflow,
            status_stack_empty,
            4'b0000
        }
    );

    // PX has no documented reset value. The storage is intentionally not
    // assigned on reset; deterministic setup and architectural MOVE writes
    // both commit at the cycle-ending edge.
    always_ff @(posedge clk_i) begin
        if (
            !reset_i
            && state_write
            && (write_code == 6'h37)
        ) begin
            px_q <= write_data[7:0];
        end
    end
endmodule

`default_nettype wire
