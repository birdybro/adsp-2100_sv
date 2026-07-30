`default_nettype none

module adsp2100_mode_slice_formal (
    input logic        clk,
    input logic        reset,
    input logic        astat_move_write_enable,
    input logic [7:0]  astat_move_write_data,
    input logic        mstat_move_write_enable,
    input logic [3:0]  mstat_move_write_data,
    input logic [1:0]  mode_sr,
    input logic [1:0]  mode_br,
    input logic [1:0]  mode_ol,
    input logic [1:0]  mode_as,
    input logic [3:0]  dreg_read_address,
    input logic        dreg_write_enable,
    input logic [3:0]  dreg_write_address,
    input logic [15:0] dreg_write_data,
    input logic        alu_execute,
    input logic [4:0]  alu_amf,
    input logic [15:0] alu_x,
    input logic [15:0] alu_y,
    input logic        alu_destination_feedback,
    input logic [13:0] dag1_i,
    input logic [13:0] dag1_m,
    input logic [13:0] dag1_l
);
    import adsp2100_register_pkg::*;

    logic [15:0] dreg_read_data;
    logic        alu_valid;
    logic [15:0] alu_raw_result;
    logic [15:0] alu_destination_result;
    logic [13:0] dag1_address;
    logic [13:0] dag1_next_i;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        bit_reverse;
    logic        overflow_latch;
    logic        saturate_ar;
    logic        status_write_conflict;
    logic        register_write_conflict;
    logic        active_mode_control;
    logic        alu_commit;
    logic        past_valid;

    function automatic logic [13:0] reverse14(input logic [13:0] value);
        integer index;
        begin
            for (index = 0; index < 14; index = index + 1) begin
                reverse14[index] = value[13 - index];
            end
        end
    endfunction

    function automatic logic next_mode_bit(
        input logic previous,
        input logic [1:0] control
    );
        next_mode_bit = control[1] ? control[0] : previous;
    endfunction

    function automatic logic [15:0] direct_readback(
        input logic [3:0] address,
        input logic [15:0] data
    );
        if ((address == DREG_SE) || (address == DREG_MR2)) begin
            direct_readback = {{8{data[7]}}, data[7:0]};
        end else begin
            direct_readback = data;
        end
    endfunction

    assign active_mode_control = (
        mode_sr[1]
        || mode_br[1]
        || mode_ol[1]
        || mode_as[1]
    );
    assign alu_commit = alu_execute && alu_valid && !reset;

    adsp2100_mode_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .astat_move_write_enable_i(astat_move_write_enable),
        .astat_move_write_data_i(astat_move_write_data),
        .mstat_move_write_enable_i(mstat_move_write_enable),
        .mstat_move_write_data_i(mstat_move_write_data),
        .mode_sr_i(mode_sr),
        .mode_br_i(mode_br),
        .mode_ol_i(mode_ol),
        .mode_as_i(mode_as),
        .dreg_read_address_i(dreg_read_address),
        .dreg_read_data_o(dreg_read_data),
        .dreg_write_enable_i(dreg_write_enable),
        .dreg_write_address_i(dreg_write_address),
        .dreg_write_data_i(dreg_write_data),
        .alu_execute_i(alu_execute),
        .alu_amf_i(alu_amf),
        .alu_x_i(alu_x),
        .alu_y_i(alu_y),
        .alu_destination_feedback_i(alu_destination_feedback),
        .alu_valid_o(alu_valid),
        .alu_raw_result_o(alu_raw_result),
        .alu_destination_result_o(alu_destination_result),
        .dag1_i_i(dag1_i),
        .dag1_m_i(dag1_m),
        .dag1_l_i(dag1_l),
        .dag1_address_o(dag1_address),
        .dag1_next_i_o(dag1_next_i),
        .astat_o(astat),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .status_write_conflict_o(status_write_conflict),
        .register_write_conflict_o(register_write_conflict)
    );

    always_comb begin
        assert (
            {
                saturate_ar,
                overflow_latch,
                bit_reverse,
                alternate_bank
            }
            == mstat
        );
        assert (
            dag1_address
            == (bit_reverse ? reverse14(dag1_i) : dag1_i)
        );
        assert (
            status_write_conflict
            == (
                !reset
                && (
                    (astat_move_write_enable && alu_commit)
                    || (
                        mstat_move_write_enable
                        && active_mode_control
                    )
                )
            )
        );
        assert (
            register_write_conflict
            == (
                alu_commit
                && dreg_write_enable
                && !alu_destination_feedback
                && (dreg_write_address == DREG_AR)
            )
        );

        if (
            alu_valid
            && (alu_amf == 5'h13)
            && (alu_x == 16'h7fff)
            && (alu_y == 16'h0001)
            && !alu_destination_feedback
        ) begin
            assert (alu_raw_result == 16'h8000);
            assert (
                alu_destination_result
                == (saturate_ar ? 16'h7fff : 16'h8000)
            );
        end
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid) begin
            if ($past(reset)) begin
                assert (mstat == 4'h0);
            end else if (!$past(status_write_conflict)) begin
                if ($past(mstat_move_write_enable)) begin
                    assert (mstat == $past(mstat_move_write_data));
                end else begin
                    assert (
                        mstat[0]
                        == next_mode_bit($past(mstat[0]), $past(mode_sr))
                    );
                    assert (
                        mstat[1]
                        == next_mode_bit($past(mstat[1]), $past(mode_br))
                    );
                    assert (
                        mstat[2]
                        == next_mode_bit($past(mstat[2]), $past(mode_ol))
                    );
                    assert (
                        mstat[3]
                        == next_mode_bit($past(mstat[3]), $past(mode_as))
                    );
                end
            end

            if (
                !$past(reset)
                && !$past(register_write_conflict)
                && $past(dreg_write_enable)
                && (alternate_bank == $past(alternate_bank))
                && (dreg_read_address == $past(dreg_write_address))
            ) begin
                assert (
                    dreg_read_data
                    == direct_readback(
                        $past(dreg_write_address),
                        $past(dreg_write_data)
                    )
                );
            end
        end

        cover (bit_reverse && (dag1_address != dag1_i));
        cover (
            saturate_ar
            && alu_valid
            && (alu_destination_result != alu_raw_result)
        );
        cover (overflow_latch && (astat == 8'ha5));
        cover (alternate_bank && (dreg_read_data == 16'h2100));
        cover (dag1_next_i != dag1_i);
    end
endmodule

`default_nettype wire
