`default_nettype none

// Bounded composition of all three real architectural PM clients behind one
// original-device instruction-cache monitor, one native PM controller, and
// normal BR/BG sequencing.
//
// Ordinary fetch, Type 5, and Type 13 share one architectural
// register/DAG/status/PX owner;
// their operand reads occur at issue and their captured parallel actions
// commit together at routed PM-data completion. The retained ordinary-fetch
// client retains the sole PC/opcode sequencer but admits the PM clients'
// cycle-start reads and completion writebacks at its architectural-state
// boundary. In the optional automatic mode, a legal retained Type 5 or Type
// 13 opcode issues its PM-data cycle, holds PC/opcode through a cache-miss
// recovery fetch, and installs the returned PC+1 opcode at whole-instruction
// retirement. HALT completes ordinary fetch before stopping; recognition
// during either PM-data client commits once, forces one external recovery for
// that client even on a cache hit, and stops after recovery. Unsourced BR/HALT
// overlap fails closed. Active-loop flow remains fail-closed because the issue-time
// termination ordering is not yet closed. Simultaneous externally directed
// Type 5 and Type 13 controls fail closed.
//
// Source: ADI-UM-1989 printed pp. 4-26--4-30 and 5-3--5-8;
// ADI-DATABOOK-1987 printed pp. 2-33--2-39.
module adsp2100_program_clients_owner_control_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        br_n_i,
    input  logic        halt_n_i,
    input  logic        dmack_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,
    input  logic [3:0]  irq_n_i,

    // Select the bounded fetched-opcode path.  When enabled, legal Type 5
    // and Type 13 words issue from the retained opcode and install the
    // returned sequential PC+1 word.  The external execute/opcode/address
    // controls below are then rejected rather than mixed with this path.
    input  logic        automatic_pm_flow_i,

    input  logic        type5_execute_i,
    input  logic [23:0] type5_opcode_i,
    input  logic [13:0] type5_next_fetch_address_i,
    input  logic        type5_next_fetch_address_valid_i,
    input  logic        type13_execute_i,
    input  logic [23:0] type13_opcode_i,
    input  logic [13:0] type13_next_fetch_address_i,
    input  logic        type13_next_fetch_address_valid_i,

    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,

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
    input  logic        sb_setup_write_i,
    input  logic [4:0]  sb_setup_data_i,
    input  logic        dag_setup_write_i,
    input  logic [1:0]  dag_setup_kind_i,
    input  logic [2:0]  dag_setup_address_i,
    input  logic [13:0] dag_setup_data_i,
    input  logic        px_setup_write_i,
    input  logic [7:0]  px_setup_data_i,
    input  logic [5:0]  linear_probe_code_i,
    input  logic [3:0]  pm_probe_dreg_code_i,
    input  logic [2:0]  pm_probe_dag_address_i,

    output logic        issue_boundary_o,
    output logic        client_execute_conflict_o,
    output logic        integration_conflict_o,
    output logic        automatic_pm_instruction_issue_o,
    output logic        automatic_pm_instruction_retire_o,
    output logic        automatic_pm_flow_blocked_o,
    output logic [1:0]  halt_mode_o,
    output logic        halt_recognized_o,
    output logic        halt_stop_event_o,
    output logic        halt_force_fetch_issue_o,
    output logic        halt_resume_event_o,
    output logic        halt_release_blocked_o,
    output logic        halt_phase_hold_o,
    output logic        effective_phase_advance_o,
    output logic        halted_o,
    output logic        halt_br_conflict_o,
    output logic        halt_attachment_conflict_o,

    output logic        linear_fetch_request_presented_o,
    output logic        linear_instruction_issue_o,
    output logic        linear_retire_event_o,
    output logic        linear_instruction_valid_o,
    output logic [13:0] linear_pc_o,
    output logic [23:0] linear_opcode_o,
    output logic [15:0] linear_probe_data_o,

    output logic        type5_request_presented_o,
    output logic        type5_request_accepted_o,
    output logic        type5_retry_pending_o,
    output logic        type5_data_action_complete_o,
    output logic        type5_instruction_complete_o,
    output logic [23:0] type5_next_instruction_o,
    output logic        type5_next_instruction_valid_o,
    output logic [15:0] type5_probe_dreg_data_o,
    output logic        type5_probe_dreg_valid_o,
    output logic [7:0]  type5_px_o,
    output logic        type5_px_valid_o,

    output logic        type13_request_presented_o,
    output logic        type13_request_accepted_o,
    output logic        type13_retry_pending_o,
    output logic        type13_data_action_complete_o,
    output logic        type13_instruction_complete_o,
    output logic [23:0] type13_next_instruction_o,
    output logic        type13_next_instruction_valid_o,
    output logic [15:0] type13_probe_dreg_data_o,
    output logic        type13_probe_dreg_valid_o,
    output logic [7:0]  type13_px_o,
    output logic        type13_px_valid_o,

    output logic        cache_fill_o,
    output logic        cache_fill_accepted_o,
    output logic [13:0] cache_region_start_o,
    output logic        cache_region_start_valid_o,
    output logic [4:0]  cache_region_count_o,

    output logic [2:0]  bus_mode_o,
    output logic        issue_inhibit_o,
    output logic        bg_n_o,
    output logic        bus_relinquished_o,
    output logic        request_blocked_o,
    output logic        request_conflict_o,
    output logic        request_out_of_phase_o,
    output logic [2:0]  request_accepted_o,
    output logic [2:0]  completion_event_o,
    output logic [1:0]  owner_o,
    output logic        pm_bus_active_o,

    output logic        pm_address_output_enable_o,
    output logic        pm_control_output_enable_o,
    output logic        pm_data_output_enable_o,
    output logic [13:0] pma_o,
    output logic        pma_valid_o,
    output logic        pmda_o,
    output logic        pmda_valid_o,
    output logic        pms_n_o,
    output logic        pmrd_n_o,
    output logic        pmwr_n_o,
    output logic [23:0] pmd_write_data_o,
    output logic        pmd_write_data_valid_o
);
    import adsp2100_pkg::*;
    import adsp2100_register_pkg::*;

    logic type5_execute;
    logic type13_execute;
    logic [23:0] type5_opcode;
    logic [23:0] type13_opcode;
    logic [13:0] type5_next_fetch_address;
    logic type5_next_fetch_address_valid;
    logic [13:0] type13_next_fetch_address;
    logic type13_next_fetch_address_valid;
    logic automatic_type5_instruction;
    logic automatic_type13_instruction;
    logic automatic_pm_instruction_active;
    logic automatic_control_conflict;
    logic linear_pm_sequential_allowed;
    logic linear_pm_flow_blocked;
    logic automatic_pm_completion;
    logic [23:0] automatic_pm_next_opcode;
    logic automatic_pm_next_opcode_valid;
    logic cache_lookup_hit;
    logic [23:0] cache_lookup_instruction;
    logic cache_lookup_instruction_valid;
    logic [13:0] cache_lookup_address;
    logic cache_lookup_address_valid;
    logic cache_region_restarted_unused;
    logic cache_oldest_replaced_unused;

    logic type5_class_valid_unused;
    logic type5_action_valid_unused;
    logic type5_unsupported_unused;
    logic type5_accepted;
    logic type5_transaction_active_unused;
    logic type5_held_transaction_unused;
    logic type5_busy_unused;
    logic type5_invalid_opcode;
    logic type5_integration_conflict;
    logic type5_internal_conflict;
    logic type5_cache_selected_unused;
    logic type5_recovery_required_unused;
    logic type5_recovery_fetch;
    logic type5_event_boundary_unused;
    logic type5_pm_select;
    logic type5_pm_data_access;
    logic type5_pm_read_unused;
    logic type5_pm_write;
    logic [13:0] type5_pm_address;
    logic type5_pm_address_valid;
    logic [23:0] type5_pm_write_data;
    logic type5_pm_write_data_valid;
    logic [23:0] type5_fetched_instruction;
    logic type5_fetched_instruction_valid;
    logic type5_dm_access_unused;
    logic type5_computation_enable;
    logic type5_is_mac;
    logic type5_destination_feedback;
    logic [4:0] type5_amf;
    logic [1:0] type5_yop_unused;
    logic [2:0] type5_xop_unused;
    logic [3:0] type5_x_source;
    logic [3:0] type5_y_source;
    logic [3:0] type5_memory_dreg;
    logic [2:0] type5_i_address;
    logic [2:0] type5_m_address;
    logic type5_compute_result_known;
    logic type5_dag_configuration_valid_unused;
    logic type5_i_write;
    logic [2:0] type5_i_write_address;
    logic [13:0] type5_i_write_data;
    logic type5_i_write_known;
    logic type5_dreg_write;
    logic [3:0] type5_dreg_write_address;
    logic [15:0] type5_dreg_write_data;
    logic type5_dreg_write_known;
    logic type5_px_write;
    logic [7:0] type5_px_write_data;
    logic type5_px_write_known;
    logic type5_alu_write;
    logic type5_mac_write;
    logic type5_active_destination_feedback;
    logic [4:0] type5_active_amf;
    logic [15:0] type5_alu_result;
    logic [39:0] type5_mac_result;
    logic type5_alu_az;
    logic type5_alu_an;
    logic type5_alu_av;
    logic type5_alu_ac;
    logic type5_alu_as_write;
    logic type5_alu_as;
    logic type5_mac_mv;
    logic [23:0] type5_cache_instruction_q;
    logic type5_cache_instruction_valid_q;

    logic type13_class_valid_unused;
    logic type13_action_valid_unused;
    logic type13_unsupported_unused;
    logic type13_accepted;
    logic type13_transaction_active_unused;
    logic type13_held_transaction_unused;
    logic type13_busy_unused;
    logic type13_invalid_opcode;
    logic type13_integration_conflict;
    logic type13_internal_conflict;
    logic type13_cache_selected_unused;
    logic type13_recovery_required_unused;
    logic type13_recovery_fetch;
    logic type13_event_boundary_unused;
    logic type13_pm_select;
    logic type13_pm_data_access;
    logic type13_pm_read_unused;
    logic type13_pm_write;
    logic [13:0] type13_pm_address;
    logic type13_pm_address_valid;
    logic [23:0] type13_pm_write_data;
    logic type13_pm_write_data_valid;
    logic [23:0] type13_fetched_instruction;
    logic type13_fetched_instruction_valid;
    logic type13_dm_access_unused;
    logic type13_unavailable_xop_unused;
    logic type13_destination_collision_unused;
    logic type13_write_direction_unused;
    logic [3:0] type13_sf_unused;
    logic [2:0] type13_xop_unused;
    logic [3:0] type13_shifter_source;
    logic [3:0] type13_memory_dreg;
    logic [2:0] type13_i_address;
    logic [2:0] type13_m_address;
    logic type13_shifter_result_known;
    logic type13_dag_configuration_valid_unused;
    logic type13_i_write;
    logic [2:0] type13_i_write_address;
    logic [13:0] type13_i_write_data;
    logic type13_i_write_known;
    logic type13_dreg_write;
    logic [3:0] type13_dreg_write_address;
    logic [15:0] type13_dreg_write_data;
    logic type13_dreg_write_known;
    logic type13_px_write;
    logic [7:0] type13_px_write_data;
    logic type13_px_write_known;
    logic type13_sr_write;
    logic type13_se_write;
    logic type13_sb_write;
    logic type13_ss_write;
    logic [31:0] type13_sr_result;
    logic [7:0] type13_se_result;
    logic [4:0] type13_sb_result;
    logic type13_ss_result;
    logic [3:0] type13_active_sf;
    logic type13_active_exp_lo_destination;
    logic [23:0] type13_cache_instruction_q;
    logic type13_cache_instruction_valid_q;

    logic linear_instruction_setup_accepted_unused;
    logic [13:0] linear_fetch_address;
    logic linear_trap_event_unused;
    logic linear_interrupt_recognition_unused;
    logic linear_interrupt_entry_unused;
    logic linear_interrupt_vector_issue_unused;
    logic linear_interrupt_vector_fetch_unused;
    logic [1:0] linear_interrupt_level_unused;
    logic [13:0] linear_interrupt_vector_unused;
    logic [3:0] linear_interrupt_pending_unused;
    logic linear_interrupt_vectoring_unused;
    logic linear_interrupt_configuration_invalid_unused;
    logic linear_interrupt_reset_baseline_unused;
    logic linear_interrupt_adjacent_conflict_unused;
    logic linear_transaction_pending_unused;
    logic linear_unsupported_unused;
    logic linear_reserved_unused;
    logic linear_phase_conflict;
    logic linear_integration_conflict;
    logic linear_internal_conflict;
    logic linear_provisional_unused;
    logic [4:0] linear_icntl_unused;
    logic [3:0] linear_imask_unused;
    logic [13:0] linear_cntr_unused;
    logic linear_cntr_valid_unused;
    logic [7:0] linear_sstat_unused;
    logic [2:0] linear_count_depth_unused;
    logic linear_count_overflow_unused;
    logic linear_status_restore_event;
    logic [7:0] linear_status_restore_astat_valid_mask;
    logic [3:0] linear_status_restore_mstat_valid_mask;
    logic linear_status_restore_imask_valid;

    logic state_three_boundary_unused;
    logic bus_request_recognized_unused;
    logic grant_assert_event_unused;
    logic release_recognized_unused;
    logic grant_release_event_unused;
    logic resume_event_unused;
    logic request_withdrawn_unused;
    logic release_cancelled_unused;
    logic normal_bus_relinquished_unused;
    logic normal_bg_n_unused;
    logic reset_br_request_unused;
    logic request_ready_unused;
    logic [2:0] read_sample_event_unused;
    logic response_valid_unused;
    logic response_write_unused;
    logic [23:0] response_read_data_unused;
    logic response_read_data_valid_unused;
    logic bus_issue_inhibit;
    logic halt_instruction_issue_inhibit;
    logic halt_state_three_boundary_unused;
    logic halt_phase_conflict;
    logic halt_pm_data_cycle;
    logic halt_late_force_request;
    logic halt_control_halt_n;
    logic halt_control_br_n;
    logic halt_owner_conflict;

    logic [3:0] setup_count;
    logic shared_setup_accept;
    logic shared_setup_conflict;
    logic shared_mstat_client_conflict;
    logic shared_move_write;
    logic [5:0] shared_move_code;
    logic [15:0] shared_move_data;
    logic shared_alu_setup;
    logic shared_mac_setup;
    logic shared_sb_setup;
    logic [15:0] shared_memory_source_data;
    logic [15:0] shared_x_source_data;
    logic [15:0] shared_y_source_data;
    logic [15:0] shared_probe_data;
    logic [13:0] shared_dag_i_data;
    logic shared_dag_i_valid;
    logic [13:0] shared_dag_m_data;
    logic shared_dag_m_valid;
    logic [13:0] shared_dag_l_data;
    logic shared_dag_l_valid;
    logic [7:0] shared_astat;
    logic [3:0] shared_mstat;
    logic [7:0] shared_px;
    logic shared_alternate_bank;
    logic [15:0] shared_af;
    logic [15:0] shared_mf;
    logic [39:0] shared_mr;
    logic [7:0] shared_se;
    logic [4:0] shared_sb;
    logic [31:0] shared_sr;
    logic [15:0] shared_dreg_valid_q [0:1];
    logic shared_af_valid_q [0:1];
    logic shared_mf_valid_q [0:1];
    logic shared_sb_valid_q [0:1];
    logic [7:0] shared_astat_valid_mask_q;
    logic [3:0] shared_mstat_valid_mask_q;
    logic shared_imask_valid_q;
    logic shared_px_valid_q;
    logic shared_x_source_valid;
    logic shared_y_source_valid;
    logic shared_memory_source_valid;
    logic shared_af_valid;
    logic shared_mf_valid;
    logic shared_mr_valid;
    logic shared_se_valid;
    logic shared_sb_valid;
    logic shared_sr_valid;
    logic shared_probe_dreg_valid;
    logic [3:0] shared_dreg_read_address_1;
    logic [3:0] shared_dreg_read_address_2;
    logic [3:0] shared_memory_read_address;
    logic [2:0] shared_dag_i_address;
    logic [2:0] shared_dag_m_address;
    logic [3:0] shared_dag_setup_index;
    logic shared_dag_setup_kind_invalid;
    logic shared_state_action_conflict;
    logic linear_state_action_conflict;
    logic shared_probe_conflict;
    logic linear_type6_retire;
    logic linear_type7_retire;
    logic linear_type17_retire;
    logic linear_type18_retire;
    logic linear_type17_source_valid;

    logic validity_type8_action_valid;
    logic validity_type8_is_mac;
    logic validity_type8_destination_feedback;
    logic [4:0] validity_type8_amf;
    logic [1:0] validity_type8_yop;
    logic [3:0] validity_type8_x_source;
    logic [3:0] validity_type8_y_source;
    logic [3:0] validity_type8_move_destination;
    logic [3:0] validity_type8_move_source;
    logic validity_type9_action_valid;
    logic validity_type9_nop_action;
    logic validity_type9_is_mac;
    logic validity_type9_destination_feedback;
    logic [4:0] validity_type9_amf;
    logic [1:0] validity_type9_yop;
    logic [3:0] validity_type9_condition;
    logic [3:0] validity_type9_x_source;
    logic [3:0] validity_type9_y_source;
    logic validity_type9_condition_true;
    logic validity_type9_condition_known;
    logic validity_selected_is_mac;
    logic [4:0] validity_selected_amf;
    logic [1:0] validity_selected_yop;
    logic [3:0] validity_selected_x_source;
    logic [3:0] validity_selected_y_source;
    logic validity_selected_x_known;
    logic validity_selected_y_known;
    logic validity_selected_mr_known;
    logic validity_selected_compute_known;
    logic validity_alu_needs_x;
    logic validity_alu_needs_y;
    logic validity_alu_needs_carry;
    logic validity_mac_needs_mr;
    logic validity_compute_stage_valid_q;
    logic validity_compute_stage_type8_q;
    logic validity_compute_stage_is_mac_q;
    logic validity_compute_stage_destination_feedback_q;
    logic [4:0] validity_compute_stage_amf_q;
    logic [3:0] validity_compute_stage_move_destination_q;
    logic validity_compute_stage_move_known_q;
    logic validity_compute_stage_result_known_q;
    logic validity_compute_stage_condition_known_q;
    logic validity_compute_stage_condition_true_q;

    logic validity_type14_action_valid;
    logic [3:0] validity_type14_sf;
    logic [3:0] validity_type14_source;
    logic [3:0] validity_type14_move_destination;
    logic [3:0] validity_type14_move_source;
    logic validity_type15_action_valid;
    logic [3:0] validity_type15_sf;
    logic [3:0] validity_type15_source;
    logic validity_type16_action_valid;
    logic [3:0] validity_type16_sf;
    logic [3:0] validity_type16_source;
    logic [3:0] validity_type16_condition;
    logic validity_type16_condition_true;
    logic validity_type16_condition_known;
    logic [3:0] validity_selected_shift_sf;
    logic [3:0] validity_selected_shift_source;
    logic validity_selected_shift_source_known;
    logic validity_selected_shift_result_known;
    logic validity_shift_stage_valid_q;
    logic validity_shift_stage_type14_q;
    logic [3:0] validity_shift_stage_sf_q;
    logic [3:0] validity_shift_stage_move_destination_q;
    logic validity_shift_stage_move_known_q;
    logic validity_shift_stage_result_known_q;
    logic validity_shift_stage_condition_known_q;
    logic validity_shift_stage_condition_true_q;
    logic validity_shift_stage_exp_lo_preserve_q;

    logic validity_type23_action_valid;
    logic [3:0] validity_type23_divisor_source;
    logic validity_type24_action_valid;
    logic [3:0] validity_type24_divisor_source;
    logic [3:0] validity_type24_upper_source;
    logic validity_type24_upper_feedback;
    logic validity_type25_action_valid;
    logic validity_divide_result_known;
    logic validity_divide_stage_valid_q;
    logic validity_divide_stage_result_known_q;
    logic validity_saturation_stage_valid_q;
    logic validity_saturation_stage_condition_known_q;
    logic validity_saturation_stage_condition_true_q;
    logic validity_saturation_stage_result_known_q;

    logic unused_observation;

    function automatic logic condition_state_known(
        input logic [3:0] condition,
        input logic       az_valid,
        input logic       an_valid,
        input logic       av_valid,
        input logic       ac_valid,
        input logic       as_valid,
        input logic       mv_valid,
        input logic       cntr_valid
    );
        unique case (condition)
            4'h0,
            4'h1: condition_state_known = az_valid;
            4'h2,
            4'h3: condition_state_known = az_valid && an_valid && av_valid;
            4'h4,
            4'h5: condition_state_known = an_valid && av_valid;
            4'h6,
            4'h7: condition_state_known = av_valid;
            4'h8,
            4'h9: condition_state_known = ac_valid;
            4'ha,
            4'hb: condition_state_known = as_valid;
            4'hc,
            4'hd: condition_state_known = mv_valid;
            4'he: condition_state_known = cntr_valid;
            4'hf: condition_state_known = 1'b1;
            default: condition_state_known = 1'b0;
        endcase
    endfunction

    assign client_execute_conflict_o = (
        !reset_i && !automatic_pm_flow_i
        && type5_execute_i && type13_execute_i
    );
    // HALT and normal BR/BG are independently source-backed, but their
    // simultaneous priority is not.  Admit only the already active owner;
    // reject a same-boundary pair and report every cross-request explicitly.
    assign halt_control_halt_n = reset_i ? 1'b1 : (
        halt_n_i || (bus_mode_o != 3'd0) || !br_n_i
    );
    assign halt_control_br_n = reset_i ? br_n_i : (
        br_n_i || (halt_mode_o != 2'd0) || !halt_n_i
    );
    assign halt_br_conflict_o = !reset_i && (
        (!halt_n_i && !br_n_i)
        || (!halt_n_i && bus_mode_o != 3'd0)
        || (!br_n_i && halt_mode_o != 2'd0)
    );
    assign halt_pm_data_cycle = (
        pm_bus_active_o && pmda_valid_o && pmda_o
    );
    assign halt_late_force_request = !reset_i && (
        halt_mode_o == 2'd3
        || (halt_recognized_o && halt_pm_data_cycle)
    );
    assign halt_owner_conflict = (
        halt_recognized_o && !pm_bus_active_o
    );
    assign issue_inhibit_o = (
        bus_issue_inhibit || halt_instruction_issue_inhibit
    );
    assign automatic_control_conflict = (
        !reset_i && automatic_pm_flow_i
        && (type5_execute_i || type13_execute_i)
    );
    assign setup_count = (
        {3'h0, astat_setup_write_i}
        + {3'h0, mstat_setup_write_i}
        + {3'h0, dreg_setup_write_i}
        + {3'h0, af_setup_write_i}
        + {3'h0, mf_setup_write_i}
        + {3'h0, sb_setup_write_i}
        + {3'h0, dag_setup_write_i}
        + {3'h0, px_setup_write_i}
    );
    assign shared_setup_accept = issue_boundary_o
        && setup_count == 4'h1 && !type5_execute && !type13_execute
        && !type5_transaction_active_unused
        && !type13_transaction_active_unused;
    assign shared_dag_setup_kind_invalid = dag_setup_write_i
        && dag_setup_kind_i == 2'b11;
    assign shared_setup_conflict = !reset_i && (
        setup_count > 4'h1
        || (setup_count != 4'h0
            && (type5_execute_i || type13_execute_i
                || type5_transaction_active_unused
                || type13_transaction_active_unused))
        || (setup_count != 4'h0 && !issue_boundary_o)
        || shared_dag_setup_kind_invalid
    );
    assign type5_opcode = automatic_pm_flow_i
        ? linear_opcode_o : type5_opcode_i;
    assign type13_opcode = automatic_pm_flow_i
        ? linear_opcode_o : type13_opcode_i;
    assign type5_next_fetch_address = automatic_pm_flow_i
        ? (linear_pc_o + 14'h0001) : type5_next_fetch_address_i;
    assign type5_next_fetch_address_valid = automatic_pm_flow_i
        ? 1'b1 : type5_next_fetch_address_valid_i;
    assign type13_next_fetch_address = automatic_pm_flow_i
        ? (linear_pc_o + 14'h0001) : type13_next_fetch_address_i;
    assign type13_next_fetch_address_valid = automatic_pm_flow_i
        ? 1'b1 : type13_next_fetch_address_valid_i;
    assign automatic_type5_instruction = (
        automatic_pm_flow_i && linear_instruction_valid_o
        && type5_action_valid_unused
    );
    assign automatic_type13_instruction = (
        automatic_pm_flow_i && linear_instruction_valid_o
        && type13_action_valid_unused
    );
    assign automatic_pm_instruction_active = (
        automatic_type5_instruction || automatic_type13_instruction
    );
    assign shared_mstat_client_conflict = (
        !reset_i && issue_boundary_o
        && shared_mstat_valid_mask_q != 4'hf
        && (
            (automatic_pm_flow_i && automatic_pm_instruction_active)
            || (!automatic_pm_flow_i && (type5_execute_i || type13_execute_i))
        )
    );
    assign type5_execute = automatic_pm_flow_i
        ? (
            automatic_type5_instruction && linear_pm_sequential_allowed
            && issue_boundary_o && setup_count == 4'h0
            && !shared_mstat_client_conflict
            && !type5_held_transaction_unused
            && !type13_held_transaction_unused
        )
        : (
            type5_execute_i && !client_execute_conflict_o && issue_boundary_o
            && setup_count == 4'h0 && !shared_mstat_client_conflict
        );
    assign type13_execute = automatic_pm_flow_i
        ? (
            automatic_type13_instruction && linear_pm_sequential_allowed
            && issue_boundary_o && setup_count == 4'h0
            && !shared_mstat_client_conflict
            && !type5_held_transaction_unused
            && !type13_held_transaction_unused
        )
        : (
            type13_execute_i && !client_execute_conflict_o && issue_boundary_o
            && setup_count == 4'h0 && !shared_mstat_client_conflict
        );
    assign issue_boundary_o = (
        !reset_i && !issue_inhibit_o && !bus_relinquished_o
        && effective_phase_advance_o && phase_i == PHASE_STATE_8
    );

    always_comb begin
        cache_lookup_address = 14'h0000;
        cache_lookup_address_valid = 1'b0;
        if (type5_execute && !type13_execute) begin
            cache_lookup_address = type5_next_fetch_address;
            cache_lookup_address_valid = type5_next_fetch_address_valid;
        end else if (type13_execute && !type5_execute) begin
            cache_lookup_address = type13_next_fetch_address;
            cache_lookup_address_valid = type13_next_fetch_address_valid;
        end
    end

    assign type5_request_presented_o = issue_boundary_o && type5_pm_select;
    assign type13_request_presented_o = issue_boundary_o && type13_pm_select;
    assign type5_request_accepted_o = request_accepted_o[1];
    assign type13_request_accepted_o = request_accepted_o[2];
    assign type5_retry_pending_o = (
        type5_request_presented_o && !type5_request_accepted_o
    );
    assign type13_retry_pending_o = (
        type13_request_presented_o && !type13_request_accepted_o
    );

    assign cache_fill_o = (
        (|completion_event_o) && pmda_valid_o && !pmda_o
    );
    assign type5_next_instruction_valid_o = (
        (type5_data_action_complete_o && type5_instruction_complete_o
            && type5_cache_instruction_valid_q)
        || type5_fetched_instruction_valid
    );
    assign type5_next_instruction_o = type5_fetched_instruction_valid
        ? type5_fetched_instruction : type5_cache_instruction_q;
    assign type13_next_instruction_valid_o = (
        (type13_data_action_complete_o && type13_instruction_complete_o
            && type13_cache_instruction_valid_q)
        || type13_fetched_instruction_valid
    );
    assign type13_next_instruction_o = type13_fetched_instruction_valid
        ? type13_fetched_instruction : type13_cache_instruction_q;
    assign automatic_pm_completion = automatic_pm_flow_i
        && (type5_instruction_complete_o || type13_instruction_complete_o);
    assign automatic_pm_next_opcode = type5_instruction_complete_o
        ? type5_next_instruction_o : type13_next_instruction_o;
    assign automatic_pm_next_opcode_valid = type5_instruction_complete_o
        ? type5_next_instruction_valid_o : type13_next_instruction_valid_o;
    assign automatic_pm_instruction_issue_o = automatic_pm_flow_i
        && (
            (type5_accepted && type5_request_accepted_o)
            || (type13_accepted && type13_request_accepted_o)
        );
    assign automatic_pm_instruction_retire_o = automatic_pm_completion
        && linear_retire_event_o;
    assign automatic_pm_flow_blocked_o = automatic_pm_flow_i
        && linear_pm_flow_blocked;

    assign integration_conflict_o = (
        client_execute_conflict_o || automatic_control_conflict
        || request_conflict_o
        || request_out_of_phase_o || linear_phase_conflict
        || linear_integration_conflict || linear_internal_conflict
        || type5_integration_conflict || type5_internal_conflict
        || type13_integration_conflict || type13_internal_conflict
        || type5_invalid_opcode || type13_invalid_opcode
        || shared_setup_conflict || shared_mstat_client_conflict
        || shared_state_action_conflict
        || linear_state_action_conflict || halt_phase_conflict
        || halt_br_conflict_o || halt_owner_conflict
        || halt_attachment_conflict_o
    );

    always_comb begin
        shared_dag_setup_index = 4'h0;
        unique case (dag_setup_kind_i)
            2'b00: shared_dag_setup_index = {2'b00, dag_setup_address_i[1:0]};
            2'b01: shared_dag_setup_index = {2'b01, dag_setup_address_i[1:0]};
            2'b10: shared_dag_setup_index = {2'b10, dag_setup_address_i[1:0]};
            default: shared_dag_setup_index = 4'h0;
        endcase

        shared_move_write = 1'b0;
        shared_move_code = 6'h00;
        shared_move_data = 16'h0000;
        if (shared_setup_accept) begin
            if (astat_setup_write_i) begin
                shared_move_write = 1'b1;
                shared_move_code = 6'h30;
                shared_move_data = {8'h00, astat_setup_data_i};
            end else if (mstat_setup_write_i) begin
                shared_move_write = 1'b1;
                shared_move_code = 6'h31;
                shared_move_data = {12'h000, mstat_setup_data_i};
            end else if (dreg_setup_write_i) begin
                shared_move_write = 1'b1;
                shared_move_code = {2'b00, dreg_setup_code_i};
                shared_move_data = dreg_setup_data_i;
            end else if (dag_setup_write_i) begin
                shared_move_write = 1'b1;
                shared_move_code = {
                    dag_setup_address_i[2] ? 2'b10 : 2'b01,
                    shared_dag_setup_index
                };
                shared_move_data = {2'b00, dag_setup_data_i};
            end else if (px_setup_write_i) begin
                shared_move_write = 1'b1;
                shared_move_code = 6'h37;
                shared_move_data = {8'h00, px_setup_data_i};
            end
        end
        if (type5_px_write || type13_px_write) begin
            shared_move_write = 1'b1;
            shared_move_code = 6'h37;
            shared_move_data = {
                8'h00,
                type5_px_write ? type5_px_write_data : type13_px_write_data
            };
        end
    end

    assign shared_alu_setup = shared_setup_accept && af_setup_write_i;
    assign shared_mac_setup = shared_setup_accept && mf_setup_write_i;
    assign shared_sb_setup = shared_setup_accept && sb_setup_write_i;
    assign shared_state_action_conflict = !reset_i && (
        (type5_data_action_complete_o && type13_data_action_complete_o)
        || ((type5_data_action_complete_o || type13_data_action_complete_o)
            && shared_setup_accept)
    );

    assign shared_dreg_read_address_1 = type5_execute
        ? type5_x_source : type13_shifter_source;
    assign shared_dreg_read_address_2 = type5_y_source;
    assign shared_memory_read_address = type5_execute
        ? type5_memory_dreg : type13_memory_dreg;
    assign shared_dag_i_address = type5_execute
        ? type5_i_address : type13_i_address;
    assign shared_dag_m_address = type5_execute
        ? type5_m_address : type13_m_address;
    assign shared_x_source_valid =
        shared_mstat_valid_mask_q[0]
        && shared_dreg_valid_q[shared_alternate_bank]
            [shared_dreg_read_address_1];
    assign shared_y_source_valid =
        shared_mstat_valid_mask_q[0]
        && shared_dreg_valid_q[shared_alternate_bank]
            [shared_dreg_read_address_2];
    assign shared_memory_source_valid =
        shared_mstat_valid_mask_q[0]
        && shared_dreg_valid_q[shared_alternate_bank]
            [shared_memory_read_address];
    assign shared_af_valid = shared_mstat_valid_mask_q[0]
        && shared_af_valid_q[shared_alternate_bank];
    assign shared_mf_valid = shared_mstat_valid_mask_q[0]
        && shared_mf_valid_q[shared_alternate_bank];
    assign shared_mr_valid =
        shared_mstat_valid_mask_q[0]
        && shared_dreg_valid_q[shared_alternate_bank][DREG_MR0]
        && shared_dreg_valid_q[shared_alternate_bank][DREG_MR1]
        && shared_dreg_valid_q[shared_alternate_bank][DREG_MR2];
    assign shared_se_valid =
        shared_mstat_valid_mask_q[0]
        && shared_dreg_valid_q[shared_alternate_bank][DREG_SE];
    assign shared_sb_valid = shared_mstat_valid_mask_q[0]
        && shared_sb_valid_q[shared_alternate_bank];
    assign shared_sr_valid =
        shared_mstat_valid_mask_q[0]
        && shared_dreg_valid_q[shared_alternate_bank][DREG_SR0]
        && shared_dreg_valid_q[shared_alternate_bank][DREG_SR1];
    always_comb begin
        shared_probe_data = 16'h0000;
        shared_probe_conflict = 1'b1;
        if (linear_probe_code_i == {2'b00, pm_probe_dreg_code_i}) begin
            shared_probe_data = linear_probe_data_o;
            shared_probe_conflict = 1'b0;
        end
        if (
            (type5_execute || type13_execute)
            && pm_probe_dreg_code_i == shared_memory_read_address
        ) begin
            shared_probe_data = shared_memory_source_data;
            shared_probe_conflict = 1'b0;
        end else if (
            (type5_execute || type13_execute)
            && pm_probe_dreg_code_i == shared_dreg_read_address_1
        ) begin
            shared_probe_data = shared_x_source_data;
            shared_probe_conflict = 1'b0;
        end else if (
            type5_execute
            && pm_probe_dreg_code_i == shared_dreg_read_address_2
        ) begin
            shared_probe_data = shared_y_source_data;
            shared_probe_conflict = 1'b0;
        end
    end
    assign shared_probe_dreg_valid = !shared_probe_conflict
        && shared_mstat_valid_mask_q[0]
        && shared_dreg_valid_q[shared_alternate_bank][pm_probe_dreg_code_i];
    assign linear_type6_retire = linear_retire_event_o
        && shared_mstat_valid_mask_q[0]
        && (linear_opcode_o & 24'hf00000) == 24'h400000;
    assign linear_type7_retire = linear_retire_event_o
        && (linear_opcode_o & 24'hf00000) == 24'h300000;
    assign linear_type17_retire = linear_retire_event_o
        && (linear_opcode_o & 24'hfff000) == 24'h0d0000;
    assign linear_type18_retire = linear_retire_event_o
        && (linear_opcode_o & 24'hfff00f) == 24'h0c0000;

    // Reuse the canonical class decoders for the validity sidecar. This does
    // not create a second opcode definition: the sidecar observes the same
    // Type 8/Type 9 selectors as the executing retained-fetch client.
    /* verilator lint_off PINCONNECTEMPTY */
    adsp2100_compute_move_decode validity_type8_decode (
        .opcode_i(linear_opcode_o),
        .class_valid_o(),
        .action_valid_o(validity_type8_action_valid),
        .unsupported_subencoding_o(),
        .unverified_amf_zero_o(),
        .destination_collision_o(),
        .is_mac_o(validity_type8_is_mac),
        .destination_feedback_o(validity_type8_destination_feedback),
        .amf_o(validity_type8_amf),
        .yop_o(validity_type8_yop),
        .xop_o(),
        .x_source_dreg_o(validity_type8_x_source),
        .y_source_dreg_o(validity_type8_y_source),
        .move_destination_dreg_o(validity_type8_move_destination),
        .move_source_dreg_o(validity_type8_move_source)
    );

    adsp2100_conditional_compute_decode validity_type9_decode (
        .opcode_i(linear_opcode_o),
        .class_valid_o(),
        .action_valid_o(validity_type9_action_valid),
        .unsupported_subencoding_o(),
        .nop_action_o(validity_type9_nop_action),
        .is_mac_o(validity_type9_is_mac),
        .is_alu_o(),
        .destination_feedback_o(validity_type9_destination_feedback),
        .amf_o(validity_type9_amf),
        .yop_o(validity_type9_yop),
        .xop_o(),
        .condition_o(validity_type9_condition),
        .x_source_dreg_o(validity_type9_x_source),
        .y_source_dreg_o(validity_type9_y_source)
    );

    adsp2100_shift_move_decode validity_type14_decode (
        .opcode_i(linear_opcode_o),
        .class_valid_o(),
        .action_valid_o(validity_type14_action_valid),
        .unsupported_subencoding_o(),
        .unverified_unused_x_o(),
        .unavailable_xop_o(),
        .destination_collision_o(),
        .sf_o(validity_type14_sf),
        .xop_o(),
        .shifter_source_dreg_o(validity_type14_source),
        .move_destination_dreg_o(validity_type14_move_destination),
        .move_source_dreg_o(validity_type14_move_source)
    );

    adsp2100_immediate_shift_decode validity_type15_decode (
        .opcode_i(linear_opcode_o),
        .class_valid_o(),
        .action_valid_o(validity_type15_action_valid),
        .unsupported_subencoding_o(),
        .sf_o(validity_type15_sf),
        .xop_o(),
        .source_dreg_o(validity_type15_source),
        .exponent_o()
    );

    adsp2100_conditional_shift_decode validity_type16_decode (
        .opcode_i(linear_opcode_o),
        .class_valid_o(),
        .action_valid_o(validity_type16_action_valid),
        .unsupported_subencoding_o(),
        .sf_o(validity_type16_sf),
        .xop_o(),
        .source_dreg_o(validity_type16_source),
        .condition_o(validity_type16_condition)
    );

    adsp2100_divide_quotient_decode validity_type23_decode (
        .opcode_i(linear_opcode_o),
        .class_valid_o(),
        .action_valid_o(validity_type23_action_valid),
        .xop_o(),
        .divisor_source_dreg_o(validity_type23_divisor_source)
    );

    adsp2100_divide_sign_decode validity_type24_decode (
        .opcode_i(linear_opcode_o),
        .class_valid_o(),
        .action_valid_o(validity_type24_action_valid),
        .unsupported_yop_o(),
        .yop_o(),
        .xop_o(),
        .x_source_dreg_o(validity_type24_divisor_source),
        .upper_source_dreg_o(validity_type24_upper_source),
        .upper_source_feedback_o(validity_type24_upper_feedback)
    );

    adsp2100_mr_saturation_decode validity_type25_decode (
        .opcode_i(linear_opcode_o),
        .valid_o(validity_type25_action_valid)
    );
    /* verilator lint_on PINCONNECTEMPTY */

    adsp2100_condition_logic validity_type9_condition_eval (
        .condition_i(validity_type9_condition),
        .az_i(shared_astat[0]),
        .an_i(shared_astat[1]),
        .av_i(shared_astat[2]),
        .ac_i(shared_astat[3]),
        .as_i(shared_astat[4]),
        .mv_i(shared_astat[6]),
        .not_counter_expired_i(
            linear_cntr_valid_unused && linear_cntr_unused != 14'h0001
        ),
        .condition_true_o(validity_type9_condition_true)
    );

    assign validity_type9_condition_known = condition_state_known(
        validity_type9_condition,
        shared_astat_valid_mask_q[0],
        shared_astat_valid_mask_q[1],
        shared_astat_valid_mask_q[2],
        shared_astat_valid_mask_q[3],
        shared_astat_valid_mask_q[4],
        shared_astat_valid_mask_q[6],
        linear_cntr_valid_unused
    );

    adsp2100_condition_logic validity_type16_condition_eval (
        .condition_i(validity_type16_condition),
        .az_i(shared_astat[0]),
        .an_i(shared_astat[1]),
        .av_i(shared_astat[2]),
        .ac_i(shared_astat[3]),
        .as_i(shared_astat[4]),
        .mv_i(shared_astat[6]),
        .not_counter_expired_i(
            linear_cntr_valid_unused && linear_cntr_unused != 14'h0001
        ),
        .condition_true_o(validity_type16_condition_true)
    );

    assign validity_type16_condition_known = condition_state_known(
        validity_type16_condition,
        shared_astat_valid_mask_q[0],
        shared_astat_valid_mask_q[1],
        shared_astat_valid_mask_q[2],
        shared_astat_valid_mask_q[3],
        shared_astat_valid_mask_q[4],
        shared_astat_valid_mask_q[6],
        linear_cntr_valid_unused
    );

    always_comb begin
        validity_selected_is_mac = validity_type8_action_valid
            ? validity_type8_is_mac : validity_type9_is_mac;
        validity_selected_amf = validity_type8_action_valid
            ? validity_type8_amf : validity_type9_amf;
        validity_selected_yop = validity_type8_action_valid
            ? validity_type8_yop : validity_type9_yop;
        validity_selected_x_source = validity_type8_action_valid
            ? validity_type8_x_source : validity_type9_x_source;
        validity_selected_y_source = validity_type8_action_valid
            ? validity_type8_y_source : validity_type9_y_source;
        validity_selected_x_known = shared_dreg_valid_q[
            shared_alternate_bank
        ][validity_selected_x_source];
        if (validity_selected_yop == 2'd3) begin
            validity_selected_y_known = 1'b1;
        end else if (validity_selected_yop == 2'd2) begin
            validity_selected_y_known = validity_selected_is_mac
                ? shared_mf_valid_q[shared_alternate_bank]
                : shared_af_valid_q[shared_alternate_bank];
        end else begin
            validity_selected_y_known = shared_dreg_valid_q[
                shared_alternate_bank
            ][validity_selected_y_source];
        end
        validity_selected_mr_known =
            shared_dreg_valid_q[shared_alternate_bank][DREG_MR0]
            && shared_dreg_valid_q[shared_alternate_bank][DREG_MR1]
            && shared_dreg_valid_q[shared_alternate_bank][DREG_MR2];
        validity_alu_needs_x = !(
            validity_selected_amf == 5'h10
            || validity_selected_amf == 5'h11
            || validity_selected_amf == 5'h14
            || validity_selected_amf == 5'h15
            || validity_selected_amf == 5'h18
        );
        validity_alu_needs_y = !(
            validity_selected_amf == 5'h1b
            || validity_selected_amf == 5'h1f
        );
        validity_alu_needs_carry =
            validity_selected_amf == 5'h12
            || validity_selected_amf == 5'h16
            || validity_selected_amf == 5'h1a;
        validity_mac_needs_mr =
            validity_selected_amf == 5'h02
            || validity_selected_amf == 5'h03
            || validity_selected_amf >= 5'h08;
        validity_selected_compute_known = 1'b0;
        if (
            validity_type8_action_valid
            || (validity_type9_action_valid && !validity_type9_nop_action)
        ) begin
            if (validity_selected_is_mac) begin
                validity_selected_compute_known =
                    validity_selected_x_known
                    && validity_selected_y_known
                    && (!validity_mac_needs_mr
                        || validity_selected_mr_known);
            end else begin
                validity_selected_compute_known =
                    (!validity_alu_needs_x || validity_selected_x_known)
                    && (!validity_alu_needs_y || validity_selected_y_known)
                    && (!validity_alu_needs_carry
                        || shared_astat_valid_mask_q[3])
                    && shared_mstat_valid_mask_q[2]
                    && (!shared_mstat[2] || shared_astat_valid_mask_q[2]);
            end
        end
    end

    always_comb begin
        validity_divide_result_known = 1'b0;
        if (validity_type23_action_valid) begin
            validity_divide_result_known =
                shared_dreg_valid_q[shared_alternate_bank]
                    [validity_type23_divisor_source]
                && shared_af_valid_q[shared_alternate_bank]
                && shared_dreg_valid_q[shared_alternate_bank][DREG_AY0]
                && shared_astat_valid_mask_q[5];
        end else if (validity_type24_action_valid) begin
            validity_divide_result_known =
                shared_dreg_valid_q[shared_alternate_bank]
                    [validity_type24_divisor_source]
                && shared_dreg_valid_q[shared_alternate_bank][DREG_AY0]
                && (
                    validity_type24_upper_feedback
                        ? shared_af_valid_q[shared_alternate_bank]
                        : shared_dreg_valid_q[shared_alternate_bank]
                            [validity_type24_upper_source]
                );
        end
    end

    always_comb begin
        validity_selected_shift_sf = validity_type14_action_valid
            ? validity_type14_sf
            : (validity_type15_action_valid
                ? validity_type15_sf : validity_type16_sf);
        validity_selected_shift_source = validity_type14_action_valid
            ? validity_type14_source
            : (validity_type15_action_valid
                ? validity_type15_source : validity_type16_source);
        validity_selected_shift_source_known = shared_dreg_valid_q[
            shared_alternate_bank
        ][validity_selected_shift_source];
        validity_selected_shift_result_known = 1'b0;

        if (validity_type15_action_valid) begin
            // Immediate LSHIFT/ASHIFT uses the encoded exponent. OR forms
            // additionally consume the old 32-bit SR value.
            validity_selected_shift_result_known =
                validity_selected_shift_source_known
                && (!validity_selected_shift_sf[0] || shared_sr_valid);
        end else if (
            validity_type14_action_valid || validity_type16_action_valid
        ) begin
            unique case (validity_selected_shift_sf)
                4'h0, 4'h2, 4'h4, 4'h6, 4'ha, 4'hb:
                    validity_selected_shift_result_known =
                        validity_selected_shift_source_known
                        && shared_se_valid;
                4'h1, 4'h3, 4'h5, 4'h7:
                    validity_selected_shift_result_known =
                        validity_selected_shift_source_known
                        && shared_se_valid && shared_sr_valid;
                4'h8, 4'h9:
                    validity_selected_shift_result_known =
                        validity_selected_shift_source_known
                        && shared_se_valid
                        && shared_astat_valid_mask_q[3];
                4'hc:
                    validity_selected_shift_result_known =
                        validity_selected_shift_source_known;
                4'hd:
                    validity_selected_shift_result_known =
                        validity_selected_shift_source_known
                        && shared_astat_valid_mask_q[2];
                4'he:
                    // EXP LO writes only when old SE is -15. A known other
                    // SE value preserves the known destination even when the
                    // source or predicate is unknown.
                    validity_selected_shift_result_known =
                        shared_se_valid
                        && (
                            shared_se != 8'hf1
                            || (
                                validity_selected_shift_source_known
                                && shared_astat_valid_mask_q[5]
                            )
                        );
                4'hf:
                    validity_selected_shift_result_known =
                        validity_selected_shift_source_known
                        && shared_sb_valid;
                default:
                    validity_selected_shift_result_known = 1'b0;
            endcase
        end
    end

    // Capture validity at the same state-8 issue edge as the execution
    // pipeline. The sidecar retires with that instruction at state 7 and does
    // not add an architectural cycle.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            validity_compute_stage_valid_q <= 1'b0;
            validity_compute_stage_type8_q <= 1'b0;
            validity_compute_stage_is_mac_q <= 1'b0;
            validity_compute_stage_destination_feedback_q <= 1'b0;
            validity_compute_stage_amf_q <= 5'h00;
            validity_compute_stage_move_destination_q <= 4'h0;
            validity_compute_stage_move_known_q <= 1'b0;
            validity_compute_stage_result_known_q <= 1'b0;
            validity_compute_stage_condition_known_q <= 1'b0;
            validity_compute_stage_condition_true_q <= 1'b0;
            validity_shift_stage_valid_q <= 1'b0;
            validity_shift_stage_type14_q <= 1'b0;
            validity_shift_stage_sf_q <= 4'h0;
            validity_shift_stage_move_destination_q <= 4'h0;
            validity_shift_stage_move_known_q <= 1'b0;
            validity_shift_stage_result_known_q <= 1'b0;
            validity_shift_stage_condition_known_q <= 1'b0;
            validity_shift_stage_condition_true_q <= 1'b0;
            validity_shift_stage_exp_lo_preserve_q <= 1'b0;
            validity_divide_stage_valid_q <= 1'b0;
            validity_divide_stage_result_known_q <= 1'b0;
            validity_saturation_stage_valid_q <= 1'b0;
            validity_saturation_stage_condition_known_q <= 1'b0;
            validity_saturation_stage_condition_true_q <= 1'b0;
            validity_saturation_stage_result_known_q <= 1'b0;
        end else begin
            if (linear_retire_event_o) begin
                validity_compute_stage_valid_q <= 1'b0;
                validity_shift_stage_valid_q <= 1'b0;
                validity_divide_stage_valid_q <= 1'b0;
                validity_saturation_stage_valid_q <= 1'b0;
            end
            if (
                linear_instruction_issue_o
                && shared_mstat_valid_mask_q == 4'hf
                && (validity_type8_action_valid
                    || validity_type9_action_valid)
            ) begin
                validity_compute_stage_valid_q <= 1'b1;
                validity_compute_stage_type8_q
                    <= validity_type8_action_valid;
                validity_compute_stage_is_mac_q
                    <= validity_selected_is_mac;
                validity_compute_stage_destination_feedback_q
                    <= validity_type8_action_valid
                        ? validity_type8_destination_feedback
                        : validity_type9_destination_feedback;
                validity_compute_stage_amf_q <= validity_selected_amf;
                validity_compute_stage_move_destination_q
                    <= validity_type8_move_destination;
                validity_compute_stage_move_known_q
                    <= validity_type8_action_valid
                        && shared_dreg_valid_q[shared_alternate_bank]
                            [validity_type8_move_source];
                validity_compute_stage_result_known_q
                    <= validity_selected_compute_known;
                validity_compute_stage_condition_known_q
                    <= validity_type8_action_valid
                        || validity_type9_condition_known;
                validity_compute_stage_condition_true_q
                    <= validity_type8_action_valid
                        || validity_type9_condition_true;
            end
            if (
                linear_instruction_issue_o
                && shared_mstat_valid_mask_q[0]
                && (validity_type14_action_valid
                    || validity_type15_action_valid
                    || validity_type16_action_valid)
            ) begin
                validity_shift_stage_valid_q <= 1'b1;
                validity_shift_stage_type14_q
                    <= validity_type14_action_valid;
                validity_shift_stage_sf_q <= validity_selected_shift_sf;
                validity_shift_stage_move_destination_q
                    <= validity_type14_move_destination;
                validity_shift_stage_move_known_q
                    <= validity_type14_action_valid
                        && shared_dreg_valid_q[shared_alternate_bank]
                            [validity_type14_move_source];
                validity_shift_stage_result_known_q
                    <= validity_selected_shift_result_known;
                validity_shift_stage_condition_known_q
                    <= !validity_type16_action_valid
                        || validity_type16_condition_known;
                validity_shift_stage_condition_true_q
                    <= !validity_type16_action_valid
                        || validity_type16_condition_true;
                validity_shift_stage_exp_lo_preserve_q
                    <= validity_selected_shift_sf == 4'he
                        && shared_se_valid && shared_se != 8'hf1;
            end
            if (
                linear_instruction_issue_o
                && shared_mstat_valid_mask_q[0]
                && (validity_type23_action_valid
                    || validity_type24_action_valid)
            ) begin
                validity_divide_stage_valid_q <= 1'b1;
                validity_divide_stage_result_known_q
                    <= validity_divide_result_known;
            end
            if (
                linear_instruction_issue_o
                && shared_mstat_valid_mask_q[0]
                && validity_type25_action_valid
            ) begin
                validity_saturation_stage_valid_q <= 1'b1;
                validity_saturation_stage_condition_known_q
                    <= shared_astat_valid_mask_q[6];
                validity_saturation_stage_condition_true_q
                    <= shared_astat[6];
                // SAT MR selects its constant from the cycle-start MR sign;
                // only MR2 contains that sign bit.
                validity_saturation_stage_result_known_q
                    <= shared_dreg_valid_q[shared_alternate_bank][DREG_MR2];
            end
        end
    end

    always_comb begin
        linear_type17_source_valid = 1'b0;
        unique case (linear_opcode_o[9:8])
            2'b00: linear_type17_source_valid =
                shared_mstat_valid_mask_q[0]
                && shared_dreg_valid_q[shared_alternate_bank]
                    [linear_opcode_o[3:0]];
            2'b01,
            2'b10: begin
                if (linear_opcode_o[3:0] < 4'd4) begin
                    linear_type17_source_valid = shared_dag_i_valid;
                end else if (linear_opcode_o[3:0] < 4'd8) begin
                    linear_type17_source_valid = shared_dag_m_valid;
                end else if (linear_opcode_o[3:0] < 4'd12) begin
                    linear_type17_source_valid = shared_dag_l_valid;
                end
            end
            2'b11: begin
                unique case (linear_opcode_o[3:0])
                    4'd0: linear_type17_source_valid =
                        &shared_astat_valid_mask_q;
                    4'd1: linear_type17_source_valid =
                        &shared_mstat_valid_mask_q;
                    4'd2: linear_type17_source_valid = 1'b1;
                    4'd3: linear_type17_source_valid =
                        shared_imask_valid_q;
                    4'd4: linear_type17_source_valid =
                        !linear_interrupt_configuration_invalid_unused;
                    4'd5: linear_type17_source_valid =
                        linear_cntr_valid_unused;
                    4'd6: linear_type17_source_valid =
                        shared_mstat_valid_mask_q[0]
                        && shared_sb_valid_q[shared_alternate_bank];
                    4'd7: linear_type17_source_valid = shared_px_valid_q;
                    default: linear_type17_source_valid = 1'b0;
                endcase
            end
            default: linear_type17_source_valid = 1'b0;
        endcase
    end
    assign type5_probe_dreg_data_o = shared_probe_dreg_valid
        ? shared_probe_data : 16'h0000;
    assign type5_probe_dreg_valid_o = shared_probe_dreg_valid;
    assign type13_probe_dreg_data_o = shared_probe_dreg_valid
        ? shared_probe_data : 16'h0000;
    assign type13_probe_dreg_valid_o = shared_probe_dreg_valid;
    assign type5_px_o = shared_px_valid_q ? shared_px : 8'h00;
    assign type5_px_valid_o = shared_px_valid_q;
    assign type13_px_o = shared_px_valid_q ? shared_px : 8'h00;
    assign type13_px_valid_o = shared_px_valid_q;
    assign type5_internal_conflict = 1'b0;
    assign type13_internal_conflict = 1'b0;
    assign type5_dm_access_unused = 1'b0;
    assign type13_dm_access_unused = 1'b0;

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            type5_cache_instruction_q <= 24'h000000;
            type5_cache_instruction_valid_q <= 1'b0;
            type13_cache_instruction_q <= 24'h000000;
            type13_cache_instruction_valid_q <= 1'b0;
        end else begin
            if (type5_accepted) begin
                type5_cache_instruction_q <= cache_lookup_instruction;
                type5_cache_instruction_valid_q <=
                    cache_lookup_hit && cache_lookup_instruction_valid;
            end else if (type5_instruction_complete_o) begin
                type5_cache_instruction_valid_q <= 1'b0;
            end
            if (type13_accepted) begin
                type13_cache_instruction_q <= cache_lookup_instruction;
                type13_cache_instruction_valid_q <=
                    cache_lookup_hit && cache_lookup_instruction_valid;
            end else if (type13_instruction_complete_o) begin
                type13_cache_instruction_valid_q <= 1'b0;
            end
        end
    end

    // Validity sidecars preserve authentic reset-unknown PM-client state
    // without assigning invented values to the shared storage itself.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            shared_dreg_valid_q[0] <= 16'h0000;
            shared_dreg_valid_q[1] <= 16'h0000;
            shared_af_valid_q[0] <= 1'b0;
            shared_af_valid_q[1] <= 1'b0;
            shared_mf_valid_q[0] <= 1'b0;
            shared_mf_valid_q[1] <= 1'b0;
            shared_sb_valid_q[0] <= 1'b0;
            shared_sb_valid_q[1] <= 1'b0;
            shared_astat_valid_mask_q <= 8'h00;
            shared_mstat_valid_mask_q <= 4'hf;
            shared_imask_valid_q <= 1'b1;
            shared_px_valid_q <= 1'b0;
        end else begin
            if (shared_setup_accept && !linear_state_action_conflict) begin
                if (astat_setup_write_i) begin
                    shared_astat_valid_mask_q <= 8'hff;
                end
                if (mstat_setup_write_i) begin
                    shared_mstat_valid_mask_q <= 4'hf;
                end
                if (dreg_setup_write_i) begin
                    shared_dreg_valid_q[shared_alternate_bank]
                        [dreg_setup_code_i] <= 1'b1;
                    if (dreg_setup_code_i == DREG_MR1) begin
                        shared_dreg_valid_q[shared_alternate_bank]
                            [DREG_MR2] <= 1'b1;
                    end
                end
                if (af_setup_write_i) begin
                    shared_af_valid_q[shared_alternate_bank] <= 1'b1;
                end
                if (mf_setup_write_i) begin
                    shared_mf_valid_q[shared_alternate_bank] <= 1'b1;
                end
                if (sb_setup_write_i) begin
                    shared_sb_valid_q[shared_alternate_bank] <= 1'b1;
                end
                if (px_setup_write_i) begin
                    shared_px_valid_q <= 1'b1;
                end
            end

            // The retained fetch owner and both PM-data clients write the same
            // storage. These sidecars preserve authentic reset unknowns across
            // the source-closed fetched classes attached below.
            if (linear_type6_retire) begin
                shared_dreg_valid_q[shared_alternate_bank]
                    [linear_opcode_o[3:0]] <= 1'b1;
                if (linear_opcode_o[3:0] == DREG_MR1) begin
                    shared_dreg_valid_q[shared_alternate_bank][DREG_MR2]
                        <= 1'b1;
                end
            end else if (
                linear_type17_retire && linear_opcode_o[11:10] == 2'b00
                && shared_mstat_valid_mask_q[0]
            ) begin
                shared_dreg_valid_q[shared_alternate_bank]
                    [linear_opcode_o[7:4]] <= linear_type17_source_valid;
                if (linear_opcode_o[7:4] == DREG_MR1) begin
                    shared_dreg_valid_q[shared_alternate_bank][DREG_MR2]
                        <= linear_type17_source_valid;
                end
            end

            if (linear_type7_retire) begin
                unique case ({linear_opcode_o[19:18], linear_opcode_o[3:0]})
                    6'h30: shared_astat_valid_mask_q <= 8'hff;
                    6'h31: shared_mstat_valid_mask_q <= 4'hf;
                    6'h33: shared_imask_valid_q <= 1'b1;
                    6'h36: begin
                        if (shared_mstat_valid_mask_q[0]) begin
                            shared_sb_valid_q[shared_alternate_bank] <= 1'b1;
                        end
                    end
                    6'h37: shared_px_valid_q <= 1'b1;
                    default: begin
                    end
                endcase
            end else if (linear_type17_retire) begin
                unique case ({linear_opcode_o[11:10], linear_opcode_o[7:4]})
                    6'h30: shared_astat_valid_mask_q
                        <= {8{linear_type17_source_valid}};
                    6'h31: shared_mstat_valid_mask_q
                        <= {4{linear_type17_source_valid}};
                    6'h33: shared_imask_valid_q
                        <= linear_type17_source_valid;
                    6'h36: begin
                        if (shared_mstat_valid_mask_q[0]) begin
                            shared_sb_valid_q[shared_alternate_bank]
                                <= linear_type17_source_valid;
                        end
                    end
                    6'h37: shared_px_valid_q <= linear_type17_source_valid;
                    default: begin
                    end
                endcase
            end

            if (linear_type18_retire) begin
                if (linear_opcode_o[5]) begin
                    shared_mstat_valid_mask_q[0] <= 1'b1;
                end
                if (linear_opcode_o[7]) begin
                    shared_mstat_valid_mask_q[1] <= 1'b1;
                end
                if (linear_opcode_o[9]) begin
                    shared_mstat_valid_mask_q[2] <= 1'b1;
                end
                if (linear_opcode_o[11]) begin
                    shared_mstat_valid_mask_q[3] <= 1'b1;
                end
            end

            if (
                linear_retire_event_o && validity_compute_stage_valid_q
            ) begin
                // Type 8's parallel move is independent of compute-result
                // validity and always uses its captured cycle-start source.
                if (validity_compute_stage_type8_q) begin
                    shared_dreg_valid_q[shared_alternate_bank]
                        [validity_compute_stage_move_destination_q]
                        <= validity_compute_stage_move_known_q;
                    if (
                        validity_compute_stage_move_destination_q == DREG_MR1
                    ) begin
                        shared_dreg_valid_q[shared_alternate_bank][DREG_MR2]
                            <= validity_compute_stage_move_known_q;
                    end
                end

                // A known-false Type 9 preserves state. An unknown predicate
                // invalidates every possible destination because the model
                // cannot choose between the old value and the computed one.
                if (
                    validity_compute_stage_type8_q
                    || validity_compute_stage_condition_true_q
                    || !validity_compute_stage_condition_known_q
                ) begin
                    if (validity_compute_stage_is_mac_q) begin
                        if (
                            validity_compute_stage_destination_feedback_q
                        ) begin
                            shared_mf_valid_q[shared_alternate_bank]
                                <= validity_compute_stage_result_known_q
                                    && validity_compute_stage_condition_known_q;
                        end else begin
                            shared_dreg_valid_q[shared_alternate_bank][DREG_MR0]
                                <= validity_compute_stage_result_known_q
                                    && validity_compute_stage_condition_known_q;
                            shared_dreg_valid_q[shared_alternate_bank][DREG_MR1]
                                <= validity_compute_stage_result_known_q
                                    && validity_compute_stage_condition_known_q;
                            shared_dreg_valid_q[shared_alternate_bank][DREG_MR2]
                                <= validity_compute_stage_result_known_q
                                    && validity_compute_stage_condition_known_q;
                        end
                        shared_astat_valid_mask_q[6]
                            <= validity_compute_stage_result_known_q
                                && validity_compute_stage_condition_known_q;
                    end else if (
                        validity_compute_stage_amf_q != 5'h00
                    ) begin
                        if (
                            validity_compute_stage_destination_feedback_q
                        ) begin
                            shared_af_valid_q[shared_alternate_bank]
                                <= validity_compute_stage_result_known_q
                                    && validity_compute_stage_condition_known_q;
                        end else begin
                            shared_dreg_valid_q[shared_alternate_bank][DREG_AR]
                                <= validity_compute_stage_result_known_q
                                    && validity_compute_stage_condition_known_q;
                        end
                        shared_astat_valid_mask_q[3:0]
                            <= {4{
                                validity_compute_stage_result_known_q
                                && validity_compute_stage_condition_known_q
                            }};
                        if (validity_compute_stage_amf_q == 5'h1f) begin
                            shared_astat_valid_mask_q[4]
                                <= validity_compute_stage_result_known_q
                                    && validity_compute_stage_condition_known_q;
                        end
                    end
                end
            end

            if (
                linear_retire_event_o && validity_shift_stage_valid_q
            ) begin
                // Type 14's move reads independently at cycle start.
                if (validity_shift_stage_type14_q) begin
                    shared_dreg_valid_q[shared_alternate_bank]
                        [validity_shift_stage_move_destination_q]
                        <= validity_shift_stage_move_known_q;
                    if (
                        validity_shift_stage_move_destination_q == DREG_MR1
                    ) begin
                        shared_dreg_valid_q[shared_alternate_bank][DREG_MR2]
                            <= validity_shift_stage_move_known_q;
                    end
                end

                // Known-false Type 16 preserves state. Unknown predicates
                // invalidate possible writes, except EXP LO with a known old
                // SE other than -15 because neither outcome writes there.
                if (
                    validity_shift_stage_condition_true_q
                    || !validity_shift_stage_condition_known_q
                ) begin
                    unique case (validity_shift_stage_sf_q)
                        4'h0, 4'h1, 4'h2, 4'h3,
                        4'h4, 4'h5, 4'h6, 4'h7,
                        4'h8, 4'h9, 4'ha, 4'hb: begin
                            shared_dreg_valid_q[shared_alternate_bank]
                                [DREG_SR0]
                                <= validity_shift_stage_result_known_q
                                    && validity_shift_stage_condition_known_q;
                            shared_dreg_valid_q[shared_alternate_bank]
                                [DREG_SR1]
                                <= validity_shift_stage_result_known_q
                                    && validity_shift_stage_condition_known_q;
                        end
                        4'hc, 4'hd: begin
                            shared_dreg_valid_q[shared_alternate_bank]
                                [DREG_SE]
                                <= validity_shift_stage_result_known_q
                                    && validity_shift_stage_condition_known_q;
                            shared_astat_valid_mask_q[5]
                                <= validity_shift_stage_result_known_q
                                    && validity_shift_stage_condition_known_q;
                        end
                        4'he: begin
                            shared_dreg_valid_q[shared_alternate_bank]
                                [DREG_SE]
                                <= validity_shift_stage_exp_lo_preserve_q
                                    || (
                                        validity_shift_stage_result_known_q
                                        && validity_shift_stage_condition_known_q
                                    );
                        end
                        4'hf: begin
                            shared_sb_valid_q[shared_alternate_bank]
                                <= validity_shift_stage_result_known_q
                                    && validity_shift_stage_condition_known_q;
                        end
                        default: begin
                        end
                    endcase
                end
            end

            if (
                linear_retire_event_o && validity_divide_stage_valid_q
            ) begin
                // DIVS and DIVQ atomically replace AF, AY0, and AQ from the
                // captured cycle-start operands and preserve all other flags.
                shared_af_valid_q[shared_alternate_bank]
                    <= validity_divide_stage_result_known_q;
                shared_dreg_valid_q[shared_alternate_bank][DREG_AY0]
                    <= validity_divide_stage_result_known_q;
                shared_astat_valid_mask_q[5]
                    <= validity_divide_stage_result_known_q;
            end

            if (
                linear_retire_event_o && validity_saturation_stage_valid_q
                && (
                    validity_saturation_stage_condition_true_q
                    || !validity_saturation_stage_condition_known_q
                )
            ) begin
                // Known-false MV preserves MR. Unknown MV leaves a possible
                // write, so all three segments become invalid. A known-taken
                // action needs only the captured MR2 sign to select the exact
                // saturation constant.
                shared_dreg_valid_q[shared_alternate_bank][DREG_MR0]
                    <= validity_saturation_stage_condition_known_q
                        && validity_saturation_stage_result_known_q;
                shared_dreg_valid_q[shared_alternate_bank][DREG_MR1]
                    <= validity_saturation_stage_condition_known_q
                        && validity_saturation_stage_result_known_q;
                shared_dreg_valid_q[shared_alternate_bank][DREG_MR2]
                    <= validity_saturation_stage_condition_known_q
                        && validity_saturation_stage_result_known_q;
            end

            if (type5_dreg_write && !linear_state_action_conflict) begin
                shared_dreg_valid_q[shared_alternate_bank]
                    [type5_dreg_write_address] <= type5_dreg_write_known;
                if (type5_dreg_write_address == DREG_MR1) begin
                    shared_dreg_valid_q[shared_alternate_bank]
                        [DREG_MR2] <= type5_dreg_write_known;
                end
            end else if (type13_dreg_write
                && !linear_state_action_conflict) begin
                shared_dreg_valid_q[shared_alternate_bank]
                    [type13_dreg_write_address] <= type13_dreg_write_known;
                if (type13_dreg_write_address == DREG_MR1) begin
                    shared_dreg_valid_q[shared_alternate_bank]
                        [DREG_MR2] <= type13_dreg_write_known;
                end
            end
            if (type5_px_write && !linear_state_action_conflict) begin
                shared_px_valid_q <= type5_px_write_known;
            end else if (type13_px_write
                && !linear_state_action_conflict) begin
                shared_px_valid_q <= type13_px_write_known;
            end

            if (type5_alu_write && !linear_state_action_conflict) begin
                if (type5_active_destination_feedback) begin
                    shared_af_valid_q[shared_alternate_bank]
                        <= type5_compute_result_known;
                end else begin
                    shared_dreg_valid_q[shared_alternate_bank][DREG_AR]
                        <= type5_compute_result_known;
                end
                shared_astat_valid_mask_q[3:0]
                    <= {4{type5_compute_result_known}};
                if (type5_active_amf == 5'h1f) begin
                    shared_astat_valid_mask_q[4]
                        <= type5_compute_result_known;
                end
            end else if (type5_mac_write
                && !linear_state_action_conflict) begin
                if (type5_active_destination_feedback) begin
                    shared_mf_valid_q[shared_alternate_bank]
                        <= type5_compute_result_known;
                end else begin
                    shared_dreg_valid_q[shared_alternate_bank][DREG_MR0]
                        <= type5_compute_result_known;
                    shared_dreg_valid_q[shared_alternate_bank][DREG_MR1]
                        <= type5_compute_result_known;
                    shared_dreg_valid_q[shared_alternate_bank][DREG_MR2]
                        <= type5_compute_result_known;
                end
                shared_astat_valid_mask_q[6]
                    <= type5_compute_result_known;
            end

            if (type13_sr_write && !linear_state_action_conflict) begin
                shared_dreg_valid_q[shared_alternate_bank][DREG_SR0]
                    <= type13_shifter_result_known;
                shared_dreg_valid_q[shared_alternate_bank][DREG_SR1]
                    <= type13_shifter_result_known;
            end else if (type13_se_write
                && !linear_state_action_conflict) begin
                shared_dreg_valid_q[shared_alternate_bank][DREG_SE]
                    <= type13_shifter_result_known;
            end else if (type13_sb_write
                && !linear_state_action_conflict) begin
                shared_sb_valid_q[shared_alternate_bank]
                    <= type13_shifter_result_known;
            end
            if (type13_ss_write && !linear_state_action_conflict) begin
                shared_astat_valid_mask_q[7]
                    <= type13_shifter_result_known;
            end
            if (!linear_state_action_conflict
                && type13_data_action_complete_o
                && !type13_shifter_result_known) begin
                if (type13_active_sf <= 4'hb) begin
                    shared_dreg_valid_q[shared_alternate_bank][DREG_SR0]
                        <= 1'b0;
                    shared_dreg_valid_q[shared_alternate_bank][DREG_SR1]
                        <= 1'b0;
                end else if (type13_active_sf == 4'hc
                    || type13_active_sf == 4'hd) begin
                    shared_dreg_valid_q[shared_alternate_bank][DREG_SE]
                        <= 1'b0;
                    shared_astat_valid_mask_q[7] <= 1'b0;
                end else if (type13_active_sf == 4'he
                    && type13_active_exp_lo_destination) begin
                    shared_dreg_valid_q[shared_alternate_bank][DREG_SE]
                        <= 1'b0;
                end else if (type13_active_sf == 4'hf) begin
                    shared_sb_valid_q[shared_alternate_bank] <= 1'b0;
                end
            end

            // Interrupt entry replaces live IMASK with an exact sourced
            // mask. A valid status pop restores the known-state metadata
            // captured beside that stack entry, not metadata produced by an
            // intervening status write.
            if (linear_interrupt_entry_unused) begin
                shared_imask_valid_q <= 1'b1;
            end
            if (linear_status_restore_event) begin
                shared_astat_valid_mask_q
                    <= linear_status_restore_astat_valid_mask;
                shared_mstat_valid_mask_q
                    <= linear_status_restore_mstat_valid_mask;
                shared_imask_valid_q
                    <= linear_status_restore_imask_valid;
            end
        end
    end

    adsp2100_instruction_cache cache (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .fill_i(cache_fill_o),
        .fill_address_i(pma_o),
        .fill_address_valid_i(pma_valid_o),
        .fill_instruction_i(pmd_read_data_i),
        .fill_instruction_valid_i(pmd_read_data_valid_i),
        .lookup_address_i(cache_lookup_address),
        .lookup_address_valid_i(cache_lookup_address_valid),
        .lookup_hit_o(cache_lookup_hit),
        .lookup_instruction_o(cache_lookup_instruction),
        .lookup_instruction_valid_o(cache_lookup_instruction_valid),
        .fill_accepted_o(cache_fill_accepted_o),
        .region_restarted_o(cache_region_restarted_unused),
        .oldest_replaced_o(cache_oldest_replaced_unused),
        .region_start_o(cache_region_start_o),
        .region_start_valid_o(cache_region_start_valid_o),
        .region_count_o(cache_region_count_o)
    );

    /* verilator lint_off PINCONNECTEMPTY */
    adsp2100_linear_fetch_client linear_client (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(effective_phase_advance_o),
        .interrupt_sample_advance_i(1'b0),
        .instruction_issue_inhibit_i(issue_inhibit_o),
        .bus_relinquished_i(bus_relinquished_o),
        .instruction_setup_i(instruction_setup_i),
        .instruction_setup_pc_i(instruction_setup_pc_i),
        .instruction_setup_opcode_i(instruction_setup_opcode_i),
        .pm_request_accepted_i(request_accepted_o[0]),
        .pm_completion_event_i(completion_event_o[0]),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .irq_n_i(irq_n_i),
        .probe_code_i(linear_probe_code_i),
        .type17_source_data_valid_i(linear_type17_source_valid),
        .state_astat_valid_mask_i(shared_astat_valid_mask_q),
        .state_mstat_valid_mask_i(shared_mstat_valid_mask_q),
        .state_imask_valid_i(shared_imask_valid_q),
        .pm_instruction_active_i(automatic_pm_instruction_active),
        .pm_instruction_complete_i(automatic_pm_completion),
        .pm_instruction_next_opcode_i(automatic_pm_next_opcode),
        .pm_instruction_next_opcode_valid_i(
            automatic_pm_next_opcode_valid
        ),
        .pm_state_operand_read_i(type5_execute || type13_execute),
        .pm_state_memory_read_address_i(shared_memory_read_address),
        .pm_state_dreg_read_address_1_i(shared_dreg_read_address_1),
        .pm_state_dreg_read_address_2_i(shared_dreg_read_address_2),
        .pm_state_dag_i_address_i(shared_dag_i_address),
        .pm_state_dag_m_address_i(shared_dag_m_address),
        .pm_state_move_write_i(shared_move_write),
        .pm_state_move_code_i(shared_move_code),
        .pm_state_move_data_i(shared_move_data),
        .pm_state_dreg_write_i(type5_dreg_write || type13_dreg_write),
        .pm_state_dreg_write_address_i(
            type5_dreg_write
                ? type5_dreg_write_address : type13_dreg_write_address
        ),
        .pm_state_dreg_write_data_i(
            type5_dreg_write
                ? type5_dreg_write_data : type13_dreg_write_data
        ),
        .pm_state_alu_write_i(type5_alu_write || shared_alu_setup),
        .pm_state_alu_destination_feedback_i(
            shared_alu_setup || type5_active_destination_feedback
        ),
        .pm_state_alu_result_i(
            shared_alu_setup ? af_setup_data_i : type5_alu_result
        ),
        .pm_state_mac_write_i(type5_mac_write || shared_mac_setup),
        .pm_state_mac_destination_feedback_i(
            shared_mac_setup || type5_active_destination_feedback
        ),
        .pm_state_mac_result_i(
            shared_mac_setup
                ? {8'h00, mf_setup_data_i, 16'h0000} : type5_mac_result
        ),
        .pm_state_sr_write_i(type13_sr_write),
        .pm_state_sr_result_i(type13_sr_result),
        .pm_state_se_write_i(type13_se_write),
        .pm_state_se_result_i(type13_se_result),
        .pm_state_sb_write_i(type13_sb_write || shared_sb_setup),
        .pm_state_sb_result_i(
            shared_sb_setup ? sb_setup_data_i : type13_sb_result
        ),
        .pm_state_dag_i_write_i(type5_i_write || type13_i_write),
        .pm_state_dag_i_write_address_i(
            type5_i_write ? type5_i_write_address : type13_i_write_address
        ),
        .pm_state_dag_i_write_data_i(
            type5_i_write ? type5_i_write_data : type13_i_write_data
        ),
        .pm_state_dag_i_write_valid_i(
            type5_i_write ? type5_i_write_known : type13_i_write_known
        ),
        .pm_state_alu_status_write_i(type5_alu_write),
        .pm_state_alu_az_i(type5_alu_az),
        .pm_state_alu_an_i(type5_alu_an),
        .pm_state_alu_av_i(type5_alu_av),
        .pm_state_alu_ac_i(type5_alu_ac),
        .pm_state_alu_as_write_i(type5_alu_as_write),
        .pm_state_alu_as_i(type5_alu_as),
        .pm_state_mac_status_write_i(type5_mac_write),
        .pm_state_mac_mv_i(type5_mac_mv),
        .pm_state_shifter_status_write_i(type13_ss_write),
        .pm_state_shifter_ss_i(type13_ss_result),
        .issue_boundary_o(),
        .instruction_setup_accepted_o(
            linear_instruction_setup_accepted_unused
        ),
        .fetch_request_presented_o(linear_fetch_request_presented_o),
        .fetch_address_o(linear_fetch_address),
        .instruction_issue_o(linear_instruction_issue_o),
        .retire_event_o(linear_retire_event_o),
        .pm_instruction_sequential_allowed_o(
            linear_pm_sequential_allowed
        ),
        .pm_instruction_flow_blocked_o(linear_pm_flow_blocked),
        .trap_event_o(linear_trap_event_unused),
        .interrupt_recognition_event_o(
            linear_interrupt_recognition_unused
        ),
        .interrupt_entry_event_o(linear_interrupt_entry_unused),
        .interrupt_vector_issue_event_o(
            linear_interrupt_vector_issue_unused
        ),
        .interrupt_vector_fetch_event_o(
            linear_interrupt_vector_fetch_unused
        ),
        .interrupt_level_o(linear_interrupt_level_unused),
        .interrupt_vector_o(linear_interrupt_vector_unused),
        .interrupt_pending_o(linear_interrupt_pending_unused),
        .interrupt_vectoring_o(linear_interrupt_vectoring_unused),
        .interrupt_configuration_invalid_o(
            linear_interrupt_configuration_invalid_unused
        ),
        .interrupt_reset_baseline_provisional_o(
            linear_interrupt_reset_baseline_unused
        ),
        .interrupt_adjacent_control_conflict_o(
            linear_interrupt_adjacent_conflict_unused
        ),
        .instruction_valid_o(linear_instruction_valid_o),
        .transaction_pending_o(linear_transaction_pending_unused),
        .unsupported_instruction_o(linear_unsupported_unused),
        .reserved_subencoding_o(linear_reserved_unused),
        .phase_conflict_o(linear_phase_conflict),
        .integration_conflict_o(linear_integration_conflict),
        .internal_conflict_o(linear_internal_conflict),
        .provisional_source_extension_o(linear_provisional_unused),
        .pc_o(linear_pc_o),
        .opcode_o(linear_opcode_o),
        .probe_data_o(linear_probe_data_o),
        .astat_o(shared_astat),
        .mstat_o(shared_mstat),
        .icntl_o(linear_icntl_unused),
        .imask_o(linear_imask_unused),
        .cntr_o(linear_cntr_unused),
        .cntr_valid_o(linear_cntr_valid_unused),
        .px_o(shared_px),
        .sstat_o(linear_sstat_unused),
        .alternate_bank_o(shared_alternate_bank),
        .count_stack_depth_o(linear_count_depth_unused),
        .count_stack_overflow_o(linear_count_overflow_unused),
        .status_restore_event_o(linear_status_restore_event),
        .status_restore_astat_valid_mask_o(
            linear_status_restore_astat_valid_mask
        ),
        .status_restore_mstat_valid_mask_o(
            linear_status_restore_mstat_valid_mask
        ),
        .status_restore_imask_valid_o(
            linear_status_restore_imask_valid
        ),
        .pm_state_memory_read_data_o(shared_memory_source_data),
        .pm_state_dreg_read_data_1_o(shared_x_source_data),
        .pm_state_dreg_read_data_2_o(shared_y_source_data),
        .pm_state_dag_i_data_o(shared_dag_i_data),
        .pm_state_dag_i_valid_o(shared_dag_i_valid),
        .pm_state_dag_m_data_o(shared_dag_m_data),
        .pm_state_dag_m_valid_o(shared_dag_m_valid),
        .pm_state_dag_l_data_o(shared_dag_l_data),
        .pm_state_dag_l_valid_o(shared_dag_l_valid),
        .pm_state_af_o(shared_af), .pm_state_mf_o(shared_mf),
        .pm_state_mr_o(shared_mr), .pm_state_se_o(shared_se),
        .pm_state_sb_o(shared_sb), .pm_state_sr_o(shared_sr),
        .pm_state_action_conflict_o(linear_state_action_conflict)
    );

    adsp2100_compute_pm_shared_state_client type5_client (
        .clk_i(clk_i), .reset_i(reset_i), .execute_i(type5_execute),
        .opcode_i(type5_opcode), .pm_read_data_i(pmd_read_data_i),
        .pm_read_data_valid_i(pmd_read_data_valid_i),
        .pm_cycle_complete_i(completion_event_o[1]),
        .next_fetch_address_i(type5_next_fetch_address),
        .next_fetch_address_valid_i(type5_next_fetch_address_valid),
        .cache_next_instruction_valid_i(
            cache_lookup_hit && cache_lookup_instruction_valid
        ),
        .force_instruction_fetch_i(halt_late_force_request),
        .x_source_data_i(shared_x_source_data),
        .x_source_data_valid_i(shared_x_source_valid),
        .y_dreg_data_i(shared_y_source_data),
        .y_dreg_data_valid_i(shared_y_source_valid),
        .memory_source_data_i(shared_memory_source_data),
        .memory_source_data_valid_i(shared_memory_source_valid),
        .af_i(shared_af), .af_valid_i(shared_af_valid),
        .mf_i(shared_mf), .mf_valid_i(shared_mf_valid),
        .mr_i(shared_mr), .mr_valid_i(shared_mr_valid),
        .astat_i(shared_astat),
        .astat_valid_mask_i(shared_astat_valid_mask_q),
        .mstat_i(shared_mstat),
        .dag_i_data_i(shared_dag_i_data),
        .dag_i_data_valid_i(shared_dag_i_valid),
        .dag_m_data_i(shared_dag_m_data),
        .dag_m_data_valid_i(shared_dag_m_valid),
        .dag_l_data_i(shared_dag_l_data),
        .dag_l_data_valid_i(shared_dag_l_valid),
        .px_i(shared_px), .px_valid_i(shared_px_valid_q),
        .class_valid_o(type5_class_valid_unused),
        .action_valid_o(type5_action_valid_unused),
        .unsupported_subencoding_o(type5_unsupported_unused),
        .destination_collision_o(),
        .computation_enable_o(type5_computation_enable),
        .is_mac_o(type5_is_mac),
        .destination_feedback_o(type5_destination_feedback),
        .write_direction_o(), .amf_o(type5_amf),
        .yop_o(type5_yop_unused), .xop_o(type5_xop_unused),
        .x_source_dreg_o(type5_x_source),
        .y_source_dreg_o(type5_y_source),
        .memory_dreg_o(type5_memory_dreg),
        .i_address_o(type5_i_address), .m_address_o(type5_m_address),
        .accepted_o(type5_accepted),
        .data_action_complete_o(type5_data_action_complete_o),
        .instruction_complete_o(type5_instruction_complete_o),
        .transaction_active_o(type5_transaction_active_unused),
        .held_transaction_o(type5_held_transaction_unused),
        .busy_o(type5_busy_unused),
        .invalid_opcode_o(type5_invalid_opcode),
        .integration_conflict_o(type5_integration_conflict),
        .cache_instruction_selected_o(type5_cache_selected_unused),
        .recovery_required_o(type5_recovery_required_unused),
        .recovery_fetch_o(type5_recovery_fetch),
        .event_boundary_o(type5_event_boundary_unused),
        .pm_select_o(type5_pm_select),
        .pm_data_access_o(type5_pm_data_access),
        .pm_read_o(type5_pm_read_unused), .pm_write_o(type5_pm_write),
        .pm_address_o(type5_pm_address),
        .pm_address_valid_o(type5_pm_address_valid),
        .pm_write_data_o(type5_pm_write_data),
        .pm_write_data_valid_o(type5_pm_write_data_valid),
        .fetched_instruction_o(type5_fetched_instruction),
        .fetched_instruction_valid_o(type5_fetched_instruction_valid),
        .compute_result_known_o(type5_compute_result_known),
        .dag_configuration_valid_o(type5_dag_configuration_valid_unused),
        .i_write_o(type5_i_write),
        .i_write_address_o(type5_i_write_address),
        .i_write_data_o(type5_i_write_data),
        .i_write_known_o(type5_i_write_known),
        .dreg_write_o(type5_dreg_write),
        .dreg_write_address_o(type5_dreg_write_address),
        .dreg_write_data_o(type5_dreg_write_data),
        .dreg_write_known_o(type5_dreg_write_known),
        .px_write_o(type5_px_write),
        .px_write_data_o(type5_px_write_data),
        .px_write_known_o(type5_px_write_known),
        .alu_write_o(type5_alu_write), .mac_write_o(type5_mac_write),
        .active_destination_feedback_o(type5_active_destination_feedback),
        .active_amf_o(type5_active_amf),
        .alu_result_o(type5_alu_result), .mac_result_o(type5_mac_result),
        .alu_az_o(type5_alu_az), .alu_an_o(type5_alu_an),
        .alu_av_o(type5_alu_av), .alu_ac_o(type5_alu_ac),
        .alu_as_write_o(type5_alu_as_write), .alu_as_o(type5_alu_as),
        .mac_mv_o(type5_mac_mv)
    );

    adsp2100_shifter_pm_shared_state_client type13_client (
        .clk_i(clk_i), .reset_i(reset_i), .execute_i(type13_execute),
        .opcode_i(type13_opcode), .pm_read_data_i(pmd_read_data_i),
        .pm_read_data_valid_i(pmd_read_data_valid_i),
        .pm_cycle_complete_i(completion_event_o[2]),
        .next_fetch_address_i(type13_next_fetch_address),
        .next_fetch_address_valid_i(type13_next_fetch_address_valid),
        .cache_next_instruction_valid_i(
            cache_lookup_hit && cache_lookup_instruction_valid
        ),
        .force_instruction_fetch_i(halt_late_force_request),
        .shifter_source_data_i(shared_x_source_data),
        .shifter_source_data_valid_i(shared_x_source_valid),
        .memory_source_data_i(shared_memory_source_data),
        .memory_source_data_valid_i(shared_memory_source_valid),
        .sr_i(shared_sr), .sr_valid_i(shared_sr_valid),
        .se_i(shared_se), .se_valid_i(shared_se_valid),
        .sb_i(shared_sb), .sb_valid_i(shared_sb_valid),
        .astat_i(shared_astat),
        .astat_valid_mask_i(shared_astat_valid_mask_q),
        .dag_i_data_i(shared_dag_i_data),
        .dag_i_data_valid_i(shared_dag_i_valid),
        .dag_m_data_i(shared_dag_m_data),
        .dag_m_data_valid_i(shared_dag_m_valid),
        .dag_l_data_i(shared_dag_l_data),
        .dag_l_data_valid_i(shared_dag_l_valid),
        .px_i(shared_px), .px_valid_i(shared_px_valid_q),
        .class_valid_o(type13_class_valid_unused),
        .action_valid_o(type13_action_valid_unused),
        .unsupported_subencoding_o(type13_unsupported_unused),
        .unavailable_xop_o(type13_unavailable_xop_unused),
        .destination_collision_o(type13_destination_collision_unused),
        .write_direction_o(type13_write_direction_unused),
        .sf_o(type13_sf_unused), .xop_o(type13_xop_unused),
        .shifter_source_dreg_o(type13_shifter_source),
        .memory_dreg_o(type13_memory_dreg),
        .i_address_o(type13_i_address), .m_address_o(type13_m_address),
        .accepted_o(type13_accepted),
        .data_action_complete_o(type13_data_action_complete_o),
        .instruction_complete_o(type13_instruction_complete_o),
        .transaction_active_o(type13_transaction_active_unused),
        .held_transaction_o(type13_held_transaction_unused),
        .busy_o(type13_busy_unused),
        .invalid_opcode_o(type13_invalid_opcode),
        .integration_conflict_o(type13_integration_conflict),
        .cache_instruction_selected_o(type13_cache_selected_unused),
        .recovery_required_o(type13_recovery_required_unused),
        .recovery_fetch_o(type13_recovery_fetch),
        .event_boundary_o(type13_event_boundary_unused),
        .pm_select_o(type13_pm_select),
        .pm_data_access_o(type13_pm_data_access),
        .pm_read_o(type13_pm_read_unused), .pm_write_o(type13_pm_write),
        .pm_address_o(type13_pm_address),
        .pm_address_valid_o(type13_pm_address_valid),
        .pm_write_data_o(type13_pm_write_data),
        .pm_write_data_valid_o(type13_pm_write_data_valid),
        .fetched_instruction_o(type13_fetched_instruction),
        .fetched_instruction_valid_o(type13_fetched_instruction_valid),
        .shifter_result_known_o(type13_shifter_result_known),
        .dag_configuration_valid_o(type13_dag_configuration_valid_unused),
        .i_write_o(type13_i_write),
        .i_write_address_o(type13_i_write_address),
        .i_write_data_o(type13_i_write_data),
        .i_write_known_o(type13_i_write_known),
        .dreg_write_o(type13_dreg_write),
        .dreg_write_address_o(type13_dreg_write_address),
        .dreg_write_data_o(type13_dreg_write_data),
        .dreg_write_known_o(type13_dreg_write_known),
        .px_write_o(type13_px_write),
        .px_write_data_o(type13_px_write_data),
        .px_write_known_o(type13_px_write_known),
        .sr_write_o(type13_sr_write), .se_write_o(type13_se_write),
        .sb_write_o(type13_sb_write), .ss_write_o(type13_ss_write),
        .sr_result_o(type13_sr_result), .se_result_o(type13_se_result),
        .sb_result_o(type13_sb_result), .ss_result_o(type13_ss_result),
        .active_sf_o(type13_active_sf),
        .active_exp_lo_destination_o(type13_active_exp_lo_destination)
    );

    /* verilator lint_on PINCONNECTEMPTY */

    adsp2100_halt_control halt_control (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(phase_advance_i),
        .halt_n_i(halt_control_halt_n), .dmack_i(dmack_i),
        .pm_data_cycle_i(halt_pm_data_cycle),
        .mode_o(halt_mode_o),
        .state_three_boundary_o(halt_state_three_boundary_unused),
        .halt_recognized_o(halt_recognized_o),
        .halt_stop_event_o(halt_stop_event_o),
        .force_fetch_issue_o(halt_force_fetch_issue_o),
        .resume_event_o(halt_resume_event_o),
        .release_blocked_o(halt_release_blocked_o),
        .instruction_issue_inhibit_o(halt_instruction_issue_inhibit),
        .phase_hold_o(halt_phase_hold_o),
        .effective_phase_advance_o(effective_phase_advance_o),
        .halted_o(halted_o),
        .phase_conflict_o(halt_phase_conflict)
    );

    assign halt_attachment_conflict_o = (
        halt_force_fetch_issue_o
        && !(
            (request_accepted_o[1] && type5_recovery_fetch)
            || (request_accepted_o[2] && type13_recovery_fetch)
        )
    );

    adsp2100_program_owner_bus_control owner_control (
        .clk_i(clk_i), .reset_i(reset_i), .phase_i(phase_i),
        .phase_advance_i(effective_phase_advance_o),
        .br_n_i(halt_control_br_n),
        .fetch_valid_i(linear_fetch_request_presented_o),
        .fetch_address_i(linear_fetch_address),
        .fetch_address_valid_i(1'b1),
        .type5_valid_i(type5_request_presented_o),
        .type5_address_i(type5_pm_address),
        .type5_address_valid_i(type5_pm_address_valid),
        .type5_data_access_i(type5_pm_data_access),
        .type5_write_i(type5_pm_write),
        .type5_write_data_i(type5_pm_write_data),
        .type5_write_data_valid_i(type5_pm_write_data_valid),
        .type13_valid_i(type13_request_presented_o),
        .type13_address_i(type13_pm_address),
        .type13_address_valid_i(type13_pm_address_valid),
        .type13_data_access_i(type13_pm_data_access),
        .type13_write_i(type13_pm_write),
        .type13_write_data_i(type13_pm_write_data),
        .type13_write_data_valid_i(type13_pm_write_data_valid),
        .pmd_read_data_i(pmd_read_data_i),
        .pmd_read_data_valid_i(pmd_read_data_valid_i),
        .bus_mode_o(bus_mode_o),
        .state_three_boundary_o(state_three_boundary_unused),
        .bus_request_recognized_o(bus_request_recognized_unused),
        .grant_assert_event_o(grant_assert_event_unused),
        .release_recognized_o(release_recognized_unused),
        .grant_release_event_o(grant_release_event_unused),
        .resume_event_o(resume_event_unused),
        .request_withdrawn_o(request_withdrawn_unused),
        .release_cancelled_o(release_cancelled_unused),
        .issue_inhibit_o(bus_issue_inhibit),
        .normal_bus_relinquished_o(normal_bus_relinquished_unused),
        .normal_bg_n_o(normal_bg_n_unused),
        .reset_br_request_o(reset_br_request_unused),
        .bg_n_o(bg_n_o), .bus_relinquished_o(bus_relinquished_o),
        .request_ready_o(request_ready_unused),
        .request_blocked_o(request_blocked_o),
        .request_conflict_o(request_conflict_o),
        .request_out_of_phase_o(request_out_of_phase_o),
        .request_accepted_o(request_accepted_o),
        .completion_event_o(completion_event_o),
        .read_sample_event_o(read_sample_event_unused),
        .owner_o(owner_o), .transaction_active_o(pm_bus_active_o),
        .response_valid_o(response_valid_unused),
        .response_write_o(response_write_unused),
        .response_read_data_o(response_read_data_unused),
        .response_read_data_valid_o(response_read_data_valid_unused),
        .pm_address_output_enable_o(pm_address_output_enable_o),
        .pm_control_output_enable_o(pm_control_output_enable_o),
        .pm_data_output_enable_o(pm_data_output_enable_o),
        .pma_o(pma_o), .pma_valid_o(pma_valid_o),
        .pmda_o(pmda_o), .pmda_valid_o(pmda_valid_o),
        .pms_n_o(pms_n_o), .pmrd_n_o(pmrd_n_o), .pmwr_n_o(pmwr_n_o),
        .pmd_write_data_o(pmd_write_data_o),
        .pmd_write_data_valid_o(pmd_write_data_valid_o)
    );

    assign unused_observation = ^{
        cache_region_restarted_unused, cache_oldest_replaced_unused,
        pm_probe_dag_address_i,
        type5_class_valid_unused, type5_action_valid_unused,
        type5_unsupported_unused, type5_transaction_active_unused,
        type5_held_transaction_unused, type5_busy_unused,
        type5_cache_selected_unused, type5_recovery_required_unused,
        type5_recovery_fetch, type5_event_boundary_unused,
        type5_pm_read_unused, type5_dm_access_unused,
        type5_computation_enable, type5_is_mac,
        type5_destination_feedback, type5_amf,
        type5_yop_unused, type5_xop_unused,
        type5_dag_configuration_valid_unused,
        type13_class_valid_unused, type13_action_valid_unused,
        type13_unsupported_unused, type13_transaction_active_unused,
        type13_held_transaction_unused, type13_busy_unused,
        type13_cache_selected_unused, type13_recovery_required_unused,
        type13_recovery_fetch, type13_event_boundary_unused,
        type13_pm_read_unused, type13_dm_access_unused,
        type13_unavailable_xop_unused,
        type13_destination_collision_unused,
        type13_write_direction_unused, type13_sf_unused,
        type13_xop_unused, type13_dag_configuration_valid_unused,
        linear_instruction_setup_accepted_unused,
        linear_trap_event_unused, linear_interrupt_recognition_unused,
        linear_interrupt_entry_unused, linear_interrupt_vector_issue_unused,
        linear_interrupt_vector_fetch_unused, linear_interrupt_level_unused,
        linear_interrupt_vector_unused, linear_interrupt_pending_unused,
        linear_interrupt_vectoring_unused,
        linear_interrupt_configuration_invalid_unused,
        linear_interrupt_reset_baseline_unused,
        linear_interrupt_adjacent_conflict_unused,
        linear_transaction_pending_unused, linear_unsupported_unused,
        linear_reserved_unused,
        linear_provisional_unused, linear_icntl_unused, linear_imask_unused,
        linear_cntr_unused, linear_cntr_valid_unused,
        linear_sstat_unused,
        linear_count_depth_unused, linear_count_overflow_unused,
        state_three_boundary_unused, bus_request_recognized_unused,
        grant_assert_event_unused, release_recognized_unused,
        grant_release_event_unused, resume_event_unused,
        request_withdrawn_unused, release_cancelled_unused,
        normal_bus_relinquished_unused, normal_bg_n_unused,
        reset_br_request_unused, request_ready_unused,
        read_sample_event_unused, response_valid_unused,
        response_write_unused, response_read_data_unused,
        response_read_data_valid_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert ($onehot0(request_accepted_o));
        assert ($onehot0(completion_event_o));
        assert (!client_execute_conflict_o
            || (!type5_accepted && !type13_accepted));
        if (cache_fill_o) begin
            assert ($onehot(completion_event_o));
            assert (!pmda_o);
        end
        if (type5_request_accepted_o) begin
            assert (type5_request_presented_o);
        end
        if (type13_request_accepted_o) begin
            assert (type13_request_presented_o);
        end
        if (automatic_pm_instruction_issue_o) begin
            assert (automatic_pm_flow_i);
            assert (!linear_fetch_request_presented_o);
            assert ($onehot(request_accepted_o[2:1]));
        end
        if (automatic_pm_instruction_retire_o) begin
            assert (automatic_pm_completion);
            assert (linear_retire_event_o);
        end
        if (automatic_pm_flow_blocked_o) begin
            assert (!type5_request_presented_o);
            assert (!type13_request_presented_o);
            assert (!linear_fetch_request_presented_o);
        end
        if (halt_force_fetch_issue_o && !halt_attachment_conflict_o) begin
            assert ($onehot(request_accepted_o[2:1]));
        end
        if (halted_o && !halt_resume_event_o) begin
            assert (halt_phase_hold_o);
            assert (!effective_phase_advance_o);
        end
        if (halt_br_conflict_o && halt_mode_o == 2'd0
            && bus_mode_o == 3'd0) begin
            assert (!halt_recognized_o);
        end
        if (bus_relinquished_o) begin
            assert (!pm_address_output_enable_o);
            assert (!pm_control_output_enable_o);
            assert (!pm_data_output_enable_o);
        end
    end
`endif
endmodule

`default_nettype wire
