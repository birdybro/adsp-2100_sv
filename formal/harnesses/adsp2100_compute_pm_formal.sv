`default_nettype none

module adsp2100_compute_pm_formal (
    input logic clk_i,
    input logic reset_i,
    input logic execute_i,
    input logic [23:0] opcode_i,
    input logic [23:0] pm_read_data_i,
    input logic pm_read_data_valid_i,
    input logic pm_cycle_complete_i,
    input logic [13:0] next_fetch_address_i,
    input logic next_fetch_address_valid_i,
    input logic cache_next_instruction_valid_i,
    input logic force_instruction_fetch_i,
    input logic astat_setup_write_i,
    input logic [7:0] astat_setup_data_i,
    input logic mstat_setup_write_i,
    input logic [3:0] mstat_setup_data_i,
    input logic dreg_setup_write_i,
    input logic [3:0] dreg_setup_code_i,
    input logic [15:0] dreg_setup_data_i,
    input logic af_setup_write_i,
    input logic [15:0] af_setup_data_i,
    input logic mf_setup_write_i,
    input logic [15:0] mf_setup_data_i,
    input logic dag_setup_write_i,
    input logic [1:0] dag_setup_kind_i,
    input logic [2:0] dag_setup_address_i,
    input logic [13:0] dag_setup_data_i,
    input logic px_setup_write_i,
    input logic [7:0] px_setup_data_i,
    input logic [3:0] probe_dreg_code_i,
    input logic [2:0] probe_dag_address_i
);
    logic class_valid_o;
    logic action_valid_o;
    logic unsupported_subencoding_o;
    logic destination_collision_o;
    logic computation_enable_o;
    logic is_mac_o;
    logic destination_feedback_o;
    logic write_direction_o;
    logic [4:0] amf_o;
    logic [1:0] yop_o;
    logic [2:0] xop_o;
    logic [3:0] x_source_dreg_o;
    logic [3:0] y_source_dreg_o;
    logic [3:0] memory_dreg_o;
    logic [2:0] i_address_o;
    logic [2:0] m_address_o;
    logic boundary_valid_o;
    logic accepted_o;
    logic data_action_complete_o;
    logic instruction_complete_o;
    logic transaction_active_o;
    logic held_transaction_o;
    logic busy_o;
    logic invalid_opcode_o;
    logic integration_conflict_o;
    logic internal_conflict_o;
    logic cache_instruction_selected_o;
    logic recovery_required_o;
    logic recovery_fetch_o;
    logic event_boundary_o;
    logic pm_select_o;
    logic pm_data_access_o;
    logic pm_read_o;
    logic pm_write_o;
    logic [13:0] pm_address_o;
    logic pm_address_valid_o;
    logic [23:0] pm_write_data_o;
    logic pm_write_data_valid_o;
    logic [23:0] fetched_instruction_o;
    logic fetched_instruction_valid_o;
    logic dm_access_o;
    logic compute_result_known_o;
    logic dag_configuration_valid_o;
    logic i_write_o;
    logic i_write_known_o;
    logic dreg_write_o;
    logic dreg_write_known_o;
    logic px_write_o;
    logic px_write_known_o;
    logic alu_write_o;
    logic mac_write_o;
    logic alu_status_write_o;
    logic mac_status_write_o;
    logic [15:0] alu_result_o;
    logic [39:0] mac_result_o;
    logic [15:0] probe_dreg_data_o;
    logic probe_dreg_valid_o;
    logic [13:0] probe_i_data_o;
    logic probe_i_valid_o;
    logic [13:0] probe_m_data_o;
    logic probe_m_valid_o;
    logic [13:0] probe_l_data_o;
    logic probe_l_valid_o;
    logic [7:0] px_o;
    logic px_valid_o;
    logic [15:0] af_o;
    logic af_valid_o;
    logic [15:0] mf_o;
    logic mf_valid_o;
    logic [39:0] mr_o;
    logic mr_valid_o;
    logic [7:0] astat_o;
    logic [7:0] astat_valid_mask_o;
    logic [3:0] mstat_o;
    logic alternate_bank_o;

    logic expected_class;
    logic expected_compute;
    logic expected_collision;
    logic expected_action;
    logic expected_issue;
    logic [3:0] setup_count;
    logic past_valid;
    logic unused_observation;

    assign expected_class = ((opcode_i & 24'hf00000) == 24'h500000);
    assign expected_compute = expected_class && opcode_i[17:13] != 5'h00;
    assign expected_collision = (
        expected_compute && !opcode_i[19] && !opcode_i[18]
        && (
            (opcode_i[17] && opcode_i[7:4] == 4'ha)
            || (
                !opcode_i[17] && opcode_i[7:4] >= 4'hb
                && opcode_i[7:4] <= 4'hd
            )
        )
    );
    assign expected_action = expected_class && !expected_collision;
    assign setup_count = (
        {3'h0, astat_setup_write_i} + {3'h0, mstat_setup_write_i}
        + {3'h0, dreg_setup_write_i} + {3'h0, af_setup_write_i}
        + {3'h0, mf_setup_write_i} + {3'h0, dag_setup_write_i}
        + {3'h0, px_setup_write_i}
    );
    assign expected_issue = (
        !reset_i && !dut.recovery_q && !dut.data_pending_q
        && execute_i && expected_action && setup_count == 4'h0
    );
    assign unused_observation = ^{
        x_source_dreg_o, y_source_dreg_o, memory_dreg_o,
        i_address_o, m_address_o, integration_conflict_o,
        internal_conflict_o,
        compute_result_known_o, dag_configuration_valid_o,
        i_write_known_o, dreg_write_known_o, px_write_known_o,
        alu_result_o, mac_result_o, fetched_instruction_o,
        fetched_instruction_valid_o, probe_dreg_data_o,
        probe_dreg_valid_o, probe_i_data_o, probe_i_valid_o,
        probe_m_data_o, probe_m_valid_o, probe_l_data_o,
        probe_l_valid_o, px_o, px_valid_o, af_o, af_valid_o,
        mf_o, mf_valid_o, mr_o, mr_valid_o, astat_o,
        astat_valid_mask_o, mstat_o, alternate_bank_o
    };

    adsp2100_compute_pm_slice dut (.*);

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid_o == expected_class);
        assert (computation_enable_o == expected_compute);
        assert (destination_collision_o == expected_collision);
        assert (action_valid_o == expected_action);
        assert (unsupported_subencoding_o
            == (expected_class && !expected_action));
        assert (is_mac_o == (expected_compute && !opcode_i[17]));
        assert (destination_feedback_o
            == (expected_class ? opcode_i[18] : 1'b0));
        assert (write_direction_o
            == (expected_class ? opcode_i[19] : 1'b0));
        assert (amf_o == (expected_class ? opcode_i[17:13] : 5'h00));
        assert (yop_o == (expected_class ? opcode_i[12:11] : 2'b00));
        assert (xop_o == (expected_class ? opcode_i[10:8] : 3'b000));
        assert (boundary_valid_o == expected_issue);
        assert (accepted_o == expected_issue);
        assert (data_action_complete_o
            == (transaction_active_o && pm_data_access_o
                && pm_cycle_complete_i));
        assert (invalid_opcode_o == (
            !reset_i && !dut.recovery_q && !dut.data_pending_q
            && execute_i && !expected_action
        ));
        assert (pm_select_o == (pm_read_o || pm_write_o));
        assert (!(pm_read_o && pm_write_o));
        assert (!dm_access_o);
        assert (event_boundary_o == instruction_complete_o);
        assert (px_write_o == dreg_write_o);
        assert (alu_write_o == alu_status_write_o);
        assert (mac_write_o == mac_status_write_o);
        assert (!(alu_write_o && mac_write_o));
        assert (cache_instruction_selected_o == (
            accepted_o && cache_next_instruction_valid_i
            && !force_instruction_fetch_i
        ));
        assert (recovery_required_o == (
            accepted_o && (
                force_instruction_fetch_i
                || !cache_next_instruction_valid_i
            )
        ));
        assert (unused_observation == unused_observation);
        if (recovery_fetch_o) begin
            assert (pm_select_o && pm_read_o && !pm_data_access_o);
            assert (!data_action_complete_o);
            assert (!i_write_o && !dreg_write_o && !px_write_o);
            assert (!alu_write_o && !mac_write_o);
        end
        if (held_transaction_o && !pm_cycle_complete_i) begin
            assert (busy_o && !instruction_complete_o);
        end
        if (reset_i) begin
            assert (!transaction_active_o && !accepted_o);
            assert (!instruction_complete_o && !pm_select_o);
        end
    end

    always_ff @(posedge clk_i) begin
        past_valid <= 1'b1;
        if (
            past_valid && !reset_i && !$past(reset_i)
            && $past(held_transaction_o)
            && !$past(pm_cycle_complete_i)
        ) begin
            assert (held_transaction_o);
            assert (pm_address_o == $past(pm_address_o));
            assert (pm_address_valid_o == $past(pm_address_valid_o));
            assert (pm_write_o == $past(pm_write_o));
            assert (pm_write_data_o == $past(pm_write_data_o));
            assert (pm_write_data_valid_o
                == $past(pm_write_data_valid_o));
        end
        cover (accepted_o && recovery_required_o);
        cover (recovery_fetch_o && instruction_complete_o);
        cover (data_action_complete_o && alu_write_o);
        cover (data_action_complete_o && mac_write_o);
    end
endmodule

`default_nettype wire
