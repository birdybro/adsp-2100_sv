`default_nettype none

// Bounded logical original Type 1 execution slice.
//
// One accepted descriptor exposes simultaneous DAG1 DM and DAG2 PM reads.
// Both returned operands, PX, both selected I registers, and the optional
// ALU/MAC result/status commit atomically on transaction_complete_i. This
// logical completion port is an implementation/test boundary only; it makes
// no claim about native PM pins while DMACK extends state seven (OQ-023).
module adsp2100_compute_dual_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic        transaction_complete_i,
    input  logic [15:0] dm_read_data_i,
    input  logic        dm_read_data_valid_i,
    input  logic [23:0] pm_read_data_i,
    input  logic        pm_read_data_valid_i,

    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        dreg_setup_write_i,
    input  logic [3:0]  dreg_setup_code_i,
    input  logic [15:0] dreg_setup_data_i,
    input  logic        af_setup_write_i,
    input  logic [15:0] af_setup_data_i,
    input  logic        mf_setup_write_i,
    input  logic [15:0] mf_setup_data_i,
    input  logic        dag_setup_write_i,
    input  logic [1:0]  dag_setup_kind_i,
    input  logic [2:0]  dag_setup_address_i,
    input  logic [13:0] dag_setup_data_i,
    input  logic        px_setup_write_i,
    input  logic [7:0]  px_setup_data_i,
    input  logic        inspect_probe_i,
    input  logic [3:0]  probe_dreg_code_i,
    input  logic [2:0]  probe_dag_address_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        computation_enable_o,
    output logic        is_mac_o,
    output logic [4:0]  amf_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  y_source_dreg_o,
    output logic [3:0]  pm_destination_dreg_o,
    output logic [3:0]  dm_destination_dreg_o,
    output logic [2:0]  pm_i_address_o,
    output logic [2:0]  pm_m_address_o,
    output logic [2:0]  dm_i_address_o,
    output logic [2:0]  dm_m_address_o,

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
    output logic [13:0] dm_address_o,
    output logic        dm_address_valid_o,
    output logic        pm_select_o,
    output logic        pm_data_access_o,
    output logic        pm_read_o,
    output logic [13:0] pm_address_o,
    output logic        pm_address_valid_o,

    output logic        compute_result_known_o,
    output logic        dm_dag_configuration_valid_o,
    output logic        pm_dag_configuration_valid_o,
    output logic        dm_i_write_o,
    output logic        dm_i_write_known_o,
    output logic        pm_i_write_o,
    output logic        pm_i_write_known_o,
    output logic        dm_dreg_write_o,
    output logic        dm_dreg_write_known_o,
    output logic        pm_dreg_write_o,
    output logic        pm_dreg_write_known_o,
    output logic        px_write_o,
    output logic        px_write_known_o,
    output logic        alu_write_o,
    output logic        mac_write_o,
    output logic        alu_status_write_o,
    output logic        mac_status_write_o,
    output logic [15:0] alu_result_o,
    output logic [39:0] mac_result_o,

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
    output logic [15:0] af_o,
    output logic        af_valid_o,
    output logic [15:0] mf_o,
    output logic        mf_valid_o,
    output logic [39:0] mr_o,
    output logic        mr_valid_o,
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
    logic af_setup_enable;
    logic mf_setup_enable;
    logic dag_setup_enable;
    logic px_setup_enable;
    logic issue;
    logic pending_q;

    logic pending_computation_enable_q;
    logic pending_is_mac_q;
    logic [4:0] pending_amf_q;
    logic [3:0] pending_pm_destination_q;
    logic [3:0] pending_dm_destination_q;
    logic [2:0] pending_pm_i_address_q;
    logic [2:0] pending_dm_i_address_q;
    logic pending_bank_q;
    logic [13:0] pending_pm_address_q;
    logic pending_pm_address_valid_q;
    logic [13:0] pending_dm_address_q;
    logic pending_dm_address_valid_q;
    logic [13:0] pending_pm_next_i_q;
    logic pending_pm_next_i_valid_q;
    logic [13:0] pending_dm_next_i_q;
    logic pending_dm_next_i_valid_q;
    logic pending_pm_dag_configuration_valid_q;
    logic pending_dm_dag_configuration_valid_q;
    logic pending_compute_known_q;
    logic [15:0] pending_alu_result_q;
    logic [39:0] pending_mac_result_q;
    logic pending_alu_az_q;
    logic pending_alu_an_q;
    logic pending_alu_av_q;
    logic pending_alu_ac_q;
    logic pending_alu_as_q;
    logic pending_alu_as_write_q;
    logic pending_mac_mv_q;

    logic active_computation_enable;
    logic active_is_mac;
    logic [4:0] active_amf;
    logic [3:0] active_pm_destination;
    logic [3:0] active_dm_destination;
    logic [2:0] active_pm_i_address;
    logic [2:0] active_dm_i_address;
    logic active_bank;
    logic [13:0] active_pm_address;
    logic active_pm_address_valid;
    logic [13:0] active_dm_address;
    logic active_dm_address_valid;
    logic [13:0] active_pm_next_i;
    logic active_pm_next_i_valid;
    logic [13:0] active_dm_next_i;
    logic active_dm_next_i_valid;
    logic active_pm_dag_configuration_valid;
    logic active_dm_dag_configuration_valid;
    logic active_compute_known;
    logic [15:0] active_alu_result;
    logic [39:0] active_mac_result;
    logic active_alu_az;
    logic active_alu_an;
    logic active_alu_av;
    logic active_alu_ac;
    logic active_alu_as;
    logic active_alu_as_write;
    logic active_mac_mv;

    logic [15:0] x_source_data;
    logic [15:0] y_source_data;
    logic [15:0] unused_read_3;
    logic [47:0] unused_additional_read_data;
    logic [15:0] af_data;
    logic [15:0] mf_data;
    logic [39:0] mr_data;
    logic [7:0] unused_se;
    logic [4:0] unused_sb;
    logic [31:0] unused_sr;
    logic [15:0] dreg_valid_q [0:1];
    logic af_valid_q [0:1];
    logic mf_valid_q [0:1];
    logic [7:0] astat_valid_mask_q;
    logic live_x_known;
    logic live_y_known;
    logic live_mr_known;
    logic live_compute_known;
    logic alu_needs_x;
    logic alu_needs_y;
    logic alu_needs_carry;
    logic mac_needs_mr;

    logic live_alu_write;
    logic [15:0] live_alu_result;
    logic live_alu_az;
    logic live_alu_an;
    logic live_alu_av;
    logic live_alu_ac;
    logic live_alu_as;
    logic live_alu_as_write;
    logic live_mac_write;
    logic [39:0] live_mac_result;
    logic live_mac_mv;

    logic [13:0] dm_dag_i_data;
    logic dm_dag_i_valid;
    logic [13:0] dm_dag_m_data;
    logic dm_dag_m_valid;
    logic [13:0] dm_dag_l_data;
    logic dm_dag_l_valid;
    logic [13:0] pm_dag_i_data;
    logic pm_dag_i_valid;
    logic [13:0] pm_dag_m_data;
    logic pm_dag_m_valid;
    logic [13:0] pm_dag_l_data;
    logic pm_dag_l_valid;
    logic [13:0] live_dm_address;
    logic [13:0] live_dm_next_i;
    logic [13:0] live_pm_address;
    logic [13:0] live_pm_next_i;
    logic [13:0] unused_dm_base;
    logic [13:0] unused_pm_base;
    logic unused_dm_circular;
    logic unused_pm_circular;
    logic live_dm_dag_configuration_valid;
    logic live_pm_dag_configuration_valid;
    logic live_dm_next_i_valid;
    logic live_pm_next_i_valid;

    logic register_write_enable_0;
    logic register_write_enable_1;
    logic register_conflict;
    logic status_conflict;
    logic dag_conflict;
    logic dag_invalid_setup_kind;
    logic [4:0] unused_icntl;
    logic [3:0] unused_imask;
    logic bit_reverse;
    logic overflow_latch;
    logic saturate_ar;
    logic unused_status_push;
    logic [7:0] unused_status_push_astat;
    logic [3:0] unused_status_push_mstat;
    logic [3:0] unused_status_push_imask;
    logic [7:0] px_q;
    logic px_valid_q;

    adsp2100_compute_dual_action action (
        .opcode_i(opcode_i),
        .x_dreg_data_i(x_source_data),
        .y_dreg_data_i(y_source_data),
        .af_i(af_data),
        .mf_i(mf_data),
        .mr_i(mr_data),
        .astat_i(astat_o),
        .overflow_latch_i(overflow_latch),
        .saturate_ar_i(saturate_ar),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .unsupported_subencoding_o(unsupported_subencoding_o),
        .computation_enable_o(computation_enable_o),
        .is_mac_o(is_mac_o),
        .amf_o(amf_o),
        .yop_o(yop_o),
        .xop_o(xop_o),
        .x_source_dreg_o(x_source_dreg_o),
        .y_source_dreg_o(y_source_dreg_o),
        .pm_destination_dreg_o(pm_destination_dreg_o),
        .dm_destination_dreg_o(dm_destination_dreg_o),
        .pm_i_address_o(pm_i_address_o),
        .pm_m_address_o(pm_m_address_o),
        .dm_i_address_o(dm_i_address_o),
        .dm_m_address_o(dm_m_address_o),
        .alu_write_o(live_alu_write),
        .alu_result_o(live_alu_result),
        .alu_az_o(live_alu_az),
        .alu_an_o(live_alu_an),
        .alu_av_o(live_alu_av),
        .alu_ac_o(live_alu_ac),
        .alu_as_write_o(live_alu_as_write),
        .alu_as_o(live_alu_as),
        .mac_write_o(live_mac_write),
        .mac_result_o(live_mac_result),
        .mac_mv_o(live_mac_mv)
    );

    assign setup_count = (
        {3'h0, astat_setup_write_i}
        + {3'h0, mstat_setup_write_i}
        + {3'h0, dreg_setup_write_i}
        + {3'h0, af_setup_write_i}
        + {3'h0, mf_setup_write_i}
        + {3'h0, dag_setup_write_i}
        + {3'h0, px_setup_write_i}
    );
    assign integration_conflict_o = !reset_i && (
        (pending_q && (execute_i || setup_count != 4'h0))
        || (
            !pending_q
            && (
                (execute_i && (setup_count != 4'h0 || inspect_probe_i))
                || setup_count > 4'h1
            )
        )
    );
    assign issue = (
        !reset_i && !pending_q && execute_i && action_valid_o
        && setup_count == 4'h0 && !inspect_probe_i
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
    assign af_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && af_setup_write_i
    );
    assign mf_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && mf_setup_write_i
    );
    assign dag_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && dag_setup_write_i
    );
    assign px_setup_enable = (
        !reset_i && !pending_q && !execute_i && setup_count == 4'h1
        && px_setup_write_i
    );

    assign live_mr_known = (
        dreg_valid_q[alternate_bank_o][DREG_MR0]
        && dreg_valid_q[alternate_bank_o][DREG_MR1]
        && dreg_valid_q[alternate_bank_o][DREG_MR2]
    );
    assign live_x_known = (
        dreg_valid_q[alternate_bank_o][x_source_dreg_o]
    );
    always_comb begin
        if (yop_o == 2'd3) begin
            live_y_known = 1'b1;
        end else if (yop_o == 2'd2) begin
            live_y_known = is_mac_o
                ? mf_valid_q[alternate_bank_o]
                : af_valid_q[alternate_bank_o];
        end else begin
            live_y_known = (
                dreg_valid_q[alternate_bank_o][y_source_dreg_o]
            );
        end

        alu_needs_x = !(
            amf_o == 5'h10 || amf_o == 5'h11 || amf_o == 5'h14
            || amf_o == 5'h15 || amf_o == 5'h18
        );
        alu_needs_y = !(amf_o == 5'h1b || amf_o == 5'h1f);
        alu_needs_carry = (
            amf_o == 5'h12 || amf_o == 5'h16 || amf_o == 5'h1a
        );
        mac_needs_mr = (
            amf_o == 5'h02 || amf_o == 5'h03 || amf_o >= 5'h08
        );
        live_compute_known = 1'b0;
        if (computation_enable_o) begin
            if (is_mac_o) begin
                live_compute_known = (
                    live_x_known && live_y_known
                    && (!mac_needs_mr || live_mr_known)
                );
            end else begin
                live_compute_known = (
                    (!alu_needs_x || live_x_known)
                    && (!alu_needs_y || live_y_known)
                    && (!alu_needs_carry || astat_valid_mask_q[3])
                    && (!overflow_latch || astat_valid_mask_q[2])
                );
            end
        end
    end

    assign live_dm_next_i_valid = (
        dm_dag_i_valid && dm_dag_m_valid && dm_dag_l_valid
        && live_dm_dag_configuration_valid
    );
    assign live_pm_next_i_valid = (
        pm_dag_i_valid && pm_dag_m_valid && pm_dag_l_valid
        && live_pm_dag_configuration_valid
    );
    assign transaction_active_o = !reset_i && (pending_q || issue);
    assign instruction_complete_o = (
        transaction_active_o && transaction_complete_i
    );
    assign stalled_o = transaction_active_o && !transaction_complete_i;
    assign busy_o = stalled_o;

    always_comb begin
        if (pending_q) begin
            active_computation_enable = pending_computation_enable_q;
            active_is_mac = pending_is_mac_q;
            active_amf = pending_amf_q;
            active_pm_destination = pending_pm_destination_q;
            active_dm_destination = pending_dm_destination_q;
            active_pm_i_address = pending_pm_i_address_q;
            active_dm_i_address = pending_dm_i_address_q;
            active_bank = pending_bank_q;
            active_pm_address = pending_pm_address_q;
            active_pm_address_valid = pending_pm_address_valid_q;
            active_dm_address = pending_dm_address_q;
            active_dm_address_valid = pending_dm_address_valid_q;
            active_pm_next_i = pending_pm_next_i_q;
            active_pm_next_i_valid = pending_pm_next_i_valid_q;
            active_dm_next_i = pending_dm_next_i_q;
            active_dm_next_i_valid = pending_dm_next_i_valid_q;
            active_pm_dag_configuration_valid =
                pending_pm_dag_configuration_valid_q;
            active_dm_dag_configuration_valid =
                pending_dm_dag_configuration_valid_q;
            active_compute_known = pending_compute_known_q;
            active_alu_result = pending_alu_result_q;
            active_mac_result = pending_mac_result_q;
            active_alu_az = pending_alu_az_q;
            active_alu_an = pending_alu_an_q;
            active_alu_av = pending_alu_av_q;
            active_alu_ac = pending_alu_ac_q;
            active_alu_as = pending_alu_as_q;
            active_alu_as_write = pending_alu_as_write_q;
            active_mac_mv = pending_mac_mv_q;
        end else begin
            active_computation_enable = computation_enable_o;
            active_is_mac = is_mac_o;
            active_amf = amf_o;
            active_pm_destination = pm_destination_dreg_o;
            active_dm_destination = dm_destination_dreg_o;
            active_pm_i_address = pm_i_address_o;
            active_dm_i_address = dm_i_address_o;
            active_bank = alternate_bank_o;
            active_pm_address = live_pm_address;
            active_pm_address_valid = pm_dag_i_valid;
            active_dm_address = live_dm_address;
            active_dm_address_valid = dm_dag_i_valid;
            active_pm_next_i = live_pm_next_i;
            active_pm_next_i_valid = live_pm_next_i_valid;
            active_dm_next_i = live_dm_next_i;
            active_dm_next_i_valid = live_dm_next_i_valid;
            active_pm_dag_configuration_valid = (
                pm_dag_i_valid && pm_dag_m_valid && pm_dag_l_valid
                && live_pm_dag_configuration_valid
            );
            active_dm_dag_configuration_valid = (
                dm_dag_i_valid && dm_dag_m_valid && dm_dag_l_valid
                && live_dm_dag_configuration_valid
            );
            active_compute_known = live_compute_known;
            active_alu_result = live_alu_result;
            active_mac_result = live_mac_result;
            active_alu_az = live_alu_az;
            active_alu_an = live_alu_an;
            active_alu_av = live_alu_av;
            active_alu_ac = live_alu_ac;
            active_alu_as = live_alu_as;
            active_alu_as_write = live_alu_as_write;
            active_mac_mv = live_mac_mv;
        end
    end

    assign dm_select_o = transaction_active_o;
    assign dm_read_o = transaction_active_o;
    assign dm_address_o = (
        transaction_active_o && active_dm_address_valid
        ? active_dm_address : 14'h0000
    );
    assign dm_address_valid_o = (
        transaction_active_o && active_dm_address_valid
    );
    assign pm_select_o = transaction_active_o;
    assign pm_data_access_o = transaction_active_o;
    assign pm_read_o = transaction_active_o;
    assign pm_address_o = (
        transaction_active_o && active_pm_address_valid
        ? active_pm_address : 14'h0000
    );
    assign pm_address_valid_o = (
        transaction_active_o && active_pm_address_valid
    );

    assign compute_result_known_o = (
        transaction_active_o && active_computation_enable
        && active_compute_known
    );
    assign dm_dag_configuration_valid_o = (
        transaction_active_o && active_dm_dag_configuration_valid
    );
    assign pm_dag_configuration_valid_o = (
        transaction_active_o && active_pm_dag_configuration_valid
    );
    assign dm_i_write_o = instruction_complete_o;
    assign dm_i_write_known_o = (
        instruction_complete_o && active_dm_next_i_valid
    );
    assign pm_i_write_o = instruction_complete_o;
    assign pm_i_write_known_o = (
        instruction_complete_o && active_pm_next_i_valid
    );
    assign dm_dreg_write_o = instruction_complete_o;
    assign dm_dreg_write_known_o = (
        instruction_complete_o && dm_read_data_valid_i
    );
    assign pm_dreg_write_o = instruction_complete_o;
    assign pm_dreg_write_known_o = (
        instruction_complete_o && pm_read_data_valid_i
    );
    assign px_write_o = instruction_complete_o;
    assign px_write_known_o = (
        instruction_complete_o && pm_read_data_valid_i
    );
    assign alu_write_o = (
        instruction_complete_o && active_computation_enable && !active_is_mac
    );
    assign mac_write_o = (
        instruction_complete_o && active_computation_enable && active_is_mac
    );
    assign alu_status_write_o = alu_write_o;
    assign mac_status_write_o = mac_write_o;
    assign alu_result_o = (
        compute_result_known_o && !active_is_mac
        ? active_alu_result : 16'h0000
    );
    assign mac_result_o = (
        compute_result_known_o && active_is_mac
        ? active_mac_result : 40'h0000000000
    );

    assign probe_dreg_valid_o = (
        dreg_valid_q[alternate_bank_o][probe_dreg_code_i]
    );
    assign af_o = af_data;
    assign mf_o = mf_data;
    assign mr_o = mr_data;
    assign af_valid_o = af_valid_q[alternate_bank_o];
    assign mf_valid_o = mf_valid_q[alternate_bank_o];
    assign mr_valid_o = live_mr_known;
    assign astat_valid_mask_o = astat_valid_mask_q;
    assign px_o = px_valid_q ? px_q : 8'h00;
    assign px_valid_o = px_valid_q;

    assign register_write_enable_0 = (
        dreg_setup_enable || dm_dreg_write_known_o
    );
    assign register_write_enable_1 = pm_dreg_write_known_o;
    assign internal_conflict_o = (
        register_conflict || status_conflict || dag_conflict
        || dag_invalid_setup_kind
    );

    adsp2100_dag #(.BIT_REVERSE_CAPABLE(1'b1)) dm_dag (
        .i_i(dm_dag_i_data),
        .m_i(dm_dag_m_data),
        .l_i(dm_dag_l_data),
        .bit_reverse_enable_i(bit_reverse),
        .address_o(live_dm_address),
        .next_i_o(live_dm_next_i),
        .base_o(unused_dm_base),
        .circular_o(unused_dm_circular),
        .configuration_valid_o(live_dm_dag_configuration_valid)
    );

    adsp2100_dag #(.BIT_REVERSE_CAPABLE(1'b0)) pm_dag (
        .i_i(pm_dag_i_data),
        .m_i(pm_dag_m_data),
        .l_i(pm_dag_l_data),
        .bit_reverse_enable_i(1'b0),
        .address_o(live_pm_address),
        .next_i_o(live_pm_next_i),
        .base_o(unused_pm_base),
        .circular_o(unused_pm_circular),
        .configuration_valid_o(live_pm_dag_configuration_valid)
    );

    adsp2100_dag_register_file dag_registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .i_l_read_address_i(dm_i_address_o),
        .m_read_address_i(dm_m_address_o),
        .i_read_data_o(dm_dag_i_data),
        .i_read_valid_o(dm_dag_i_valid),
        .m_read_data_o(dm_dag_m_data),
        .m_read_valid_o(dm_dag_m_valid),
        .l_read_data_o(dm_dag_l_data),
        .l_read_valid_o(dm_dag_l_valid),
        .i_l_read_address_2_i(pm_i_address_o),
        .m_read_address_2_i(pm_m_address_o),
        .i_read_data_2_o(pm_dag_i_data),
        .i_read_valid_2_o(pm_dag_i_valid),
        .m_read_data_2_o(pm_dag_m_data),
        .m_read_valid_2_o(pm_dag_m_valid),
        .l_read_data_2_o(pm_dag_l_data),
        .l_read_valid_2_o(pm_dag_l_valid),
        .probe_address_i(probe_dag_address_i),
        .probe_i_data_o(probe_i_data_o),
        .probe_i_valid_o(probe_i_valid_o),
        .probe_m_data_o(probe_m_data_o),
        .probe_m_valid_o(probe_m_valid_o),
        .probe_l_data_o(probe_l_data_o),
        .probe_l_valid_o(probe_l_valid_o),
        .setup_write_i(dag_setup_enable),
        .setup_data_valid_i(1'b1),
        .setup_kind_i(dag_setup_kind_i),
        .setup_address_i(dag_setup_address_i),
        .setup_data_i(dag_setup_data_i),
        .i_write_enable_i(dm_i_write_o),
        .i_write_address_i(active_dm_i_address),
        .i_write_data_i(active_dm_next_i),
        .i_write_result_valid_i(active_dm_next_i_valid),
        .i_write_enable_2_i(pm_i_write_o),
        .i_write_address_2_i(active_pm_i_address),
        .i_write_data_2_i(active_pm_next_i),
        .i_write_result_valid_2_i(active_pm_next_i_valid),
        .invalid_setup_kind_o(dag_invalid_setup_kind),
        .write_conflict_o(dag_conflict)
    );

    adsp2100_register_file registers (
        .clk_i(clk_i),
        .alternate_bank_i(alternate_bank_o),
        .read_address_0_i(x_source_dreg_o),
        .read_address_1_i(y_source_dreg_o),
        .read_address_2_i(probe_dreg_code_i),
        .read_address_3_i(4'h0),
        .read_address_4_i(4'h0),
        .read_address_5_i(4'h0),
        .read_address_6_i(4'h0),
        .read_data_0_o(x_source_data),
        .read_data_1_o(y_source_data),
        .read_data_2_o(probe_dreg_data_o),
        .read_data_3_o(unused_read_3),
        .read_data_4_o(unused_additional_read_data[15:0]),
        .read_data_5_o(unused_additional_read_data[31:16]),
        .read_data_6_o(unused_additional_read_data[47:32]),
        .write_enable_0_i(register_write_enable_0),
        .write_address_0_i(
            dreg_setup_enable ? dreg_setup_code_i : active_dm_destination
        ),
        .write_data_0_i(
            dreg_setup_enable ? dreg_setup_data_i : dm_read_data_i
        ),
        .write_enable_1_i(register_write_enable_1),
        .write_address_1_i(active_pm_destination),
        .write_data_1_i(pm_read_data_i[23:8]),
        .write_enable_2_i(1'b0),
        .write_address_2_i(4'h0),
        .write_data_2_i(16'h0000),
        .sb_move_write_enable_i(1'b0),
        .sb_move_write_data_i(5'h00),
        .alu_write_enable_i(alu_write_o || af_setup_enable),
        .alu_destination_feedback_i(af_setup_enable),
        .alu_result_i(af_setup_enable ? af_setup_data_i : active_alu_result),
        .mac_write_enable_i(mac_write_o || mf_setup_enable),
        .mac_destination_feedback_i(mf_setup_enable),
        .mac_result_i(
            mf_setup_enable ? {8'h00, mf_setup_data_i, 16'h0000}
            : active_mac_result
        ),
        .shifter_sr_write_enable_i(1'b0),
        .shifter_sr_result_i(32'h00000000),
        .shifter_se_write_enable_i(1'b0),
        .shifter_se_result_i(8'h00),
        .shifter_sb_write_enable_i(1'b0),
        .shifter_sb_result_i(5'h00),
        .af_o(af_data),
        .mf_o(mf_data),
        .mr_o(mr_data),
        .se_o(unused_se),
        .sb_o(unused_sb),
        .sr_o(unused_sr),
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
        .alu_status_write_enable_i(alu_status_write_o),
        .alu_az_i(active_alu_az),
        .alu_an_i(active_alu_an),
        .alu_av_i(active_alu_av),
        .alu_ac_i(active_alu_ac),
        .alu_as_write_enable_i(active_alu_as_write),
        .alu_as_i(active_alu_as),
        .divide_status_write_enable_i(1'b0),
        .divide_aq_i(1'b0),
        .mac_status_write_enable_i(mac_status_write_o),
        .mac_mv_i(active_mac_mv),
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
        .icntl_o(unused_icntl),
        .imask_o(unused_imask),
        .alternate_bank_o(alternate_bank_o),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
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
            af_valid_q[0] <= 1'b0;
            af_valid_q[1] <= 1'b0;
            mf_valid_q[0] <= 1'b0;
            mf_valid_q[1] <= 1'b0;
            astat_valid_mask_q <= 8'h00;
            px_valid_q <= 1'b0;
        end else begin
            if (pending_q) begin
                if (transaction_complete_i) begin
                    pending_q <= 1'b0;
                end
            end else if (issue && !transaction_complete_i) begin
                pending_q <= 1'b1;
                pending_computation_enable_q <= computation_enable_o;
                pending_is_mac_q <= is_mac_o;
                pending_amf_q <= amf_o;
                pending_pm_destination_q <= pm_destination_dreg_o;
                pending_dm_destination_q <= dm_destination_dreg_o;
                pending_pm_i_address_q <= pm_i_address_o;
                pending_dm_i_address_q <= dm_i_address_o;
                pending_bank_q <= alternate_bank_o;
                pending_pm_address_q <= live_pm_address;
                pending_pm_address_valid_q <= pm_dag_i_valid;
                pending_dm_address_q <= live_dm_address;
                pending_dm_address_valid_q <= dm_dag_i_valid;
                pending_pm_next_i_q <= live_pm_next_i;
                pending_pm_next_i_valid_q <= live_pm_next_i_valid;
                pending_dm_next_i_q <= live_dm_next_i;
                pending_dm_next_i_valid_q <= live_dm_next_i_valid;
                pending_pm_dag_configuration_valid_q <= (
                    pm_dag_i_valid && pm_dag_m_valid && pm_dag_l_valid
                    && live_pm_dag_configuration_valid
                );
                pending_dm_dag_configuration_valid_q <= (
                    dm_dag_i_valid && dm_dag_m_valid && dm_dag_l_valid
                    && live_dm_dag_configuration_valid
                );
                pending_compute_known_q <= live_compute_known;
                pending_alu_result_q <= live_alu_result;
                pending_mac_result_q <= live_mac_result;
                pending_alu_az_q <= live_alu_az;
                pending_alu_an_q <= live_alu_an;
                pending_alu_av_q <= live_alu_av;
                pending_alu_ac_q <= live_alu_ac;
                pending_alu_as_q <= live_alu_as;
                pending_alu_as_write_q <= live_alu_as_write;
                pending_mac_mv_q <= live_mac_mv;
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
            if (af_setup_enable) begin
                af_valid_q[alternate_bank_o] <= 1'b1;
            end
            if (mf_setup_enable) begin
                mf_valid_q[alternate_bank_o] <= 1'b1;
            end
            if (px_setup_enable) begin
                px_q <= px_setup_data_i;
                px_valid_q <= 1'b1;
            end
            if (instruction_complete_o) begin
                dreg_valid_q[active_bank][active_dm_destination]
                    <= dm_read_data_valid_i;
                dreg_valid_q[active_bank][active_pm_destination]
                    <= pm_read_data_valid_i;
                px_valid_q <= pm_read_data_valid_i;
                if (pm_read_data_valid_i) begin
                    px_q <= pm_read_data_i[7:0];
                end
                if (active_computation_enable) begin
                    if (active_is_mac) begin
                        dreg_valid_q[active_bank][DREG_MR0]
                            <= active_compute_known;
                        dreg_valid_q[active_bank][DREG_MR1]
                            <= active_compute_known;
                        dreg_valid_q[active_bank][DREG_MR2]
                            <= active_compute_known;
                        astat_valid_mask_q[6] <= active_compute_known;
                    end else begin
                        dreg_valid_q[active_bank][DREG_AR]
                            <= active_compute_known;
                        astat_valid_mask_q[0] <= active_compute_known;
                        astat_valid_mask_q[1] <= active_compute_known;
                        astat_valid_mask_q[2] <= active_compute_known;
                        astat_valid_mask_q[3] <= active_compute_known;
                        if (active_amf == 5'h1f) begin
                            astat_valid_mask_q[4] <= active_compute_known;
                        end
                    end
                end
            end
        end
    end

`ifndef SYNTHESIS
    always_comb begin
        assert (dm_select_o == dm_read_o);
        assert (pm_select_o == pm_read_o);
        assert (pm_data_access_o == pm_select_o);
        assert (dm_select_o == pm_select_o);
        assert (!(alu_write_o && mac_write_o));
        assert (alu_write_o == alu_status_write_o);
        assert (mac_write_o == mac_status_write_o);
        assert (dm_i_write_o == pm_i_write_o);
        assert (dm_dreg_write_o == pm_dreg_write_o);
        assert (px_write_o == pm_dreg_write_o);
        if (stalled_o) begin
            assert (!instruction_complete_o);
            assert (!dm_i_write_o && !pm_i_write_o);
            assert (!dm_dreg_write_o && !pm_dreg_write_o && !px_write_o);
            assert (!alu_write_o && !mac_write_o);
        end
        if (!compute_result_known_o) begin
            assert (alu_result_o == 16'h0000);
            assert (mac_result_o == 40'h0000000000);
        end
        if (pending_q && !reset_i) begin
            assert (active_bank == alternate_bank_o);
            if (pending_dm_address_valid_q) begin
                assert (dm_address_o == pending_dm_address_q);
            end
            if (pending_pm_address_valid_q) begin
                assert (pm_address_o == pending_pm_address_q);
            end
        end
        if (transaction_active_o) begin
            assert (active_dm_destination <= DREG_MX1);
            assert (
                active_pm_destination >= DREG_AY0
                && active_pm_destination <= DREG_MY1
            );
            assert (!active_dm_i_address[2]);
            assert (active_pm_i_address[2]);
        end
        if (transaction_active_o && active_computation_enable) begin
            assert (
                active_is_mac
                ? (active_amf >= 5'h01 && active_amf <= 5'h0f)
                : (active_amf >= 5'h10)
            );
        end
        if (issue) begin
            assert (live_alu_write == (computation_enable_o && !is_mac_o));
            assert (live_mac_write == (computation_enable_o && is_mac_o));
        end
        if (instruction_complete_o) begin
            assert (!register_conflict);
            assert (!dag_conflict);
        end
    end
`endif
endmodule

`default_nettype wire
