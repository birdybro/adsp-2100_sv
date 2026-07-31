`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_modify_address_slice;
    logic        clk;
    logic [48:0] stimulus;
    logic [20:0] expected_event;
    logic [55:0] expected_selected_data;
    logic [44:0] expected_probe;

    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        setup_write;
    logic [1:0]  setup_kind;
    logic [2:0]  setup_address;
    logic [13:0] setup_data;
    logic [2:0]  probe_address;

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

    logic        expected_operands_valid;
    logic [13:0] expected_old_i;
    logic [13:0] expected_m;
    logic [13:0] expected_l;
    logic [13:0] expected_next_i;
    logic        expected_probe_i_valid;
    logic [13:0] expected_probe_i_data;
    logic        expected_probe_m_valid;
    logic [13:0] expected_probe_m_data;
    logic        expected_probe_l_valid;
    logic [13:0] expected_probe_l_data;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset,
        execute,
        opcode,
        setup_write,
        setup_kind,
        setup_address,
        setup_data,
        probe_address
    } = stimulus;
    assign expected_operands_valid = expected_event[15];
    assign {
        expected_old_i,
        expected_m,
        expected_l,
        expected_next_i
    } = expected_selected_data;
    assign {
        expected_probe_i_valid,
        expected_probe_i_data,
        expected_probe_m_valid,
        expected_probe_m_data,
        expected_probe_l_valid,
        expected_probe_l_data
    } = expected_probe;

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

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_event = '0;
        expected_selected_data = '0;
        expected_probe = '0;
        vector_file = $fopen(
            "build/modify_address_slice_vectors.txt",
            "r"
        );
        if (vector_file == 0) begin
            $fatal(
                1,
                "cannot open build/modify_address_slice_vectors.txt"
            );
        end

        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h %h\n",
                stimulus,
                expected_event,
                expected_selected_data,
                expected_probe
            );
            if (scan_count == 4) begin
                #1;
                if (
                    {
                        boundary_valid,
                        invalid_opcode,
                        integration_conflict,
                        invalid_setup_kind,
                        internal_conflict,
                        operands_valid,
                        configuration_valid,
                        writeback_valid,
                        selected_dag2,
                        selected_i_local,
                        selected_m_local,
                        selected_i_address,
                        selected_m_address,
                        pm_data_access,
                        dm_access
                    }
                    !== expected_event
                ) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d actual=%06x expected=%06x",
                        vector_count,
                        {
                            boundary_valid,
                            invalid_opcode,
                            integration_conflict,
                            invalid_setup_kind,
                            internal_conflict,
                            operands_valid,
                            configuration_valid,
                            writeback_valid,
                            selected_dag2,
                            selected_i_local,
                            selected_m_local,
                            selected_i_address,
                            selected_m_address,
                            pm_data_access,
                            dm_access
                        },
                        expected_event
                    );
                end
                if (
                    expected_operands_valid
                    && (
                        selected_old_i !== expected_old_i
                        || selected_m !== expected_m
                        || selected_l !== expected_l
                        || next_i !== expected_next_i
                    )
                ) begin
                    $fatal(
                        1,
                        "selected data mismatch vector=%0d",
                        vector_count
                    );
                end

                #4 clk = 1'b1;
                #1;
                if (
                    probe_i_valid !== expected_probe_i_valid
                    || probe_m_valid !== expected_probe_m_valid
                    || probe_l_valid !== expected_probe_l_valid
                ) begin
                    $fatal(
                        1,
                        "probe validity mismatch vector=%0d",
                        vector_count
                    );
                end
                if (
                    (expected_probe_i_valid
                        && probe_i_data !== expected_probe_i_data)
                    || (expected_probe_m_valid
                        && probe_m_data !== expected_probe_m_data)
                    || (expected_probe_l_valid
                        && probe_l_data !== expected_probe_l_data)
                ) begin
                    $fatal(
                        1,
                        "probe data mismatch vector=%0d",
                        vector_count
                    );
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50_000) begin
            $fatal(1, "insufficient vectors: %0d", vector_count);
        end
        $display(
            "PASS Type 21 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
