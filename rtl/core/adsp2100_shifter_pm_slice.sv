`default_nettype none

module adsp2100_shifter_pm_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic [23:0] pm_read_data_i,
    input  logic        pm_read_data_valid_i,
    input  logic [13:0] next_fetch_address_i,
    input  logic        next_fetch_address_valid_i,
    input  logic        cache_next_instruction_valid_i,
    input  logic        force_instruction_fetch_i,

    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        dreg_setup_write_i,
    input  logic [3:0]  dreg_setup_code_i,
    input  logic [15:0] dreg_setup_data_i,
    input  logic        sb_setup_write_i,
    input  logic [4:0]  sb_setup_data_i,
    input  logic        dag_setup_write_i,
    input  logic [1:0]  dag_setup_kind_i,
    input  logic [2:0]  dag_setup_address_i,
    input  logic [13:0] dag_setup_data_i,
    input  logic        px_setup_write_i,
    input  logic [7:0]  px_setup_data_i,
    input  logic [3:0]  probe_dreg_code_i,
    input  logic [2:0]  probe_dag_address_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        unavailable_xop_o,
    output logic        destination_collision_o,
    output logic        write_direction_o,
    output logic [3:0]  sf_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  shifter_source_dreg_o,
    output logic [3:0]  memory_dreg_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,

    output logic        boundary_valid_o,
    output logic        accepted_o,
    output logic        data_action_complete_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        busy_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        cache_instruction_selected_o,
    output logic        recovery_required_o,
    output logic        recovery_fetch_o,
    output logic        event_boundary_o,

    output logic        pm_select_o,
    output logic        pm_data_access_o,
    output logic        pm_read_o,
    output logic        pm_write_o,
    output logic [13:0] pm_address_o,
    output logic        pm_address_valid_o,
    output logic [23:0] pm_write_data_o,
    output logic        pm_write_data_valid_o,
    output logic [23:0] fetched_instruction_o,
    output logic        fetched_instruction_valid_o,
    output logic        dm_access_o,

    output logic        shifter_result_known_o,
    output logic        dag_configuration_valid_o,
    output logic        i_write_o,
    output logic        i_write_known_o,
    output logic        dreg_write_o,
    output logic        dreg_write_known_o,
    output logic        px_write_o,
    output logic        px_write_known_o,
    output logic        sr_write_o,
    output logic        se_write_o,
    output logic        sb_write_o,
    output logic        ss_write_o,
    output logic [31:0] sr_result_o,
    output logic [7:0]  se_result_o,
    output logic [4:0]  sb_result_o,
    output logic        ss_result_o,

    output logic [15:0] probe_dreg_data_o,
    output logic        probe_dreg_valid_o,
    output logic [13:0] probe_i_data_o,
    output logic        probe_i_valid_o,
    output logic [13:0] probe_m_data_o,
    output logic        probe_m_valid_o,
    output logic [13:0] probe_l_data_o,
    output logic        probe_l_valid_o,
    output logic [7:0]  px_o,
    output logic        px_valid_o,
    output logic [31:0] sr_o,
    output logic        sr_valid_o,
    output logic [7:0]  se_o,
    output logic        se_valid_o,
    output logic [4:0]  sb_o,
    output logic        sb_valid_o,
    output logic [7:0]  astat_o,
    output logic [7:0]  astat_valid_mask_o,
    output logic [3:0]  mstat_o,
    output logic        alternate_bank_o
);
    import adsp2100_register_pkg::*;

    logic [3:0] setup_count;
    logic astat_setup_enable;
    logic mstat_setup_enable;
    logic dreg_setup_enable;
    logic sb_setup_enable;
    logic dag_setup_enable;
    logic px_setup_enable;
    logic issue;
    logic needs_recovery;
    logic recovery_q;
    logic [13:0] recovery_address_q;
    logic recovery_address_valid_q;

    logic [15:0] shifter_source_data;
    logic [15:0] memory_source_data;
    logic [15:0] dreg_valid_q [0:1];
    logic sb_valid_q [0:1];
    logic [7:0] astat_valid_mask_q;
    logic [7:0] px_q;
    logic px_valid_q;
    logic live_shifter_known;
    logic live_sr_pair_valid;
    logic raw_sr_write;
    logic raw_se_write;
    logic raw_sb_write;
    logic raw_ss_write;
    logic [31:0] raw_sr_result;
    logic [7:0] raw_se_result;
    logic [4:0] raw_sb_result;
    logic raw_ss_result;
    logic exp_lo_destination;

    logic [13:0] dag_i_data;
    logic dag_i_valid;
    logic [13:0] dag_m_data;
    logic dag_m_valid;
    logic [13:0] dag_l_data;
    logic dag_l_valid;
    logic [13:0] live_pm_address;
    logic [13:0] live_next_i;
    logic [13:0] unused_dag_base;
    logic unused_dag_circular;
    logic live_dag_configuration_valid;
    logic live_next_i_valid;

    logic register_write_enable;
    logic [3:0] register_write_address;
    logic [15:0] register_write_data;
    logic register_conflict;
    logic status_conflict;
    logic dag_conflict;
    logic dag_invalid_setup_kind;
    logic [15:0] unused_af;
    logic [15:0] unused_mf;
    logic [39:0] unused_mr;
    logic [4:0] unused_icntl;
    logic [3:0] unused_imask;
    logic unused_bit_reverse;
    logic unused_overflow_latch;
    logic unused_saturate_ar;
    logic unused_status_push;
    logic [7:0] unused_status_push_astat;
    logic [3:0] unused_status_push_mstat;
    logic [3:0] unused_status_push_imask;

    adsp2100_shifter_pm_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .unavailable_xop_o(unavailable_xop_o),
        .destination_collision_o(destination_collision_o),
        .write_o(write_direction_o),
        .sf_o(sf_o),
        .xop_o(xop_o),
        .shifter_source_dreg_o(shifter_source_dreg_o),
        .memory_dreg_o(memory_dreg_o),
        .i_address_o(i_address_o),
        .m_address_o(m_address_o)
    );

    assign setup_count = (
        {3'h0, astat_setup_write_i}
        + {3'h0, mstat_setup_write_i}
        + {3'h0, dreg_setup_write_i}
        + {3'h0, sb_setup_write_i}
        + {3'h0, dag_setup_write_i}
        + {3'h0, px_setup_write_i}
    );
    assign integration_conflict_o = !reset_i && (
        (
            recovery_q
            && (execute_i || setup_count != 4'h0)
        )
        || (
            !recovery_q
            && (
                (execute_i && setup_count != 4'h0)
                || setup_count > 4'h1
            )
        )
    );
    assign issue = (
        !reset_i
        && !recovery_q
        && execute_i
        && action_valid_o
        && setup_count == 4'h0
    );
    assign needs_recovery = (
        issue
        && (
            force_instruction_fetch_i
            || !cache_next_instruction_valid_i
        )
    );
    assign boundary_valid_o = issue;
    assign accepted_o = issue;
    assign data_action_complete_o = issue;
    assign invalid_opcode_o = (
        !reset_i && !recovery_q && execute_i && !action_valid_o
    );
    assign astat_setup_enable = (
        !reset_i && !recovery_q && !execute_i && setup_count == 4'h1
        && astat_setup_write_i
    );
    assign mstat_setup_enable = (
        !reset_i && !recovery_q && !execute_i && setup_count == 4'h1
        && mstat_setup_write_i
    );
    assign dreg_setup_enable = (
        !reset_i && !recovery_q && !execute_i && setup_count == 4'h1
        && dreg_setup_write_i
    );
    assign sb_setup_enable = (
        !reset_i && !recovery_q && !execute_i && setup_count == 4'h1
        && sb_setup_write_i
    );
    assign dag_setup_enable = (
        !reset_i && !recovery_q && !execute_i && setup_count == 4'h1
        && dag_setup_write_i
    );
    assign px_setup_enable = (
        !reset_i && !recovery_q && !execute_i && setup_count == 4'h1
        && px_setup_write_i
    );

    assign live_sr_pair_valid = (
        dreg_valid_q[alternate_bank_o][DREG_SR0]
        && dreg_valid_q[alternate_bank_o][DREG_SR1]
    );
    always_comb begin
        live_shifter_known = (
            dreg_valid_q[alternate_bank_o][shifter_source_dreg_o]
        );
        if (sf_o <= 4'hb) begin
            live_shifter_known = (
                live_shifter_known
                && dreg_valid_q[alternate_bank_o][DREG_SE]
                && (!sf_o[0] || live_sr_pair_valid)
                && (
                    (sf_o != 4'h8 && sf_o != 4'h9)
                    || astat_valid_mask_q[3]
                )
            );
        end else if (sf_o == 4'hd) begin
            live_shifter_known = live_shifter_known && astat_valid_mask_q[2];
        end else if (sf_o == 4'he) begin
            live_shifter_known = (
                live_shifter_known
                && dreg_valid_q[alternate_bank_o][DREG_SE]
                && (se_o != 8'hf1 || astat_valid_mask_q[7])
            );
        end else if (sf_o == 4'hf) begin
            live_shifter_known = (
                live_shifter_known && sb_valid_q[alternate_bank_o]
            );
        end
    end
    assign exp_lo_destination = (
        !dreg_valid_q[alternate_bank_o][DREG_SE] || se_o == 8'hf1
    );
    assign live_next_i_valid = (
        dag_i_valid
        && dag_m_valid
        && dag_l_valid
        && live_dag_configuration_valid
    );

    assign transaction_active_o = !reset_i && (issue || recovery_q);
    assign instruction_complete_o = (
        !reset_i && ((issue && !needs_recovery) || recovery_q)
    );
    assign cache_instruction_selected_o = (
        issue && cache_next_instruction_valid_i
        && !force_instruction_fetch_i
    );
    assign recovery_required_o = needs_recovery;
    assign recovery_fetch_o = !reset_i && recovery_q;
    assign event_boundary_o = instruction_complete_o;
    // A recovery fetch is a fixed, completing cycle rather than a wait. Busy
    // therefore describes only the newly scheduled follow-on state returned
    // by the PM-data cycle.
    assign busy_o = !reset_i && needs_recovery;

    assign pm_select_o = transaction_active_o;
    assign pm_data_access_o = issue;
    assign pm_read_o = recovery_q || (issue && !write_direction_o);
    assign pm_write_o = issue && write_direction_o;
    assign pm_address_o = recovery_q
        ? (recovery_address_valid_q ? recovery_address_q : 14'h0000)
        : (issue && dag_i_valid ? live_pm_address : 14'h0000);
    assign pm_address_valid_o = recovery_q
        ? recovery_address_valid_q : (issue && dag_i_valid);
    assign pm_write_data_o = (
        pm_write_data_valid_o
        ? {memory_source_data, px_q} : 24'h000000
    );
    assign pm_write_data_valid_o = (
        pm_write_o
        && dreg_valid_q[alternate_bank_o][memory_dreg_o]
        && px_valid_q
    );
    assign fetched_instruction_o = (
        fetched_instruction_valid_o ? pm_read_data_i : 24'h000000
    );
    assign fetched_instruction_valid_o = (
        recovery_q && recovery_address_valid_q && pm_read_data_valid_i
    );
    assign dm_access_o = 1'b0;

    assign shifter_result_known_o = issue && live_shifter_known;
    assign dag_configuration_valid_o = (
        issue && dag_i_valid && dag_m_valid && dag_l_valid
        && live_dag_configuration_valid
    );
    assign i_write_o = issue;
    assign i_write_known_o = issue && live_next_i_valid;
    assign dreg_write_o = issue && !write_direction_o;
    assign dreg_write_known_o = dreg_write_o && pm_read_data_valid_i;
    assign px_write_o = dreg_write_o;
    assign px_write_known_o = px_write_o && pm_read_data_valid_i;
    assign sr_write_o = issue && live_shifter_known && raw_sr_write;
    assign se_write_o = issue && live_shifter_known && raw_se_write;
    assign sb_write_o = issue && live_shifter_known && raw_sb_write;
    assign ss_write_o = issue && live_shifter_known && raw_ss_write;
    assign sr_result_o = sr_write_o ? raw_sr_result : 32'h00000000;
    assign se_result_o = se_write_o ? raw_se_result : 8'h00;
    assign sb_result_o = sb_write_o ? raw_sb_result : 5'h00;
    assign ss_result_o = ss_write_o ? raw_ss_result : 1'b0;

    assign register_write_enable = dreg_setup_enable || dreg_write_known_o;
    assign register_write_address = (
        dreg_setup_enable ? dreg_setup_code_i : memory_dreg_o
    );
    assign register_write_data = (
        dreg_setup_enable ? dreg_setup_data_i : pm_read_data_i[23:8]
    );
    assign probe_dreg_valid_o = (
        dreg_valid_q[alternate_bank_o][probe_dreg_code_i]
    );
    assign px_o = px_valid_q ? px_q : 8'h00;
    assign px_valid_o = px_valid_q;
    assign sr_valid_o = live_sr_pair_valid;
    assign se_valid_o = dreg_valid_q[alternate_bank_o][DREG_SE];
    assign sb_valid_o = sb_valid_q[alternate_bank_o];
    assign astat_valid_mask_o = astat_valid_mask_q;
    assign internal_conflict_o = (
        register_conflict || status_conflict || dag_conflict
        || dag_invalid_setup_kind
    );

    adsp2100_shifter shifter (
        .sf_i(sf_o),
        .x_i(shifter_source_data),
        .shift_or_se_i(se_o),
        .sr_i(sr_o),
        .sb_i(sb_o),
        .av_i(astat_o[2]),
        .ac_i(astat_o[3]),
        .ss_i(astat_o[7]),
        .sr_result_o(raw_sr_result),
        .sr_write_o(raw_sr_write),
        .se_result_o(raw_se_result),
        .se_write_o(raw_se_write),
        .sb_result_o(raw_sb_result),
        .sb_write_o(raw_sb_write),
        .ss_result_o(raw_ss_result),
        .ss_write_o(raw_ss_write)
    );

    adsp2100_dag #(.BIT_REVERSE_CAPABLE(1'b0)) dag (
        .i_i(dag_i_data),
        .m_i(dag_m_data),
        .l_i(dag_l_data),
        .bit_reverse_enable_i(1'b0),
        .address_o(live_pm_address),
        .next_i_o(live_next_i),
        .base_o(unused_dag_base),
        .circular_o(unused_dag_circular),
        .configuration_valid_o(live_dag_configuration_valid)
    );

    adsp2100_dag_register_file dag_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .i_l_read_address_i(i_address_o),
        .m_read_address_i(m_address_o),
        .i_read_data_o(dag_i_data),
        .i_read_valid_o(dag_i_valid),
        .m_read_data_o(dag_m_data),
        .m_read_valid_o(dag_m_valid),
        .l_read_data_o(dag_l_data),
        .l_read_valid_o(dag_l_valid),
        .probe_address_i(probe_dag_address_i),
        .probe_i_data_o(probe_i_data_o),
        .probe_i_valid_o(probe_i_valid_o),
        .probe_m_data_o(probe_m_data_o),
        .probe_m_valid_o(probe_m_valid_o),
        .probe_l_data_o(probe_l_data_o),
        .probe_l_valid_o(probe_l_valid_o),
        .setup_write_i(dag_setup_enable),
        .setup_kind_i(dag_setup_kind_i),
        .setup_address_i(dag_setup_address_i),
        .setup_data_i(dag_setup_data_i),
        .i_write_enable_i(i_write_o),
        .i_write_address_i(i_address_o),
        .i_write_data_i(live_next_i),
        .i_write_result_valid_i(live_next_i_valid),
        .invalid_setup_kind_o(dag_invalid_setup_kind),
        .write_conflict_o(dag_conflict)
    );

    adsp2100_register_file registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(shifter_source_dreg_o),
        .read_address_1_i(memory_dreg_o),
        .read_address_2_i(probe_dreg_code_i),
        .read_data_0_o(shifter_source_data),
        .read_data_1_o(memory_source_data),
        .read_data_2_o(probe_dreg_data_o),
        .write_enable_0_i(register_write_enable),
        .write_address_0_i(register_write_address),
        .write_data_0_i(register_write_data),
        .write_enable_1_i(1'b0),
        .write_address_1_i(4'h0),
        .write_data_1_i(16'h0000),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(sb_setup_enable),
        .sb_move_write_data_i(sb_setup_data_i),
        .alu_write_enable_i(1'b0),
        .alu_destination_feedback_i(1'b0),
        .alu_result_i(16'h0000),
        .mac_write_enable_i(1'b0),
        .mac_destination_feedback_i(1'b0),
        .mac_result_i(40'h0000000000),
        .shifter_sr_write_enable_i(sr_write_o),
        .shifter_sr_result_i(raw_sr_result),
        .shifter_se_write_enable_i(se_write_o),
        .shifter_se_result_i(raw_se_result),
        .shifter_sb_write_enable_i(sb_write_o),
        .shifter_sb_result_i(raw_sb_result),
        .af_o(unused_af),
        .mf_o(unused_mf),
        .mr_o(unused_mr),
        .se_o(se_o),
        .sb_o(sb_o),
        .sr_o(sr_o),
        .write_conflict_o(register_conflict)
    );

    adsp2100_status_registers status (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .astat_move_write_enable_i(astat_setup_enable),
        .astat_move_write_data_i(astat_setup_data_i),
        .mstat_move_write_enable_i(mstat_setup_enable),
        .mstat_move_write_data_i(mstat_setup_data_i),
        .icntl_move_write_enable_i(1'b0),
        .icntl_move_write_data_i(5'h00),
        .imask_move_write_enable_i(1'b0),
        .imask_move_write_data_i(4'h0),
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
        .shifter_status_write_enable_i(ss_write_o),
        .shifter_ss_i(raw_ss_result),
        .interrupt_entry_i(1'b0),
        .interrupt_level_i(2'b00),
        .status_restore_i(1'b0),
        .restore_astat_i(8'h00),
        .restore_mstat_i(4'h0),
        .restore_imask_i(4'h0),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(unused_icntl),
        .imask_o(unused_imask),
        .alternate_bank_o(alternate_bank_o),
        .bit_reverse_o(unused_bit_reverse),
        .overflow_latch_o(unused_overflow_latch),
        .saturate_ar_o(unused_saturate_ar),
        .write_conflict_o(status_conflict),
        .status_push_o(unused_status_push),
        .status_push_astat_o(unused_status_push_astat),
        .status_push_mstat_o(unused_status_push_mstat),
        .status_push_imask_o(unused_status_push_imask)
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            recovery_q <= 1'b0;
            recovery_address_q <= 14'h0000;
            recovery_address_valid_q <= 1'b0;
            dreg_valid_q[0] <= 16'h0000;
            dreg_valid_q[1] <= 16'h0000;
            sb_valid_q[0] <= 1'b0;
            sb_valid_q[1] <= 1'b0;
            astat_valid_mask_q <= 8'h00;
            px_q <= 8'h00;
            px_valid_q <= 1'b0;
        end else begin
            if (recovery_q) begin
                recovery_q <= 1'b0;
            end else if (needs_recovery) begin
                recovery_q <= 1'b1;
                recovery_address_q <= next_fetch_address_i;
                recovery_address_valid_q <= next_fetch_address_valid_i;
            end

            if (astat_setup_enable) begin
                astat_valid_mask_q <= 8'hff;
            end
            if (dreg_setup_enable) begin
                dreg_valid_q[alternate_bank_o][dreg_setup_code_i] <= 1'b1;
                if (dreg_setup_code_i == DREG_MR1) begin
                    dreg_valid_q[alternate_bank_o][DREG_MR2] <= 1'b1;
                end
            end
            if (sb_setup_enable) begin
                sb_valid_q[alternate_bank_o] <= 1'b1;
            end
            if (px_setup_enable) begin
                px_q <= px_setup_data_i;
                px_valid_q <= 1'b1;
            end
            if (issue) begin
                if (live_shifter_known) begin
                    if (raw_sr_write) begin
                        dreg_valid_q[alternate_bank_o][DREG_SR0] <= 1'b1;
                        dreg_valid_q[alternate_bank_o][DREG_SR1] <= 1'b1;
                    end else if (raw_se_write) begin
                        dreg_valid_q[alternate_bank_o][DREG_SE] <= 1'b1;
                    end else if (raw_sb_write) begin
                        sb_valid_q[alternate_bank_o] <= 1'b1;
                    end
                    if (raw_ss_write) begin
                        astat_valid_mask_q[7] <= 1'b1;
                    end
                end else if (sf_o <= 4'hb) begin
                    dreg_valid_q[alternate_bank_o][DREG_SR0] <= 1'b0;
                    dreg_valid_q[alternate_bank_o][DREG_SR1] <= 1'b0;
                end else if (sf_o == 4'hc || sf_o == 4'hd) begin
                    dreg_valid_q[alternate_bank_o][DREG_SE] <= 1'b0;
                    astat_valid_mask_q[7] <= 1'b0;
                end else if (sf_o == 4'he && exp_lo_destination) begin
                    dreg_valid_q[alternate_bank_o][DREG_SE] <= 1'b0;
                end else if (sf_o == 4'hf) begin
                    sb_valid_q[alternate_bank_o] <= 1'b0;
                end
                if (!write_direction_o) begin
                    dreg_valid_q[alternate_bank_o][memory_dreg_o]
                        <= pm_read_data_valid_i;
                    if (memory_dreg_o == DREG_MR1) begin
                        dreg_valid_q[alternate_bank_o][DREG_MR2]
                            <= pm_read_data_valid_i;
                    end
                    px_q <= pm_read_data_i[7:0];
                    px_valid_q <= pm_read_data_valid_i;
                end
            end
        end
    end

    always_comb begin
        assert (!(pm_read_o && pm_write_o));
        assert (pm_select_o == (pm_read_o || pm_write_o));
        assert (pm_data_access_o == issue);
        assert (!dm_access_o);
        assert (!(sr_write_o && (se_write_o || sb_write_o)));
        assert (!(se_write_o && sb_write_o));
        assert (event_boundary_o == instruction_complete_o);
        if (recovery_fetch_o) begin
            assert (pm_read_o && !pm_write_o && !pm_data_access_o);
            assert (!data_action_complete_o);
            assert (!i_write_o && !dreg_write_o && !px_write_o);
            assert (!sr_write_o && !se_write_o && !sb_write_o && !ss_write_o);
        end
        if (recovery_required_o) begin
            assert (data_action_complete_o && !instruction_complete_o);
        end
        if (instruction_complete_o && data_action_complete_o) begin
            assert (!recovery_required_o);
        end
        if (dreg_write_o) begin
            assert (px_write_o);
            assert (!(
                raw_sr_write
                && (memory_dreg_o == DREG_SR0
                    || memory_dreg_o == DREG_SR1)
            ));
            assert (!(raw_se_write && memory_dreg_o == DREG_SE));
        end
        if (!sr_write_o) begin
            assert (sr_result_o == 32'h00000000);
        end
        if (!se_write_o) begin
            assert (se_result_o == 8'h00);
        end
        if (!sb_write_o) begin
            assert (sb_result_o == 5'h00);
        end
        if (!ss_write_o) begin
            assert (!ss_result_o);
        end
    end
endmodule

`default_nettype wire
