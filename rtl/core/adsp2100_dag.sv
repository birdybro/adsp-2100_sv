`default_nettype none

module adsp2100_dag #(
    parameter bit BIT_REVERSE_CAPABLE = 1'b1
) (
    input  logic [13:0] i_i,
    input  logic [13:0] m_i,
    input  logic [13:0] l_i,
    input  logic        bit_reverse_enable_i,
    output logic [13:0] address_o,
    output logic [13:0] next_i_o,
    output logic [13:0] base_o,
    output logic        circular_o,
    output logic        configuration_valid_o
);
    logic [13:0] base_mask;
    logic [13:0] reversed_address;
    logic [31:0] i_extended;
    logic [31:0] l_extended;
    logic [31:0] base_extended;
    logic [31:0] upper_bound;
    logic [31:0] modify_magnitude;
    logic signed [31:0] modify_value;
    logic signed [31:0] next_value;
    integer      bit_index;
    integer      length_bits;

    always_comb begin
        base_mask = 14'h3fff;
        reversed_address = 14'h0000;
        address_o = i_i;
        next_i_o = i_i;
        base_o = 14'h0000;
        circular_o = l_i != 14'h0000;
        configuration_valid_o = 1'b1;
        i_extended = {18'h00000, i_i};
        l_extended = {18'h00000, l_i};
        base_extended = 32'h00000000;
        upper_bound = 32'h00000000;
        modify_value = $signed({{18{m_i[13]}}, m_i});
        modify_magnitude = modify_value[31]
            ? $unsigned(-modify_value) : $unsigned(modify_value);
        next_value = 32'sh00000000;
        bit_index = 32'sd0;
        length_bits = 32'sd0;

        for (
            bit_index = 32'sd0;
            bit_index < 32'sd14;
            bit_index = bit_index + 32'sd1
        ) begin
            reversed_address[32'sd13 - bit_index] = i_i[bit_index];
            if (l_i[bit_index]) begin
                length_bits = bit_index + 32'sd1;
            end
        end

        if (BIT_REVERSE_CAPABLE && bit_reverse_enable_i) begin
            address_o = reversed_address;
        end

        if (!circular_o) begin
            next_value = $signed(i_extended) + modify_value;
            next_i_o = next_value[13:0];
        end else begin
            base_mask = 14'h0000;
            for (
                bit_index = 32'sd0;
                bit_index < 32'sd14;
                bit_index = bit_index + 32'sd1
            ) begin
                if (bit_index >= length_bits) begin
                    base_mask[bit_index] = 1'b1;
                end
            end
            base_o = i_i & base_mask;
            base_extended = {18'h00000, base_o};
            upper_bound = base_extended + l_extended;
            configuration_valid_o = (
                (i_extended >= base_extended)
                && (i_extended < upper_bound)
                && (modify_magnitude <= l_extended)
                && (upper_bound <= 32'd16384)
            );

            next_value = $signed(i_extended) + modify_value;
            if (next_value < $signed(base_extended)) begin
                next_value = next_value + $signed(l_extended);
            end else if (next_value >= $signed(upper_bound)) begin
                next_value = next_value - $signed(l_extended);
            end
            next_i_o = next_value[13:0];
        end
    end
endmodule

`default_nettype wire
