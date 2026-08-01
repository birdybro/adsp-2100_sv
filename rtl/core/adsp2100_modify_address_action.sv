`default_nettype none

// Stateless Type 21 MODIFY action producer for the shared state owner.
// Selected I/M/L operands are cycle-start values. The owner commits the
// selected-I validity and value only at the instruction retirement edge.
module adsp2100_modify_address_action (
    input  logic [23:0] opcode_i,
    input  logic [13:0] i_data_i,
    input  logic        i_data_valid_i,
    input  logic [13:0] m_data_i,
    input  logic        m_data_valid_i,
    input  logic [13:0] l_data_i,
    input  logic        l_data_valid_i,

    output logic        action_valid_o,
    output logic        dag2_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o,
    output logic        operands_valid_o,
    output logic        configuration_valid_o,
    output logic        i_write_o,
    output logic [13:0] i_write_data_o,
    output logic        i_write_result_valid_o
);
    logic [1:0] i_local_unused;
    logic [1:0] m_local_unused;
    logic [2:0] l_address_unused;
    logic [13:0] address_unused;
    logic [13:0] base_unused;
    logic circular_unused;
    logic dag_configuration_valid;
    logic unused_observation;

    adsp2100_modify_address_decode decode (
        .opcode_i(opcode_i),
        .valid_o(action_valid_o),
        .dag2_o(dag2_o),
        .i_local_o(i_local_unused),
        .m_local_o(m_local_unused),
        .i_address_o(i_address_o),
        .m_address_o(m_address_o),
        .l_address_o(l_address_unused)
    );

    assign operands_valid_o = (
        action_valid_o && i_data_valid_i && m_data_valid_i && l_data_valid_i
    );
    assign configuration_valid_o = (
        operands_valid_o && dag_configuration_valid
    );
    assign i_write_o = action_valid_o;
    assign i_write_result_valid_o = configuration_valid_o;

    // MODIFY uses ordinary post-modification arithmetic. The BR mode affects
    // generated DAG1 memory addresses, not the I-register value written here.
    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b0)
    ) arithmetic (
        .i_i(i_data_i),
        .m_i(m_data_i),
        .l_i(l_data_i),
        .bit_reverse_enable_i(1'b0),
        .address_o(address_unused),
        .next_i_o(i_write_data_o),
        .base_o(base_unused),
        .circular_o(circular_unused),
        .configuration_valid_o(dag_configuration_valid)
    );

    assign unused_observation = ^{
        i_local_unused, m_local_unused, l_address_unused, address_unused,
        base_unused, circular_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        if (!action_valid_o) begin
            assert (!i_write_o);
            assert (!i_write_result_valid_o);
        end
        if (i_write_result_valid_o) begin
            assert (i_write_o && operands_valid_o);
        end
    end
`endif
endmodule

`default_nettype wire
