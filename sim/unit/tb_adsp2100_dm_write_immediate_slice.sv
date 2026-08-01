`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_dm_write_immediate_slice;
    logic clk;
    logic [54:0] stimulus;
    logic [80:0] expected_events;
    logic [48:0] expected_post;

    logic reset;
    logic execute;
    logic [23:0] opcode;
    logic dm_ack;
    logic mstat_setup;
    logic [3:0] mstat_setup_data;
    logic dag_setup;
    logic [1:0] dag_setup_kind;
    logic [2:0] dag_setup_address;
    logic [13:0] dag_setup_data;
    logic [2:0] probe_address;

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
    logic [13:0] probe_i_data;
    logic probe_i_valid;
    logic [13:0] probe_m_data;
    logic probe_m_valid;
    logic [13:0] probe_l_data;
    logic probe_l_valid;
    logic [3:0] mstat;

    logic exp_probe_i_valid;
    logic [13:0] exp_probe_i_data;
    logic exp_probe_m_valid;
    logic [13:0] exp_probe_m_data;
    logic exp_probe_l_valid;
    logic [13:0] exp_probe_l_data;
    logic [3:0] exp_mstat;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset, execute, opcode, dm_ack,
        mstat_setup, mstat_setup_data,
        dag_setup, dag_setup_kind, dag_setup_address, dag_setup_data,
        probe_address
    } = stimulus;
    assign {
        exp_probe_i_valid, exp_probe_i_data,
        exp_probe_m_valid, exp_probe_m_data,
        exp_probe_l_valid, exp_probe_l_data,
        exp_mstat
    } = expected_post;

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

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_post = '0;
        vector_file = $fopen("build/dm_write_immediate_vectors.txt", "r");
        if (vector_file == 0) begin
            $fatal(1, "cannot open build/dm_write_immediate_vectors.txt");
        end
        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_events,
                expected_post
            );
            if (scan_count == 3) begin
                #1;
                if ({
                    class_valid, action_valid, immediate, dag2,
                    i_local, m_local, i_address, m_address, l_address,
                    boundary_valid, accepted, instruction_complete,
                    transaction_active, stalled, busy, invalid_opcode,
                    integration_conflict, internal_conflict,
                    dm_select, dm_read, dm_write,
                    dm_address_valid, dm_address,
                    dm_write_data_valid, dm_write_data,
                    dag_configuration_valid, i_write, i_write_known,
                    pm_data_access, dm_access
                } !== expected_events) begin
                    $fatal(
                        1,
                        "Type 2 execution event mismatch vector=%0d expected=%h actual=%h",
                        vector_count,
                        expected_events,
                        {
                            class_valid, action_valid, immediate, dag2,
                            i_local, m_local, i_address, m_address, l_address,
                            boundary_valid, accepted, instruction_complete,
                            transaction_active, stalled, busy, invalid_opcode,
                            integration_conflict, internal_conflict,
                            dm_select, dm_read, dm_write,
                            dm_address_valid, dm_address,
                            dm_write_data_valid, dm_write_data,
                            dag_configuration_valid, i_write, i_write_known,
                            pm_data_access, dm_access
                        }
                    );
                end
                #4 clk = 1'b1;
                #1;
                if (
                    probe_i_valid !== exp_probe_i_valid
                    || probe_m_valid !== exp_probe_m_valid
                    || probe_l_valid !== exp_probe_l_valid
                    || mstat !== exp_mstat
                ) begin
                    $fatal(
                        1,
                        "Type 2 execution post-validity mismatch vector=%0d expected=%h actual=%h",
                        vector_count,
                        expected_post,
                        {
                            probe_i_valid, probe_i_data,
                            probe_m_valid, probe_m_data,
                            probe_l_valid, probe_l_data,
                            mstat
                        }
                    );
                end
                if (exp_probe_i_valid && probe_i_data !== exp_probe_i_data)
                    $fatal(1, "Type 2 I mismatch vector=%0d", vector_count);
                if (exp_probe_m_valid && probe_m_data !== exp_probe_m_data)
                    $fatal(1, "Type 2 M mismatch vector=%0d", vector_count);
                if (exp_probe_l_valid && probe_l_data !== exp_probe_l_data)
                    $fatal(1, "Type 2 L mismatch vector=%0d", vector_count);
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 50_000) begin
            $fatal(1, "insufficient vectors: %0d", vector_count);
        end
        $display(
            "PASS Type 2 state/bus model-RTL differential: %0d clocks",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
