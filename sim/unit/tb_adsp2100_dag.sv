`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_dag;
    logic [43:0] stimulus;
    logic [43:0] expected;
    logic [43:0] actual;
    logic [13:0] i_value;
    logic [13:0] m_value;
    logic [13:0] l_value;
    logic        select_dag1;
    logic        bit_reverse;
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
    integer      vector_file;
    integer      scan_count;
    integer      vector_count;

    assign {
        i_value, m_value, l_value, select_dag1, bit_reverse
    } = stimulus;
    assign actual = select_dag1
        ? {
            dag1_address,
            dag1_next_i,
            dag1_base,
            dag1_circular,
            dag1_valid
        }
        : {
            dag2_address,
            dag2_next_i,
            dag2_base,
            dag2_circular,
            dag2_valid
        };

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

    initial begin
        vector_file = $fopen("build/dag_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/dag_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(vector_file, "%h %h\n", stimulus, expected);
            if (scan_count == 2) begin
                #1;
                if (actual !== expected) begin
                    $fatal(
                        1,
                        "DAG mismatch vector=%0d i=%0h m=%0h l=%0h dag1=%0b rev=%0b expected=%0h actual=%0h",
                        vector_count,
                        i_value,
                        m_value,
                        l_value,
                        select_dag1,
                        bit_reverse,
                        expected,
                        actual
                    );
                end
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        $display("PASS %0d original ADSP-2100 DAG vectors", vector_count);
        $finish;
    end
endmodule

`default_nettype wire
