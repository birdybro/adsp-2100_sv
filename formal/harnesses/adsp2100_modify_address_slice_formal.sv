`default_nettype none

module adsp2100_modify_address_slice_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        setup_write,
    input logic [1:0]  setup_kind,
    input logic [2:0]  setup_address,
    input logic [13:0] setup_data,
    input logic [2:0]  probe_address
);
    logic [13:0] probe_i_data;
    logic        probe_i_valid;
    logic [13:0] probe_m_data;
    logic        probe_m_valid;
    logic [13:0] probe_l_data;
    logic        probe_l_valid;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        invalid_setup_kind;
    logic        internal_conflict;
    logic        operands_valid;
    logic        configuration_valid;
    logic        writeback_valid;
    logic        selected_dag2;
    logic [1:0]  selected_i_local;
    logic [1:0]  selected_m_local;
    logic [2:0]  selected_i_address;
    logic [2:0]  selected_m_address;
    logic [13:0] selected_old_i;
    logic [13:0] selected_m;
    logic [13:0] selected_l;
    logic [13:0] next_i;
    logic        pm_data_access;
    logic        dm_access;
    logic        type_21_valid;
    logic        past_valid;

    assign type_21_valid = (
        (opcode & 24'hffffe0) == 24'h090000
    );

    adsp2100_modify_address_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .setup_write_i(setup_write),
        .setup_kind_i(setup_kind),
        .setup_address_i(setup_address),
        .setup_data_i(setup_data),
        .probe_address_i(probe_address),
        .probe_i_data_o(probe_i_data),
        .probe_i_valid_o(probe_i_valid),
        .probe_m_data_o(probe_m_data),
        .probe_m_valid_o(probe_m_valid),
        .probe_l_data_o(probe_l_data),
        .probe_l_valid_o(probe_l_valid),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .invalid_setup_kind_o(invalid_setup_kind),
        .internal_conflict_o(internal_conflict),
        .operands_valid_o(operands_valid),
        .configuration_valid_o(configuration_valid),
        .writeback_valid_o(writeback_valid),
        .selected_dag2_o(selected_dag2),
        .selected_i_local_o(selected_i_local),
        .selected_m_local_o(selected_m_local),
        .selected_i_address_o(selected_i_address),
        .selected_m_address_o(selected_m_address),
        .selected_old_i_o(selected_old_i),
        .selected_m_o(selected_m),
        .selected_l_o(selected_l),
        .next_i_o(next_i),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    always_comb begin
        assert (
            boundary_valid
            == (
                !reset
                && execute
                && type_21_valid
                && !setup_write
            )
        );
        assert (
            invalid_opcode
            == (!reset && execute && !type_21_valid)
        );
        assert (
            integration_conflict
            == (!reset && execute && setup_write)
        );
        assert (
            invalid_setup_kind
            == (
                !reset
                && setup_write
                && !execute
                && (setup_kind == 2'b11)
            )
        );
        assert (!internal_conflict);
        assert (!pm_data_access);
        assert (!dm_access);
        assert (writeback_valid == configuration_valid);
        assert (!configuration_valid || operands_valid);
        assert (!operands_valid || boundary_valid);
        if (type_21_valid) begin
            assert (selected_dag2 == opcode[4]);
            assert (selected_i_local == opcode[3:2]);
            assert (selected_m_local == opcode[1:0]);
            assert (
                selected_i_address
                == {opcode[4], opcode[3:2]}
            );
            assert (
                selected_m_address
                == {opcode[4], opcode[1:0]}
            );
            assert (selected_i_address[2] == selected_m_address[2]);
        end else begin
            assert (!selected_dag2);
            assert (selected_i_local == 2'b00);
            assert (selected_m_local == 2'b00);
            assert (selected_i_address == 3'b000);
            assert (selected_m_address == 3'b000);
        end
        cover (boundary_valid && writeback_valid);
        cover (boundary_valid && operands_valid && !configuration_valid);
        cover (boundary_valid && !operands_valid);
        cover (
            operands_valid
            && (selected_old_i == selected_m)
            && (selected_l == 14'h0000)
        );
        cover (integration_conflict);
        cover (invalid_opcode);
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (!probe_i_valid);
            assert (!probe_m_valid);
            assert (!probe_l_valid);
        end else begin
            if (
                $past(boundary_valid)
                && (probe_address == $past(selected_i_address))
            ) begin
                assert (probe_i_valid == $past(writeback_valid));
                if ($past(writeback_valid)) begin
                    assert (probe_i_data == $past(next_i));
                end
            end
            if (
                $past(setup_write)
                && !$past(execute)
                && ($past(setup_kind) != 2'b11)
                && (probe_address == $past(setup_address))
            ) begin
                case ($past(setup_kind))
                    2'b00: begin
                        assert (probe_i_valid);
                        assert (probe_i_data == $past(setup_data));
                    end
                    2'b01: begin
                        assert (probe_m_valid);
                        assert (probe_m_data == $past(setup_data));
                    end
                    2'b10: begin
                        assert (probe_l_valid);
                        assert (probe_l_data == $past(setup_data));
                    end
                    default: begin
                    end
                endcase
            end
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
