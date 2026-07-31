`default_nettype none

module adsp2100_modify_address_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        setup_write_i,
    input  logic [1:0]  setup_kind_i,
    input  logic [2:0]  setup_address_i,
    input  logic [13:0] setup_data_i,

    input  logic [2:0]  probe_address_i,
    output logic [13:0] probe_i_data_o,
    output logic        probe_i_valid_o,
    output logic [13:0] probe_m_data_o,
    output logic        probe_m_valid_o,
    output logic [13:0] probe_l_data_o,
    output logic        probe_l_valid_o,

    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        integration_conflict_o,
    output logic        invalid_setup_kind_o,
    output logic        internal_conflict_o,
    output logic        operands_valid_o,
    output logic        configuration_valid_o,
    output logic        writeback_valid_o,
    output logic        selected_dag2_o,
    output logic [1:0]  selected_i_local_o,
    output logic [1:0]  selected_m_local_o,
    output logic [2:0]  selected_i_address_o,
    output logic [2:0]  selected_m_address_o,
    output logic [13:0] selected_old_i_o,
    output logic [13:0] selected_m_o,
    output logic [13:0] selected_l_o,
    output logic [13:0] next_i_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic       decode_valid;
    logic       decoded_dag2;
    logic [1:0] decoded_i_local;
    logic [1:0] decoded_m_local;
    logic [2:0] decoded_i_address;
    logic [2:0] decoded_m_address;
    logic [2:0] decoded_l_address;
    logic       selected_i_valid;
    logic       selected_m_valid;
    logic       selected_l_valid;
    logic [13:0] dag_address_unused;
    logic [13:0] dag_base_unused;
    logic       dag_circular_unused;
    logic       dag_configuration_valid;
    logic       setup_forward;
    logic       register_invalid_setup;
    logic       register_write_conflict;

    adsp2100_modify_address_decode decode (
        .opcode_i(opcode_i),
        .valid_o(decode_valid),
        .dag2_o(decoded_dag2),
        .i_local_o(decoded_i_local),
        .m_local_o(decoded_m_local),
        .i_address_o(decoded_i_address),
        .m_address_o(decoded_m_address),
        .l_address_o(decoded_l_address)
    );

    assign integration_conflict_o = (
        !reset_i
        && execute_i
        && setup_write_i
    );
    assign invalid_opcode_o = (
        !reset_i
        && execute_i
        && !decode_valid
    );
    assign boundary_valid_o = (
        !reset_i
        && execute_i
        && decode_valid
        && !integration_conflict_o
    );
    assign setup_forward = (
        !reset_i
        && setup_write_i
        && !execute_i
    );
    assign invalid_setup_kind_o = register_invalid_setup;
    assign internal_conflict_o = register_write_conflict;

    assign selected_dag2_o = decoded_dag2;
    assign selected_i_local_o = decoded_i_local;
    assign selected_m_local_o = decoded_m_local;
    assign selected_i_address_o = decoded_i_address;
    assign selected_m_address_o = decoded_m_address;
    assign operands_valid_o = (
        boundary_valid_o
        && selected_i_valid
        && selected_m_valid
        && selected_l_valid
    );
    assign configuration_valid_o = (
        operands_valid_o
        && dag_configuration_valid
    );
    assign writeback_valid_o = configuration_valid_o;

    // Type 21 performs no PM-data or DM transaction. Instruction fetch is
    // intentionally outside this bounded execution slice.
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b0)
    ) arithmetic (
        .i_i(selected_old_i_o),
        .m_i(selected_m_o),
        .l_i(selected_l_o),
        .bit_reverse_enable_i(1'b0),
        .address_o(dag_address_unused),
        .next_i_o(next_i_o),
        .base_o(dag_base_unused),
        .circular_o(dag_circular_unused),
        .configuration_valid_o(dag_configuration_valid)
    );

    adsp2100_dag_register_file registers (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .i_l_read_address_i(decoded_l_address),
        .m_read_address_i(decoded_m_address),
        .i_read_data_o(selected_old_i_o),
        .i_read_valid_o(selected_i_valid),
        .m_read_data_o(selected_m_o),
        .m_read_valid_o(selected_m_valid),
        .l_read_data_o(selected_l_o),
        .l_read_valid_o(selected_l_valid),
        .probe_address_i(probe_address_i),
        .probe_i_data_o(probe_i_data_o),
        .probe_i_valid_o(probe_i_valid_o),
        .probe_m_data_o(probe_m_data_o),
        .probe_m_valid_o(probe_m_valid_o),
        .probe_l_data_o(probe_l_data_o),
        .probe_l_valid_o(probe_l_valid_o),
        .setup_write_i(setup_forward),
        .setup_kind_i(setup_kind_i),
        .setup_address_i(setup_address_i),
        .setup_data_i(setup_data_i),
        .i_write_enable_i(boundary_valid_o),
        .i_write_address_i(decoded_i_address),
        .i_write_data_i(next_i_o),
        .i_write_result_valid_i(writeback_valid_o),
        .invalid_setup_kind_o(register_invalid_setup),
        .write_conflict_o(register_write_conflict)
    );
endmodule

`default_nettype wire
