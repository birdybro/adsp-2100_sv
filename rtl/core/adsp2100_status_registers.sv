`default_nettype none

module adsp2100_status_registers (
    input  logic       clk_i,
    input  logic       reset_i,

    input  logic       astat_move_write_enable_i,
    input  logic [7:0] astat_move_write_data_i,
    input  logic       mstat_move_write_enable_i,
    input  logic [3:0] mstat_move_write_data_i,
    input  logic       icntl_move_write_enable_i,
    input  logic [4:0] icntl_move_write_data_i,
    input  logic       imask_move_write_enable_i,
    input  logic [3:0] imask_move_write_data_i,

    input  logic [1:0] mode_sr_i,
    input  logic [1:0] mode_br_i,
    input  logic [1:0] mode_ol_i,
    input  logic [1:0] mode_as_i,

    input  logic       alu_status_write_enable_i,
    input  logic       alu_az_i,
    input  logic       alu_an_i,
    input  logic       alu_av_i,
    input  logic       alu_ac_i,
    input  logic       alu_as_write_enable_i,
    input  logic       alu_as_i,

    input  logic       divide_status_write_enable_i,
    input  logic       divide_aq_i,
    input  logic       mac_status_write_enable_i,
    input  logic       mac_mv_i,
    input  logic       shifter_status_write_enable_i,
    input  logic       shifter_ss_i,

    input  logic       interrupt_entry_i,
    input  logic [1:0] interrupt_level_i,
    input  logic       status_restore_i,
    input  logic [7:0] restore_astat_i,
    input  logic [3:0] restore_mstat_i,
    input  logic [3:0] restore_imask_i,

    output logic [7:0] astat_o,
    output logic [3:0] mstat_o,
    output logic [4:0] icntl_o,
    output logic [3:0] imask_o,
    output logic       alternate_bank_o,
    output logic       bit_reverse_o,
    output logic       overflow_latch_o,
    output logic       saturate_ar_o,
    output logic       write_conflict_o,
    output logic       status_push_o,
    output logic [7:0] status_push_astat_o,
    output logic [3:0] status_push_mstat_o,
    output logic [3:0] status_push_imask_o
);
    logic [7:0] astat_q;
    logic [3:0] mstat_q;
    logic [4:0] icntl_q;
    logic [3:0] imask_q;
    logic       automatic_astat_conflict;
    logic       automatic_astat_write;
    logic       active_mode_control;
    logic       ordinary_state_write;
    logic [3:0] nested_imask;

    assign automatic_astat_write = (
        alu_status_write_enable_i
        || divide_status_write_enable_i
        || mac_status_write_enable_i
        || shifter_status_write_enable_i
    );
    assign automatic_astat_conflict = (
        (
            alu_status_write_enable_i
            && (
                divide_status_write_enable_i
                || mac_status_write_enable_i
                || shifter_status_write_enable_i
            )
        )
        || (
            divide_status_write_enable_i
            && (
                mac_status_write_enable_i
                || shifter_status_write_enable_i
            )
        )
        || (
            mac_status_write_enable_i
            && shifter_status_write_enable_i
        )
    );
    assign active_mode_control = (
        mode_sr_i[1]
        || mode_br_i[1]
        || mode_ol_i[1]
        || mode_as_i[1]
    );
    assign ordinary_state_write = (
        astat_move_write_enable_i
        || mstat_move_write_enable_i
        || icntl_move_write_enable_i
        || imask_move_write_enable_i
        || automatic_astat_write
        || active_mode_control
    );
    assign write_conflict_o = !reset_i && (
        automatic_astat_conflict
        || (astat_move_write_enable_i && automatic_astat_write)
        || (mstat_move_write_enable_i && active_mode_control)
        || (
            status_restore_i
            && (ordinary_state_write || interrupt_entry_i)
        )
    );

    always_comb begin
        unique case (interrupt_level_i)
            2'd0: nested_imask = 4'he;
            2'd1: nested_imask = 4'hc;
            2'd2: nested_imask = 4'h8;
            default: nested_imask = 4'h0;
        endcase
    end

    assign astat_o = astat_q;
    assign mstat_o = mstat_q;
    assign icntl_o = icntl_q;
    assign imask_o = imask_q;
    assign alternate_bank_o = mstat_q[0];
    assign bit_reverse_o = mstat_q[1];
    assign overflow_latch_o = mstat_q[2];
    assign saturate_ar_o = mstat_q[3];
    assign status_push_o = (
        interrupt_entry_i
        && !reset_i
        && !write_conflict_o
    );
    assign status_push_astat_o = astat_q;
    assign status_push_mstat_o = mstat_q;
    assign status_push_imask_o = imask_q;

    // RESET is a sampled architectural-reset indication at this block
    // boundary. The phase-level asynchronous pin behavior belongs in the
    // future sequencer/bus control. The original reset list clears MSTAT and
    // IMASK but does not define ASTAT or ICNTL, so those two registers
    // deliberately have no reset assignment.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            mstat_q <= 4'h0;
            imask_q <= 4'h0;
        end else if (!write_conflict_o) begin
            if (interrupt_entry_i) begin
                // The instruction present when an interrupt is recognized is
                // aborted. The pre-entry status is exposed on status_push_*,
                // while only IMASK changes in the live register set.
                imask_q <= icntl_q[4] ? nested_imask : 4'h0;
            end else if (status_restore_i) begin
                astat_q <= restore_astat_i;
                mstat_q <= restore_mstat_i;
                imask_q <= restore_imask_i;
            end else begin
                if (astat_move_write_enable_i) begin
                    astat_q <= astat_move_write_data_i;
                end else if (alu_status_write_enable_i) begin
                    astat_q[0] <= alu_az_i;
                    astat_q[1] <= alu_an_i;
                    astat_q[2] <= alu_av_i;
                    astat_q[3] <= alu_ac_i;
                    if (alu_as_write_enable_i) begin
                        astat_q[4] <= alu_as_i;
                    end
                end else if (divide_status_write_enable_i) begin
                    astat_q[5] <= divide_aq_i;
                end else if (mac_status_write_enable_i) begin
                    astat_q[6] <= mac_mv_i;
                end else if (shifter_status_write_enable_i) begin
                    astat_q[7] <= shifter_ss_i;
                end

                if (mstat_move_write_enable_i) begin
                    mstat_q <= mstat_move_write_data_i;
                end else begin
                    if (mode_sr_i[1]) begin
                        mstat_q[0] <= mode_sr_i[0];
                    end
                    if (mode_br_i[1]) begin
                        mstat_q[1] <= mode_br_i[0];
                    end
                    if (mode_ol_i[1]) begin
                        mstat_q[2] <= mode_ol_i[0];
                    end
                    if (mode_as_i[1]) begin
                        mstat_q[3] <= mode_as_i[0];
                    end
                end
                if (icntl_move_write_enable_i) begin
                    icntl_q <= icntl_move_write_data_i;
                end
                if (imask_move_write_enable_i) begin
                    imask_q <= imask_move_write_data_i;
                end
            end
        end
    end
endmodule

`default_nettype wire
