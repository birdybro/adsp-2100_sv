`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_mode_control_slice;
    logic        clk;
    logic [30:0] stimulus;
    logic [13:0] expected_events;
    logic [3:0]  expected_mstat;

    logic        reset;
    logic        execute;
    logic [23:0] opcode;
    logic        setup_write;
    logic [3:0]  setup_write_data;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [1:0]  decoded_sr;
    logic [1:0]  decoded_br;
    logic [1:0]  decoded_ol;
    logic [1:0]  decoded_as;
    logic        decoded_has_effect;
    logic        decoded_has_alias;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        bit_reverse;
    logic        overflow_latch;
    logic        saturate_ar;

    logic        expected_boundary_valid;
    logic        expected_invalid_opcode;
    logic        expected_integration_conflict;
    logic        expected_internal_conflict;
    logic [1:0]  expected_sr;
    logic [1:0]  expected_br;
    logic [1:0]  expected_ol;
    logic [1:0]  expected_as;
    logic        expected_has_effect;
    logic        expected_has_alias;

    integer vector_file;
    integer scan_count;
    integer vector_count;

    assign {
        reset,
        execute,
        opcode,
        setup_write,
        setup_write_data
    } = stimulus;
    assign {
        expected_boundary_valid,
        expected_invalid_opcode,
        expected_integration_conflict,
        expected_internal_conflict,
        expected_sr,
        expected_br,
        expected_ol,
        expected_as,
        expected_has_effect,
        expected_has_alias
    } = expected_events;

    adsp2100_mode_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .mstat_setup_write_i(setup_write),
        .mstat_setup_write_data_i(setup_write_data),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .decoded_mode_sr_o(decoded_sr),
        .decoded_mode_br_o(decoded_br),
        .decoded_mode_ol_o(decoded_ol),
        .decoded_mode_as_o(decoded_as),
        .decoded_has_effect_o(decoded_has_effect),
        .decoded_has_alias_o(decoded_has_alias),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar)
    );

    initial begin
        clk = 1'b0;
        stimulus = '0;
        expected_events = '0;
        expected_mstat = '0;
        vector_file = $fopen(
            "build/mode_control_slice_vectors.txt",
            "r"
        );
        if (vector_file == 0) begin
            $fatal(
                1,
                "cannot open build/mode_control_slice_vectors.txt"
            );
        end

        vector_count = 0;
        while (!$feof(vector_file)) begin
            scan_count = $fscanf(
                vector_file,
                "%h %h %h\n",
                stimulus,
                expected_events,
                expected_mstat
            );
            if (scan_count == 3) begin
                #1;
                if (
                    boundary_valid !== expected_boundary_valid
                    || invalid_opcode !== expected_invalid_opcode
                    || integration_conflict
                        !== expected_integration_conflict
                    || internal_conflict !== expected_internal_conflict
                    || decoded_sr !== expected_sr
                    || decoded_br !== expected_br
                    || decoded_ol !== expected_ol
                    || decoded_as !== expected_as
                    || decoded_has_effect !== expected_has_effect
                    || decoded_has_alias !== expected_has_alias
                ) begin
                    $fatal(
                        1,
                        "event mismatch vector=%0d actual=%04x expected=%04x",
                        vector_count,
                        {
                            boundary_valid,
                            invalid_opcode,
                            integration_conflict,
                            internal_conflict,
                            decoded_sr,
                            decoded_br,
                            decoded_ol,
                            decoded_as,
                            decoded_has_effect,
                            decoded_has_alias
                        },
                        expected_events
                    );
                end

                #4 clk = 1'b1;
                #1;
                if (
                    mstat !== expected_mstat
                    || alternate_bank !== expected_mstat[0]
                    || bit_reverse !== expected_mstat[1]
                    || overflow_latch !== expected_mstat[2]
                    || saturate_ar !== expected_mstat[3]
                ) begin
                    $fatal(
                        1,
                        "MSTAT mismatch vector=%0d actual=%x expected=%x",
                        vector_count,
                        mstat,
                        expected_mstat
                    );
                end
                #4 clk = 1'b0;
                vector_count = vector_count + 1;
            end
        end
        $fclose(vector_file);
        if (vector_count < 58_000) begin
            $fatal(1, "insufficient vectors: %0d", vector_count);
        end
        $display(
            "PASS Type 18 stateful model/RTL differential: %0d cycles",
            vector_count
        );
        $finish;
    end
endmodule

`default_nettype wire
