`default_nettype none

module adsp2100_dag_formal (
    input logic [13:0] i_value,
    input logic [13:0] m_value,
    input logic [13:0] l_value,
    input logic        bit_reverse
);
    logic [13:0] dag1_address;
    logic [13:0] dag1_next_i;
    logic [13:0] dag1_base;
    logic        dag1_circular;
    logic        dag1_valid;
    logic [13:0] dag2_address;
    logic [13:0] dag2_next_i;
    logic [13:0] dag2_base;
    logic        dag2_circular;
    logic        dag2_valid;
    logic [13:0] expected_reverse;
    integer      bit_index;

    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b1)
    ) dag1 (
        .i_i(i_value),
        .m_i(m_value),
        .l_i(l_value),
        .bit_reverse_enable_i(bit_reverse),
        .address_o(dag1_address),
        .next_i_o(dag1_next_i),
        .base_o(dag1_base),
        .circular_o(dag1_circular),
        .configuration_valid_o(dag1_valid)
    );

    adsp2100_dag #(
        .BIT_REVERSE_CAPABLE(1'b0)
    ) dag2 (
        .i_i(i_value),
        .m_i(m_value),
        .l_i(l_value),
        .bit_reverse_enable_i(bit_reverse),
        .address_o(dag2_address),
        .next_i_o(dag2_next_i),
        .base_o(dag2_base),
        .circular_o(dag2_circular),
        .configuration_valid_o(dag2_valid)
    );

    always_comb begin
        expected_reverse = 14'h0000;
        bit_index = 32'sd0;
        for (
            bit_index = 32'sd0;
            bit_index < 32'sd14;
            bit_index = bit_index + 32'sd1
        ) begin
            expected_reverse[32'sd13 - bit_index] = i_value[bit_index];
        end

        assert (dag2_address == i_value);
        assert (dag1_address == (bit_reverse ? expected_reverse : i_value));
        assert (dag1_next_i == dag2_next_i);
        assert (dag1_base == dag2_base);
        assert (dag1_circular == dag2_circular);
        assert (dag1_valid == dag2_valid);

        if (l_value == 14'h0000) begin
            assert (!dag1_circular);
            assert (dag1_base == 14'h0000);
            assert (dag1_valid);
        end
        if (dag1_valid && dag1_circular) begin
            assert (dag1_next_i >= dag1_base);
            assert (
                {1'b0, dag1_next_i}
                < ({1'b0, dag1_base} + {1'b0, l_value})
            );
        end
        if (l_value == 14'h0008) begin
            assert (dag1_base[3:0] == 4'h0);
        end
    end
endmodule

`default_nettype wire
