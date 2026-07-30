`default_nettype none

module adsp2100_register_file_formal (
    input logic        clk,
    input logic        alternate_bank,
    input logic        write_enable_0,
    input logic [3:0]  write_address_0,
    input logic [15:0] write_data_0,
    input logic        write_enable_1,
    input logic [3:0]  write_address_1,
    input logic [15:0] write_data_1,
    input logic        write_enable_2,
    input logic [3:0]  write_address_2,
    input logic [15:0] write_data_2
);
    import adsp2100_register_pkg::*;

    logic [15:0] mr1_data;
    logic [15:0] mr2_data;
    logic [15:0] se_data;
    logic        write_conflict;
    logic        expected_conflict;
    logic        past_valid;

    function automatic logic overlap(
        input logic [3:0] left,
        input logic [3:0] right
    );
        overlap = (
            (left == right)
            || ((left == DREG_MR1) && (right == DREG_MR2))
            || ((left == DREG_MR2) && (right == DREG_MR1))
        );
    endfunction

    adsp2100_register_file dut (
        .clk_i(clk),
        .alternate_bank_i(alternate_bank),
        .read_address_0_i(DREG_MR1),
        .read_address_1_i(DREG_MR2),
        .read_address_2_i(DREG_SE),
        .read_data_0_o(mr1_data),
        .read_data_1_o(mr2_data),
        .read_data_2_o(se_data),
        .write_enable_0_i(write_enable_0),
        .write_address_0_i(write_address_0),
        .write_data_0_i(write_data_0),
        .write_enable_1_i(write_enable_1),
        .write_address_1_i(write_address_1),
        .write_data_1_i(write_data_1),
        .write_enable_2_i(write_enable_2),
        .write_address_2_i(write_address_2),
        .write_data_2_i(write_data_2),
        .write_conflict_o(write_conflict)
    );

    always_comb begin
        expected_conflict = (
            (
                write_enable_0
                && write_enable_1
                && overlap(write_address_0, write_address_1)
            )
            || (
                write_enable_0
                && write_enable_2
                && overlap(write_address_0, write_address_2)
            )
            || (
                write_enable_1
                && write_enable_2
                && overlap(write_address_1, write_address_2)
            )
        );
        assert (write_conflict == expected_conflict);
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (
            past_valid
            && (alternate_bank == $past(alternate_bank))
            && !$past(write_conflict)
        ) begin
            if ($past(write_enable_0 && (write_address_0 == DREG_MR1))) begin
                assert (mr1_data == $past(write_data_0));
                assert (mr2_data == {16{$past(write_data_0[15])}});
            end
            if ($past(write_enable_1 && (write_address_1 == DREG_MR1))) begin
                assert (mr1_data == $past(write_data_1));
                assert (mr2_data == {16{$past(write_data_1[15])}});
            end
            if ($past(write_enable_2 && (write_address_2 == DREG_MR1))) begin
                assert (mr1_data == $past(write_data_2));
                assert (mr2_data == {16{$past(write_data_2[15])}});
            end

            if ($past(write_enable_0 && (write_address_0 == DREG_MR2))) begin
                assert (
                    mr2_data
                    == {
                        {8{$past(write_data_0[7])}},
                        $past(write_data_0[7:0])
                    }
                );
            end
            if ($past(write_enable_1 && (write_address_1 == DREG_MR2))) begin
                assert (
                    mr2_data
                    == {
                        {8{$past(write_data_1[7])}},
                        $past(write_data_1[7:0])
                    }
                );
            end
            if ($past(write_enable_2 && (write_address_2 == DREG_MR2))) begin
                assert (
                    mr2_data
                    == {
                        {8{$past(write_data_2[7])}},
                        $past(write_data_2[7:0])
                    }
                );
            end

            if ($past(write_enable_0 && (write_address_0 == DREG_SE))) begin
                assert (
                    se_data
                    == {
                        {8{$past(write_data_0[7])}},
                        $past(write_data_0[7:0])
                    }
                );
            end
            if ($past(write_enable_1 && (write_address_1 == DREG_SE))) begin
                assert (
                    se_data
                    == {
                        {8{$past(write_data_1[7])}},
                        $past(write_data_1[7:0])
                    }
                );
            end
            if ($past(write_enable_2 && (write_address_2 == DREG_SE))) begin
                assert (
                    se_data
                    == {
                        {8{$past(write_data_2[7])}},
                        $past(write_data_2[7:0])
                    }
                );
            end
        end
    end
endmodule

`default_nettype wire
