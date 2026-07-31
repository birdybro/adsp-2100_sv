`default_nettype none

module adsp2100_stack_control_slice_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        astat_write,
    input logic [7:0]  astat_write_data,
    input logic        mstat_write,
    input logic [3:0]  mstat_write_data,
    input logic        imask_write,
    input logic [3:0]  imask_write_data,
    input logic        counter_load,
    input logic [13:0] counter_load_data,
    input logic        pc_push,
    input logic [13:0] pc_push_data,
    input logic        loop_push,
    input logic [17:0] loop_push_data
);
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [1:0]  status_operation;
    logic        count_pop;
    logic        loop_pop;
    logic        pc_pop;
    logic        has_effect;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic [3:0]  imask;
    logic        alternate_bank;
    logic        bit_reverse;
    logic        overflow_latch;
    logic        saturate_ar;
    logic [13:0] cntr_data;
    logic        cntr_valid;
    logic        counter_restore;
    logic        counter_empty_manual_pop;
    logic [13:0] pc_top_data;
    logic [13:0] count_top_data;
    logic [17:0] loop_top_data;
    logic [15:0] status_top_data;
    logic [3:0]  stack_top_valid;
    logic [4:0]  pc_depth;
    logic [2:0]  count_depth;
    logic [2:0]  loop_depth;
    logic [2:0]  status_depth;
    logic [3:0]  stack_empty;
    logic [3:0]  stack_overflow;
    logic [3:0]  stack_pop_valid;
    logic [3:0]  stack_push_accepted;
    logic [3:0]  stack_overflow_event;
    logic [3:0]  stack_empty_pop;
    logic [7:0]  sstat;
    logic        type_26_valid;
    logic        setup_action;
    logic        past_valid;

    assign type_26_valid = (
        (opcode & 24'hffffe0) == 24'h040000
    );
    assign setup_action = (
        astat_write
        || mstat_write
        || imask_write
        || counter_load
        || pc_push
        || loop_push
    );

    adsp2100_stack_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .astat_write_i(astat_write),
        .astat_write_data_i(astat_write_data),
        .mstat_write_i(mstat_write),
        .mstat_write_data_i(mstat_write_data),
        .imask_write_i(imask_write),
        .imask_write_data_i(imask_write_data),
        .counter_load_i(counter_load),
        .counter_load_data_i(counter_load_data),
        .pc_push_i(pc_push),
        .pc_push_data_i(pc_push_data),
        .loop_push_i(loop_push),
        .loop_push_data_i(loop_push_data),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .status_operation_o(status_operation),
        .count_pop_o(count_pop),
        .loop_pop_o(loop_pop),
        .pc_pop_o(pc_pop),
        .has_effect_o(has_effect),
        .astat_o(astat),
        .mstat_o(mstat),
        .imask_o(imask),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .cntr_data_o(cntr_data),
        .cntr_valid_o(cntr_valid),
        .counter_restore_o(counter_restore),
        .counter_empty_manual_pop_o(counter_empty_manual_pop),
        .pc_top_data_o(pc_top_data),
        .count_top_data_o(count_top_data),
        .loop_top_data_o(loop_top_data),
        .status_top_data_o(status_top_data),
        .stack_top_valid_o(stack_top_valid),
        .pc_depth_o(pc_depth),
        .count_depth_o(count_depth),
        .loop_depth_o(loop_depth),
        .status_depth_o(status_depth),
        .stack_empty_o(stack_empty),
        .stack_overflow_o(stack_overflow),
        .stack_pop_valid_o(stack_pop_valid),
        .stack_push_accepted_o(stack_push_accepted),
        .stack_overflow_event_o(stack_overflow_event),
        .stack_empty_pop_o(stack_empty_pop),
        .sstat_o(sstat)
    );

    always_comb begin
        assert (
            boundary_valid
            == (execute && type_26_valid && !setup_action && !reset)
        );
        assert (
            invalid_opcode
            == (execute && !type_26_valid && !reset)
        );
        assert (
            integration_conflict
            == (execute && setup_action && !reset)
        );
        assert (!internal_conflict);

        assert (
            status_operation
            == (boundary_valid ? opcode[1:0] : 2'b00)
        );
        assert (count_pop == (boundary_valid && opcode[2]));
        assert (loop_pop == (boundary_valid && opcode[3]));
        assert (pc_pop == (boundary_valid && opcode[4]));
        assert (
            has_effect
            == (boundary_valid && (opcode[4:1] != 4'b0000))
        );

        assert (stack_empty == ~stack_top_valid);
        assert (pc_depth <= 5'd16);
        assert (count_depth <= 3'd4);
        assert (loop_depth <= 3'd4);
        assert (status_depth <= 3'd4);
        assert (stack_top_valid[0] == (pc_depth != 5'd0));
        assert (stack_top_valid[1] == (count_depth != 3'd0));
        assert (stack_top_valid[2] == (loop_depth != 3'd0));
        assert (stack_top_valid[3] == (status_depth != 3'd0));
        assert (
            sstat
            == {
                stack_overflow[2],
                stack_empty[2],
                stack_overflow[3],
                stack_empty[3],
                stack_overflow[1],
                stack_empty[1],
                stack_overflow[0],
                stack_empty[0]
            }
        );
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
            (stack_pop_valid & ~{
                boundary_valid && (opcode[1:0] == 2'b11),
                loop_pop,
                count_pop,
                pc_pop
            })
            == 4'b0000
        );
        assert (
            (stack_empty_pop & ~{
                boundary_valid && (opcode[1:0] == 2'b11),
                loop_pop,
                count_pop,
                pc_pop
            })
            == 4'b0000
        );
        assert (
            (stack_push_accepted & ~{
                boundary_valid && (opcode[1:0] == 2'b10),
                loop_push && !integration_conflict && !reset,
                counter_load && !integration_conflict && !reset,
                pc_push && !integration_conflict && !reset
            })
            == 4'b0000
        );
        assert (!counter_restore || stack_pop_valid[1]);
        assert (
            !counter_empty_manual_pop
            || (count_pop && stack_empty[1])
        );

        cover (boundary_valid && status_operation == 2'b10);
        cover (boundary_valid && status_operation == 2'b11);
        cover (boundary_valid && count_pop && loop_pop && pc_pop);
        cover (stack_overflow_event != 4'b0000);
        cover (stack_empty_pop == 4'b1111);
        cover (integration_conflict);
        cover (invalid_opcode);
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
            assert (imask == 4'h0);
            assert (!cntr_valid);
            assert (pc_depth == 5'd0);
            assert (count_depth == 3'd0);
            assert (loop_depth == 3'd0);
            assert (status_depth == 3'd0);
            assert (stack_overflow == 4'b0000);
        end else if (
            $past(integration_conflict)
            || $past(invalid_opcode)
        ) begin
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
            assert (imask == $past(imask));
            assert (cntr_valid == $past(cntr_valid));
            if ($past(cntr_valid)) begin
                assert (cntr_data == $past(cntr_data));
            end
            assert (pc_depth == $past(pc_depth));
            assert (count_depth == $past(count_depth));
            assert (loop_depth == $past(loop_depth));
            assert (status_depth == $past(status_depth));
            assert (stack_overflow == $past(stack_overflow));
            if ($past(stack_top_valid[0])) begin
                assert (pc_top_data == $past(pc_top_data));
            end
            if ($past(stack_top_valid[2])) begin
                assert (loop_top_data == $past(loop_top_data));
            end
        end else if (
            $past(boundary_valid)
            && ($past(opcode[4:1]) == 4'b0000)
        ) begin
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
            assert (imask == $past(imask));
            assert (cntr_valid == $past(cntr_valid));
            if ($past(cntr_valid)) begin
                assert (cntr_data == $past(cntr_data));
            end
            assert (pc_depth == $past(pc_depth));
            assert (count_depth == $past(count_depth));
            assert (loop_depth == $past(loop_depth));
            assert (status_depth == $past(status_depth));
            assert (stack_overflow == $past(stack_overflow));
            if ($past(stack_top_valid[0])) begin
                assert (pc_top_data == $past(pc_top_data));
            end
            if ($past(stack_top_valid[2])) begin
                assert (loop_top_data == $past(loop_top_data));
            end
        end

        if (
            past_valid
            && !$past(reset)
            && $past(stack_pop_valid[3])
        ) begin
            assert (
                {astat, mstat, imask}
                == $past(status_top_data)
            );
        end
        if (
            past_valid
            && !$past(reset)
            && $past(counter_restore)
        ) begin
            assert (cntr_valid);
            assert (cntr_data == $past(count_top_data));
        end
        if (
            past_valid
            && !$past(reset)
            && $past(stack_push_accepted[3])
        ) begin
            assert (status_top_data == $past({astat, mstat, imask}));
        end
        if (
            past_valid
            && !$past(reset)
            && $past(counter_load)
            && !$past(integration_conflict)
        ) begin
            assert (cntr_valid);
            assert (cntr_data == $past(counter_load_data));
        end

        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
