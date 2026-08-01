`default_nettype none

module adsp2100_counter (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        load_i,
    input  logic        invalidate_i,
    input  logic [13:0] load_data_i,
    input  logic        ce_test_i,
    input  logic        manual_pop_i,
    input  logic [13:0] count_stack_top_data_i,
    input  logic        count_stack_top_valid_i,
    output logic [13:0] cntr_data_o,
    output logic        cntr_valid_o,
    output logic        condition_valid_o,
    output logic        counter_expired_o,
    output logic        not_counter_expired_o,
    output logic        count_stack_push_o,
    output logic [13:0] count_stack_push_data_o,
    output logic        count_stack_pop_o,
    output logic        decrement_o,
    output logic        restore_o,
    output logic        empty_ce_invalidate_o,
    output logic        invalid_ce_test_o,
    output logic        empty_manual_pop_o,
    output logic        write_conflict_o
);
    logic [13:0] cntr_q;
    logic        cntr_valid_q;
    logic [2:0]  action_count;

    always_comb begin
        action_count = (
            {2'b00, load_i}
            + {2'b00, invalidate_i}
            + {2'b00, ce_test_i}
            + {2'b00, manual_pop_i}
        );
    end

    assign write_conflict_o = !reset_i && (action_count > 3'd1);
    assign cntr_data_o = cntr_q;
    assign cntr_valid_o = cntr_valid_q;

    // CE observes cycle-start CNTR. The result is meaningful only while the
    // separate validity state is set.
    assign condition_valid_o = (
        cntr_valid_q
        && !reset_i
        && !write_conflict_o
    );
    assign counter_expired_o = (
        condition_valid_o
        && (cntr_q == 14'h0001)
    );
    assign not_counter_expired_o = (
        condition_valid_o
        && (cntr_q != 14'h0001)
    );

    assign count_stack_push_o = (
        load_i
        && cntr_valid_q
        && !reset_i
        && !write_conflict_o
    );
    assign count_stack_push_data_o = cntr_q;
    assign count_stack_pop_o = (
        !reset_i
        && !write_conflict_o
        && (
            manual_pop_i
            || (ce_test_i && counter_expired_o)
        )
    );
    assign decrement_o = (
        ce_test_i
        && not_counter_expired_o
        && !reset_i
        && !write_conflict_o
    );
    assign restore_o = (
        count_stack_pop_o
        && count_stack_top_valid_i
    );
    assign empty_ce_invalidate_o = (
        ce_test_i
        && counter_expired_o
        && !count_stack_top_valid_i
        && !reset_i
        && !write_conflict_o
    );
    assign invalid_ce_test_o = (
        ce_test_i
        && !cntr_valid_q
        && !reset_i
        && !write_conflict_o
    );
    assign empty_manual_pop_o = (
        manual_pop_i
        && !count_stack_top_valid_i
        && !reset_i
        && !write_conflict_o
    );

    // RESET invalidates CNTR without assigning an undocumented value. Multiple
    // requested CNTR actions are illegal at this boundary and fail closed.
    // An empty manual pop also preserves state because its architectural
    // effect remains unresolved as OQ-013.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            cntr_valid_q <= 1'b0;
        end else if (!write_conflict_o) begin
            if (load_i) begin
                cntr_q <= load_data_i;
                cntr_valid_q <= 1'b1;
            end else if (invalidate_i) begin
                cntr_valid_q <= 1'b0;
            end else if (manual_pop_i) begin
                if (count_stack_top_valid_i) begin
                    cntr_q <= count_stack_top_data_i;
                    cntr_valid_q <= 1'b1;
                end
            end else if (ce_test_i && cntr_valid_q) begin
                if (cntr_q == 14'h0001) begin
                    if (count_stack_top_valid_i) begin
                        cntr_q <= count_stack_top_data_i;
                        cntr_valid_q <= 1'b1;
                    end else begin
                        cntr_valid_q <= 1'b0;
                    end
                end else begin
                    cntr_q <= cntr_q - 14'h0001;
                    cntr_valid_q <= 1'b1;
                end
            end
        end
    end
endmodule

`default_nettype wire
