`default_nettype none

module adsp2100_dm_write_immediate_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic        dm_ack_i,

    input  logic        mstat_setup_write_i,
    input  logic [3:0]  mstat_setup_data_i,
    input  logic        dag_setup_write_i,
    input  logic [1:0]  dag_setup_kind_i,
    input  logic [2:0]  dag_setup_address_i,
    input  logic [13:0] dag_setup_data_i,

    input  logic [2:0]  probe_dag_address_i,
    output logic [13:0] probe_i_data_o,
    output logic        probe_i_valid_o,
    output logic [13:0] probe_m_data_o,
    output logic        probe_m_valid_o,
    output logic [13:0] probe_l_data_o,
    output logic        probe_l_valid_o,
    output logic [3:0]  mstat_o,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic [15:0] immediate_o,
    output logic        dag2_o,
    output logic [1:0]  i_local_o,
    output logic [1:0]  m_local_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,
    output logic [2:0]  l_address_o,

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
    output logic        dag_configuration_valid_o,
    output logic        i_write_o,
    output logic        i_write_known_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic decode_valid;
    logic issue;
    logic [1:0] setup_count;
    logic mstat_setup_forward;
    logic dag_setup_forward;

    logic [3:0] mstat_q;
    logic [13:0] selected_i;
    logic selected_i_valid;
    logic [13:0] selected_m;
    logic selected_m_valid;
    logic [13:0] selected_l;
    logic selected_l_valid;
    logic [13:0] live_address;
    logic [13:0] live_next_i;
    logic [13:0] dag_base_unused;
    logic dag_circular_unused;
    logic live_dag_configuration_valid;
    logic live_address_valid;
    logic live_next_i_valid;
    logic live_bit_reverse;

    logic pending_q;
    logic [13:0] pending_address_q;
    logic pending_address_valid_q;
    logic [15:0] pending_write_data_q;
    logic [2:0] pending_i_address_q;
    logic [13:0] pending_next_i_q;
    logic pending_next_i_valid_q;

    logic [13:0] active_address;
    logic active_address_valid;
    logic [15:0] active_write_data;
    logic [2:0] active_i_address;
    logic [13:0] active_next_i;
    logic active_next_i_valid;
    logic dag_invalid_setup_kind;
    logic dag_write_conflict;

    adsp2100_dm_write_immediate_decode decode (
        .opcode_i(opcode_i),
        .valid_o(decode_valid),
        .immediate_o(immediate_o),
        .dag2_o(dag2_o),
        .i_local_o(i_local_o),
        .m_local_o(m_local_o),
        .i_address_o(i_address_o),
        .m_address_o(m_address_o),
        .l_address_o(l_address_o)
    );

    assign class_valid_o = decode_valid;
    assign action_valid_o = decode_valid;
    assign setup_count = (
        {1'b0, mstat_setup_write_i}
        + {1'b0, dag_setup_write_i}
    );
    assign integration_conflict_o = (
        !reset_i
        && (
            (pending_q && (execute_i || setup_count != 2'b00))
            || (!pending_q && (
                (execute_i && setup_count != 2'b00)
                || setup_count > 2'b01
            ))
        )
    );
    assign invalid_opcode_o = (
        !reset_i
        && !pending_q
        && execute_i
        && !decode_valid
    );
    assign issue = (
        !reset_i
        && !pending_q
        && execute_i
        && decode_valid
        && setup_count == 2'b00
    );
    assign boundary_valid_o = issue;
    assign accepted_o = issue;

    assign mstat_setup_forward = (
        !reset_i
        && !pending_q
        && !execute_i
        && mstat_setup_write_i
        && !dag_setup_write_i
    );
    assign dag_setup_forward = (
        !reset_i
        && !pending_q
        && !execute_i
        && dag_setup_write_i
        && !mstat_setup_write_i
    );

    assign live_bit_reverse = !dag2_o && mstat_q[1];
    assign live_address_valid = selected_i_valid;
    assign live_next_i_valid = (
        selected_i_valid
        && selected_m_valid
        && selected_l_valid
        && live_dag_configuration_valid
    );

    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b1)
    ) arithmetic (
        .i_i(selected_i),
        .m_i(selected_m),
        .l_i(selected_l),
        .bit_reverse_enable_i(live_bit_reverse),
        .address_o(live_address),
        .next_i_o(live_next_i),
        .base_o(dag_base_unused),
        .circular_o(dag_circular_unused),
        .configuration_valid_o(live_dag_configuration_valid)
    );

    always_comb begin
        if (pending_q) begin
            active_address = pending_address_q;
            active_address_valid = pending_address_valid_q;
            active_write_data = pending_write_data_q;
            active_i_address = pending_i_address_q;
            active_next_i = pending_next_i_q;
            active_next_i_valid = pending_next_i_valid_q;
        end else begin
            active_address = live_address;
            active_address_valid = live_address_valid;
            active_write_data = immediate_o;
            active_i_address = i_address_o;
            active_next_i = live_next_i;
            active_next_i_valid = live_next_i_valid;
        end
    end

    assign transaction_active_o = !reset_i && (pending_q || issue);
    assign instruction_complete_o = transaction_active_o && dm_ack_i;
    assign stalled_o = transaction_active_o && !dm_ack_i;
    assign busy_o = stalled_o;
    assign dm_select_o = transaction_active_o;
    assign dm_read_o = 1'b0;
    assign dm_write_o = transaction_active_o;
    assign dm_address_valid_o = (
        transaction_active_o && active_address_valid
    );
    assign dm_address_o = (
        dm_address_valid_o ? active_address : 14'h0000
    );
    assign dm_write_data_valid_o = transaction_active_o;
    assign dm_write_data_o = (
        dm_write_data_valid_o ? active_write_data : 16'h0000
    );
    assign dag_configuration_valid_o = (
        transaction_active_o && active_next_i_valid
    );
    assign i_write_o = instruction_complete_o;
    assign i_write_known_o = (
        instruction_complete_o && active_next_i_valid
    );
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = dm_select_o;
    assign mstat_o = mstat_q;
    assign internal_conflict_o = (
        dag_invalid_setup_kind || dag_write_conflict
    );

    adsp2100_dag_register_file registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .i_l_read_address_i(i_address_o),
        .m_read_address_i(m_address_o),
        .i_read_data_o(selected_i),
        .i_read_valid_o(selected_i_valid),
        .m_read_data_o(selected_m),
        .m_read_valid_o(selected_m_valid),
        .l_read_data_o(selected_l),
        .l_read_valid_o(selected_l_valid),
        .i_l_read_address_2_i(3'b000),
        .m_read_address_2_i(3'b000),
        /* verilator lint_off PINCONNECTEMPTY */
        .i_read_data_2_o(),
        .i_read_valid_2_o(),
        .m_read_data_2_o(),
        .m_read_valid_2_o(),
        .l_read_data_2_o(),
        .l_read_valid_2_o(),
        /* verilator lint_on PINCONNECTEMPTY */
        .probe_address_i(probe_dag_address_i),
        .probe_i_data_o(probe_i_data_o),
        .probe_i_valid_o(probe_i_valid_o),
        .probe_m_data_o(probe_m_data_o),
        .probe_m_valid_o(probe_m_valid_o),
        .probe_l_data_o(probe_l_data_o),
        .probe_l_valid_o(probe_l_valid_o),
        .setup_write_i(dag_setup_forward),
        .setup_data_valid_i(1'b1),
        .setup_kind_i(dag_setup_kind_i),
        .setup_address_i(dag_setup_address_i),
        .setup_data_i(dag_setup_data_i),
        .i_write_enable_i(instruction_complete_o),
        .i_write_address_i(active_i_address),
        .i_write_data_i(active_next_i),
        .i_write_result_valid_i(active_next_i_valid),
        .i_write_enable_2_i(1'b0),
        .i_write_address_2_i(3'b000),
        .i_write_data_2_i(14'h0000),
        .i_write_result_valid_2_i(1'b0),
        .invalid_setup_kind_o(dag_invalid_setup_kind),
        .write_conflict_o(dag_write_conflict)
    );

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            mstat_q <= 4'h0;
            pending_q <= 1'b0;
        end else begin
            if (mstat_setup_forward) begin
                mstat_q <= mstat_setup_data_i;
            end
            if (pending_q) begin
                if (dm_ack_i) begin
                    pending_q <= 1'b0;
                end
            end else if (issue && !dm_ack_i) begin
                pending_q <= 1'b1;
                pending_address_q <= live_address;
                pending_address_valid_q <= live_address_valid;
                pending_write_data_q <= immediate_o;
                pending_i_address_q <= i_address_o;
                pending_next_i_q <= live_next_i;
                pending_next_i_valid_q <= live_next_i_valid;
            end
        end
    end

    always_comb begin
        assert (class_valid_o == action_valid_o);
        assert (!dm_read_o);
        assert (dm_select_o == dm_write_o);
        assert (dm_access_o == dm_select_o);
        assert (!pm_data_access_o);
        assert (boundary_valid_o == accepted_o);
        assert (instruction_complete_o == (transaction_active_o && dm_ack_i));
        assert (stalled_o == (transaction_active_o && !dm_ack_i));
        assert (busy_o == stalled_o);
        assert (i_write_o == instruction_complete_o);
        if (!dm_address_valid_o) begin
            assert (dm_address_o == 14'h0000);
        end
        if (!dm_write_data_valid_o) begin
            assert (dm_write_data_o == 16'h0000);
        end
        if (stalled_o) begin
            assert (!instruction_complete_o && !i_write_o);
        end
        if (reset_i) begin
            assert (!transaction_active_o && !accepted_o);
        end
        if (pending_q && !reset_i) begin
            assert (!boundary_valid_o);
            if (pending_address_valid_q) begin
                assert (dm_address_o == pending_address_q);
            end
            assert (dm_write_data_o == pending_write_data_q);
        end
    end
endmodule

`default_nettype wire
