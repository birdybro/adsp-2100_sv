`default_nettype none

// Bounded steady-state ordinary-fetch architectural client.
//
// The client retains the current instruction and all supported architectural
// state. It presents the selected next PC until an external PM owner accepts
// the request, then retires only when that owner routes the corresponding
// completion back.
// Native PM pin phases and multi-owner arbitration are deliberately external.
module adsp2100_linear_fetch_client #(
    parameter bit FETCHED_TYPE2_ENABLED = 1'b0,
    parameter bit FETCHED_TYPE3_ENABLED = 1'b0,
    parameter bit FETCHED_TYPE4_ENABLED = 1'b0,
    parameter bit FETCHED_TYPE12_ENABLED = 1'b0,
    // A larger composed owner may retain exact unknown-state metadata beside
    // this two-state storage. Standalone owners keep the conservative
    // invalid-DMD conflict unless that external sidecar is explicitly present.
    parameter bit EXTERNAL_FETCHED_DM_VALIDITY_SIDECARS = 1'b0
) (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        interrupt_sample_advance_i,
    input  logic        instruction_issue_inhibit_i,
    input  logic        bus_relinquished_i,

    input  logic        instruction_setup_i,
    input  logic [13:0] instruction_setup_pc_i,
    input  logic [23:0] instruction_setup_opcode_i,

    input  logic        pm_request_accepted_i,
    input  logic        pm_completion_event_i,
    input  logic [23:0] pmd_read_data_i,
    input  logic        pmd_read_data_valid_i,
    input  logic [15:0] dmd_read_data_i,
    input  logic        dmd_read_data_valid_i,
    input  logic [3:0]  irq_n_i,
    input  logic [5:0]  probe_code_i,

    // A composed owner supplies the cycle-start validity of the selected
    // Type 17 or fetched-DM store source. Standalone bounded owners initialize
    // every exercised source and tie this input high.
    input  logic        type17_source_data_valid_i,
    input  logic [7:0]  state_astat_valid_mask_i,
    input  logic [3:0]  state_mstat_valid_mask_i,
    input  logic        state_imask_valid_i,

    // Optional instruction-level PM-data boundary.  A composed Type 5 or
    // Type 13 client owns the physical PM cycle while this block retains the
    // sole PC/opcode sequencer.  Only sequential PC+1 flow is admitted here;
    // an active automatic loop is reported and rejected because its
    // termination decision must be captured at PM-data issue, not
    // recomputed after a possible miss-recovery cycle.
    input  logic        pm_instruction_active_i,
    input  logic        pm_instruction_complete_i,
    input  logic [23:0] pm_instruction_next_opcode_i,
    input  logic        pm_instruction_next_opcode_valid_i,

    // Optional state-external PM-data client boundary.  This is used by the
    // three-client composition to make ordinary fetch, Type 5, and Type 13
    // observe one physical architectural-state instance.  The external
    // client supplies already-decoded cycle-start read selectors and
    // completion-qualified write actions; PM timing and ownership remain
    // outside this module.
    input  logic        pm_state_operand_read_i,
    input  logic [3:0]  pm_state_memory_read_address_i,
    input  logic [3:0]  pm_state_dreg_read_address_1_i,
    input  logic [3:0]  pm_state_dreg_read_address_2_i,
    input  logic [2:0]  pm_state_dag_i_address_i,
    input  logic [2:0]  pm_state_dag_m_address_i,
    input  logic        pm_state_move_write_i,
    input  logic [5:0]  pm_state_move_code_i,
    input  logic [15:0] pm_state_move_data_i,
    input  logic        pm_state_dreg_write_i,
    input  logic [3:0]  pm_state_dreg_write_address_i,
    input  logic [15:0] pm_state_dreg_write_data_i,
    input  logic        pm_state_alu_write_i,
    input  logic        pm_state_alu_destination_feedback_i,
    input  logic [15:0] pm_state_alu_result_i,
    input  logic        pm_state_mac_write_i,
    input  logic        pm_state_mac_destination_feedback_i,
    input  logic [39:0] pm_state_mac_result_i,
    input  logic        pm_state_sr_write_i,
    input  logic [31:0] pm_state_sr_result_i,
    input  logic        pm_state_se_write_i,
    input  logic [7:0]  pm_state_se_result_i,
    input  logic        pm_state_sb_write_i,
    input  logic [4:0]  pm_state_sb_result_i,
    input  logic        pm_state_dag_i_write_i,
    input  logic [2:0]  pm_state_dag_i_write_address_i,
    input  logic [13:0] pm_state_dag_i_write_data_i,
    input  logic        pm_state_dag_i_write_valid_i,
    input  logic        pm_state_alu_status_write_i,
    input  logic        pm_state_alu_az_i,
    input  logic        pm_state_alu_an_i,
    input  logic        pm_state_alu_av_i,
    input  logic        pm_state_alu_ac_i,
    input  logic        pm_state_alu_as_write_i,
    input  logic        pm_state_alu_as_i,
    input  logic        pm_state_mac_status_write_i,
    input  logic        pm_state_mac_mv_i,
    input  logic        pm_state_shifter_status_write_i,
    input  logic        pm_state_shifter_ss_i,

    output logic        issue_boundary_o,
    output logic        instruction_setup_accepted_o,
    output logic        fetch_request_presented_o,
    output logic [13:0] fetch_address_o,
    output logic        instruction_issue_o,
    output logic        retire_event_o,
    output logic        pm_instruction_sequential_allowed_o,
    output logic        pm_instruction_flow_blocked_o,
    output logic        trap_event_o,
    output logic        interrupt_recognition_event_o,
    output logic        interrupt_entry_event_o,
    output logic        interrupt_vector_issue_event_o,
    output logic        interrupt_vector_fetch_event_o,
    output logic [1:0]  interrupt_level_o,
    output logic [13:0] interrupt_vector_o,
    output logic [3:0]  interrupt_pending_o,
    output logic        interrupt_vectoring_o,
    output logic        interrupt_configuration_invalid_o,
    output logic        interrupt_reset_baseline_provisional_o,
    output logic        interrupt_adjacent_control_conflict_o,
    output logic        instruction_valid_o,
    output logic        transaction_pending_o,
    output logic        unsupported_instruction_o,
    output logic        reserved_subencoding_o,
    output logic        phase_conflict_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic        provisional_source_extension_o,
    output logic [13:0] pc_o,
    output logic [23:0] opcode_o,

    output logic        fetched_dm_request_candidate_o,
    output logic        fetched_dm_request_presented_o,
    output logic [13:0] fetched_dm_request_address_o,
    output logic        fetched_dm_request_address_valid_o,
    output logic        fetched_dm_request_write_o,
    output logic [15:0] fetched_dm_request_write_data_o,
    output logic        fetched_dm_request_write_data_valid_o,

    output logic [15:0] probe_data_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [4:0]  icntl_o,
    output logic [3:0]  imask_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic [7:0]  px_o,
    output logic [7:0]  sstat_o,
    output logic        alternate_bank_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,
    output logic        status_restore_event_o,
    output logic [7:0]  status_restore_astat_valid_mask_o,
    output logic [3:0]  status_restore_mstat_valid_mask_o,
    output logic        status_restore_imask_valid_o,

    output logic [15:0] pm_state_memory_read_data_o,
    output logic [15:0] pm_state_dreg_read_data_1_o,
    output logic [15:0] pm_state_dreg_read_data_2_o,
    output logic [13:0] pm_state_dag_i_data_o,
    output logic        pm_state_dag_i_valid_o,
    output logic [13:0] pm_state_dag_m_data_o,
    output logic        pm_state_dag_m_valid_o,
    output logic [13:0] pm_state_dag_l_data_o,
    output logic        pm_state_dag_l_valid_o,
    output logic [15:0] pm_state_af_o,
    output logic [15:0] pm_state_mf_o,
    output logic [39:0] pm_state_mr_o,
    output logic [7:0]  pm_state_se_o,
    output logic [4:0]  pm_state_sb_o,
    output logic [31:0] pm_state_sr_o,
    output logic        pm_state_action_conflict_o
);
    import adsp2100_pkg::*;
    import adsp2100_register_pkg::*;

    localparam logic [1:0] FLOW_NONE = 2'b00;
    localparam logic [1:0] FLOW_JUMP = 2'b01;
    localparam logic [1:0] FLOW_CALL = 2'b10;
    localparam logic [1:0] FLOW_RETURN = 2'b11;

    logic [13:0] pc_q;
    logic [23:0] opcode_q;
    logic instruction_valid_q;
    logic pending_q;
    logic interrupt_vectoring_q;
    logic [1:0] interrupt_level_q;

    logic nop_valid;
    logic type2_action_valid;
    logic [15:0] type2_immediate;
    logic type2_dag2;
    logic [1:0] type2_i_local_unused;
    logic [1:0] type2_m_local_unused;
    logic [2:0] type2_i_address;
    logic [2:0] type2_m_address;
    logic [2:0] type2_l_address_unused;
    logic [13:0] type2_address;
    logic type2_address_valid;
    logic [13:0] type2_next_i;
    logic type2_next_i_valid;
    logic [13:0] type2_base_unused;
    logic type2_circular_unused;
    logic type2_configuration_valid;
    logic type3_class_valid;
    logic type3_action_valid;
    logic type3_invalid_subencoding;
    logic type3_write;
    logic [13:0] type3_address;
    logic [1:0] type3_register_group_unused;
    logic [3:0] type3_register_index;
    logic [5:0] type3_register_code;
    logic type3_register_present_unused;
    logic type3_register_writable_unused;
    logic type3_reserved_source_unused;
    logic type3_reserved_destination_unused;
    logic type3_read_only_destination_unused;
    logic type4_class_valid;
    logic type4_action_valid;
    logic type4_unsupported_subencoding;
    logic type4_destination_collision_unused;
    logic type4_computation_enable;
    logic type4_is_mac_unused;
    logic type4_live_destination_feedback_unused;
    logic type4_dag2;
    logic type4_write;
    logic [4:0] type4_amf_unused;
    logic [1:0] type4_yop_unused;
    logic [2:0] type4_xop_unused;
    logic [3:0] type4_x_source_dreg;
    logic [3:0] type4_y_source_dreg;
    logic [3:0] type4_memory_dreg;
    logic [2:0] type4_i_address;
    logic [2:0] type4_m_address;
    logic [13:0] type4_address;
    logic type4_address_valid;
    logic [13:0] type4_next_i;
    logic type4_next_i_valid;
    logic [13:0] type4_base_unused;
    logic type4_circular_unused;
    logic type4_configuration_valid;
    logic type12_class_valid;
    logic type12_action_valid;
    logic type12_unsupported_subencoding;
    logic type12_unavailable_xop_unused;
    logic type12_destination_collision_unused;
    logic type12_dag2;
    logic type12_write;
    logic [3:0] type12_sf_unused;
    logic [2:0] type12_xop_unused;
    logic [3:0] type12_shifter_source_dreg;
    logic [3:0] type12_memory_dreg;
    logic [2:0] type12_i_address;
    logic [2:0] type12_m_address;
    logic [13:0] type12_address;
    logic type12_address_valid;
    logic [13:0] type12_next_i;
    logic type12_next_i_valid;
    logic [13:0] type12_base_unused;
    logic type12_circular_unused;
    logic type12_configuration_valid;
    logic type6_valid;
    logic [3:0] type6_destination;
    logic [15:0] type6_data;
    logic type7_class_valid;
    logic type7_action_valid;
    logic type7_invalid_subencoding;
    logic [1:0] type7_group_unused;
    logic [3:0] type7_index_unused;
    logic [5:0] type7_code;
    logic [13:0] type7_data;
    logic type7_present_unused;
    logic type7_writable_unused;
    logic type7_dreg_unused;
    logic type7_reserved_unused;
    logic type7_read_only_unused;
    logic type18_valid;
    logic [1:0] type18_mode_sr;
    logic [1:0] type18_mode_br;
    logic [1:0] type18_mode_ol;
    logic [1:0] type18_mode_as;
    logic type18_has_effect_unused;
    logic type18_has_alias_unused;
    logic type21_action_valid;
    logic type21_dag2_unused;
    logic [2:0] type21_i_address;
    logic [2:0] type21_m_address;
    logic type21_operands_valid_unused;
    logic type21_configuration_valid_unused;
    logic type21_i_write;
    logic [13:0] type21_i_write_data;
    logic type21_i_write_result_valid;
    logic type26_action_valid;
    logic [1:0] type26_status_operation;
    logic type26_count_pop;
    logic type26_loop_pop;
    logic type26_pc_pop;
    logic type26_has_effect_unused;
    logic type10_class_valid;
    logic type10_action_valid;
    logic type10_unsupported_call_ce;
    logic type10_call;
    logic [13:0] type10_address;
    logic [3:0] type10_condition;
    logic type10_condition_true;
    logic type10_condition_state_valid;
    logic type10_taken;
    logic type10_invalid_condition_state;
    logic type11_class_valid;
    logic type11_action_valid;
    logic [13:0] type11_end_address;
    logic [3:0] type11_termination;
    logic type19_class_valid;
    logic type19_action_valid;
    logic type19_unsupported_call_ce;
    logic type19_call;
    logic [1:0] type19_i_local_unused;
    logic [2:0] type19_i_address;
    logic [3:0] type19_condition;
    logic type19_condition_true;
    logic type19_condition_state_valid;
    logic type19_taken;
    logic type19_invalid_condition_state;
    logic type19_invalid_target_state;
    logic type20_class_valid;
    logic type20_action_valid;
    logic type20_interrupt_return;
    logic [3:0] type20_condition;
    logic type20_condition_true;
    logic type20_condition_state_valid;
    logic type20_taken;
    logic type20_invalid_condition_state;
    logic type20_invalid_return_context;
    logic type22_class_valid;
    logic type22_action_valid;
    logic [3:0] type22_condition;
    logic type22_condition_true;
    logic type22_condition_state_valid;
    logic type22_taken;
    logic type22_invalid_condition_state;
    logic [1:0] sequencer_explicit_flow;
    logic sequencer_explicit_taken;
    logic [13:0] sequencer_explicit_target;
    logic [13:0] sequencer_next_pc;
    logic sequencer_pc_stack_push;
    logic [13:0] sequencer_pc_stack_push_value;
    logic sequencer_pc_stack_pop;
    logic sequencer_loop_stack_pop;
    logic sequencer_count_stack_pop_unused;
    logic sequencer_loop_counter_test;
    logic sequencer_loop_back_unused;
    logic sequencer_loop_exit;
    logic sequencer_explicit_transfer_unused;
    logic loop_active;
    logic [13:0] loop_end;
    logic [3:0] loop_termination;
    logic loop_uses_counter;
    logic loop_if_predicate;
    logic loop_termination_true;
    logic loop_at_end;
    logic automatic_loop_flow;
    logic invalid_loop_context;
    logic unsupported_do_at_loop_end;
    logic unsupported_nested_same_end;
    logic automatic_manual_conflict;
    logic instruction_writes_cntr;
    logic type17_class_valid;
    logic type17_action_valid;
    logic type17_invalid_subencoding;
    logic [1:0] type17_destination_group_unused;
    logic [1:0] type17_source_group_unused;
    logic [3:0] type17_destination_index_unused;
    logic [3:0] type17_source_index_unused;
    logic [5:0] type17_destination_code;
    logic [5:0] type17_source_code;
    logic type17_destination_present_unused;
    logic type17_destination_writable_unused;
    logic type17_source_valid_unused;
    logic type8_class_valid;
    logic type8_action_valid;
    logic type8_unsupported_subencoding;
    logic type8_unverified_amf_zero_unused;
    logic type8_destination_collision_unused;
    logic type8_is_mac_unused;
    logic type8_live_destination_feedback_unused;
    logic [4:0] type8_live_amf_unused;
    logic [1:0] type8_live_yop_unused;
    logic [2:0] type8_live_xop_unused;
    logic [3:0] type8_live_move_destination_unused;
    logic type8_destination_feedback;
    logic [3:0] type8_x_source_dreg;
    logic [3:0] type8_y_source_dreg;
    logic [3:0] type8_move_destination_dreg;
    logic [3:0] type8_move_source_dreg;
    logic type8_move_write;
    logic [15:0] type8_move_data;
    logic type8_alu_write;
    logic [15:0] type8_alu_result;
    logic type8_alu_az;
    logic type8_alu_an;
    logic type8_alu_av;
    logic type8_alu_ac;
    logic type8_alu_as_write;
    logic type8_alu_as;
    logic type8_mac_write;
    logic [39:0] type8_mac_result;
    logic type8_mac_mv;
    logic type9_class_valid;
    logic type9_action_valid;
    logic type9_nop_action;
    logic type9_condition_true;
    logic type9_is_mac;
    logic type9_is_alu;
    logic type9_live_unsupported_unused;
    logic type9_live_destination_feedback_unused;
    logic [4:0] type9_live_amf_unused;
    logic [1:0] type9_live_yop_unused;
    logic [2:0] type9_live_xop_unused;
    logic [3:0] type9_live_condition_unused;
    logic type9_destination_feedback;
    logic [3:0] type9_x_source_dreg;
    logic [3:0] type9_y_source_dreg;
    logic type9_alu_write;
    logic [15:0] type9_alu_result;
    logic type9_alu_az;
    logic type9_alu_an;
    logic type9_alu_av;
    logic type9_alu_ac;
    logic type9_alu_as_write;
    logic type9_alu_as;
    logic type9_mac_write;
    logic [39:0] type9_mac_result;
    logic type9_mac_mv;

    // Type 4/8/9 computations read cycle-start state at the state-8 issue
    // edge, evaluate from those captured operands during state 1, and retain
    // the result until state-7 retirement.  This is an internal FPGA
    // pipeline across sourced logical substates; it adds no architectural
    // instruction cycle and prevents the full MAC/rounding chain from
    // landing directly on the retirement edge.
    logic compute_stage1_valid_q;
    logic [23:0] compute_stage1_opcode_q;
    logic compute_stage1_not_counter_expired_q;
    logic [15:0] compute_stage1_x_q;
    logic [15:0] compute_stage1_y_q;
    logic [15:0] compute_stage1_move_q;
    logic [15:0] compute_stage1_af_q;
    logic [15:0] compute_stage1_mf_q;
    logic [39:0] compute_stage1_mr_q;
    logic [7:0] compute_stage1_astat_q;
    logic [31:0] compute_stage1_sr_q;
    logic [7:0] compute_stage1_se_q;
    logic [4:0] compute_stage1_sb_q;
    logic compute_stage1_overflow_latch_q;
    logic compute_stage1_saturate_ar_q;
    logic compute_stage1_capture;

    logic type8_pipeline_class_unused;
    logic type8_pipeline_action_unused;
    logic type8_pipeline_unsupported_unused;
    logic type8_pipeline_amf_zero_unused;
    logic type8_pipeline_collision_unused;
    logic type8_pipeline_is_mac_unused;
    logic type8_pipeline_destination_feedback;
    logic [3:0] type8_pipeline_x_unused;
    logic [3:0] type8_pipeline_y_unused;
    logic [3:0] type8_pipeline_move_destination;
    logic [3:0] type8_pipeline_move_source_unused;
    logic type8_pipeline_move_write;
    logic [15:0] type8_pipeline_move_data;
    logic type8_pipeline_alu_write;
    logic [15:0] type8_pipeline_alu_result;
    logic type8_pipeline_alu_az;
    logic type8_pipeline_alu_an;
    logic type8_pipeline_alu_av;
    logic type8_pipeline_alu_ac;
    logic type8_pipeline_alu_as_write;
    logic type8_pipeline_alu_as;
    logic type8_pipeline_mac_write;
    logic [39:0] type8_pipeline_mac_result;
    logic type8_pipeline_mac_mv;

    logic type9_pipeline_class_unused;
    logic type9_pipeline_action_unused;
    logic type9_pipeline_nop_unused;
    logic type9_pipeline_condition_unused;
    logic type9_pipeline_is_mac_unused;
    logic type9_pipeline_is_alu_unused;
    logic type9_pipeline_destination_feedback;
    logic [3:0] type9_pipeline_x_unused;
    logic [3:0] type9_pipeline_y_unused;
    logic [15:0] type9_pipeline_x_data_unused;
    logic [15:0] type9_pipeline_y_data_unused;
    logic type9_pipeline_alu_write;
    logic [15:0] type9_pipeline_alu_result;
    logic type9_pipeline_alu_az;
    logic type9_pipeline_alu_an;
    logic type9_pipeline_alu_av;
    logic type9_pipeline_alu_ac;
    logic type9_pipeline_alu_as_write;
    logic type9_pipeline_alu_as;
    logic type9_pipeline_mac_write;
    logic [39:0] type9_pipeline_mac_result;
    logic type9_pipeline_mac_mv;
    logic type4_pipeline_class_unused;
    logic type4_pipeline_action_unused;
    logic type4_pipeline_unsupported_unused;
    logic type4_pipeline_collision_unused;
    logic type4_pipeline_computation_enable_unused;
    logic type4_pipeline_is_mac_unused;
    logic type4_pipeline_destination_feedback;
    logic type4_pipeline_dag2_unused;
    logic type4_pipeline_write;
    logic [3:0] type4_pipeline_x_unused;
    logic [3:0] type4_pipeline_y_unused;
    logic [3:0] type4_pipeline_memory_dreg;
    logic [2:0] type4_pipeline_i_unused;
    logic [2:0] type4_pipeline_m_unused;
    logic [15:0] type4_pipeline_memory_data_unused;
    logic type4_pipeline_alu_write;
    logic [15:0] type4_pipeline_alu_result;
    logic type4_pipeline_alu_az;
    logic type4_pipeline_alu_an;
    logic type4_pipeline_alu_av;
    logic type4_pipeline_alu_ac;
    logic type4_pipeline_alu_as_write;
    logic type4_pipeline_alu_as;
    logic type4_pipeline_mac_write;
    logic [39:0] type4_pipeline_mac_result;
    logic type4_pipeline_mac_mv;
    logic type4_destination_feedback;
    logic type4_retired_write;
    logic [3:0] type4_retired_memory_dreg;
    logic type4_alu_write;
    logic [15:0] type4_alu_result;
    logic type4_alu_az;
    logic type4_alu_an;
    logic type4_alu_av;
    logic type4_alu_ac;
    logic type4_alu_as_write;
    logic type4_alu_as;
    logic type4_mac_write;
    logic [39:0] type4_mac_result;
    logic type4_mac_mv;
    logic type12_pipeline_class_unused;
    logic type12_pipeline_action_unused;
    logic type12_pipeline_unsupported_unused;
    logic type12_pipeline_unavailable_xop_unused;
    logic type12_pipeline_collision_unused;
    logic type12_pipeline_dag2_unused;
    logic type12_pipeline_write;
    logic [3:0] type12_pipeline_source_unused;
    logic [3:0] type12_pipeline_memory_dreg;
    logic [2:0] type12_pipeline_i_unused;
    logic [2:0] type12_pipeline_m_unused;
    logic [15:0] type12_pipeline_memory_data_unused;
    logic type12_pipeline_sr_write;
    logic [31:0] type12_pipeline_sr_result;
    logic type12_pipeline_se_write;
    logic [7:0] type12_pipeline_se_result;
    logic type12_pipeline_sb_write;
    logic [4:0] type12_pipeline_sb_result;
    logic type12_pipeline_ss_write;
    logic type12_pipeline_ss_result;
    logic type12_retired_write;
    logic [3:0] type12_retired_memory_dreg;
    logic type12_sr_write;
    logic [31:0] type12_sr_result;
    logic type12_se_write;
    logic [7:0] type12_se_result;
    logic type12_sb_write;
    logic [4:0] type12_sb_result;
    logic type12_ss_write;
    logic type12_ss_result;
    logic type23_class_valid;
    logic type23_action_valid;
    logic [2:0] type23_xop_unused;
    logic [3:0] type23_divisor_source_dreg;
    logic type23_add_divisor_unused;
    logic [15:0] type23_alu_result_unused;
    logic type23_new_aq_unused;
    logic type23_quotient_bit_unused;
    logic type23_af_write;
    logic [15:0] type23_af_result;
    logic type23_ay0_write;
    logic [15:0] type23_ay0_result;
    logic type23_aq_write;
    logic type23_aq_result;
    logic type24_class_valid;
    logic type24_action_valid;
    logic type24_unsupported_yop;
    logic [1:0] type24_yop_unused;
    logic [2:0] type24_xop_unused;
    logic [3:0] type24_divisor_source_dreg;
    logic [3:0] type24_upper_source_dreg;
    logic type24_upper_source_feedback_unused;
    logic [15:0] type24_upper_value_unused;
    logic type24_quotient_sign_unused;
    logic type24_af_write;
    logic [15:0] type24_af_result;
    logic type24_ay0_write;
    logic [15:0] type24_ay0_result;
    logic type24_aq_write;
    logic type24_aq_result;
    logic type25_action_valid;
    logic type25_condition_mv_unused;
    logic type25_mr_write;
    logic [39:0] type25_mr_result;
    logic type14_class_valid;
    logic type14_action_valid;
    logic type14_unsupported_subencoding;
    logic type14_unverified_unused_x_unused;
    logic type14_unavailable_xop_unused;
    logic type14_destination_collision_unused;
    logic [3:0] type14_shifter_source_dreg;
    logic [3:0] type14_move_destination_dreg;
    logic [3:0] type14_move_source_dreg;
    logic type14_move_write;
    logic [15:0] type14_move_data;
    logic type14_sr_write;
    logic [31:0] type14_sr_result;
    logic type14_se_write;
    logic [7:0] type14_se_result;
    logic type14_sb_write;
    logic [4:0] type14_sb_result;
    logic type14_ss_write;
    logic type14_ss_result;
    logic type15_class_valid;
    logic type15_action_valid;
    logic type15_unsupported_subencoding;
    logic [3:0] type15_source_dreg;
    logic type15_sr_write;
    logic [31:0] type15_sr_result;
    logic type16_class_valid;
    logic type16_action_valid;
    logic type16_unsupported_subencoding;
    logic type16_condition_true;
    logic [3:0] type16_source_dreg;
    logic type16_sr_write;
    logic [31:0] type16_sr_result;
    logic type16_se_write;
    logic [7:0] type16_se_result;
    logic type16_sb_write;
    logic [4:0] type16_sb_result;
    logic type16_ss_write;
    logic type16_ss_result;
    logic supported_instruction;
    logic state_write;
    logic [5:0] state_write_code;
    logic [15:0] state_write_data;
    logic state_invalid_setup;
    logic [5:0] state_read_code;
    logic [15:0] state_read_data;
    logic [15:0] state_move_dreg_read_data;
    logic [15:0] state_dreg_read_data;
    logic [15:0] state_dreg_read_data_2;
    logic [15:0] state_dreg_read_data_3;
    logic [15:0] state_dreg_read_data_4;
    logic [15:0] state_dreg_read_data_5;
    logic state_count_push_unused;
    logic [13:0] state_count_push_data_unused;
    logic state_not_counter_expired_raw;
    logic state_not_counter_expired_unused;
    logic state_bit_reverse_unused;
    logic state_overflow_latch;
    logic state_saturate_ar;
    logic [15:0] state_af;
    logic [15:0] state_mf;
    logic [39:0] state_mr;
    logic [7:0] state_se;
    logic [4:0] state_sb;
    logic [31:0] state_sr;
    logic [13:0] state_dag_i_read_data;
    logic state_dag_i_read_valid;
    logic [13:0] state_dag_m_read_data;
    logic state_dag_m_read_valid;
    logic [13:0] state_dag_l_read_data;
    logic state_dag_l_read_valid;
    logic [13:0] state_pm_dag_i_read_data;
    logic state_pm_dag_i_read_valid;
    logic [13:0] state_pm_dag_m_read_data;
    logic state_pm_dag_m_read_valid;
    logic [13:0] state_pm_dag_l_read_data;
    logic state_pm_dag_l_read_valid;
    logic [13:0] state_pc_stack_top;
    logic state_pc_stack_top_valid;
    logic [15:0] state_status_stack_top_unused;
    logic state_status_stack_top_valid;
    logic [17:0] state_loop_stack_top;
    logic state_loop_stack_top_valid;
    logic state_internal_conflict;
    logic state_icntl_valid;
    logic interrupt_sample_event_unused;
    logic [3:0] interrupt_sampled_requests_unused;
    logic [3:0] interrupt_enabled_requests;
    logic [3:0] interrupt_edge_pending;
    logic [1:0] interrupt_recognized_level;
    logic interrupt_sample_history_valid_unused;
    logic interrupt_service_allowed;
    logic interrupt_phase_advance;
    logic interrupt_adjacent_control_write;
    logic interrupt_vector_request;
    logic linear_fetch_retire;
    logic state_action_retire;
    logic mstat_dependency_invalid;
    logic pm_instruction_retire;
    logic pm_instruction_completion_conflict;
    logic pm_state_action;
    logic linear_state_action;
    logic pm_state_action_enable;
    logic unused_observation;

    assign state_not_counter_expired_raw = (
        cntr_valid_o && (cntr_o != 14'h0001)
    );

    assign issue_boundary_o = (
        !reset_i && !instruction_issue_inhibit_i
        && !bus_relinquished_i && phase_advance_i
        && phase_i == PHASE_STATE_8
    );
    assign instruction_setup_accepted_o = (
        issue_boundary_o && instruction_setup_i
        && !instruction_valid_q && !pending_q && !interrupt_vectoring_q
    );
    assign phase_conflict_o = (
        !reset_i && instruction_setup_i && !issue_boundary_o
    );
    assign integration_conflict_o = (
        (!reset_i && instruction_setup_i
            && (instruction_valid_q || pending_q || interrupt_vectoring_q))
        || (issue_boundary_o && mstat_dependency_invalid)
    );

    assign nop_valid = opcode_q == 24'h000000;
    assign supported_instruction = (
        nop_valid
        || (FETCHED_TYPE2_ENABLED && type2_action_valid)
        || (FETCHED_TYPE3_ENABLED && type3_action_valid)
        || (FETCHED_TYPE4_ENABLED && type4_action_valid)
        || (FETCHED_TYPE12_ENABLED && type12_action_valid)
        || type6_valid || type7_action_valid || type8_action_valid
        || type17_action_valid
        || type18_valid || type9_action_valid || type15_action_valid
        || type16_action_valid || type14_action_valid || type23_action_valid
        || type21_action_valid || type24_action_valid || type25_action_valid
        || type26_action_valid || type10_action_valid || type11_action_valid
        || type19_action_valid || type20_action_valid || type22_action_valid
        || pm_instruction_active_i
    );
    assign reserved_subencoding_o = (
        issue_boundary_o && instruction_valid_q
        && (
            (type7_class_valid && type7_invalid_subencoding)
            || (
                FETCHED_TYPE3_ENABLED && type3_class_valid
                && type3_invalid_subencoding
            )
            || (
                FETCHED_TYPE4_ENABLED && type4_class_valid
                && type4_unsupported_subencoding
            )
            || (
                FETCHED_TYPE12_ENABLED && type12_class_valid
                && type12_unsupported_subencoding
            )
            || (type8_class_valid && type8_unsupported_subencoding)
            || (type17_class_valid && type17_invalid_subencoding)
            || (type14_class_valid && type14_unsupported_subencoding)
            || (type15_class_valid && type15_unsupported_subencoding)
            || (type16_class_valid && type16_unsupported_subencoding)
            || (type24_class_valid && type24_unsupported_yop)
        )
    );
    assign unsupported_instruction_o = (
        issue_boundary_o && instruction_valid_q
        && !supported_instruction && !reserved_subencoding_o
    );
    // The one-stage pipeline fetches the selected next address in the current
    // instruction cycle. This bounded preload owner assumes required ASTAT
    // bits are initialized; CNTR retains an explicit validity state.
    assign type10_condition_state_valid = (
        (type10_condition != 4'he) || cntr_valid_o
    );
    assign type10_taken = (
        type10_action_valid && type10_condition_state_valid
        && type10_condition_true
    );
    assign type10_invalid_condition_state = (
        issue_boundary_o && type10_action_valid
        && !type10_condition_state_valid
    );
    assign type20_condition_state_valid = (
        (type20_condition != 4'he) || cntr_valid_o
    );
    assign type20_taken = (
        type20_action_valid && type20_condition_state_valid
        && type20_condition_true
    );
    assign type20_invalid_condition_state = (
        issue_boundary_o && type20_action_valid
        && !type20_condition_state_valid
    );
    assign type20_invalid_return_context = (
        issue_boundary_o && type20_taken
        && (
            !state_pc_stack_top_valid
            || (type20_interrupt_return && !state_status_stack_top_valid)
        )
    );
    assign type19_condition_state_valid = (
        (type19_condition != 4'he) || cntr_valid_o
    );
    assign type19_taken = (
        type19_action_valid && type19_condition_state_valid
        && type19_condition_true
    );
    assign type19_invalid_condition_state = (
        issue_boundary_o && type19_action_valid
        && !type19_condition_state_valid
    );
    assign type19_invalid_target_state = (
        issue_boundary_o && type19_taken && !state_dag_i_read_valid
    );
    assign type22_condition_state_valid = (
        (type22_condition != 4'he) || cntr_valid_o
    );
    assign type22_taken = (
        type22_action_valid && type22_condition_state_valid
        && type22_condition_true
    );
    assign type22_invalid_condition_state = (
        issue_boundary_o && type22_action_valid
        && !type22_condition_state_valid
    );
    assign loop_active = state_loop_stack_top_valid;
    assign loop_end = state_loop_stack_top[13:0];
    assign loop_termination = state_loop_stack_top[17:14];
    assign loop_uses_counter = loop_termination == 4'he;
    assign loop_termination_true = ~loop_if_predicate;
    assign loop_at_end = loop_active && (pc_q == loop_end);
    assign sequencer_explicit_taken = (
        type10_taken || type19_taken || type20_taken || type22_taken
    );
    always_comb begin
        sequencer_explicit_flow = FLOW_NONE;
        sequencer_explicit_target = 14'h0000;
        if (type10_action_valid) begin
            sequencer_explicit_flow = type10_call ? FLOW_CALL : FLOW_JUMP;
            sequencer_explicit_target = type10_address;
        end else if (type19_action_valid) begin
            sequencer_explicit_flow = type19_call ? FLOW_CALL : FLOW_JUMP;
            sequencer_explicit_target = state_dag_i_read_data;
        end else if (type20_action_valid) begin
            sequencer_explicit_flow = FLOW_RETURN;
            sequencer_explicit_target = state_pc_stack_top;
        end else if (type22_action_valid) begin
            // A taken TRAP is an explicit flow action for loop precedence,
            // but its fetch target remains the sequential PC+1 word.
            sequencer_explicit_flow = FLOW_JUMP;
            sequencer_explicit_target = pc_q + 14'h0001;
        end
    end
    assign automatic_loop_flow = (
        loop_at_end
        && !(
            sequencer_explicit_taken
            && (sequencer_explicit_flow != FLOW_NONE)
        )
    );
    assign invalid_loop_context = (
        issue_boundary_o && loop_active
        && (
            !state_pc_stack_top_valid
            || (loop_uses_counter && !cntr_valid_o)
        )
    );
    assign unsupported_do_at_loop_end = (
        issue_boundary_o && type11_action_valid && loop_at_end
    );
    assign unsupported_nested_same_end = (
        issue_boundary_o && type11_action_valid && loop_active
        && (type11_end_address == loop_end)
    );
    assign instruction_writes_cntr = (
        (type7_action_valid && (type7_code == 6'h35))
        || (type17_action_valid && (type17_destination_code == 6'h35))
        || (
            FETCHED_TYPE3_ENABLED && type3_action_valid && !type3_write
            && (type3_register_code == 6'h35)
        )
    );
    assign automatic_manual_conflict = (
        issue_boundary_o && automatic_loop_flow
        && (
            (type26_action_valid && type26_pc_pop
                && sequencer_pc_stack_pop)
            || (type26_action_valid && type26_loop_pop
                && sequencer_loop_stack_pop)
            || (sequencer_loop_counter_test
                && (
                    (type26_action_valid && type26_count_pop)
                    || instruction_writes_cntr
                ))
        )
    );
    assign interrupt_adjacent_control_write = (
        (type18_valid && type18_has_effect_unused)
        || (
            type7_action_valid
            && (
                (type7_code == 6'h31) || (type7_code == 6'h33)
                || (type7_code == 6'h34)
            )
        )
        || (
            type17_action_valid
            && (
                (type17_destination_code == 6'h31)
                || (type17_destination_code == 6'h33)
                || (type17_destination_code == 6'h34)
            )
        )
        || (
            FETCHED_TYPE3_ENABLED && type3_action_valid && !type3_write
            && (
                (type3_register_code == 6'h31)
                || (type3_register_code == 6'h33)
                || (type3_register_code == 6'h34)
            )
        )
    );
    assign interrupt_vector_request = (
        issue_boundary_o && interrupt_vectoring_q && !pending_q
        && !instruction_setup_i
    );
    assign fetch_address_o = interrupt_vectoring_q
        ? {12'h000, interrupt_level_q} : sequencer_next_pc;
    assign fetch_request_presented_o = (
        interrupt_vector_request
        || (
            issue_boundary_o && instruction_valid_q
            && supported_instruction && !pending_q
            && !interrupt_vectoring_q && !instruction_setup_i
            && !pm_instruction_active_i
            && !type10_invalid_condition_state
            && !type19_invalid_condition_state
            && !type19_invalid_target_state
            && !type20_invalid_condition_state
            && !type20_invalid_return_context
            && !type22_invalid_condition_state
            && !invalid_loop_context
            && !unsupported_do_at_loop_end
            && !unsupported_nested_same_end
            && !automatic_manual_conflict
        )
    );
    // This conservative state-8 preflight is independent of the external
    // issue inhibit so a composition can inhibit both PM and DM admission
    // before either controller captures a colliding request. Contextual flow
    // conflicts remain authoritative in fetch_request_presented_o.
    assign fetched_dm_request_candidate_o = (
        !reset_i && !bus_relinquished_i && phase_advance_i
        && phase_i == PHASE_STATE_8
        && instruction_valid_q && !pending_q && !interrupt_vectoring_q
        && !instruction_setup_i && !pm_instruction_active_i
        && (
            (FETCHED_TYPE2_ENABLED && type2_action_valid)
            || (FETCHED_TYPE3_ENABLED && type3_action_valid)
            || (FETCHED_TYPE4_ENABLED && type4_action_valid)
            || (FETCHED_TYPE12_ENABLED && type12_action_valid)
        )
    );
    assign fetched_dm_request_presented_o = (
        (
            (FETCHED_TYPE2_ENABLED && type2_action_valid)
            || (FETCHED_TYPE3_ENABLED && type3_action_valid)
            || (FETCHED_TYPE4_ENABLED && type4_action_valid)
            || (FETCHED_TYPE12_ENABLED && type12_action_valid)
        )
        && fetch_request_presented_o && !interrupt_vector_request
    );
    assign fetched_dm_request_address_valid_o = (
        fetched_dm_request_presented_o
        && (
            (FETCHED_TYPE2_ENABLED && type2_action_valid)
                ? type2_address_valid
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? type4_address_valid
                        : (
                            FETCHED_TYPE12_ENABLED && type12_action_valid
                                ? type12_address_valid : 1'b1
                        )
                )
        )
    );
    assign fetched_dm_request_address_o = fetched_dm_request_address_valid_o
        ? (
            FETCHED_TYPE2_ENABLED && type2_action_valid
                ? type2_address
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? type4_address
                        : (
                            FETCHED_TYPE12_ENABLED && type12_action_valid
                                ? type12_address : type3_address
                        )
                )
        )
        : 14'h0000;
    assign fetched_dm_request_write_o = (
        fetched_dm_request_presented_o
        && (
            (FETCHED_TYPE2_ENABLED && type2_action_valid)
            || (
                FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_write
                    : (
                        FETCHED_TYPE12_ENABLED && type12_action_valid
                            ? type12_write : type3_write
                    )
            )
        )
    );
    assign fetched_dm_request_write_data_valid_o = (
        fetched_dm_request_write_o
        && (
            (FETCHED_TYPE2_ENABLED && type2_action_valid)
            || type17_source_data_valid_i
        )
    );
    assign fetched_dm_request_write_data_o = (
        fetched_dm_request_write_data_valid_o
            ? (
                FETCHED_TYPE2_ENABLED && type2_action_valid
                    ? type2_immediate
                    : (
                        FETCHED_TYPE4_ENABLED && type4_action_valid
                            ? state_dreg_read_data_2
                            : (
                                FETCHED_TYPE12_ENABLED
                                && type12_action_valid
                                    ? state_dreg_read_data_2
                                    : state_read_data
                            )
                    )
            )
            : 16'h0000
    );
    assign instruction_issue_o = pm_request_accepted_i;
    assign pm_instruction_sequential_allowed_o = (
        !loop_active && !pending_q && !interrupt_vectoring_q
        && !instruction_setup_i
    );
    assign pm_instruction_flow_blocked_o = (
        !reset_i && issue_boundary_o && instruction_valid_q
        && pm_instruction_active_i
        && !pm_instruction_sequential_allowed_o
    );
    assign linear_fetch_retire = (
        pending_q && pm_completion_event_i && !interrupt_vectoring_q
    );
    assign pm_instruction_retire = (
        pm_instruction_complete_i && instruction_valid_q
        && pm_instruction_active_i
        && pm_instruction_sequential_allowed_o
        && phase_advance_i && phase_i == PHASE_STATE_7
    );
    assign retire_event_o = linear_fetch_retire || pm_instruction_retire;
    assign pm_instruction_completion_conflict = (
        !reset_i && pm_instruction_complete_i && !pm_instruction_retire
    );
    assign trap_event_o = linear_fetch_retire && type22_taken;
    assign interrupt_service_allowed = (
        retire_event_o && instruction_valid_q && supported_instruction
        && !trap_event_o && !interrupt_adjacent_control_write
    );
    // A native DMACK extension holds the architectural owner in state 7
    // while the physical eight-state pins continue to circulate. The
    // separate sample input admits only that physical state-7 IRQ sample;
    // issue, retirement, and service remain governed by phase_advance_i.
    assign interrupt_phase_advance = (
        phase_advance_i || interrupt_sample_advance_i
    );
    assign interrupt_entry_event_o = (
        interrupt_vector_request && pm_request_accepted_i
    );
    assign interrupt_vector_issue_event_o = interrupt_entry_event_o;
    assign interrupt_vector_fetch_event_o = (
        interrupt_vectoring_q && pending_q && pm_completion_event_i
    );
    assign interrupt_level_o = interrupt_recognition_event_o
        ? interrupt_recognized_level : interrupt_level_q;
    assign interrupt_pending_o = interrupt_edge_pending;
    assign interrupt_vectoring_o = interrupt_vectoring_q;
    assign interrupt_adjacent_control_conflict_o = (
        linear_fetch_retire && interrupt_adjacent_control_write
        && (interrupt_enabled_requests != 4'h0)
    );

    assign mstat_dependency_invalid = instruction_valid_q && (
        (
            !state_mstat_valid_mask_i[0]
            && (
                type6_valid
                || (type7_action_valid && type7_code == 6'h36)
                || type8_action_valid || type9_action_valid
                || type14_action_valid || type15_action_valid
                || type16_action_valid || type23_action_valid
                || type24_action_valid || type25_action_valid
                || (FETCHED_TYPE4_ENABLED && type4_action_valid)
                || (FETCHED_TYPE12_ENABLED && type12_action_valid)
                || (
                    FETCHED_TYPE3_ENABLED && type3_action_valid
                    && (
                        type3_register_code[5:4] == 2'b00
                        || type3_register_code == 6'h36
                    )
                )
                || (
                    type17_action_valid
                    && (
                        type17_source_code[5:4] == 2'b00
                        || type17_source_code == 6'h36
                        || type17_destination_code[5:4] == 2'b00
                        || type17_destination_code == 6'h36
                    )
                )
            )
        )
        || (
            state_mstat_valid_mask_i != 4'hf
            && (
                type8_action_valid || type9_action_valid
                || (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                    && type4_computation_enable
                )
            )
        )
        || (
            FETCHED_TYPE2_ENABLED && type2_action_valid && !type2_dag2
            && !state_mstat_valid_mask_i[1]
        )
        || (
            FETCHED_TYPE4_ENABLED && type4_action_valid && !type4_dag2
            && !state_mstat_valid_mask_i[1]
        )
        || (
            FETCHED_TYPE12_ENABLED && type12_action_valid && !type12_dag2
            && !state_mstat_valid_mask_i[1]
        )
    );
    assign state_action_retire =
        linear_fetch_retire && !mstat_dependency_invalid;
    assign state_write = state_action_retire && (
        type6_valid || type7_action_valid || type17_action_valid
        || (
            FETCHED_TYPE3_ENABLED && type3_action_valid && !type3_write
        )
    );
    assign state_write_code = type6_valid
        ? {2'b00, type6_destination}
        : (
            type7_action_valid ? type7_code
            : (
                type17_action_valid
                    ? type17_destination_code : type3_register_code
            )
        );
    assign state_write_data = type6_valid
        ? type6_data
        : (
            type7_action_valid
                ? {2'b00, type7_data}
                : (
                    type17_action_valid ? state_read_data : dmd_read_data_i
                )
        );
    always_comb begin
        state_read_code = {2'b00, type9_x_source_dreg};
        if (type8_class_valid) begin
            state_read_code = {2'b00, type8_x_source_dreg};
        end
        if (type23_class_valid) begin
            state_read_code = {2'b00, type23_divisor_source_dreg};
        end
        if (type24_class_valid) begin
            state_read_code = {2'b00, type24_divisor_source_dreg};
        end
        if (type14_class_valid) begin
            state_read_code = {2'b00, type14_shifter_source_dreg};
        end
        if (type16_class_valid) begin
            state_read_code = {2'b00, type16_source_dreg};
        end
        if (type15_class_valid) begin
            state_read_code = {2'b00, type15_source_dreg};
        end
        if (type17_class_valid) begin
            state_read_code = type17_source_code;
        end
        if (
            FETCHED_TYPE3_ENABLED && type3_action_valid && type3_write
        ) begin
            state_read_code = type3_register_code;
        end
        if (FETCHED_TYPE4_ENABLED && type4_action_valid) begin
            state_read_code = {2'b00, type4_x_source_dreg};
        end
        if (FETCHED_TYPE12_ENABLED && type12_action_valid) begin
            state_read_code = {2'b00, type12_shifter_source_dreg};
        end
    end

    assign instruction_valid_o = instruction_valid_q;
    assign transaction_pending_o = pending_q;
    assign pc_o = pc_q;
    assign opcode_o = opcode_q;
    assign internal_conflict_o = (
        state_internal_conflict || type10_invalid_condition_state
        || type19_invalid_condition_state || type19_invalid_target_state
        || type20_invalid_condition_state || type20_invalid_return_context
        || type22_invalid_condition_state
        || invalid_loop_context || unsupported_do_at_loop_end
        || unsupported_nested_same_end || automatic_manual_conflict
        || interrupt_adjacent_control_conflict_o
        || pm_instruction_flow_blocked_o
        || pm_instruction_completion_conflict
        || pm_state_action_conflict_o
        || (!EXTERNAL_FETCHED_DM_VALIDITY_SIDECARS
            && (
                (
                    linear_fetch_retire && FETCHED_TYPE4_ENABLED
                    && type4_action_valid && !type4_retired_write
                    && !dmd_read_data_valid_i
                )
                || (
                    linear_fetch_retire && FETCHED_TYPE12_ENABLED
                    && type12_action_valid && !type12_retired_write
                    && !dmd_read_data_valid_i
                )
            ))
    );

    assign pm_state_action = (
        pm_state_move_write_i || pm_state_dreg_write_i
        || pm_state_alu_write_i || pm_state_mac_write_i
        || pm_state_sr_write_i || pm_state_se_write_i
        || pm_state_sb_write_i || pm_state_dag_i_write_i
        || pm_state_alu_status_write_i
        || pm_state_mac_status_write_i
        || pm_state_shifter_status_write_i
    );
    assign linear_state_action = (
        linear_fetch_retire || interrupt_entry_event_o
    );
    assign pm_state_action_conflict_o = (
        !reset_i && pm_state_action && linear_state_action
    );
    // The overlap is outside the bounded owner contract.  Preserve the
    // already accepted fetched action and reject the external write bundle;
    // the composition reports the conflict instead of inventing priority.
    assign pm_state_action_enable = (
        pm_state_action && !pm_state_action_conflict_o
    );

    assign pm_state_memory_read_data_o = state_dreg_read_data_3;
    assign pm_state_dreg_read_data_1_o = state_dreg_read_data_4;
    assign pm_state_dreg_read_data_2_o = state_dreg_read_data_5;
    assign pm_state_dag_i_data_o = state_pm_dag_i_read_data;
    assign pm_state_dag_i_valid_o = state_pm_dag_i_read_valid;
    assign pm_state_dag_m_data_o = state_pm_dag_m_read_data;
    assign pm_state_dag_m_valid_o = state_pm_dag_m_read_valid;
    assign pm_state_dag_l_data_o = state_pm_dag_l_read_data;
    assign pm_state_dag_l_valid_o = state_pm_dag_l_read_valid;
    assign pm_state_af_o = state_af;
    assign pm_state_mf_o = state_mf;
    assign pm_state_mr_o = state_mr;
    assign pm_state_se_o = state_se;
    assign pm_state_sb_o = state_sb;
    assign pm_state_sr_o = state_sr;
    assign provisional_source_extension_o = (
        linear_fetch_retire
        && (
            (
                type17_action_valid
                && (type17_source_code[5:4] == 2'b11)
                && (type17_source_code[3:0] <= 4'd4)
            )
            || (
                FETCHED_TYPE3_ENABLED && type3_action_valid && type3_write
                && (type3_register_code[5:4] == 2'b11)
                && (type3_register_index <= 4'd4)
            )
        )
    );

    adsp2100_load_dreg_immediate_decode type6_decode (
        .opcode_i(opcode_q),
        .valid_o(type6_valid),
        .destination_dreg_o(type6_destination),
        .immediate_data_o(type6_data)
    );

    adsp2100_dm_write_immediate_decode type2_decode (
        .opcode_i(opcode_q),
        .valid_o(type2_action_valid),
        .immediate_o(type2_immediate),
        .dag2_o(type2_dag2),
        .i_local_o(type2_i_local_unused),
        .m_local_o(type2_m_local_unused),
        .i_address_o(type2_i_address),
        .m_address_o(type2_m_address),
        .l_address_o(type2_l_address_unused)
    );

    adsp2100_direct_dm_decode type3_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type3_class_valid),
        .action_valid_o(type3_action_valid),
        .invalid_subencoding_o(type3_invalid_subencoding),
        .write_o(type3_write),
        .address_o(type3_address),
        .register_group_o(type3_register_group_unused),
        .register_index_o(type3_register_index),
        .register_code_o(type3_register_code),
        .register_present_o(type3_register_present_unused),
        .register_writable_o(type3_register_writable_unused),
        .reserved_source_o(type3_reserved_source_unused),
        .reserved_destination_o(type3_reserved_destination_unused),
        .read_only_destination_o(type3_read_only_destination_unused)
    );

    adsp2100_compute_dm_decode type4_live_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type4_class_valid),
        .action_valid_o(type4_action_valid),
        .unsupported_subencoding_o(type4_unsupported_subencoding),
        .destination_collision_o(type4_destination_collision_unused),
        .computation_enable_o(type4_computation_enable),
        .is_mac_o(type4_is_mac_unused),
        .destination_feedback_o(
            type4_live_destination_feedback_unused
        ),
        .dag_select_o(type4_dag2),
        .write_o(type4_write),
        .amf_o(type4_amf_unused),
        .yop_o(type4_yop_unused),
        .xop_o(type4_xop_unused),
        .x_source_dreg_o(type4_x_source_dreg),
        .y_source_dreg_o(type4_y_source_dreg),
        .memory_dreg_o(type4_memory_dreg),
        .i_address_o(type4_i_address),
        .m_address_o(type4_m_address)
    );

    adsp2100_shifter_dm_decode type12_live_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type12_class_valid),
        .action_valid_o(type12_action_valid),
        .unsupported_subencoding_o(type12_unsupported_subencoding),
        .unavailable_xop_o(type12_unavailable_xop_unused),
        .destination_collision_o(type12_destination_collision_unused),
        .dag_select_o(type12_dag2),
        .write_o(type12_write),
        .sf_o(type12_sf_unused),
        .xop_o(type12_xop_unused),
        .shifter_source_dreg_o(type12_shifter_source_dreg),
        .memory_dreg_o(type12_memory_dreg),
        .i_address_o(type12_i_address),
        .m_address_o(type12_m_address)
    );

    assign type2_address_valid = (
        state_dag_i_read_valid
        && (type2_dag2 || state_mstat_valid_mask_i[1])
    );
    assign type2_next_i_valid = (
        state_dag_i_read_valid && state_dag_m_read_valid
        && state_dag_l_read_valid && type2_configuration_valid
    );

    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b1)
    ) type2_dag_arithmetic (
        .i_i(state_dag_i_read_data),
        .m_i(state_dag_m_read_data),
        .l_i(state_dag_l_read_data),
        .bit_reverse_enable_i(!type2_dag2 && state_bit_reverse_unused),
        .address_o(type2_address),
        .next_i_o(type2_next_i),
        .base_o(type2_base_unused),
        .circular_o(type2_circular_unused),
        .configuration_valid_o(type2_configuration_valid)
    );

    assign type4_address_valid = (
        state_dag_i_read_valid
        && (type4_dag2 || state_mstat_valid_mask_i[1])
    );
    assign type4_next_i_valid = (
        state_dag_i_read_valid && state_dag_m_read_valid
        && state_dag_l_read_valid && type4_configuration_valid
    );

    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b1)
    ) type4_dag_arithmetic (
        .i_i(state_dag_i_read_data),
        .m_i(state_dag_m_read_data),
        .l_i(state_dag_l_read_data),
        .bit_reverse_enable_i(!type4_dag2 && state_bit_reverse_unused),
        .address_o(type4_address),
        .next_i_o(type4_next_i),
        .base_o(type4_base_unused),
        .circular_o(type4_circular_unused),
        .configuration_valid_o(type4_configuration_valid)
    );

    assign type12_address_valid = (
        state_dag_i_read_valid
        && (type12_dag2 || state_mstat_valid_mask_i[1])
    );
    assign type12_next_i_valid = (
        state_dag_i_read_valid && state_dag_m_read_valid
        && state_dag_l_read_valid && type12_configuration_valid
    );

    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b1)
    ) type12_dag_arithmetic (
        .i_i(state_dag_i_read_data),
        .m_i(state_dag_m_read_data),
        .l_i(state_dag_l_read_data),
        .bit_reverse_enable_i(!type12_dag2 && state_bit_reverse_unused),
        .address_o(type12_address),
        .next_i_o(type12_next_i),
        .base_o(type12_base_unused),
        .circular_o(type12_circular_unused),
        .configuration_valid_o(type12_configuration_valid)
    );

    adsp2100_load_non_dreg_immediate_decode type7_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type7_class_valid),
        .action_valid_o(type7_action_valid),
        .invalid_subencoding_o(type7_invalid_subencoding),
        .register_group_o(type7_group_unused),
        .register_index_o(type7_index_unused),
        .register_code_o(type7_code),
        .immediate_data_o(type7_data),
        .register_present_o(type7_present_unused),
        .register_writable_o(type7_writable_unused),
        .data_register_destination_o(type7_dreg_unused),
        .reserved_destination_o(type7_reserved_unused),
        .read_only_destination_o(type7_read_only_unused)
    );

    adsp2100_mode_control_decode type18_decode (
        .opcode_i(opcode_q),
        .valid_o(type18_valid),
        .mode_sr_o(type18_mode_sr),
        .mode_br_o(type18_mode_br),
        .mode_ol_o(type18_mode_ol),
        .mode_as_o(type18_mode_as),
        .has_effect_o(type18_has_effect_unused),
        .has_no_change_one_alias_o(type18_has_alias_unused)
    );

    adsp2100_internal_move_decode type17_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type17_class_valid),
        .move_valid_o(type17_action_valid),
        .invalid_subencoding_o(type17_invalid_subencoding),
        .destination_group_o(type17_destination_group_unused),
        .source_group_o(type17_source_group_unused),
        .destination_index_o(type17_destination_index_unused),
        .source_index_o(type17_source_index_unused),
        .destination_code_o(type17_destination_code),
        .source_code_o(type17_source_code),
        .destination_present_o(type17_destination_present_unused),
        .destination_writable_o(type17_destination_writable_unused),
        .source_valid_o(type17_source_valid_unused)
    );

    adsp2100_modify_address_action type21_action (
        .opcode_i(opcode_q),
        .i_data_i(state_dag_i_read_data),
        .i_data_valid_i(state_dag_i_read_valid),
        .m_data_i(state_dag_m_read_data),
        .m_data_valid_i(state_dag_m_read_valid),
        .l_data_i(state_dag_l_read_data),
        .l_data_valid_i(state_dag_l_read_valid),
        .action_valid_o(type21_action_valid),
        .dag2_o(type21_dag2_unused),
        .i_address_o(type21_i_address),
        .m_address_o(type21_m_address),
        .operands_valid_o(type21_operands_valid_unused),
        .configuration_valid_o(type21_configuration_valid_unused),
        .i_write_o(type21_i_write),
        .i_write_data_o(type21_i_write_data),
        .i_write_result_valid_o(type21_i_write_result_valid)
    );

    adsp2100_stack_control_decode type26_action (
        .opcode_i(opcode_q),
        .valid_o(type26_action_valid),
        .status_operation_o(type26_status_operation),
        .count_pop_o(type26_count_pop),
        .loop_pop_o(type26_loop_pop),
        .pc_pop_o(type26_pc_pop),
        .has_effect_o(type26_has_effect_unused)
    );

    adsp2100_direct_jump_decode type10_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type10_class_valid),
        .action_valid_o(type10_action_valid),
        .unsupported_call_ce_o(type10_unsupported_call_ce),
        .call_o(type10_call),
        .address_o(type10_address),
        .condition_o(type10_condition)
    );

    adsp2100_do_until_decode type11_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type11_class_valid),
        .action_valid_o(type11_action_valid),
        .end_address_o(type11_end_address),
        .termination_o(type11_termination)
    );

    adsp2100_indirect_jump_decode type19_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type19_class_valid),
        .action_valid_o(type19_action_valid),
        .unsupported_call_ce_o(type19_unsupported_call_ce),
        .call_o(type19_call),
        .i_local_o(type19_i_local_unused),
        .i_address_o(type19_i_address),
        .condition_o(type19_condition)
    );

    adsp2100_conditional_return_decode type20_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type20_class_valid),
        .action_valid_o(type20_action_valid),
        .interrupt_return_o(type20_interrupt_return),
        .condition_o(type20_condition)
    );

    adsp2100_conditional_trap_decode type22_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type22_class_valid),
        .action_valid_o(type22_action_valid),
        .condition_o(type22_condition)
    );

    adsp2100_condition_logic type22_condition_logic (
        .condition_i(type22_condition),
        .az_i(astat_o[0]),
        .an_i(astat_o[1]),
        .av_i(astat_o[2]),
        .ac_i(astat_o[3]),
        .as_i(astat_o[4]),
        .mv_i(astat_o[6]),
        .not_counter_expired_i(state_not_counter_expired_raw),
        .condition_true_o(type22_condition_true)
    );

    adsp2100_condition_logic type20_condition_logic (
        .condition_i(type20_condition),
        .az_i(astat_o[0]),
        .an_i(astat_o[1]),
        .av_i(astat_o[2]),
        .ac_i(astat_o[3]),
        .as_i(astat_o[4]),
        .mv_i(astat_o[6]),
        .not_counter_expired_i(state_not_counter_expired_raw),
        .condition_true_o(type20_condition_true)
    );

    adsp2100_condition_logic type10_condition_logic (
        .condition_i(type10_condition),
        .az_i(astat_o[0]),
        .an_i(astat_o[1]),
        .av_i(astat_o[2]),
        .ac_i(astat_o[3]),
        .as_i(astat_o[4]),
        .mv_i(astat_o[6]),
        .not_counter_expired_i(state_not_counter_expired_raw),
        .condition_true_o(type10_condition_true)
    );

    adsp2100_condition_logic type19_condition_logic (
        .condition_i(type19_condition),
        .az_i(astat_o[0]),
        .an_i(astat_o[1]),
        .av_i(astat_o[2]),
        .ac_i(astat_o[3]),
        .as_i(astat_o[4]),
        .mv_i(astat_o[6]),
        .not_counter_expired_i(state_not_counter_expired_raw),
        .condition_true_o(type19_condition_true)
    );

    adsp2100_condition_logic loop_condition_logic (
        .condition_i(loop_termination),
        .az_i(astat_o[0]),
        .an_i(astat_o[1]),
        .av_i(astat_o[2]),
        .ac_i(astat_o[3]),
        .as_i(astat_o[4]),
        .mv_i(astat_o[6]),
        .not_counter_expired_i(state_not_counter_expired_raw),
        .condition_true_o(loop_if_predicate)
    );

    adsp2100_sequencer_flow sequencer_flow (
        .pc_i(pc_q),
        .explicit_flow_i(sequencer_explicit_flow),
        .explicit_taken_i(sequencer_explicit_taken),
        .explicit_target_i(sequencer_explicit_target),
        .loop_active_i(loop_active),
        .loop_end_i(loop_end),
        .loop_start_i(state_pc_stack_top),
        .loop_termination_true_i(loop_termination_true),
        .loop_uses_counter_i(loop_uses_counter),
        .next_pc_o(sequencer_next_pc),
        .pc_stack_push_o(sequencer_pc_stack_push),
        .pc_stack_push_value_o(sequencer_pc_stack_push_value),
        .pc_stack_pop_o(sequencer_pc_stack_pop),
        .loop_stack_pop_o(sequencer_loop_stack_pop),
        .count_stack_pop_o(sequencer_count_stack_pop_unused),
        .loop_counter_test_o(sequencer_loop_counter_test),
        .loop_back_o(sequencer_loop_back_unused),
        .loop_exit_o(sequencer_loop_exit),
        .explicit_transfer_o(sequencer_explicit_transfer_unused)
    );

    // Live decoders choose the cycle-start read ports at issue.  The action
    // producers below consume only the captured stage-1 bundle.
    adsp2100_compute_move_decode type8_live_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type8_class_valid),
        .action_valid_o(type8_action_valid),
        .unsupported_subencoding_o(type8_unsupported_subencoding),
        .unverified_amf_zero_o(type8_unverified_amf_zero_unused),
        .destination_collision_o(type8_destination_collision_unused),
        .is_mac_o(type8_is_mac_unused),
        .destination_feedback_o(type8_live_destination_feedback_unused),
        .amf_o(type8_live_amf_unused),
        .yop_o(type8_live_yop_unused), .xop_o(type8_live_xop_unused),
        .x_source_dreg_o(type8_x_source_dreg),
        .y_source_dreg_o(type8_y_source_dreg),
        .move_destination_dreg_o(type8_live_move_destination_unused),
        .move_source_dreg_o(type8_move_source_dreg)
    );

    adsp2100_conditional_compute_decode type9_live_decode (
        .opcode_i(opcode_q),
        .class_valid_o(type9_class_valid),
        .action_valid_o(type9_action_valid),
        .unsupported_subencoding_o(type9_live_unsupported_unused),
        .nop_action_o(type9_nop_action),
        .is_mac_o(type9_is_mac),
        .is_alu_o(type9_is_alu),
        .destination_feedback_o(type9_live_destination_feedback_unused),
        .amf_o(type9_live_amf_unused),
        .yop_o(type9_live_yop_unused), .xop_o(type9_live_xop_unused),
        .condition_o(type9_live_condition_unused),
        .x_source_dreg_o(type9_x_source_dreg),
        .y_source_dreg_o(type9_y_source_dreg)
    );

    adsp2100_compute_move_action type8_pipeline_action (
        .opcode_i(compute_stage1_opcode_q),
        .x_dreg_data_i(compute_stage1_x_q),
        .y_dreg_data_i(compute_stage1_y_q),
        .move_source_data_i(compute_stage1_move_q),
        .af_i(compute_stage1_af_q),
        .mf_i(compute_stage1_mf_q),
        .mr_i(compute_stage1_mr_q),
        .astat_i(compute_stage1_astat_q),
        .overflow_latch_i(compute_stage1_overflow_latch_q),
        .saturate_ar_i(compute_stage1_saturate_ar_q),
        .class_valid_o(type8_pipeline_class_unused),
        .action_valid_o(type8_pipeline_action_unused),
        .unsupported_subencoding_o(type8_pipeline_unsupported_unused),
        .unverified_amf_zero_o(type8_pipeline_amf_zero_unused),
        .destination_collision_o(type8_pipeline_collision_unused),
        .is_mac_o(type8_pipeline_is_mac_unused),
        .destination_feedback_o(type8_pipeline_destination_feedback),
        .x_source_dreg_o(type8_pipeline_x_unused),
        .y_source_dreg_o(type8_pipeline_y_unused),
        .move_destination_dreg_o(type8_pipeline_move_destination),
        .move_source_dreg_o(type8_pipeline_move_source_unused),
        .move_write_o(type8_pipeline_move_write),
        .move_data_o(type8_pipeline_move_data),
        .alu_write_o(type8_pipeline_alu_write),
        .alu_result_o(type8_pipeline_alu_result),
        .alu_az_o(type8_pipeline_alu_az),
        .alu_an_o(type8_pipeline_alu_an),
        .alu_av_o(type8_pipeline_alu_av),
        .alu_ac_o(type8_pipeline_alu_ac),
        .alu_as_write_o(type8_pipeline_alu_as_write),
        .alu_as_o(type8_pipeline_alu_as),
        .mac_write_o(type8_pipeline_mac_write),
        .mac_result_o(type8_pipeline_mac_result),
        .mac_mv_o(type8_pipeline_mac_mv)
    );

    adsp2100_conditional_compute_action type9_pipeline_action (
        .opcode_i(compute_stage1_opcode_q),
        .not_counter_expired_i(compute_stage1_not_counter_expired_q),
        .x_dreg_data_i(compute_stage1_x_q),
        .y_dreg_data_i(compute_stage1_y_q),
        .af_i(compute_stage1_af_q),
        .mf_i(compute_stage1_mf_q),
        .mr_i(compute_stage1_mr_q),
        .astat_i(compute_stage1_astat_q),
        .overflow_latch_i(compute_stage1_overflow_latch_q),
        .saturate_ar_i(compute_stage1_saturate_ar_q),
        .class_valid_o(type9_pipeline_class_unused),
        .action_valid_o(type9_pipeline_action_unused),
        .nop_action_o(type9_pipeline_nop_unused),
        .condition_true_o(type9_pipeline_condition_unused),
        .is_mac_o(type9_pipeline_is_mac_unused),
        .is_alu_o(type9_pipeline_is_alu_unused),
        .destination_feedback_o(type9_pipeline_destination_feedback),
        .x_source_dreg_o(type9_pipeline_x_unused),
        .y_source_dreg_o(type9_pipeline_y_unused),
        .x_source_data_o(type9_pipeline_x_data_unused),
        .y_source_data_o(type9_pipeline_y_data_unused),
        .alu_write_o(type9_pipeline_alu_write),
        .alu_result_o(type9_pipeline_alu_result),
        .alu_az_o(type9_pipeline_alu_az),
        .alu_an_o(type9_pipeline_alu_an),
        .alu_av_o(type9_pipeline_alu_av),
        .alu_ac_o(type9_pipeline_alu_ac),
        .alu_as_write_o(type9_pipeline_alu_as_write),
        .alu_as_o(type9_pipeline_alu_as),
        .mac_write_o(type9_pipeline_mac_write),
        .mac_result_o(type9_pipeline_mac_result),
        .mac_mv_o(type9_pipeline_mac_mv)
    );

    adsp2100_compute_dm_action type4_pipeline_action (
        .opcode_i(compute_stage1_opcode_q),
        .x_dreg_data_i(compute_stage1_x_q),
        .y_dreg_data_i(compute_stage1_y_q),
        .memory_dreg_data_i(compute_stage1_move_q),
        .af_i(compute_stage1_af_q),
        .mf_i(compute_stage1_mf_q),
        .mr_i(compute_stage1_mr_q),
        .astat_i(compute_stage1_astat_q),
        .overflow_latch_i(compute_stage1_overflow_latch_q),
        .saturate_ar_i(compute_stage1_saturate_ar_q),
        .class_valid_o(type4_pipeline_class_unused),
        .action_valid_o(type4_pipeline_action_unused),
        .unsupported_subencoding_o(type4_pipeline_unsupported_unused),
        .destination_collision_o(type4_pipeline_collision_unused),
        .computation_enable_o(
            type4_pipeline_computation_enable_unused
        ),
        .is_mac_o(type4_pipeline_is_mac_unused),
        .destination_feedback_o(type4_pipeline_destination_feedback),
        .dag_select_o(type4_pipeline_dag2_unused),
        .write_o(type4_pipeline_write),
        .x_source_dreg_o(type4_pipeline_x_unused),
        .y_source_dreg_o(type4_pipeline_y_unused),
        .memory_dreg_o(type4_pipeline_memory_dreg),
        .i_address_o(type4_pipeline_i_unused),
        .m_address_o(type4_pipeline_m_unused),
        .memory_source_data_o(type4_pipeline_memory_data_unused),
        .alu_write_o(type4_pipeline_alu_write),
        .alu_result_o(type4_pipeline_alu_result),
        .alu_az_o(type4_pipeline_alu_az),
        .alu_an_o(type4_pipeline_alu_an),
        .alu_av_o(type4_pipeline_alu_av),
        .alu_ac_o(type4_pipeline_alu_ac),
        .alu_as_write_o(type4_pipeline_alu_as_write),
        .alu_as_o(type4_pipeline_alu_as),
        .mac_write_o(type4_pipeline_mac_write),
        .mac_result_o(type4_pipeline_mac_result),
        .mac_mv_o(type4_pipeline_mac_mv)
    );

    adsp2100_shifter_dm_action type12_pipeline_action (
        .opcode_i(compute_stage1_opcode_q),
        .shifter_source_data_i(compute_stage1_x_q),
        .memory_dreg_data_i(compute_stage1_move_q),
        .sr_i(compute_stage1_sr_q),
        .se_i(compute_stage1_se_q),
        .sb_i(compute_stage1_sb_q),
        .astat_i(compute_stage1_astat_q),
        .class_valid_o(type12_pipeline_class_unused),
        .action_valid_o(type12_pipeline_action_unused),
        .unsupported_subencoding_o(type12_pipeline_unsupported_unused),
        .unavailable_xop_o(type12_pipeline_unavailable_xop_unused),
        .destination_collision_o(type12_pipeline_collision_unused),
        .dag_select_o(type12_pipeline_dag2_unused),
        .write_o(type12_pipeline_write),
        .shifter_source_dreg_o(type12_pipeline_source_unused),
        .memory_dreg_o(type12_pipeline_memory_dreg),
        .i_address_o(type12_pipeline_i_unused),
        .m_address_o(type12_pipeline_m_unused),
        .memory_source_data_o(type12_pipeline_memory_data_unused),
        .sr_write_o(type12_pipeline_sr_write),
        .sr_result_o(type12_pipeline_sr_result),
        .se_write_o(type12_pipeline_se_write),
        .se_result_o(type12_pipeline_se_result),
        .sb_write_o(type12_pipeline_sb_write),
        .sb_result_o(type12_pipeline_sb_result),
        .ss_write_o(type12_pipeline_ss_write),
        .ss_result_o(type12_pipeline_ss_result)
    );

    assign compute_stage1_capture = (
        pm_request_accepted_i
        && (
            type8_action_valid || type9_action_valid
            || (FETCHED_TYPE4_ENABLED && type4_action_valid)
            || (FETCHED_TYPE12_ENABLED && type12_action_valid)
        )
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            compute_stage1_valid_q <= 1'b0;
            compute_stage1_opcode_q <= 24'h000000;
            compute_stage1_not_counter_expired_q <= 1'b0;
            compute_stage1_x_q <= 16'h0000;
            compute_stage1_y_q <= 16'h0000;
            compute_stage1_move_q <= 16'h0000;
            compute_stage1_af_q <= 16'h0000;
            compute_stage1_mf_q <= 16'h0000;
            compute_stage1_mr_q <= 40'h0000000000;
            compute_stage1_astat_q <= 8'h00;
            compute_stage1_sr_q <= 32'h00000000;
            compute_stage1_se_q <= 8'h00;
            compute_stage1_sb_q <= 5'h00;
            compute_stage1_overflow_latch_q <= 1'b0;
            compute_stage1_saturate_ar_q <= 1'b0;
            type8_destination_feedback <= 1'b0;
            type8_move_destination_dreg <= 4'h0;
            type8_move_write <= 1'b0;
            type8_move_data <= 16'h0000;
            type8_alu_write <= 1'b0;
            type8_alu_result <= 16'h0000;
            type8_alu_az <= 1'b0;
            type8_alu_an <= 1'b0;
            type8_alu_av <= 1'b0;
            type8_alu_ac <= 1'b0;
            type8_alu_as_write <= 1'b0;
            type8_alu_as <= 1'b0;
            type8_mac_write <= 1'b0;
            type8_mac_result <= 40'h0000000000;
            type8_mac_mv <= 1'b0;
            type9_condition_true <= 1'b0;
            type9_destination_feedback <= 1'b0;
            type9_alu_write <= 1'b0;
            type9_alu_result <= 16'h0000;
            type9_alu_az <= 1'b0;
            type9_alu_an <= 1'b0;
            type9_alu_av <= 1'b0;
            type9_alu_ac <= 1'b0;
            type9_alu_as_write <= 1'b0;
            type9_alu_as <= 1'b0;
            type9_mac_write <= 1'b0;
            type9_mac_result <= 40'h0000000000;
            type9_mac_mv <= 1'b0;
            type4_destination_feedback <= 1'b0;
            type4_retired_write <= 1'b0;
            type4_retired_memory_dreg <= 4'h0;
            type4_alu_write <= 1'b0;
            type4_alu_result <= 16'h0000;
            type4_alu_az <= 1'b0;
            type4_alu_an <= 1'b0;
            type4_alu_av <= 1'b0;
            type4_alu_ac <= 1'b0;
            type4_alu_as_write <= 1'b0;
            type4_alu_as <= 1'b0;
            type4_mac_write <= 1'b0;
            type4_mac_result <= 40'h0000000000;
            type4_mac_mv <= 1'b0;
            type12_retired_write <= 1'b0;
            type12_retired_memory_dreg <= 4'h0;
            type12_sr_write <= 1'b0;
            type12_sr_result <= 32'h00000000;
            type12_se_write <= 1'b0;
            type12_se_result <= 8'h00;
            type12_sb_write <= 1'b0;
            type12_sb_result <= 5'h00;
            type12_ss_write <= 1'b0;
            type12_ss_result <= 1'b0;
        end else if (retire_event_o || instruction_setup_accepted_o) begin
            compute_stage1_valid_q <= 1'b0;
            type8_move_write <= 1'b0;
            type8_alu_write <= 1'b0;
            type8_mac_write <= 1'b0;
            type9_condition_true <= 1'b0;
            type9_alu_write <= 1'b0;
            type9_mac_write <= 1'b0;
            type4_alu_write <= 1'b0;
            type4_mac_write <= 1'b0;
            type12_sr_write <= 1'b0;
            type12_se_write <= 1'b0;
            type12_sb_write <= 1'b0;
            type12_ss_write <= 1'b0;
        end else begin
            if (compute_stage1_valid_q) begin
                compute_stage1_valid_q <= 1'b0;
                type8_destination_feedback
                    <= type8_pipeline_destination_feedback;
                type8_move_destination_dreg
                    <= type8_pipeline_move_destination;
                type8_move_write <= type8_pipeline_move_write;
                type8_move_data <= type8_pipeline_move_data;
                type8_alu_write <= type8_pipeline_alu_write;
                type8_alu_result <= type8_pipeline_alu_result;
                type8_alu_az <= type8_pipeline_alu_az;
                type8_alu_an <= type8_pipeline_alu_an;
                type8_alu_av <= type8_pipeline_alu_av;
                type8_alu_ac <= type8_pipeline_alu_ac;
                type8_alu_as_write <= type8_pipeline_alu_as_write;
                type8_alu_as <= type8_pipeline_alu_as;
                type8_mac_write <= type8_pipeline_mac_write;
                type8_mac_result <= type8_pipeline_mac_result;
                type8_mac_mv <= type8_pipeline_mac_mv;
                type9_condition_true <= type9_pipeline_condition_unused;
                type9_destination_feedback
                    <= type9_pipeline_destination_feedback;
                type9_alu_write <= type9_pipeline_alu_write;
                type9_alu_result <= type9_pipeline_alu_result;
                type9_alu_az <= type9_pipeline_alu_az;
                type9_alu_an <= type9_pipeline_alu_an;
                type9_alu_av <= type9_pipeline_alu_av;
                type9_alu_ac <= type9_pipeline_alu_ac;
                type9_alu_as_write <= type9_pipeline_alu_as_write;
                type9_alu_as <= type9_pipeline_alu_as;
                type9_mac_write <= type9_pipeline_mac_write;
                type9_mac_result <= type9_pipeline_mac_result;
                type9_mac_mv <= type9_pipeline_mac_mv;
                type4_destination_feedback
                    <= type4_pipeline_destination_feedback;
                type4_retired_write <= type4_pipeline_write;
                type4_retired_memory_dreg
                    <= type4_pipeline_memory_dreg;
                type4_alu_write <= type4_pipeline_alu_write;
                type4_alu_result <= type4_pipeline_alu_result;
                type4_alu_az <= type4_pipeline_alu_az;
                type4_alu_an <= type4_pipeline_alu_an;
                type4_alu_av <= type4_pipeline_alu_av;
                type4_alu_ac <= type4_pipeline_alu_ac;
                type4_alu_as_write <= type4_pipeline_alu_as_write;
                type4_alu_as <= type4_pipeline_alu_as;
                type4_mac_write <= type4_pipeline_mac_write;
                type4_mac_result <= type4_pipeline_mac_result;
                type4_mac_mv <= type4_pipeline_mac_mv;
                type12_retired_write <= type12_pipeline_write;
                type12_retired_memory_dreg
                    <= type12_pipeline_memory_dreg;
                type12_sr_write <= type12_pipeline_sr_write;
                type12_sr_result <= type12_pipeline_sr_result;
                type12_se_write <= type12_pipeline_se_write;
                type12_se_result <= type12_pipeline_se_result;
                type12_sb_write <= type12_pipeline_sb_write;
                type12_sb_result <= type12_pipeline_sb_result;
                type12_ss_write <= type12_pipeline_ss_write;
                type12_ss_result <= type12_pipeline_ss_result;
            end
            if (compute_stage1_capture) begin
                compute_stage1_valid_q <= 1'b1;
                compute_stage1_opcode_q <= opcode_q;
                compute_stage1_not_counter_expired_q
                    <= state_not_counter_expired_raw;
                compute_stage1_x_q <= state_move_dreg_read_data;
                compute_stage1_y_q <= state_dreg_read_data;
                compute_stage1_move_q <= state_dreg_read_data_2;
                compute_stage1_af_q <= state_af;
                compute_stage1_mf_q <= state_mf;
                compute_stage1_mr_q <= state_mr;
                compute_stage1_astat_q <= astat_o;
                compute_stage1_sr_q <= state_sr;
                compute_stage1_se_q <= state_se;
                compute_stage1_sb_q <= state_sb;
                compute_stage1_overflow_latch_q <= state_overflow_latch;
                compute_stage1_saturate_ar_q <= state_saturate_ar;
                type8_move_write <= 1'b0;
                type8_alu_write <= 1'b0;
                type8_mac_write <= 1'b0;
                type9_condition_true <= 1'b0;
                type9_alu_write <= 1'b0;
                type9_mac_write <= 1'b0;
                type4_alu_write <= 1'b0;
                type4_mac_write <= 1'b0;
                type12_sr_write <= 1'b0;
                type12_se_write <= 1'b0;
                type12_sb_write <= 1'b0;
                type12_ss_write <= 1'b0;
            end
        end
    end

    adsp2100_shift_move_action type14_action (
        .opcode_i(opcode_q),
        .shifter_source_data_i(state_move_dreg_read_data),
        .move_source_data_i(state_dreg_read_data),
        .sr_i(state_sr),
        .se_i(state_se),
        .sb_i(state_sb),
        .astat_i(astat_o),
        .class_valid_o(type14_class_valid),
        .action_valid_o(type14_action_valid),
        .unsupported_subencoding_o(type14_unsupported_subencoding),
        .unverified_unused_x_o(type14_unverified_unused_x_unused),
        .unavailable_xop_o(type14_unavailable_xop_unused),
        .destination_collision_o(type14_destination_collision_unused),
        .shifter_source_dreg_o(type14_shifter_source_dreg),
        .move_destination_dreg_o(type14_move_destination_dreg),
        .move_source_dreg_o(type14_move_source_dreg),
        .move_write_o(type14_move_write),
        .move_data_o(type14_move_data),
        .sr_write_o(type14_sr_write),
        .sr_result_o(type14_sr_result),
        .se_write_o(type14_se_write),
        .se_result_o(type14_se_result),
        .sb_write_o(type14_sb_write),
        .sb_result_o(type14_sb_result),
        .ss_write_o(type14_ss_write),
        .ss_result_o(type14_ss_result)
    );

    adsp2100_mr_saturation_action type25_action (
        .opcode_i(opcode_q),
        .mr_i(state_mr),
        .mv_i(astat_o[6]),
        .action_valid_o(type25_action_valid),
        .condition_mv_o(type25_condition_mv_unused),
        .mr_write_o(type25_mr_write),
        .mr_result_o(type25_mr_result)
    );

    adsp2100_divide_quotient_action type23_action (
        .opcode_i(opcode_q),
        .divisor_i(state_move_dreg_read_data),
        .partial_remainder_i(state_af),
        .ay0_i(state_dreg_read_data),
        .old_aq_i(astat_o[5]),
        .class_valid_o(type23_class_valid),
        .action_valid_o(type23_action_valid),
        .xop_o(type23_xop_unused),
        .divisor_source_dreg_o(type23_divisor_source_dreg),
        .add_divisor_o(type23_add_divisor_unused),
        .alu_result_o(type23_alu_result_unused),
        .new_aq_o(type23_new_aq_unused),
        .quotient_bit_o(type23_quotient_bit_unused),
        .af_write_o(type23_af_write),
        .af_result_o(type23_af_result),
        .ay0_write_o(type23_ay0_write),
        .ay0_result_o(type23_ay0_result),
        .aq_write_o(type23_aq_write),
        .aq_result_o(type23_aq_result)
    );

    adsp2100_divide_sign_action type24_action (
        .opcode_i(opcode_q),
        .divisor_sign_i(state_move_dreg_read_data[15]),
        .upper_dreg_i(state_dreg_read_data_2),
        .partial_remainder_i(state_af),
        .ay0_i(state_dreg_read_data),
        .class_valid_o(type24_class_valid),
        .action_valid_o(type24_action_valid),
        .unsupported_yop_o(type24_unsupported_yop),
        .yop_o(type24_yop_unused),
        .xop_o(type24_xop_unused),
        .divisor_source_dreg_o(type24_divisor_source_dreg),
        .upper_source_dreg_o(type24_upper_source_dreg),
        .upper_source_feedback_o(type24_upper_source_feedback_unused),
        .upper_value_o(type24_upper_value_unused),
        .quotient_sign_o(type24_quotient_sign_unused),
        .af_write_o(type24_af_write),
        .af_result_o(type24_af_result),
        .ay0_write_o(type24_ay0_write),
        .ay0_result_o(type24_ay0_result),
        .aq_write_o(type24_aq_write),
        .aq_result_o(type24_aq_result)
    );

    adsp2100_immediate_shift_action type15_action (
        .opcode_i(opcode_q),
        .source_data_i(state_move_dreg_read_data),
        .sr_i(state_sr),
        .class_valid_o(type15_class_valid),
        .action_valid_o(type15_action_valid),
        .unsupported_subencoding_o(type15_unsupported_subencoding),
        .source_dreg_o(type15_source_dreg),
        .sr_write_o(type15_sr_write),
        .sr_result_o(type15_sr_result)
    );

    adsp2100_conditional_shift_action type16_action (
        .opcode_i(opcode_q),
        .not_counter_expired_i(state_not_counter_expired_raw),
        .source_data_i(state_move_dreg_read_data),
        .sr_i(state_sr),
        .se_i(state_se),
        .sb_i(state_sb),
        .astat_i(astat_o),
        .class_valid_o(type16_class_valid),
        .action_valid_o(type16_action_valid),
        .unsupported_subencoding_o(type16_unsupported_subencoding),
        .condition_true_o(type16_condition_true),
        .source_dreg_o(type16_source_dreg),
        .sr_write_o(type16_sr_write),
        .sr_result_o(type16_sr_result),
        .se_write_o(type16_se_write),
        .se_result_o(type16_se_result),
        .sb_write_o(type16_sb_write),
        .sb_result_o(type16_sb_result),
        .ss_write_o(type16_ss_write),
        .ss_result_o(type16_ss_result)
    );

    adsp2100_interrupt_control interrupt_control (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .phase_i(phase_i),
        .phase_advance_i(interrupt_phase_advance),
        .irq_n_i(irq_n_i),
        .icntl_i(icntl_o),
        .icntl_valid_i(state_icntl_valid),
        .imask_i(imask_o),
        .imask_valid_i(1'b1),
        .service_allowed_i(interrupt_service_allowed),
        .sample_event_o(interrupt_sample_event_unused),
        .sampled_requests_o(interrupt_sampled_requests_unused),
        .enabled_requests_o(interrupt_enabled_requests),
        .recognition_event_o(interrupt_recognition_event_o),
        .recognized_level_o(interrupt_recognized_level),
        .vector_address_o(interrupt_vector_o),
        .edge_pending_o(interrupt_edge_pending),
        .sample_history_valid_o(interrupt_sample_history_valid_unused),
        .configuration_invalid_o(interrupt_configuration_invalid_o),
        .reset_baseline_provisional_o(
            interrupt_reset_baseline_provisional_o
        )
    );

    adsp2100_architectural_state #(
        // Vector issue cannot coincide with ordinary retirement, and the
        // PM action bundle is rejected above on any vector-entry overlap.
        .INTERRUPT_ACTIONS_PREVALIDATED(1'b1)
    ) state (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .move_write_i(
            state_write
            || (pm_state_action_enable && pm_state_move_write_i)
        ),
        .move_data_valid_i(
            FETCHED_TYPE3_ENABLED && type3_action_valid && !type3_write
                ? dmd_read_data_valid_i
                : (
                    type17_action_valid
                        ? type17_source_data_valid_i : 1'b1
                )
        ),
        .move_code_i(
            pm_state_action_enable && pm_state_move_write_i
                ? pm_state_move_code_i : state_write_code
        ),
        .move_data_i(
            pm_state_action_enable && pm_state_move_write_i
                ? pm_state_move_data_i : state_write_data
        ),
        .read_code_i(state_read_code),
        .read_data_o(state_read_data),
        .move_dreg_read_data_o(state_move_dreg_read_data),
        .probe_code_i(probe_code_i),
        .probe_data_o(probe_data_o),
        .dreg_read_address_i(
            (type23_action_valid || type24_action_valid)
                ? DREG_AY0
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? type4_y_source_dreg
                        : (
                            type8_action_valid
                                ? type8_y_source_dreg
                                : (
                                    type14_action_valid
                                        ? type14_move_source_dreg
                                        : type9_y_source_dreg
                                )
                        )
                )
        ),
        .dreg_read_data_o(state_dreg_read_data),
        .dreg_read_address_2_i(
            FETCHED_TYPE4_ENABLED && type4_action_valid
                ? type4_memory_dreg
                : (
                    FETCHED_TYPE12_ENABLED && type12_action_valid
                        ? type12_memory_dreg
                        : (type8_action_valid
                            ? type8_move_source_dreg
                            : type24_upper_source_dreg)
                )
        ),
        .dreg_read_data_2_o(state_dreg_read_data_2),
        // PM-data operands have independent combinational ports so their
        // issue-time selectors cannot propagate through inactive ordinary
        // instruction action producers. All six reads still observe the
        // same cycle-start selected-bank state.
        .dreg_read_address_3_i(pm_state_memory_read_address_i),
        .dreg_read_data_3_o(state_dreg_read_data_3),
        .dreg_read_address_4_i(pm_state_dreg_read_address_1_i),
        .dreg_read_data_4_o(state_dreg_read_data_4),
        .dreg_read_address_5_i(pm_state_dreg_read_address_2_i),
        .dreg_read_data_5_o(state_dreg_read_data_5),
        .dreg_write_enable_1_i(
            (pm_state_action_enable && pm_state_dreg_write_i)
            || (state_action_retire
                && (
                    type8_move_write || type14_move_write
                    || (
                        FETCHED_TYPE4_ENABLED && type4_action_valid
                        && !type4_retired_write
                        && dmd_read_data_valid_i
                    )
                    || (
                        FETCHED_TYPE12_ENABLED && type12_action_valid
                        && !type12_retired_write
                        && dmd_read_data_valid_i
                    )
                ))
        ),
        .dreg_write_address_1_i(
            pm_state_action_enable && pm_state_dreg_write_i
                ? pm_state_dreg_write_address_i
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? type4_retired_memory_dreg
                        : (
                            FETCHED_TYPE12_ENABLED && type12_action_valid
                                ? type12_retired_memory_dreg
                                : (type8_move_write
                                    ? type8_move_destination_dreg
                                    : type14_move_destination_dreg)
                        )
                )
        ),
        .dreg_write_data_1_i(
            pm_state_action_enable && pm_state_dreg_write_i
                ? pm_state_dreg_write_data_i
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? dmd_read_data_i
                        : (
                            FETCHED_TYPE12_ENABLED && type12_action_valid
                                ? dmd_read_data_i
                                : (type8_move_write
                                    ? type8_move_data : type14_move_data)
                        )
                )
        ),
        .dreg_write_enable_2_i(
            state_action_retire && (type23_ay0_write || type24_ay0_write)
        ),
        .dreg_write_address_2_i(DREG_AY0),
        .dreg_write_data_2_i(
            type24_ay0_write ? type24_ay0_result : type23_ay0_result
        ),
        .alu_write_enable_i(
            (pm_state_action_enable && pm_state_alu_write_i)
            || (
                state_action_retire
                && (
                    type8_alu_write || type9_alu_write
                    || type23_af_write || type24_af_write
                    || (
                        FETCHED_TYPE4_ENABLED && type4_action_valid
                        && type4_alu_write
                    )
                )
            )
        ),
        .alu_destination_feedback_i(
            pm_state_action_enable && pm_state_alu_write_i
                ? pm_state_alu_destination_feedback_i
                : ((type23_af_write || type24_af_write)
                ? 1'b1
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? type4_destination_feedback
                        : (type8_alu_write
                            ? type8_destination_feedback
                            : type9_destination_feedback)
                ))
        ),
        .alu_result_i(
            pm_state_action_enable && pm_state_alu_write_i
                ? pm_state_alu_result_i
                : (type24_af_write
                ? type24_af_result
                : (
                    type23_af_write
                        ? type23_af_result
                        : (
                            FETCHED_TYPE4_ENABLED && type4_action_valid
                                ? type4_alu_result
                                : (type8_alu_write
                                    ? type8_alu_result : type9_alu_result)
                        )
                ))
        ),
        .mac_write_enable_i(
            (pm_state_action_enable && pm_state_mac_write_i)
            || (
                state_action_retire
                && (
                    type8_mac_write || type9_mac_write || type25_mr_write
                    || (
                        FETCHED_TYPE4_ENABLED && type4_action_valid
                        && type4_mac_write
                    )
                )
            )
        ),
        .mac_destination_feedback_i(
            pm_state_action_enable && pm_state_mac_write_i
                ? pm_state_mac_destination_feedback_i
                : (type25_mr_write
                ? 1'b0
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? type4_destination_feedback
                        : (type8_mac_write
                            ? type8_destination_feedback
                            : type9_destination_feedback)
                ))
        ),
        .mac_result_i(
            pm_state_action_enable && pm_state_mac_write_i
                ? pm_state_mac_result_i
                : (type25_mr_write
                ? type25_mr_result
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? type4_mac_result
                        : (type8_mac_write
                            ? type8_mac_result : type9_mac_result)
                )
                )
        ),
        .shifter_sr_write_enable_i(
            (pm_state_action_enable && pm_state_sr_write_i)
            || (
                state_action_retire
                && (
                    type14_sr_write || type15_sr_write || type16_sr_write
                    || (
                        FETCHED_TYPE12_ENABLED && type12_action_valid
                        && type12_sr_write
                    )
                )
            )
        ),
        .shifter_sr_result_i(
            pm_state_action_enable && pm_state_sr_write_i
                ? pm_state_sr_result_i
                : (
                    FETCHED_TYPE12_ENABLED && type12_action_valid
                        ? type12_sr_result
                        : (type14_sr_write
                            ? type14_sr_result
                            : (type15_sr_write
                                ? type15_sr_result : type16_sr_result)
                        )
                )
        ),
        .shifter_se_write_enable_i(
            (pm_state_action_enable && pm_state_se_write_i)
            || (state_action_retire
                && (
                    type14_se_write || type16_se_write
                    || (
                        FETCHED_TYPE12_ENABLED && type12_action_valid
                        && type12_se_write
                    )
                ))
        ),
        .shifter_se_result_i(
            pm_state_action_enable && pm_state_se_write_i
                ? pm_state_se_result_i
                : (
                    FETCHED_TYPE12_ENABLED && type12_action_valid
                        ? type12_se_result
                        : (type14_se_write
                            ? type14_se_result : type16_se_result)
                )
        ),
        .shifter_sb_write_enable_i(
            (pm_state_action_enable && pm_state_sb_write_i)
            || (state_action_retire
                && (
                    type14_sb_write || type16_sb_write
                    || (
                        FETCHED_TYPE12_ENABLED && type12_action_valid
                        && type12_sb_write
                    )
                ))
        ),
        .shifter_sb_result_i(
            pm_state_action_enable && pm_state_sb_write_i
                ? pm_state_sb_result_i
                : (
                    FETCHED_TYPE12_ENABLED && type12_action_valid
                        ? type12_sb_result
                        : (type14_sb_write
                            ? type14_sb_result : type16_sb_result)
                )
        ),
        .dag_i_write_enable_i(
            (pm_state_action_enable && pm_state_dag_i_write_i)
            || (
                state_action_retire
                && (
                    (FETCHED_TYPE2_ENABLED && type2_action_valid)
                    || (FETCHED_TYPE4_ENABLED && type4_action_valid)
                    || (FETCHED_TYPE12_ENABLED && type12_action_valid)
                    || type21_i_write
                )
            )
        ),
        .dag_i_write_address_i(
            pm_state_action_enable && pm_state_dag_i_write_i
                ? pm_state_dag_i_write_address_i
                : (
                    FETCHED_TYPE2_ENABLED && type2_action_valid
                        ? type2_i_address
                        : (FETCHED_TYPE4_ENABLED && type4_action_valid
                            ? type4_i_address
                            : (FETCHED_TYPE12_ENABLED
                                && type12_action_valid
                                ? type12_i_address : type21_i_address))
                )
        ),
        .dag_i_write_data_i(
            pm_state_action_enable && pm_state_dag_i_write_i
                ? pm_state_dag_i_write_data_i
                : (
                    FETCHED_TYPE2_ENABLED && type2_action_valid
                        ? type2_next_i
                        : (FETCHED_TYPE4_ENABLED && type4_action_valid
                            ? type4_next_i
                            : (FETCHED_TYPE12_ENABLED
                                && type12_action_valid
                                ? type12_next_i : type21_i_write_data))
                )
        ),
        .dag_i_write_result_valid_i(
            pm_state_action_enable && pm_state_dag_i_write_i
                ? pm_state_dag_i_write_valid_i
                : (
                    FETCHED_TYPE2_ENABLED && type2_action_valid
                        ? type2_next_i_valid
                        : (FETCHED_TYPE4_ENABLED && type4_action_valid
                            ? type4_next_i_valid
                            : (FETCHED_TYPE12_ENABLED
                                && type12_action_valid
                                ? type12_next_i_valid
                                : type21_i_write_result_valid))
                )
        ),
        .dag_execution_read_i(
            (FETCHED_TYPE2_ENABLED && type2_action_valid)
            || (FETCHED_TYPE4_ENABLED && type4_action_valid)
            || (FETCHED_TYPE12_ENABLED && type12_action_valid)
            || type21_action_valid || type19_action_valid
        ),
        .dag_i_l_read_address_i(
            FETCHED_TYPE2_ENABLED && type2_action_valid
                ? type2_i_address
                : (
                    FETCHED_TYPE4_ENABLED && type4_action_valid
                        ? type4_i_address
                        : (
                            FETCHED_TYPE12_ENABLED && type12_action_valid
                                ? type12_i_address
                                : (type19_action_valid
                                    ? type19_i_address : type21_i_address)
                        )
                )
        ),
        .dag_m_read_address_i(
            FETCHED_TYPE2_ENABLED && type2_action_valid
                ? type2_m_address
                : (FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_m_address
                    : (FETCHED_TYPE12_ENABLED && type12_action_valid
                        ? type12_m_address : type21_m_address))
        ),
        .dag_i_read_data_o(state_dag_i_read_data),
        .dag_i_read_valid_o(state_dag_i_read_valid),
        .dag_m_read_data_o(state_dag_m_read_data),
        .dag_m_read_valid_o(state_dag_m_read_valid),
        .dag_l_read_data_o(state_dag_l_read_data),
        .dag_l_read_valid_o(state_dag_l_read_valid),
        .dag_i_l_read_address_2_i(
            pm_state_operand_read_i ? pm_state_dag_i_address_i : 3'b000
        ),
        .dag_m_read_address_2_i(
            pm_state_operand_read_i ? pm_state_dag_m_address_i : 3'b000
        ),
        .dag_i_read_data_2_o(state_pm_dag_i_read_data),
        .dag_i_read_valid_2_o(state_pm_dag_i_read_valid),
        .dag_m_read_data_2_o(state_pm_dag_m_read_data),
        .dag_m_read_valid_2_o(state_pm_dag_m_read_valid),
        .dag_l_read_data_2_o(state_pm_dag_l_read_data),
        .dag_l_read_valid_2_o(state_pm_dag_l_read_valid),
        .mode_sr_i(
            state_action_retire && type18_valid ? type18_mode_sr : 2'b00
        ),
        .mode_br_i(
            state_action_retire && type18_valid ? type18_mode_br : 2'b00
        ),
        .mode_ol_i(
            state_action_retire && type18_valid ? type18_mode_ol : 2'b00
        ),
        .mode_as_i(
            state_action_retire && type18_valid ? type18_mode_as : 2'b00
        ),
        .alu_status_write_enable_i(
            (pm_state_action_enable && pm_state_alu_status_write_i)
            || (state_action_retire
                && (
                    type8_alu_write || type9_alu_write
                    || (
                        FETCHED_TYPE4_ENABLED && type4_action_valid
                        && type4_alu_write
                    )
                ))
        ),
        .alu_az_i(
            pm_state_action_enable && pm_state_alu_status_write_i
                ? pm_state_alu_az_i
                : (FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_alu_az
                    : (type8_alu_write ? type8_alu_az : type9_alu_az))
        ),
        .alu_an_i(
            pm_state_action_enable && pm_state_alu_status_write_i
                ? pm_state_alu_an_i
                : (FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_alu_an
                    : (type8_alu_write ? type8_alu_an : type9_alu_an))
        ),
        .alu_av_i(
            pm_state_action_enable && pm_state_alu_status_write_i
                ? pm_state_alu_av_i
                : (FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_alu_av
                    : (type8_alu_write ? type8_alu_av : type9_alu_av))
        ),
        .alu_ac_i(
            pm_state_action_enable && pm_state_alu_status_write_i
                ? pm_state_alu_ac_i
                : (FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_alu_ac
                    : (type8_alu_write ? type8_alu_ac : type9_alu_ac))
        ),
        .alu_as_write_enable_i(
            pm_state_action_enable && pm_state_alu_status_write_i
                ? pm_state_alu_as_write_i
                : (FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_alu_as_write
                    : (type8_alu_write
                        ? type8_alu_as_write : type9_alu_as_write))
        ),
        .alu_as_i(
            pm_state_action_enable && pm_state_alu_status_write_i
                ? pm_state_alu_as_i
                : (FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_alu_as
                    : (type8_alu_write ? type8_alu_as : type9_alu_as))
        ),
        .divide_status_write_enable_i(
            state_action_retire && (type23_aq_write || type24_aq_write)
        ),
        .divide_aq_i(type24_aq_write ? type24_aq_result : type23_aq_result),
        .mac_status_write_enable_i(
            (pm_state_action_enable && pm_state_mac_status_write_i)
            || (state_action_retire
                && (
                    type8_mac_write || type9_mac_write
                    || (
                        FETCHED_TYPE4_ENABLED && type4_action_valid
                        && type4_mac_write
                    )
                ))
        ),
        .mac_mv_i(
            pm_state_action_enable && pm_state_mac_status_write_i
                ? pm_state_mac_mv_i
                : (FETCHED_TYPE4_ENABLED && type4_action_valid
                    ? type4_mac_mv
                    : (type8_mac_write ? type8_mac_mv : type9_mac_mv))
        ),
        .shifter_status_write_enable_i(
            (pm_state_action_enable && pm_state_shifter_status_write_i)
            || (state_action_retire
                && (
                    type14_ss_write || type16_ss_write
                    || (
                        FETCHED_TYPE12_ENABLED && type12_action_valid
                        && type12_ss_write
                    )
                ))
        ),
        .shifter_ss_i(
            pm_state_action_enable && pm_state_shifter_status_write_i
                ? pm_state_shifter_ss_i
                : (
                    FETCHED_TYPE12_ENABLED && type12_action_valid
                        ? type12_ss_result
                        : (type14_ss_write
                            ? type14_ss_result : type16_ss_result)
                )
        ),
        .stack_status_operation_i(
            state_action_retire && type20_taken && type20_interrupt_return
                ? 2'b11
                : (state_action_retire && type26_action_valid
                    ? type26_status_operation : 2'b00)
        ),
        .stack_counter_ce_test_i(
            state_action_retire
            && (
                (
                    type10_action_valid && !type10_call
                    && (type10_condition == 4'he)
                )
                || (
                    type19_action_valid && !type19_call
                    && (type19_condition == 4'he)
                )
                || sequencer_loop_counter_test
            )
        ),
        .stack_count_pop_i(
            state_action_retire && type26_action_valid && type26_count_pop
        ),
        .stack_loop_push_i(state_action_retire && type11_action_valid),
        .stack_loop_push_data_i({type11_termination, type11_end_address}),
        .stack_loop_pop_i(
            state_action_retire
            && (
                (type26_action_valid && type26_loop_pop)
                || sequencer_loop_stack_pop
            )
        ),
        .stack_pc_push_i(
            linear_fetch_retire
            && (
                sequencer_pc_stack_push || type11_action_valid
            )
        ),
        .stack_pc_push_data_i(sequencer_pc_stack_push_value),
        .stack_pc_pop_i(
            linear_fetch_retire
            && (
                (type26_action_valid && type26_pc_pop)
                || sequencer_pc_stack_pop
            )
        ),
        .status_stack_push_validity_i({
            state_astat_valid_mask_i,
            state_mstat_valid_mask_i,
            state_imask_valid_i
        }),
        .interrupt_entry_i(interrupt_entry_event_o),
        .interrupt_level_i(interrupt_level_q),
        .interrupt_pc_push_data_i(pc_q),
        .invalid_move_write_o(state_invalid_setup),
        .internal_conflict_o(state_internal_conflict),
        .count_stack_push_o(state_count_push_unused),
        .count_stack_push_data_o(state_count_push_data_unused),
        .count_stack_depth_o(count_stack_depth_o),
        .count_stack_overflow_o(count_stack_overflow_o),
        .pc_stack_top_o(state_pc_stack_top),
        .pc_stack_top_valid_o(state_pc_stack_top_valid),
        .status_stack_top_o(state_status_stack_top_unused),
        .status_stack_top_valid_o(state_status_stack_top_valid),
        .status_restore_event_o(status_restore_event_o),
        .status_restore_validity_o({
            status_restore_astat_valid_mask_o,
            status_restore_mstat_valid_mask_o,
            status_restore_imask_valid_o
        }),
        .loop_stack_top_o(state_loop_stack_top),
        .loop_stack_top_valid_o(state_loop_stack_top_valid),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .icntl_valid_o(state_icntl_valid),
        .imask_o(imask_o),
        .cntr_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .not_counter_expired_o(state_not_counter_expired_unused),
        .px_o(px_o),
        .sstat_o(sstat_o),
        .alternate_bank_o(alternate_bank_o),
        .bit_reverse_o(state_bit_reverse_unused),
        .overflow_latch_o(state_overflow_latch),
        .saturate_ar_o(state_saturate_ar),
        .af_o(state_af),
        .mf_o(state_mf),
        .mr_o(state_mr),
        .se_o(state_se),
        .sb_o(state_sb),
        .sr_o(state_sr)
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pc_q <= 14'h0004;
            opcode_q <= 24'h000000;
            instruction_valid_q <= 1'b0;
            pending_q <= 1'b0;
            interrupt_vectoring_q <= 1'b0;
            interrupt_level_q <= 2'b00;
        end else begin
            if (pm_request_accepted_i) begin
                pending_q <= 1'b1;
            end
            if (retire_event_o) begin
                pc_q <= fetch_address_o;
                pending_q <= 1'b0;
                if (interrupt_recognition_event_o) begin
                    opcode_q <= 24'h000000;
                    instruction_valid_q <= 1'b0;
                    interrupt_vectoring_q <= 1'b1;
                    interrupt_level_q <= interrupt_recognized_level;
                end else if (pm_instruction_retire) begin
                    opcode_q <= pm_instruction_next_opcode_i;
                    instruction_valid_q
                        <= pm_instruction_next_opcode_valid_i;
                end else begin
                    opcode_q <= pmd_read_data_i;
                    instruction_valid_q <= pmd_read_data_valid_i;
                end
            end
            if (interrupt_vector_fetch_event_o) begin
                pc_q <= {12'h000, interrupt_level_q};
                opcode_q <= pmd_read_data_i;
                instruction_valid_q <= pmd_read_data_valid_i;
                pending_q <= 1'b0;
                interrupt_vectoring_q <= 1'b0;
                interrupt_level_q <= 2'b00;
            end
            if (instruction_setup_accepted_o) begin
                pc_q <= instruction_setup_pc_i;
                opcode_q <= instruction_setup_opcode_i;
                instruction_valid_q <= 1'b1;
                pending_q <= 1'b0;
                interrupt_vectoring_q <= 1'b0;
                interrupt_level_q <= 2'b00;
            end
        end
    end

    assign unused_observation = ^{
        type7_group_unused, type7_index_unused, type7_present_unused,
        type2_i_local_unused, type2_m_local_unused,
        type2_l_address_unused, type2_base_unused, type2_circular_unused,
        type3_register_group_unused, type3_register_present_unused,
        type3_register_writable_unused, type3_reserved_source_unused,
        type3_reserved_destination_unused,
        type3_read_only_destination_unused,
        type4_destination_collision_unused, type4_is_mac_unused,
        type4_live_destination_feedback_unused, type4_amf_unused,
        type4_yop_unused, type4_xop_unused, type4_base_unused,
        type4_circular_unused,
        type12_unavailable_xop_unused,
        type12_destination_collision_unused, type12_sf_unused,
        type12_xop_unused, type12_base_unused, type12_circular_unused,
        type7_writable_unused, type7_dreg_unused, type7_reserved_unused,
        type7_read_only_unused, type18_has_effect_unused,
        type18_has_alias_unused, type17_destination_group_unused,
        type17_source_group_unused, type17_destination_index_unused,
        type17_source_index_unused, type17_destination_present_unused,
        type17_destination_writable_unused, type17_source_valid_unused,
        type8_unverified_amf_zero_unused, type8_destination_collision_unused,
        type8_is_mac_unused, type8_live_destination_feedback_unused,
        type8_live_amf_unused, type8_live_yop_unused,
        type8_live_xop_unused, type8_live_move_destination_unused,
        type21_dag2_unused, type21_operands_valid_unused,
        type21_configuration_valid_unused,
        type26_has_effect_unused,
        type10_class_valid, type10_unsupported_call_ce,
        type11_class_valid,
        type19_class_valid, type19_unsupported_call_ce,
        type19_i_local_unused,
        type20_class_valid, type22_class_valid, state_status_stack_top_unused,
        type9_class_valid, type9_nop_action, type9_condition_true,
        type9_is_mac, type9_is_alu, type9_live_unsupported_unused,
        type9_live_destination_feedback_unused, type9_live_amf_unused,
        type9_live_yop_unused, type9_live_xop_unused,
        type9_live_condition_unused, type16_condition_true,
        type8_pipeline_class_unused, type8_pipeline_action_unused,
        type8_pipeline_unsupported_unused,
        type8_pipeline_amf_zero_unused,
        type8_pipeline_collision_unused, type8_pipeline_is_mac_unused,
        type8_pipeline_x_unused, type8_pipeline_y_unused,
        type8_pipeline_move_source_unused,
        type9_pipeline_class_unused, type9_pipeline_action_unused,
        type9_pipeline_nop_unused, type9_pipeline_is_mac_unused,
        type9_pipeline_is_alu_unused, type9_pipeline_x_unused,
        type9_pipeline_y_unused, type9_pipeline_x_data_unused,
        type9_pipeline_y_data_unused,
        type4_pipeline_class_unused, type4_pipeline_action_unused,
        type4_pipeline_unsupported_unused, type4_pipeline_collision_unused,
        type4_pipeline_computation_enable_unused,
        type4_pipeline_is_mac_unused, type4_pipeline_dag2_unused,
        type4_pipeline_x_unused, type4_pipeline_y_unused,
        type4_pipeline_i_unused, type4_pipeline_m_unused,
        type4_pipeline_memory_data_unused,
        type12_pipeline_class_unused, type12_pipeline_action_unused,
        type12_pipeline_unsupported_unused,
        type12_pipeline_unavailable_xop_unused,
        type12_pipeline_collision_unused, type12_pipeline_dag2_unused,
        type12_pipeline_source_unused, type12_pipeline_i_unused,
        type12_pipeline_m_unused, type12_pipeline_memory_data_unused,
        type23_class_valid, type23_xop_unused,
        type23_add_divisor_unused, type23_alu_result_unused,
        type23_new_aq_unused, type23_quotient_bit_unused,
        type24_yop_unused, type24_xop_unused,
        type24_upper_source_feedback_unused, type24_upper_value_unused,
        type24_quotient_sign_unused,
        type25_condition_mv_unused,
        type14_unverified_unused_x_unused, type14_unavailable_xop_unused,
        type14_destination_collision_unused,
        state_invalid_setup,
        state_count_push_unused, state_count_push_data_unused,
        state_bit_reverse_unused, state_not_counter_expired_unused,
        sequencer_count_stack_pop_unused, sequencer_loop_back_unused,
        sequencer_loop_exit, sequencer_explicit_transfer_unused,
        interrupt_sample_event_unused,
        interrupt_sampled_requests_unused,
        interrupt_sample_history_valid_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(linear_fetch_retire && !pending_q));
        assert (!(instruction_issue_o && !fetch_request_presented_o));
        if (instruction_issue_o) begin
            assert (issue_boundary_o);
        end
        if (fetched_dm_request_presented_o) begin
            assert (fetched_dm_request_candidate_o);
            assert (
                (FETCHED_TYPE2_ENABLED && type2_action_valid)
                || (FETCHED_TYPE3_ENABLED && type3_action_valid)
                || (FETCHED_TYPE4_ENABLED && type4_action_valid)
                || (FETCHED_TYPE12_ENABLED && type12_action_valid)
            );
            assert (fetch_request_presented_o && !interrupt_vector_request);
        end
        if (!fetched_dm_request_presented_o) begin
            assert (!fetched_dm_request_address_valid_o);
            assert (fetched_dm_request_address_o == 14'h0000);
            assert (!fetched_dm_request_write_o);
            assert (fetched_dm_request_write_data_o == 16'h0000);
            assert (!fetched_dm_request_write_data_valid_o);
        end
        if (
            fetched_dm_request_presented_o
            && FETCHED_TYPE3_ENABLED && type3_action_valid
        ) begin
            assert (fetched_dm_request_write_o == type3_write);
            assert (fetched_dm_request_address_o == type3_address);
        end
        if (
            fetched_dm_request_presented_o
            && FETCHED_TYPE4_ENABLED && type4_action_valid
        ) begin
            assert (fetched_dm_request_write_o == type4_write);
            if (type4_address_valid) begin
                assert (fetched_dm_request_address_o == type4_address);
            end
            if (type4_write && type17_source_data_valid_i) begin
                assert (
                    fetched_dm_request_write_data_o
                    == state_dreg_read_data_2
                );
            end
        end
        if (
            fetched_dm_request_presented_o
            && FETCHED_TYPE12_ENABLED && type12_action_valid
        ) begin
            assert (fetched_dm_request_write_o == type12_write);
            if (type12_address_valid) begin
                assert (fetched_dm_request_address_o == type12_address);
            end
            if (type12_write && type17_source_data_valid_i) begin
                assert (
                    fetched_dm_request_write_data_o
                    == state_dreg_read_data_2
                );
            end
        end
        if (interrupt_recognition_event_o) begin
            assert (retire_event_o);
            assert (!trap_event_o);
        end
        if (interrupt_entry_event_o || interrupt_vector_issue_event_o) begin
            assert (
                interrupt_entry_event_o && interrupt_vector_issue_event_o
            );
            assert (instruction_issue_o && interrupt_vectoring_q);
            assert (fetch_address_o == {12'h000, interrupt_level_q});
            assert (!linear_fetch_retire);
            assert (!pm_state_action_enable);
        end
        if (interrupt_vector_fetch_event_o) begin
            assert (pending_q && interrupt_vectoring_q);
            assert (!retire_event_o);
        end
        if (interrupt_adjacent_control_conflict_o) begin
            assert (retire_event_o);
            assert (!interrupt_recognition_event_o);
        end
        if (instruction_issue_inhibit_i || bus_relinquished_i) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
        if (retire_event_o) begin
            assert (phase_i == PHASE_STATE_7 && phase_advance_i);
        end
        if (pm_instruction_retire) begin
            assert (pm_instruction_active_i);
            assert (pm_instruction_sequential_allowed_o);
            assert (fetch_address_o == pc_q + 14'h0001);
        end
        if (pm_instruction_flow_blocked_o) begin
            assert (!fetch_request_presented_o);
        end
        if (provisional_source_extension_o) begin
            assert (retire_event_o);
        end
        if (reserved_subencoding_o || unsupported_instruction_o) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
        if (type10_invalid_condition_state) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
        if (type19_invalid_condition_state || type19_invalid_target_state) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
        if (type20_invalid_condition_state || type20_invalid_return_context) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
        if (type22_invalid_condition_state) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
        if (
            invalid_loop_context || unsupported_do_at_loop_end
            || unsupported_nested_same_end || automatic_manual_conflict
        ) begin
            assert (!fetch_request_presented_o);
            assert (!instruction_issue_o);
        end
        if (fetch_request_presented_o && type20_action_valid) begin
            if (type20_taken) begin
                assert (fetch_address_o == state_pc_stack_top);
                assert (state_pc_stack_top_valid);
                if (type20_interrupt_return) begin
                    assert (state_status_stack_top_valid);
                end
            end else begin
                assert (fetch_address_o == pc_q + 14'h0001);
            end
        end
        if (fetch_request_presented_o && type10_action_valid) begin
            if (type10_taken) begin
                assert (fetch_address_o == type10_address);
            end else begin
                assert (fetch_address_o == pc_q + 14'h0001);
            end
        end
        if (fetch_request_presented_o && type19_action_valid) begin
            if (type19_taken) begin
                assert (fetch_address_o == state_dag_i_read_data);
                assert (state_dag_i_read_valid);
            end else begin
                assert (fetch_address_o == pc_q + 14'h0001);
            end
        end
        if (fetch_request_presented_o && type11_action_valid) begin
            assert (fetch_address_o == pc_q + 14'h0001);
            assert (!unsupported_do_at_loop_end);
            assert (!unsupported_nested_same_end);
        end
        if (fetch_request_presented_o && type22_action_valid) begin
            if (type22_taken) begin
                assert (fetch_address_o == pc_q + 14'h0001);
                assert (!automatic_loop_flow);
            end
        end
        if (trap_event_o) begin
            assert (retire_event_o && type22_taken);
        end
        if (
            fetch_request_presented_o && automatic_loop_flow
            && !sequencer_explicit_taken
        ) begin
            if (loop_termination_true) begin
                assert (fetch_address_o == pc_q + 14'h0001);
                assert (sequencer_loop_exit);
            end else begin
                assert (fetch_address_o == state_pc_stack_top);
                assert (sequencer_loop_back_unused);
            end
        end
        if (type10_action_valid && type10_call) begin
            assert (type10_condition != 4'he);
        end
        if (type19_action_valid && type19_call) begin
            assert (type19_condition != 4'he);
        end
    end
`endif
endmodule

`default_nettype wire
