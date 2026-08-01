`default_nettype none

module adsp2100_shifter_dm_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic        dm_ack_i,
    input  logic [15:0] dm_read_data_i,
    input  logic        dm_read_data_valid_i,

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
    input  logic [3:0]  probe_dreg_code_i,
    input  logic [2:0]  probe_dag_address_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        unavailable_xop_o,
    output logic        destination_collision_o,
    output logic        dag_select_o,
    output logic        write_direction_o,
    output logic [3:0]  sf_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  shifter_source_dreg_o,
    output logic [3:0]  memory_dreg_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,

    output logic        boundary_valid_o,
    output logic        accepted_o,
    output logic        instruction_complete_o,
    output logic        transaction_active_o,
    output logic        stalled_o,
    output logic        busy_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,

    output logic        dm_select_o,
    output logic        dm_read_o,
    output logic        dm_write_o,
    output logic [13:0] dm_address_o,
    output logic        dm_address_valid_o,
    output logic [15:0] dm_write_data_o,
    output logic        dm_write_data_valid_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o,

    output logic        shifter_result_known_o,
    output logic        dag_configuration_valid_o,
    output logic        i_write_o,
    output logic        i_write_known_o,
    output logic        dreg_write_o,
    output logic        dreg_write_known_o,
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
    logic issue;
    logic pending_q;

    logic pending_write_q;
    logic [3:0] pending_sf_q;
    logic [3:0] pending_memory_dreg_q;
    logic [2:0] pending_i_address_q;
    logic [13:0] pending_dm_address_q;
    logic pending_dm_address_valid_q;
    logic [15:0] pending_dm_write_data_q;
    logic pending_dm_write_data_valid_q;
    logic [13:0] pending_next_i_q;
    logic pending_next_i_valid_q;
    logic pending_dag_configuration_valid_q;
    logic pending_shifter_known_q;
    logic [31:0] pending_sr_result_q;
    logic [7:0] pending_se_result_q;
    logic [4:0] pending_sb_result_q;
    logic pending_ss_result_q;
    logic pending_raw_sr_write_q;
    logic pending_raw_se_write_q;
    logic pending_raw_sb_write_q;
    logic pending_raw_ss_write_q;
    logic pending_exp_lo_destination_q;

    logic [15:0] shifter_source_data;
    logic [15:0] memory_source_data;
    logic [15:0] dreg_valid_q [0:1];
    logic sb_valid_q [0:1];
    logic [7:0] astat_valid_mask_q;
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

    logic [13:0] dag_i_data;
    logic dag_i_valid;
    logic [13:0] dag_m_data;
    logic dag_m_valid;
    logic [13:0] dag_l_data;
    logic dag_l_valid;
    logic [13:0] live_dm_address;
    logic [13:0] live_next_i;
    logic [13:0] unused_dag_base;
    logic unused_dag_circular;
    logic live_dag_configuration_valid;
    logic live_next_i_valid;

    logic active_write;
    logic [3:0] active_sf;
    logic [3:0] active_memory_dreg;
    logic [2:0] active_i_address;
    logic [13:0] active_dm_address;
    logic active_dm_address_valid;
    logic [15:0] active_dm_write_data;
    logic active_dm_write_data_valid;
    logic [13:0] active_next_i;
    logic active_next_i_valid;
    logic active_dag_configuration_valid;
    logic active_shifter_known;
    logic [31:0] active_sr_result;
    logic [7:0] active_se_result;
    logic [4:0] active_sb_result;
    logic active_ss_result;
    logic active_raw_sr_write;
    logic active_raw_se_write;
    logic active_raw_sb_write;
    logic active_raw_ss_write;
    logic active_exp_lo_destination;

    logic register_write_enable;
    logic [3:0] register_write_address;
    logic [15:0] register_write_data;
    logic register_conflict;
    logic status_conflict;
    logic dag_conflict;
    logic dag_invalid_setup_kind;
    logic [15:0] unused_af;
    logic [15:0] unused_read_3;
    logic [15:0] unused_mf;
    logic [39:0] unused_mr;
    logic [4:0] unused_icntl;
    logic [3:0] unused_imask;
    logic bit_reverse;
    logic unused_overflow_latch;
    logic unused_saturate_ar;
    logic unused_status_push;
    logic [7:0] unused_status_push_astat;
    logic [3:0] unused_status_push_mstat;
    logic [3:0] unused_status_push_imask;

    adsp2100_shifter_dm_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .unavailable_xop_o(unavailable_xop_o),
        .destination_collision_o(destination_collision_o),
        .dag_select_o(dag_select_o),
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
    );
    assign integration_conflict_o = !reset_i && (
        (
            pending_q
            && (execute_i || setup_count != 4'h0)
        )
        || (
            !pending_q
            && (
                (execute_i && setup_count != 4'h0)
                || setup_count > 4'h1
            )
        )
    );
    assign issue = (
        !reset_i
        && !pending_q
        && execute_i
        && action_valid_o
        && setup_count == 4'h0
    );
    assign boundary_valid_o = issue;
    assign accepted_o = issue;
    assign invalid_opcode_o = (
        !reset_i && !pending_q && execute_i && !action_valid_o
    );
    assign astat_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && astat_setup_write_i
    );
    assign mstat_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && mstat_setup_write_i
    );
    assign dreg_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && dreg_setup_write_i
    );
    assign sb_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && sb_setup_write_i
    );
    assign dag_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && dag_setup_write_i
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

    assign live_next_i_valid = (
        dag_i_valid
        && dag_m_valid
        && dag_l_valid
        && live_dag_configuration_valid
    );

    assign transaction_active_o = !reset_i && (pending_q || issue);
    assign instruction_complete_o = transaction_active_o && dm_ack_i;
    assign stalled_o = transaction_active_o && !dm_ack_i;
    assign busy_o = stalled_o;

    always_comb begin
        if (pending_q) begin
            active_write = pending_write_q;
            active_sf = pending_sf_q;
            active_memory_dreg = pending_memory_dreg_q;
            active_i_address = pending_i_address_q;
            active_dm_address = pending_dm_address_q;
            active_dm_address_valid = pending_dm_address_valid_q;
            active_dm_write_data = pending_dm_write_data_q;
            active_dm_write_data_valid = pending_dm_write_data_valid_q;
            active_next_i = pending_next_i_q;
            active_next_i_valid = pending_next_i_valid_q;
            active_dag_configuration_valid = (
                pending_dag_configuration_valid_q
            );
            active_shifter_known = pending_shifter_known_q;
            active_sr_result = pending_sr_result_q;
            active_se_result = pending_se_result_q;
            active_sb_result = pending_sb_result_q;
            active_ss_result = pending_ss_result_q;
            active_raw_sr_write = pending_raw_sr_write_q;
            active_raw_se_write = pending_raw_se_write_q;
            active_raw_sb_write = pending_raw_sb_write_q;
            active_raw_ss_write = pending_raw_ss_write_q;
            active_exp_lo_destination = pending_exp_lo_destination_q;
        end else begin
            active_write = write_direction_o;
            active_sf = sf_o;
            active_memory_dreg = memory_dreg_o;
            active_i_address = i_address_o;
            active_dm_address = live_dm_address;
            active_dm_address_valid = dag_i_valid;
            active_dm_write_data = memory_source_data;
            active_dm_write_data_valid = (
                write_direction_o
                && dreg_valid_q[alternate_bank_o][memory_dreg_o]
            );
            active_next_i = live_next_i;
            active_next_i_valid = live_next_i_valid;
            active_dag_configuration_valid = (
                dag_i_valid && dag_m_valid && dag_l_valid
                && live_dag_configuration_valid
            );
            active_shifter_known = live_shifter_known;
            active_sr_result = raw_sr_result;
            active_se_result = raw_se_result;
            active_sb_result = raw_sb_result;
            active_ss_result = raw_ss_result;
            active_raw_sr_write = raw_sr_write;
            active_raw_se_write = raw_se_write;
            active_raw_sb_write = raw_sb_write;
            active_raw_ss_write = raw_ss_write;
            active_exp_lo_destination = (
                !dreg_valid_q[alternate_bank_o][DREG_SE]
                || se_o == 8'hf1
            );
        end
    end

    assign dm_select_o = transaction_active_o;
    assign dm_read_o = transaction_active_o && !active_write;
    assign dm_write_o = transaction_active_o && active_write;
    assign dm_address_o = (
        transaction_active_o && active_dm_address_valid
        ? active_dm_address : 14'h0000
    );
    assign dm_address_valid_o = (
        transaction_active_o && active_dm_address_valid
    );
    assign dm_write_data_o = dm_write_o && active_dm_write_data_valid
        ? active_dm_write_data : 16'h0000;
    assign dm_write_data_valid_o = (
        dm_write_o && active_dm_write_data_valid
    );
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = transaction_active_o;

    assign shifter_result_known_o = (
        transaction_active_o && active_shifter_known
    );
    assign dag_configuration_valid_o = (
        transaction_active_o && active_dag_configuration_valid
    );
    assign i_write_o = instruction_complete_o;
    assign i_write_known_o = instruction_complete_o && active_next_i_valid;
    assign dreg_write_o = instruction_complete_o && !active_write;
    assign dreg_write_known_o = (
        dreg_write_o && dm_read_data_valid_i
    );
    assign sr_write_o = (
        instruction_complete_o && active_shifter_known
        && active_raw_sr_write
    );
    assign se_write_o = (
        instruction_complete_o && active_shifter_known
        && active_raw_se_write
    );
    assign sb_write_o = (
        instruction_complete_o && active_shifter_known
        && active_raw_sb_write
    );
    assign ss_write_o = (
        instruction_complete_o && active_shifter_known
        && active_raw_ss_write
    );
    assign sr_result_o = sr_write_o ? active_sr_result : 32'h00000000;
    assign se_result_o = se_write_o ? active_se_result : 8'h00;
    assign sb_result_o = sb_write_o ? active_sb_result : 5'h00;
    assign ss_result_o = ss_write_o ? active_ss_result : 1'b0;

    assign register_write_enable = dreg_setup_enable || dreg_write_known_o;
    assign register_write_address = (
        dreg_setup_enable ? dreg_setup_code_i : active_memory_dreg
    );
    assign register_write_data = (
        dreg_setup_enable ? dreg_setup_data_i : dm_read_data_i
    );
    assign probe_dreg_valid_o = (
        dreg_valid_q[alternate_bank_o][probe_dreg_code_i]
    );
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

    adsp2100_dag #(.BIT_REVERSE_CAPABLE(1'b1)) dag (
        .i_i(dag_i_data),
        .m_i(dag_m_data),
        .l_i(dag_l_data),
        .bit_reverse_enable_i(!dag_select_o && bit_reverse),
        .address_o(live_dm_address),
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
        .i_write_address_i(active_i_address),
        .i_write_data_i(active_next_i),
        .i_write_result_valid_i(active_next_i_valid),
        .invalid_setup_kind_o(dag_invalid_setup_kind),
        .write_conflict_o(dag_conflict)
    );

    adsp2100_register_file registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(shifter_source_dreg_o),
        .read_address_1_i(memory_dreg_o),
        .read_address_2_i(probe_dreg_code_i),
        .read_address_3_i(4'h0),
        .read_data_0_o(shifter_source_data),
        .read_data_1_o(memory_source_data),
        .read_data_2_o(probe_dreg_data_o),
        .read_data_3_o(unused_read_3),
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
        .shifter_sr_result_i(active_sr_result),
        .shifter_se_write_enable_i(se_write_o),
        .shifter_se_result_i(active_se_result),
        .shifter_sb_write_enable_i(sb_write_o),
        .shifter_sb_result_i(active_sb_result),
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
        .shifter_ss_i(active_ss_result),
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
        .bit_reverse_o(bit_reverse),
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
            pending_q <= 1'b0;
            dreg_valid_q[0] <= 16'h0000;
            dreg_valid_q[1] <= 16'h0000;
            sb_valid_q[0] <= 1'b0;
            sb_valid_q[1] <= 1'b0;
            astat_valid_mask_q <= 8'h00;
        end else begin
            if (pending_q) begin
                if (dm_ack_i) begin
                    pending_q <= 1'b0;
                end
            end else if (issue && !dm_ack_i) begin
                pending_q <= 1'b1;
                pending_write_q <= write_direction_o;
                pending_sf_q <= sf_o;
                pending_memory_dreg_q <= memory_dreg_o;
                pending_i_address_q <= i_address_o;
                pending_dm_address_q <= live_dm_address;
                pending_dm_address_valid_q <= dag_i_valid;
                pending_dm_write_data_q <= write_direction_o
                    ? memory_source_data : 16'h0000;
                pending_dm_write_data_valid_q <= (
                    write_direction_o
                    && dreg_valid_q[alternate_bank_o][memory_dreg_o]
                );
                pending_next_i_q <= live_next_i;
                pending_next_i_valid_q <= live_next_i_valid;
                pending_dag_configuration_valid_q <= (
                    dag_i_valid && dag_m_valid && dag_l_valid
                    && live_dag_configuration_valid
                );
                pending_shifter_known_q <= live_shifter_known;
                pending_sr_result_q <= raw_sr_result;
                pending_se_result_q <= raw_se_result;
                pending_sb_result_q <= raw_sb_result;
                pending_ss_result_q <= raw_ss_result;
                pending_raw_sr_write_q <= raw_sr_write;
                pending_raw_se_write_q <= raw_se_write;
                pending_raw_sb_write_q <= raw_sb_write;
                pending_raw_ss_write_q <= raw_ss_write;
                pending_exp_lo_destination_q <= (
                    !dreg_valid_q[alternate_bank_o][DREG_SE]
                    || se_o == 8'hf1
                );
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
            if (instruction_complete_o) begin
                if (active_shifter_known) begin
                    if (active_raw_sr_write) begin
                        dreg_valid_q[alternate_bank_o][DREG_SR0] <= 1'b1;
                        dreg_valid_q[alternate_bank_o][DREG_SR1] <= 1'b1;
                    end else if (active_raw_se_write) begin
                        dreg_valid_q[alternate_bank_o][DREG_SE] <= 1'b1;
                    end else if (active_raw_sb_write) begin
                        sb_valid_q[alternate_bank_o] <= 1'b1;
                    end
                    if (active_raw_ss_write) begin
                        astat_valid_mask_q[7] <= 1'b1;
                    end
                end else if (active_sf <= 4'hb) begin
                    dreg_valid_q[alternate_bank_o][DREG_SR0] <= 1'b0;
                    dreg_valid_q[alternate_bank_o][DREG_SR1] <= 1'b0;
                end else if (active_sf == 4'hc || active_sf == 4'hd) begin
                    dreg_valid_q[alternate_bank_o][DREG_SE] <= 1'b0;
                    astat_valid_mask_q[7] <= 1'b0;
                end else if (
                    active_sf == 4'he && active_exp_lo_destination
                ) begin
                    dreg_valid_q[alternate_bank_o][DREG_SE] <= 1'b0;
                end else if (active_sf == 4'hf) begin
                    sb_valid_q[alternate_bank_o] <= 1'b0;
                end
                if (!active_write) begin
                    dreg_valid_q[alternate_bank_o][active_memory_dreg]
                        <= dm_read_data_valid_i;
                    if (active_memory_dreg == DREG_MR1) begin
                        dreg_valid_q[alternate_bank_o][DREG_MR2]
                            <= dm_read_data_valid_i;
                    end
                end
            end
        end
    end

    always_comb begin
        assert (!(dm_read_o && dm_write_o));
        assert (dm_select_o == (dm_read_o || dm_write_o));
        assert (!pm_data_access_o);
        assert (dm_access_o == dm_select_o);
        assert (!(sr_write_o && (se_write_o || sb_write_o)));
        assert (!(se_write_o && sb_write_o));
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
        if (stalled_o) begin
            assert (!instruction_complete_o);
            assert (!i_write_o && !dreg_write_o);
            assert (!sr_write_o && !se_write_o && !sb_write_o && !ss_write_o);
        end
        if (pending_q && !reset_i) begin
            if (pending_dm_address_valid_q) begin
                assert (dm_address_o == pending_dm_address_q);
            end
            if (pending_write_q && pending_dm_write_data_valid_q) begin
                assert (dm_write_data_o == pending_dm_write_data_q);
            end
        end
        if (instruction_complete_o && !active_write) begin
            assert (!(
                active_raw_sr_write
                && (active_memory_dreg == DREG_SR0
                    || active_memory_dreg == DREG_SR1)
            ));
            assert (!(
                active_raw_se_write && active_memory_dreg == DREG_SE
            ));
        end
    end
endmodule

`default_nettype wire
