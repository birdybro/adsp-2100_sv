`default_nettype none

module adsp2100_status_registers (
    input  logic       clk_i,
    input  logic       reset_i,

    input  logic       astat_move_write_enable_i,
    input  logic [7:0] astat_move_write_data_i,
    input  logic       mstat_move_write_enable_i,
    input  logic [3:0] mstat_move_write_data_i,

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

    output logic [7:0] astat_o,
    output logic [3:0] mstat_o,
    output logic       alternate_bank_o,
    output logic       bit_reverse_o,
    output logic       overflow_latch_o,
    output logic       saturate_ar_o,
    output logic       write_conflict_o
);
    logic [7:0] astat_q;
    logic [3:0] mstat_q;
    logic       automatic_astat_conflict;
    logic       automatic_astat_write;
    logic       active_mode_control;

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
    assign write_conflict_o = !reset_i && (
        automatic_astat_conflict
        || (astat_move_write_enable_i && automatic_astat_write)
        || (mstat_move_write_enable_i && active_mode_control)
    );

    assign astat_o = astat_q;
    assign mstat_o = mstat_q;
    assign alternate_bank_o = mstat_q[0];
    assign bit_reverse_o = mstat_q[1];
    assign overflow_latch_o = mstat_q[2];
    assign saturate_ar_o = mstat_q[3];

    // RESET is a sampled architectural-reset indication at this block
    // boundary. The phase-level asynchronous pin behavior belongs in the
    // future sequencer/bus control. The original reset list clears MSTAT but
    // does not define ASTAT, so ASTAT deliberately has no reset assignment.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            mstat_q <= 4'h0;
        end else if (!write_conflict_o) begin
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
        end
    end
endmodule

`default_nettype wire
