`default_nettype none

module adsp2100_dm_write_immediate_slice_formal (
    input logic clk,
    input logic reset,
    input logic execute,
    input logic [23:0] opcode,
    input logic dm_ack,
    input logic mstat_setup,
    input logic [3:0] mstat_setup_data,
    input logic dag_setup,
    input logic [1:0] dag_setup_kind,
    input logic [2:0] dag_setup_address,
    input logic [13:0] dag_setup_data,
    input logic [2:0] probe_address
);
    logic [13:0] probe_i_data;
    logic probe_i_valid;
    logic [13:0] probe_m_data;
    logic probe_m_valid;
    logic [13:0] probe_l_data;
    logic probe_l_valid;
    logic [3:0] mstat;
    logic class_valid;
    logic action_valid;
    logic [15:0] immediate;
    logic dag2;
    logic [1:0] i_local;
    logic [1:0] m_local;
    logic [2:0] i_address;
    logic [2:0] m_address;
    logic [2:0] l_address;
    logic boundary_valid;
    logic accepted;
    logic instruction_complete;
    logic transaction_active;
    logic stalled;
    logic busy;
    logic invalid_opcode;
    logic integration_conflict;
    logic internal_conflict;
    logic dm_select;
    logic dm_read;
    logic dm_write;
    logic [13:0] dm_address;
    logic dm_address_valid;
    logic [15:0] dm_write_data;
    logic dm_write_data_valid;
    logic dag_configuration_valid;
    logic i_write;
    logic i_write_known;
    logic pm_data_access;
    logic dm_access;
    logic expected_class;
    logic [1:0] setup_count;
    logic past_valid;
    logic unused_observation;

    assign expected_class = opcode[23:21] == 3'b101;
    assign setup_count = (
        {1'b0, mstat_setup} + {1'b0, dag_setup}
    );
    assign unused_observation = ^{
        dag_configuration_valid, i_write_known, probe_i_data,
        probe_m_data, probe_l_data
    };

    adsp2100_dm_write_immediate_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .dm_ack_i(dm_ack),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dag_setup_write_i(dag_setup),
        .dag_setup_kind_i(dag_setup_kind),
        .dag_setup_address_i(dag_setup_address),
        .dag_setup_data_i(dag_setup_data),
        .probe_dag_address_i(probe_address),
        .probe_i_data_o(probe_i_data),
        .probe_i_valid_o(probe_i_valid),
        .probe_m_data_o(probe_m_data),
        .probe_m_valid_o(probe_m_valid),
        .probe_l_data_o(probe_l_data),
        .probe_l_valid_o(probe_l_valid),
        .mstat_o(mstat),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .immediate_o(immediate),
        .dag2_o(dag2),
        .i_local_o(i_local),
        .m_local_o(m_local),
        .i_address_o(i_address),
        .m_address_o(m_address),
        .l_address_o(l_address),
        .boundary_valid_o(boundary_valid),
        .accepted_o(accepted),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .stalled_o(stalled),
        .busy_o(busy),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .dm_select_o(dm_select),
        .dm_read_o(dm_read),
        .dm_write_o(dm_write),
        .dm_address_o(dm_address),
        .dm_address_valid_o(dm_address_valid),
        .dm_write_data_o(dm_write_data),
        .dm_write_data_valid_o(dm_write_data_valid),
        .dag_configuration_valid_o(dag_configuration_valid),
        .i_write_o(i_write),
        .i_write_known_o(i_write_known),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_class);
        assert (immediate == (expected_class ? opcode[19:4] : 16'h0000));
        assert (dag2 == (expected_class ? opcode[20] : 1'b0));
        assert (i_local == (expected_class ? opcode[3:2] : 2'b00));
        assert (m_local == (expected_class ? opcode[1:0] : 2'b00));
        assert (
            i_address
            == (expected_class ? {opcode[20], opcode[3:2]} : 3'b000)
        );
        assert (
            m_address
            == (expected_class ? {opcode[20], opcode[1:0]} : 3'b000)
        );
        assert (l_address == i_address);
        assert (
            boundary_valid
            == (!reset && !dut.pending_q && execute && expected_class
                && setup_count == 2'b00)
        );
        assert (accepted == boundary_valid);
        assert (
            invalid_opcode
            == (!reset && !dut.pending_q && execute && !expected_class)
        );
        assert (
            integration_conflict
            == (!reset && (
                (dut.pending_q && (execute || setup_count != 2'b00))
                || (!dut.pending_q && (
                    (execute && setup_count != 2'b00)
                    || setup_count > 2'b01
                ))
            ))
        );
        assert (instruction_complete == (transaction_active && dm_ack));
        assert (stalled == (transaction_active && !dm_ack));
        assert (busy == stalled);
        assert (dm_select == transaction_active);
        assert (!dm_read);
        assert (dm_write == transaction_active);
        assert (dm_access == dm_select);
        assert (!pm_data_access);
        assert (i_write == instruction_complete);
        assert (
            internal_conflict
            == (dut.dag_invalid_setup_kind || dut.dag_write_conflict)
        );
        assert (unused_observation == unused_observation);
        if (reset) begin
            assert (!transaction_active && !accepted && !instruction_complete);
        end
        if (stalled) begin
            assert (!i_write && !instruction_complete);
        end
        if (!dm_address_valid) begin
            assert (dm_address == 14'h0000);
        end
        if (!dm_write_data_valid) begin
            assert (dm_write_data == 16'h0000);
        end
        if (transaction_active) begin
            assert (dm_write_data_valid);
        end
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && $past(stalled) && stalled) begin
            assert (dm_select && dm_write && !dm_read);
            assert (dm_address_valid == $past(dm_address_valid));
            assert (dm_address == $past(dm_address));
            assert (dm_write_data_valid == $past(dm_write_data_valid));
            assert (dm_write_data == $past(dm_write_data));
            assert (mstat == $past(mstat));
            if (probe_address == $past(probe_address)) begin
                assert (probe_i_valid == $past(probe_i_valid));
                assert (probe_m_valid == $past(probe_m_valid));
                assert (probe_l_valid == $past(probe_l_valid));
                if (probe_i_valid) assert (probe_i_data == $past(probe_i_data));
                if (probe_m_valid) assert (probe_m_data == $past(probe_m_data));
                if (probe_l_valid) assert (probe_l_data == $past(probe_l_data));
            end
        end
        cover (past_valid && $past(stalled) && instruction_complete);
    end
endmodule

`default_nettype wire
