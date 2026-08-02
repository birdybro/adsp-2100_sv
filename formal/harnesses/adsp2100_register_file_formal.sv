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
    input logic [15:0] write_data_2,
    input logic        sb_move_write_enable,
    input logic [4:0]  sb_move_write_data,
    input logic        alu_write_enable,
    input logic        alu_destination_feedback,
    input logic [15:0] alu_result,
    input logic        mac_write_enable,
    input logic        mac_destination_feedback,
    input logic [39:0] mac_result,
    input logic        shifter_sr_write_enable,
    input logic [31:0] shifter_sr_result,
    input logic        shifter_se_write_enable,
    input logic [7:0]  shifter_se_result,
    input logic        shifter_sb_write_enable,
    input logic [4:0]  shifter_sb_result
);
    import adsp2100_register_pkg::*;

    logic [15:0] mr2_data;
    logic [15:0] se_data;
    logic [15:0] ar_data;
    logic [15:0] ar_data_2;
    logic [47:0] unused_additional_read_data;
    logic [15:0] af_state;
    logic [15:0] mf_state;
    logic [39:0] mr_state;
    logic [7:0]  se_state;
    logic [4:0]  sb_state;
    logic [31:0] sr_state;
    logic        write_conflict;
    logic        expected_conflict;
    logic        shifter_write_enable;
    logic        past_valid;
    integer      conflict_port;
    logic [2:0]  write_enable;
    logic [3:0]  write_address [0:2];

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

    assign write_enable[0] = write_enable_0;
    assign write_enable[1] = write_enable_1;
    assign write_enable[2] = write_enable_2;
    assign write_address[0] = write_address_0;
    assign write_address[1] = write_address_1;
    assign write_address[2] = write_address_2;
    assign shifter_write_enable = (
        shifter_sr_write_enable
        || shifter_se_write_enable
        || shifter_sb_write_enable
    );

    adsp2100_register_file dut (
        .clk_i(clk),
        .alternate_bank_i(alternate_bank),
        .read_address_0_i(DREG_MR2),
        .read_address_1_i(DREG_SE),
        .read_address_2_i(DREG_AR),
        .read_address_3_i(DREG_AR),
        .read_address_4_i(DREG_AR),
        .read_address_5_i(DREG_AR),
        .read_address_6_i(DREG_AR),
        .read_data_0_o(mr2_data),
        .read_data_1_o(se_data),
        .read_data_2_o(ar_data),
        .read_data_3_o(ar_data_2),
        .read_data_4_o(unused_additional_read_data[15:0]),
        .read_data_5_o(unused_additional_read_data[31:16]),
        .read_data_6_o(unused_additional_read_data[47:32]),
        .write_enable_0_i(write_enable_0),
        .write_address_0_i(write_address_0),
        .write_data_0_i(write_data_0),
        .write_enable_1_i(write_enable_1),
        .write_address_1_i(write_address_1),
        .write_data_1_i(write_data_1),
        .write_enable_2_i(write_enable_2),
        .write_address_2_i(write_address_2),
        .write_data_2_i(write_data_2),
        .sb_move_write_enable_i(sb_move_write_enable),
        .sb_move_write_data_i(sb_move_write_data),
        .alu_write_enable_i(alu_write_enable),
        .alu_destination_feedback_i(alu_destination_feedback),
        .alu_result_i(alu_result),
        .mac_write_enable_i(mac_write_enable),
        .mac_destination_feedback_i(mac_destination_feedback),
        .mac_result_i(mac_result),
        .shifter_sr_write_enable_i(shifter_sr_write_enable),
        .shifter_sr_result_i(shifter_sr_result),
        .shifter_se_write_enable_i(shifter_se_write_enable),
        .shifter_se_result_i(shifter_se_result),
        .shifter_sb_write_enable_i(shifter_sb_write_enable),
        .shifter_sb_result_i(shifter_sb_result),
        .af_o(af_state),
        .mf_o(mf_state),
        .mr_o(mr_state),
        .se_o(se_state),
        .sb_o(sb_state),
        .sr_o(sr_state),
        .write_conflict_o(write_conflict)
    );

    always_comb begin
        assert (ar_data_2 == ar_data);
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
        if (
            (alu_write_enable && mac_write_enable)
            || (alu_write_enable && shifter_write_enable)
            || (mac_write_enable && shifter_write_enable)
            || (shifter_sr_write_enable && shifter_se_write_enable)
            || (shifter_sr_write_enable && shifter_sb_write_enable)
            || (shifter_se_write_enable && shifter_sb_write_enable)
            || (sb_move_write_enable && shifter_sb_write_enable)
        ) begin
            expected_conflict = 1'b1;
        end
        for (
            conflict_port = 0;
            conflict_port < 3;
            conflict_port = conflict_port + 1
        ) begin
            if (write_enable[conflict_port]) begin
                if (
                    alu_write_enable
                    && !alu_destination_feedback
                    && (write_address[conflict_port] == DREG_AR)
                ) begin
                    expected_conflict = 1'b1;
                end
                if (
                    mac_write_enable
                    && !mac_destination_feedback
                    && (
                        (write_address[conflict_port] == DREG_MR0)
                        || (write_address[conflict_port] == DREG_MR1)
                        || (write_address[conflict_port] == DREG_MR2)
                    )
                ) begin
                    expected_conflict = 1'b1;
                end
                if (
                    shifter_sr_write_enable
                    && (
                        (write_address[conflict_port] == DREG_SR0)
                        || (write_address[conflict_port] == DREG_SR1)
                    )
                ) begin
                    expected_conflict = 1'b1;
                end
                if (
                    shifter_se_write_enable
                    && (write_address[conflict_port] == DREG_SE)
                ) begin
                    expected_conflict = 1'b1;
                end
            end
        end
        assert (write_conflict == expected_conflict);
        assert (
            mr2_data
            == {{8{mr_state[39]}}, mr_state[39:32]}
        );
        assert (se_data == {{8{se_state[7]}}, se_state});
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (
            past_valid
            && (alternate_bank == $past(alternate_bank))
        ) begin
            if ($past(write_conflict)) begin
                assert (
                    {
                        mr2_data,
                        se_data,
                        ar_data,
                        af_state,
                        mf_state,
                        mr_state,
                        se_state,
                        sb_state,
                        sr_state
                    }
                    == $past(
                        {
                            mr2_data,
                            se_data,
                            ar_data,
                            af_state,
                            mf_state,
                            mr_state,
                            se_state,
                            sb_state,
                            sr_state
                        }
                    )
                );
            end
            if (!$past(write_conflict)) begin
                if (
                    $past(alu_write_enable)
                    && $past(alu_destination_feedback)
                ) begin
                    assert (af_state == $past(alu_result));
                end
                if (
                    $past(alu_write_enable)
                    && !$past(alu_destination_feedback)
                ) begin
                    assert (ar_data == $past(alu_result));
                end
                if (
                    $past(mac_write_enable)
                    && $past(mac_destination_feedback)
                ) begin
                    assert (mf_state == $past(mac_result[31:16]));
                end
                if (
                    $past(mac_write_enable)
                    && !$past(mac_destination_feedback)
                ) begin
                    assert (mr_state == $past(mac_result));
                end
                if ($past(shifter_sr_write_enable)) begin
                    assert (sr_state == $past(shifter_sr_result));
                end
                if ($past(shifter_se_write_enable)) begin
                    assert (se_state == $past(shifter_se_result));
                end
                if ($past(shifter_sb_write_enable)) begin
                    assert (sb_state == $past(shifter_sb_result));
                end
                if ($past(sb_move_write_enable)) begin
                    assert (sb_state == $past(sb_move_write_data));
                end

                if (
                    $past(write_enable_0 && (write_address_0 == DREG_MR1))
                ) begin
                    assert (mr_state[31:16] == $past(write_data_0));
                    assert (mr2_data == {16{$past(write_data_0[15])}});
                end
                if (
                    $past(write_enable_1 && (write_address_1 == DREG_MR1))
                ) begin
                    assert (mr_state[31:16] == $past(write_data_1));
                    assert (mr2_data == {16{$past(write_data_1[15])}});
                end
                if (
                    $past(write_enable_2 && (write_address_2 == DREG_MR1))
                ) begin
                    assert (mr_state[31:16] == $past(write_data_2));
                    assert (mr2_data == {16{$past(write_data_2[15])}});
                end

                if (
                    $past(write_enable_0 && (write_address_0 == DREG_MR2))
                ) begin
                    assert (
                        mr2_data
                        == {
                            {8{$past(write_data_0[7])}},
                            $past(write_data_0[7:0])
                        }
                    );
                end
                if (
                    $past(write_enable_1 && (write_address_1 == DREG_MR2))
                ) begin
                    assert (
                        mr2_data
                        == {
                            {8{$past(write_data_1[7])}},
                            $past(write_data_1[7:0])
                        }
                    );
                end
                if (
                    $past(write_enable_2 && (write_address_2 == DREG_MR2))
                ) begin
                    assert (
                        mr2_data
                        == {
                            {8{$past(write_data_2[7])}},
                            $past(write_data_2[7:0])
                        }
                    );
                end

                if (
                    $past(write_enable_0 && (write_address_0 == DREG_SE))
                ) begin
                    assert (
                        se_data
                        == {
                            {8{$past(write_data_0[7])}},
                            $past(write_data_0[7:0])
                        }
                    );
                end
                if (
                    $past(write_enable_1 && (write_address_1 == DREG_SE))
                ) begin
                    assert (
                        se_data
                        == {
                            {8{$past(write_data_1[7])}},
                            $past(write_data_1[7:0])
                        }
                    );
                end
                if (
                    $past(write_enable_2 && (write_address_2 == DREG_SE))
                ) begin
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
    end
endmodule

`default_nettype wire
