`default_nettype none

module adsp2100_status_registers_formal (
    input logic       clk,
    input logic       reset,
    input logic       astat_move_write_enable,
    input logic [7:0] astat_move_write_data,
    input logic       mstat_move_write_enable,
    input logic [3:0] mstat_move_write_data,
    input logic       icntl_move_write_enable,
    input logic [4:0] icntl_move_write_data,
    input logic       imask_move_write_enable,
    input logic [3:0] imask_move_write_data,
    input logic [1:0] mode_sr,
    input logic [1:0] mode_br,
    input logic [1:0] mode_ol,
    input logic [1:0] mode_as,
    input logic       alu_status_write_enable,
    input logic       alu_az,
    input logic       alu_an,
    input logic       alu_av,
    input logic       alu_ac,
    input logic       alu_as_write_enable,
    input logic       alu_as,
    input logic       divide_status_write_enable,
    input logic       divide_aq,
    input logic       mac_status_write_enable,
    input logic       mac_mv,
    input logic       shifter_status_write_enable,
    input logic       shifter_ss,
    input logic       interrupt_entry,
    input logic [1:0] interrupt_level,
    input logic       status_restore,
    input logic [7:0] restore_astat,
    input logic [3:0] restore_mstat,
    input logic [3:0] restore_imask
);
    logic [7:0] astat;
    logic [3:0] mstat;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic       alternate_bank;
    logic       bit_reverse;
    logic       overflow_latch;
    logic       saturate_ar;
    logic       write_conflict;
    logic       status_push;
    logic [7:0] status_push_astat;
    logic [3:0] status_push_mstat;
    logic [3:0] status_push_imask;
    logic       expected_conflict;
    logic       automatic_astat_write;
    logic       automatic_astat_conflict;
    logic       active_mode_control;
    logic       ordinary_state_write;
    logic       past_valid;

    function automatic logic next_mode_bit(
        input logic previous,
        input logic [1:0] control
    );
        next_mode_bit = control[1] ? control[0] : previous;
    endfunction

    assign automatic_astat_write = (
        alu_status_write_enable
        || divide_status_write_enable
        || mac_status_write_enable
        || shifter_status_write_enable
    );
    assign automatic_astat_conflict = (
        (
            alu_status_write_enable
            && (
                divide_status_write_enable
                || mac_status_write_enable
                || shifter_status_write_enable
            )
        )
        || (
            divide_status_write_enable
            && (
                mac_status_write_enable
                || shifter_status_write_enable
            )
        )
        || (
            mac_status_write_enable
            && shifter_status_write_enable
        )
    );
    assign active_mode_control = (
        mode_sr[1]
        || mode_br[1]
        || mode_ol[1]
        || mode_as[1]
    );
    assign ordinary_state_write = (
        astat_move_write_enable
        || mstat_move_write_enable
        || icntl_move_write_enable
        || imask_move_write_enable
        || automatic_astat_write
        || active_mode_control
    );
    assign expected_conflict = !reset && (
        automatic_astat_conflict
        || (astat_move_write_enable && automatic_astat_write)
        || (mstat_move_write_enable && active_mode_control)
        || (
            status_restore
            && (ordinary_state_write || interrupt_entry)
        )
    );

    adsp2100_status_registers dut (
        .clk_i(clk),
        .reset_i(reset),
        .astat_move_write_enable_i(astat_move_write_enable),
        .astat_move_write_data_i(astat_move_write_data),
        .mstat_move_write_enable_i(mstat_move_write_enable),
        .mstat_move_write_data_i(mstat_move_write_data),
        .icntl_move_write_enable_i(icntl_move_write_enable),
        .icntl_move_write_data_i(icntl_move_write_data),
        .imask_move_write_enable_i(imask_move_write_enable),
        .imask_move_write_data_i(imask_move_write_data),
        .mode_sr_i(mode_sr),
        .mode_br_i(mode_br),
        .mode_ol_i(mode_ol),
        .mode_as_i(mode_as),
        .alu_status_write_enable_i(alu_status_write_enable),
        .alu_az_i(alu_az),
        .alu_an_i(alu_an),
        .alu_av_i(alu_av),
        .alu_ac_i(alu_ac),
        .alu_as_write_enable_i(alu_as_write_enable),
        .alu_as_i(alu_as),
        .divide_status_write_enable_i(divide_status_write_enable),
        .divide_aq_i(divide_aq),
        .mac_status_write_enable_i(mac_status_write_enable),
        .mac_mv_i(mac_mv),
        .shifter_status_write_enable_i(shifter_status_write_enable),
        .shifter_ss_i(shifter_ss),
        .interrupt_entry_i(interrupt_entry),
        .interrupt_level_i(interrupt_level),
        .status_restore_i(status_restore),
        .restore_astat_i(restore_astat),
        .restore_mstat_i(restore_mstat),
        .restore_imask_i(restore_imask),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .write_conflict_o(write_conflict),
        .status_push_o(status_push),
        .status_push_astat_o(status_push_astat),
        .status_push_mstat_o(status_push_mstat),
        .status_push_imask_o(status_push_imask)
    );

    always_comb begin
        assert (write_conflict == expected_conflict);
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
            status_push
            == (interrupt_entry && !reset && !write_conflict)
        );
        assert (status_push_astat == astat);
        assert (status_push_mstat == mstat);
        assert (status_push_imask == imask);
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid) begin
            if ($past(reset)) begin
                assert (mstat == 4'h0);
                assert (imask == 4'h0);
            end else if ($past(write_conflict)) begin
                assert (astat == $past(astat));
                assert (mstat == $past(mstat));
                assert (icntl == $past(icntl));
                assert (imask == $past(imask));
            end else if ($past(interrupt_entry)) begin
                assert (astat == $past(astat));
                assert (mstat == $past(mstat));
                assert (icntl == $past(icntl));
                if (!$past(icntl[4])) begin
                    assert (imask == 4'h0);
                end else begin
                    unique case ($past(interrupt_level))
                        2'd0: assert (imask == 4'he);
                        2'd1: assert (imask == 4'hc);
                        2'd2: assert (imask == 4'h8);
                        default: assert (imask == 4'h0);
                    endcase
                end
            end else if ($past(status_restore)) begin
                assert (astat == $past(restore_astat));
                assert (mstat == $past(restore_mstat));
                assert (imask == $past(restore_imask));
                assert (icntl == $past(icntl));
            end else begin
                if ($past(astat_move_write_enable)) begin
                    assert (astat == $past(astat_move_write_data));
                end else if ($past(alu_status_write_enable)) begin
                    assert (
                        astat[3:0]
                        == $past({alu_ac, alu_av, alu_an, alu_az})
                    );
                    assert (astat[7:5] == $past(astat[7:5]));
                    if ($past(alu_as_write_enable)) begin
                        assert (astat[4] == $past(alu_as));
                    end else begin
                        assert (astat[4] == $past(astat[4]));
                    end
                end else if ($past(divide_status_write_enable)) begin
                    assert (astat[5] == $past(divide_aq));
                    assert (astat[7:6] == $past(astat[7:6]));
                    assert (astat[4:0] == $past(astat[4:0]));
                end else if ($past(mac_status_write_enable)) begin
                    assert (astat[6] == $past(mac_mv));
                    assert (astat[7] == $past(astat[7]));
                    assert (astat[5:0] == $past(astat[5:0]));
                end else if ($past(shifter_status_write_enable)) begin
                    assert (astat[7] == $past(shifter_ss));
                    assert (astat[6:0] == $past(astat[6:0]));
                end else begin
                    assert (astat == $past(astat));
                end

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
                if ($past(icntl_move_write_enable)) begin
                    assert (icntl == $past(icntl_move_write_data));
                end else begin
                    assert (icntl == $past(icntl));
                end
                if ($past(imask_move_write_enable)) begin
                    assert (imask == $past(imask_move_write_data));
                end else begin
                    assert (imask == $past(imask));
                end
            end
        end
    end
endmodule

`default_nettype wire
