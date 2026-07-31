`default_nettype none

module adsp2100_conditional_return_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        pc_setup,
    input logic [13:0] pc_setup_data,
    input logic        astat_setup,
    input logic [7:0]  astat_setup_data,
    input logic        mstat_setup,
    input logic [3:0]  mstat_setup_data,
    input logic        imask_setup,
    input logic [3:0]  imask_setup_data,
    input logic        counter_setup,
    input logic [13:0] counter_setup_data,
    input logic        pc_stack_setup,
    input logic [13:0] pc_stack_setup_data,
    input logic        status_stack_setup,
    input logic [15:0] status_stack_setup_data
);
    logic        class_valid;
    logic        action_valid;
    logic        interrupt_return;
    logic [3:0]  condition;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic        invalid_condition_state;
    logic        invalid_return_context;
    logic        condition_known;
    logic        condition_true;
    logic [13:0] pc;
    logic        pc_write;
    logic        explicit_transfer;
    logic        pc_stack_pop;
    logic        pc_stack_pop_valid;
    logic [13:0] pc_stack_top;
    logic        pc_stack_top_valid;
    logic [4:0]  pc_stack_depth;
    logic        pc_stack_overflow;
    logic        status_stack_pop;
    logic        status_stack_pop_valid;
    logic [15:0] status_stack_top;
    logic        status_stack_top_valid;
    logic [2:0]  status_stack_depth;
    logic        status_stack_overflow;
    logic        status_restored;
    logic [7:0]  astat;
    logic        astat_valid;
    logic [3:0]  mstat;
    logic [3:0]  imask;
    logic [13:0] cntr;
    logic        cntr_valid;
    logic        counter_test;
    logic        counter_decrement;
    logic        counter_restore;
    logic        count_stack_push;
    logic [13:0] count_stack_top;
    logic        count_stack_top_valid;
    logic [2:0]  count_stack_depth;
    logic        count_stack_overflow;
    logic [7:0]  sstat;
    logic        pm_data_access;
    logic        dm_access;
    logic        expected_class;
    logic [3:0]  setup_count;
    logic        expected_conflict;
    logic        raw_condition_context_valid;
    logic        raw_condition_true;
    logic        expected_return_context_valid;
    logic        expected_invalid_return_context;
    logic        past_valid;

    assign expected_class = ((opcode & 24'hffffe0) == 24'h0a0000);
    assign setup_count = (
        {3'b000, pc_setup}
        + {3'b000, astat_setup}
        + {3'b000, mstat_setup}
        + {3'b000, imask_setup}
        + {3'b000, counter_setup}
        + {3'b000, pc_stack_setup}
        + {3'b000, status_stack_setup}
    );
    assign expected_conflict = !reset && (
        (execute && setup_count != 4'd0) || setup_count > 4'd1
    );
    assign raw_condition_context_valid = (
        (opcode[3:0] == 4'hf)
        || ((opcode[3:0] == 4'he) ? cntr_valid : astat_valid)
    );
    assign expected_return_context_valid = (
        pc_stack_top_valid
        && (!opcode[4] || status_stack_top_valid)
    );
    assign expected_invalid_return_context = (
        !reset && execute && expected_class && !expected_conflict
        && raw_condition_context_valid && raw_condition_true
        && !expected_return_context_valid
    );

    always_comb begin
        unique case (opcode[3:0])
            4'h0: raw_condition_true = astat[0];
            4'h1: raw_condition_true = !astat[0];
            4'h2: raw_condition_true = !(astat[1] ^ astat[2]) && !astat[0];
            4'h3: raw_condition_true = (astat[1] ^ astat[2]) || astat[0];
            4'h4: raw_condition_true = astat[1] ^ astat[2];
            4'h5: raw_condition_true = !(astat[1] ^ astat[2]);
            4'h6: raw_condition_true = astat[2];
            4'h7: raw_condition_true = !astat[2];
            4'h8: raw_condition_true = astat[3];
            4'h9: raw_condition_true = !astat[3];
            4'ha: raw_condition_true = astat[6];
            4'hb: raw_condition_true = !astat[6];
            4'hc: raw_condition_true = astat[1];
            4'hd: raw_condition_true = !astat[1];
            4'he: raw_condition_true = cntr != 14'h0001;
            default: raw_condition_true = 1'b1;
        endcase
    end

    adsp2100_conditional_return_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .pc_setup_write_i(pc_setup),
        .pc_setup_data_i(pc_setup_data),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .imask_setup_write_i(imask_setup),
        .imask_setup_data_i(imask_setup_data),
        .counter_setup_write_i(counter_setup),
        .counter_setup_data_i(counter_setup_data),
        .pc_stack_setup_push_i(pc_stack_setup),
        .pc_stack_setup_data_i(pc_stack_setup_data),
        .status_stack_setup_push_i(status_stack_setup),
        .status_stack_setup_data_i(status_stack_setup_data),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .interrupt_return_o(interrupt_return),
        .condition_o(condition),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .invalid_condition_state_o(invalid_condition_state),
        .invalid_return_context_o(invalid_return_context),
        .condition_known_o(condition_known),
        .condition_true_o(condition_true),
        .pc_o(pc),
        .pc_write_o(pc_write),
        .explicit_transfer_o(explicit_transfer),
        .pc_stack_pop_o(pc_stack_pop),
        .pc_stack_pop_valid_o(pc_stack_pop_valid),
        .pc_stack_top_o(pc_stack_top),
        .pc_stack_top_valid_o(pc_stack_top_valid),
        .pc_stack_depth_o(pc_stack_depth),
        .pc_stack_overflow_o(pc_stack_overflow),
        .status_stack_pop_o(status_stack_pop),
        .status_stack_pop_valid_o(status_stack_pop_valid),
        .status_stack_top_o(status_stack_top),
        .status_stack_top_valid_o(status_stack_top_valid),
        .status_stack_depth_o(status_stack_depth),
        .status_stack_overflow_o(status_stack_overflow),
        .status_restored_o(status_restored),
        .astat_o(astat),
        .astat_valid_o(astat_valid),
        .mstat_o(mstat),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .counter_test_o(counter_test),
        .counter_decrement_o(counter_decrement),
        .counter_restore_o(counter_restore),
        .count_stack_push_o(count_stack_push),
        .count_stack_top_o(count_stack_top),
        .count_stack_top_valid_o(count_stack_top_valid),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .sstat_o(sstat),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_class);
        assert (interrupt_return == (expected_class ? opcode[4] : 1'b0));
        assert (condition == (expected_class ? opcode[3:0] : 4'h0));
        assert (integration_conflict == expected_conflict);
        assert (invalid_opcode == (!reset && execute && !expected_class));
        assert (
            condition_known
            == (
                !reset && execute && expected_class && !expected_conflict
                && raw_condition_context_valid
            )
        );
        assert (invalid_return_context == expected_invalid_return_context);
        assert (condition_known == (boundary_valid || invalid_return_context));
        assert (!(boundary_valid && invalid_return_context));
        assert (
            invalid_condition_state
            == (
                !reset && execute && expected_class && !expected_conflict
                && !raw_condition_context_valid
            )
        );
        assert (condition_true == (boundary_valid && raw_condition_true));
        assert (pc_write == boundary_valid);
        assert (explicit_transfer == condition_true);
        assert (pc_stack_pop == explicit_transfer);
        assert (pc_stack_pop_valid == pc_stack_pop);
        assert (status_stack_pop == (condition_true && interrupt_return));
        assert (status_stack_pop_valid == status_stack_pop);
        assert (status_restored == status_stack_pop_valid);
        assert (!(counter_test || counter_decrement || counter_restore));
        assert (!count_stack_push || counter_setup);
        assert (!internal_conflict);
        assert (!pm_data_access && !dm_access);
        assert (pc_stack_depth <= 5'd16);
        assert (status_stack_depth <= 3'd4);
        assert (count_stack_depth <= 3'd4);
        assert (pc_stack_top_valid == (pc_stack_depth != 5'd0));
        assert (status_stack_top_valid == (status_stack_depth != 3'd0));
        assert (count_stack_top_valid == (count_stack_depth != 3'd0));
        assert (sstat[0] == !pc_stack_top_valid);
        assert (sstat[1] == pc_stack_overflow);
        assert (sstat[2] == !count_stack_top_valid);
        assert (sstat[3] == count_stack_overflow);
        assert (sstat[4] == !status_stack_top_valid);
        assert (sstat[5] == status_stack_overflow);
        assert (sstat[7:6] == 2'b01);
        cover (boundary_valid && !condition_true);
        cover (condition_true && !interrupt_return && pc_stack_top == 14'h1555);
        cover (condition_true && interrupt_return);
        cover (invalid_return_context);
        cover (status_restored);
        cover (boundary_valid && condition == 4'he && condition_true);
        cover (astat == 8'h55 && mstat == 4'ha && imask == 4'h5);
        cover (cntr == 14'h1555 && count_stack_top == 14'h0aaa);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (pc == 14'h0004);
            assert (!astat_valid);
            assert (mstat == 4'h0);
            assert (imask == 4'h0);
            assert (!cntr_valid);
            assert (pc_stack_depth == 5'd0);
            assert (status_stack_depth == 3'd0);
            assert (count_stack_depth == 3'd0);
        end else if ($past(boundary_valid)) begin
            assert (
                pc
                == (
                    $past(condition_true)
                    ? $past(pc_stack_top)
                    : ($past(pc) + 14'h0001)
                )
            );
            if ($past(status_stack_pop_valid)) begin
                assert (astat == $past(status_stack_top[15:8]));
                assert (mstat == $past(status_stack_top[7:4]));
                assert (imask == $past(status_stack_top[3:0]));
                assert (astat_valid);
            end
        end else if ($past(
            !execute && pc_setup && !astat_setup && !mstat_setup
            && !imask_setup && !counter_setup && !pc_stack_setup
            && !status_stack_setup
        )) begin
            assert (pc == $past(pc_setup_data));
        end else begin
            assert (pc == $past(pc));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
