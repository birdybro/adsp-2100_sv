`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_architectural_state;
    logic clk;
    logic reset;
    logic move_write;
    logic move_data_valid;
    logic [5:0] move_code;
    logic [15:0] move_data;
    logic [5:0] read_code;
    logic [15:0] read_data;
    logic [5:0] probe_code;
    logic [15:0] probe_data;
    logic [3:0] dreg_read_address;
    logic [15:0] dreg_read_data;
    logic [3:0] dreg_read_address_2;
    logic [15:0] dreg_read_data_2;
    logic dreg_write_enable_1;
    logic [3:0] dreg_write_address_1;
    logic [15:0] dreg_write_data_1;
    logic dreg_write_enable_2;
    logic [3:0] dreg_write_address_2;
    logic [15:0] dreg_write_data_2;
    logic alu_write_enable;
    logic alu_destination_feedback;
    logic [15:0] alu_result;
    logic mac_write_enable;
    logic mac_destination_feedback;
    logic [39:0] mac_result;
    logic shifter_sr_write_enable;
    logic [31:0] shifter_sr_result;
    logic shifter_se_write_enable;
    logic [7:0] shifter_se_result;
    logic shifter_sb_write_enable;
    logic [4:0] shifter_sb_result;
    logic dag_i_write_enable;
    logic [2:0] dag_i_write_address;
    logic [13:0] dag_i_write_data;
    logic dag_i_write_result_valid;
    logic dag_execution_read;
    logic [2:0] dag_i_l_read_address;
    logic [2:0] dag_m_read_address;
    logic [13:0] dag_i_read_data;
    logic dag_i_read_valid;
    logic [13:0] dag_m_read_data;
    logic dag_m_read_valid;
    logic [13:0] dag_l_read_data;
    logic dag_l_read_valid;
    logic [1:0] mode_sr;
    logic [1:0] mode_br;
    logic [1:0] mode_ol;
    logic [1:0] mode_as;
    logic alu_status_write_enable;
    logic alu_az;
    logic alu_an;
    logic alu_av;
    logic alu_ac;
    logic alu_as_write_enable;
    logic alu_as;
    logic divide_status_write_enable;
    logic divide_aq;
    logic mac_status_write_enable;
    logic mac_mv;
    logic shifter_status_write_enable;
    logic shifter_ss;
    logic [1:0] stack_status_operation;
    logic stack_counter_ce_test;
    logic stack_count_pop;
    logic stack_loop_pop;
    logic stack_pc_push;
    logic [13:0] stack_pc_push_data;
    logic stack_pc_pop;
    logic invalid_move_write;
    logic internal_conflict;
    logic count_stack_push;
    logic [13:0] count_stack_push_data;
    logic [2:0] count_stack_depth;
    logic count_stack_overflow;
    logic [13:0] pc_stack_top;
    logic pc_stack_top_valid;
    logic [7:0] astat;
    logic [3:0] mstat;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic [13:0] cntr;
    logic cntr_valid;
    logic not_counter_expired;
    logic [7:0] px;
    logic [7:0] sstat;
    logic alternate_bank;
    logic bit_reverse;
    logic overflow_latch;
    logic saturate_ar;
    logic [15:0] af;
    logic [15:0] mf;
    logic [39:0] mr;
    logic [7:0] se;
    logic [4:0] sb;
    logic [31:0] sr;
    logic unused_observation;

    task automatic clear_actions;
        begin
            move_write = 1'b0;
            move_data_valid = 1'b1;
            move_code = 6'h00;
            move_data = 16'h0000;
            dreg_write_enable_1 = 1'b0;
            dreg_write_address_1 = 4'h0;
            dreg_write_data_1 = 16'h0000;
            dreg_write_enable_2 = 1'b0;
            dreg_write_address_2 = 4'h0;
            dreg_write_data_2 = 16'h0000;
            alu_write_enable = 1'b0;
            alu_destination_feedback = 1'b0;
            alu_result = 16'h0000;
            mac_write_enable = 1'b0;
            mac_destination_feedback = 1'b0;
            mac_result = 40'h0000000000;
            shifter_sr_write_enable = 1'b0;
            shifter_sr_result = 32'h00000000;
            shifter_se_write_enable = 1'b0;
            shifter_se_result = 8'h00;
            shifter_sb_write_enable = 1'b0;
            shifter_sb_result = 5'h00;
            dag_i_write_enable = 1'b0;
            dag_i_write_address = 3'b000;
            dag_i_write_data = 14'h0000;
            dag_i_write_result_valid = 1'b0;
            dag_execution_read = 1'b0;
            dag_i_l_read_address = 3'b000;
            dag_m_read_address = 3'b000;
            mode_sr = 2'b00;
            mode_br = 2'b00;
            mode_ol = 2'b00;
            mode_as = 2'b00;
            alu_status_write_enable = 1'b0;
            alu_az = 1'b0;
            alu_an = 1'b0;
            alu_av = 1'b0;
            alu_ac = 1'b0;
            alu_as_write_enable = 1'b0;
            alu_as = 1'b0;
            divide_status_write_enable = 1'b0;
            divide_aq = 1'b0;
            mac_status_write_enable = 1'b0;
            mac_mv = 1'b0;
            shifter_status_write_enable = 1'b0;
            shifter_ss = 1'b0;
            stack_status_operation = 2'b00;
            stack_counter_ce_test = 1'b0;
            stack_count_pop = 1'b0;
            stack_loop_pop = 1'b0;
            stack_pc_push = 1'b0;
            stack_pc_push_data = 14'h0000;
            stack_pc_pop = 1'b0;
        end
    endtask

    task automatic tick;
        begin
            #4;
            clk = 1'b1;
            #1;
            clk = 1'b0;
            #5;
        end
    endtask

    task automatic move_register(
        input logic [5:0] code,
        input logic [15:0] data
    );
        begin
            clear_actions();
            move_write = 1'b1;
            move_code = code;
            move_data = data;
            tick();
        end
    endtask

    task automatic expect16(
        input logic [15:0] actual,
        input logic [15:0] expected,
        input string label
    );
        begin
            if (actual !== expected) begin
                $fatal(
                    1,
                    "%s expected=%04h actual=%04h",
                    label,
                    expected,
                    actual
                );
            end
        end
    endtask

    adsp2100_architectural_state dut (
        .clk_i(clk),
        .reset_i(reset),
        .move_write_i(move_write),
        .move_data_valid_i(move_data_valid),
        .move_code_i(move_code),
        .move_data_i(move_data),
        .read_code_i(read_code),
        .read_data_o(read_data),
        .probe_code_i(probe_code),
        .probe_data_o(probe_data),
        .dreg_read_address_i(dreg_read_address),
        .dreg_read_data_o(dreg_read_data),
        .dreg_read_address_2_i(dreg_read_address_2),
        .dreg_read_data_2_o(dreg_read_data_2),
        .dreg_write_enable_1_i(dreg_write_enable_1),
        .dreg_write_address_1_i(dreg_write_address_1),
        .dreg_write_data_1_i(dreg_write_data_1),
        .dreg_write_enable_2_i(dreg_write_enable_2),
        .dreg_write_address_2_i(dreg_write_address_2),
        .dreg_write_data_2_i(dreg_write_data_2),
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
        .dag_i_write_enable_i(dag_i_write_enable),
        .dag_i_write_address_i(dag_i_write_address),
        .dag_i_write_data_i(dag_i_write_data),
        .dag_i_write_result_valid_i(dag_i_write_result_valid),
        .dag_execution_read_i(dag_execution_read),
        .dag_i_l_read_address_i(dag_i_l_read_address),
        .dag_m_read_address_i(dag_m_read_address),
        .dag_i_read_data_o(dag_i_read_data),
        .dag_i_read_valid_o(dag_i_read_valid),
        .dag_m_read_data_o(dag_m_read_data),
        .dag_m_read_valid_o(dag_m_read_valid),
        .dag_l_read_data_o(dag_l_read_data),
        .dag_l_read_valid_o(dag_l_read_valid),
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
        .stack_status_operation_i(stack_status_operation),
        .stack_counter_ce_test_i(stack_counter_ce_test),
        .stack_count_pop_i(stack_count_pop),
        .stack_loop_pop_i(stack_loop_pop),
        .stack_pc_push_i(stack_pc_push),
        .stack_pc_push_data_i(stack_pc_push_data),
        .stack_pc_pop_i(stack_pc_pop),
        .invalid_move_write_o(invalid_move_write),
        .internal_conflict_o(internal_conflict),
        .count_stack_push_o(count_stack_push),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .pc_stack_top_o(pc_stack_top),
        .pc_stack_top_valid_o(pc_stack_top_valid),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .not_counter_expired_o(not_counter_expired),
        .px_o(px),
        .sstat_o(sstat),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar),
        .af_o(af),
        .mf_o(mf),
        .mr_o(mr),
        .se_o(se),
        .sb_o(sb),
        .sr_o(sr)
    );

    assign unused_observation = ^{
        probe_data, invalid_move_write, count_stack_push,
        count_stack_push_data, count_stack_depth, count_stack_overflow,
        icntl, imask, cntr, cntr_valid, not_counter_expired, px, sstat,
        bit_reverse,
        overflow_latch, saturate_ar, mf
    };

    initial begin
        clk = 1'b0;
        reset = 1'b1;
        read_code = 6'h00;
        probe_code = 6'h00;
        dreg_read_address = 4'h0;
        dreg_read_address_2 = 4'h0;
        clear_actions();
        tick();
        reset = 1'b0;
        if (mstat !== 4'h0 || alternate_bank !== 1'b0) begin
            $fatal(1, "reset did not select the primary register bank");
        end

        // Initialize three primary-bank DREGs through the move boundary.
        move_register(6'h00, 16'h1111);
        move_register(6'h01, 16'h2222);
        move_register(6'h02, 16'h3333);

        // Reads remain at the cycle-start values while all three independent
        // DREG write ports are active, then expose all writes after the edge.
        clear_actions();
        move_write = 1'b1;
        move_code = 6'h00;
        move_data = 16'haaaa;
        dreg_write_enable_1 = 1'b1;
        dreg_write_address_1 = 4'h1;
        dreg_write_data_1 = 16'hbbbb;
        dreg_write_enable_2 = 1'b1;
        dreg_write_address_2 = 4'h2;
        dreg_write_data_2 = 16'hcccc;
        read_code = 6'h00;
        probe_code = 6'h01;
        dreg_read_address = 4'h2;
        dreg_read_address_2 = 4'h0;
        #1;
        expect16(read_data, 16'h1111, "old move read");
        expect16(probe_data, 16'h2222, "old probe read");
        expect16(dreg_read_data, 16'h3333, "old execution read");
        expect16(dreg_read_data_2, 16'h1111, "old second execution read");
        if (internal_conflict !== 1'b0) begin
            $fatal(1, "nonoverlapping DREG writes reported conflict");
        end
        tick();
        expect16(read_data, 16'haaaa, "new move read");
        expect16(probe_data, 16'hbbbb, "new probe read");
        expect16(dreg_read_data, 16'hcccc, "new execution read");
        expect16(dreg_read_data_2, 16'haaaa, "new second execution read");

        // The computational result ports update the selected bank only.
        clear_actions();
        alu_write_enable = 1'b1;
        alu_destination_feedback = 1'b1;
        alu_result = 16'h1357;
        tick();
        expect16(af, 16'h1357, "primary AF");

        clear_actions();
        mac_write_enable = 1'b1;
        mac_destination_feedback = 1'b0;
        mac_result = 40'h89abcdef01;
        tick();
        if (mr !== 40'h89abcdef01) begin
            $fatal(1, "MR write mismatch");
        end

        clear_actions();
        shifter_sr_write_enable = 1'b1;
        shifter_sr_result = 32'h76543210;
        tick();
        if (sr !== 32'h76543210) begin
            $fatal(1, "SR write mismatch");
        end
        clear_actions();
        shifter_se_write_enable = 1'b1;
        shifter_se_result = 8'h8f;
        tick();
        if (se !== 8'h8f) begin
            $fatal(1, "SE write mismatch");
        end
        clear_actions();
        shifter_sb_write_enable = 1'b1;
        shifter_sb_result = 5'h1b;
        tick();
        if (sb !== 5'h1b) begin
            $fatal(1, "SB write mismatch");
        end

        // Automatic status actions and mode controls share the same owner.
        move_register(6'h30, 16'h0000);
        clear_actions();
        alu_status_write_enable = 1'b1;
        alu_az = 1'b1;
        alu_an = 1'b0;
        alu_av = 1'b1;
        alu_ac = 1'b1;
        alu_as_write_enable = 1'b1;
        alu_as = 1'b1;
        tick();
        if (astat !== 8'h1d) begin
            $fatal(1, "ALU ASTAT update mismatch expected=1d actual=%02h", astat);
        end
        clear_actions();
        mac_status_write_enable = 1'b1;
        mac_mv = 1'b1;
        tick();
        clear_actions();
        shifter_status_write_enable = 1'b1;
        shifter_ss = 1'b1;
        tick();
        if (astat !== 8'hdd) begin
            $fatal(1, "MAC/shifter ASTAT update mismatch");
        end
        clear_actions();
        mode_br = 2'b11;
        mode_ol = 2'b11;
        mode_as = 2'b11;
        tick();
        if (
            mstat !== 4'he || bit_reverse !== 1'b1
            || overflow_latch !== 1'b1 || saturate_ar !== 1'b1
        ) begin
            $fatal(1, "mode-control write mismatch");
        end

        // Select alternate bank, populate it, and prove primary AF isolation.
        move_register(6'h31, 16'h000f);
        if (alternate_bank !== 1'b1) begin
            $fatal(1, "alternate bank was not selected");
        end
        clear_actions();
        alu_write_enable = 1'b1;
        alu_destination_feedback = 1'b1;
        alu_result = 16'h2468;
        tick();
        expect16(af, 16'h2468, "alternate AF");
        move_register(6'h31, 16'h000e);
        expect16(af, 16'h1357, "preserved primary AF");

        // DAG setup and execution updates use old-value/new-value timing.
        move_register(6'h10, 16'h0123);
        move_register(6'h15, 16'h3ffd);
        move_register(6'h18, 16'h0005);
        read_code = 6'h10;
        #1;
        expect16(read_data, 16'h0123, "DAG I0 setup");
        dag_execution_read = 1'b1;
        dag_i_l_read_address = 3'd0;
        dag_m_read_address = 3'd1;
        #1;
        if (
            !dag_i_read_valid || !dag_m_read_valid || !dag_l_read_valid
            || dag_i_read_data !== 14'h0123
            || dag_m_read_data !== 14'h3ffd
            || dag_l_read_data !== 14'h0005
        ) begin
            $fatal(1, "dedicated DAG execution read mismatch");
        end
        clear_actions();
        dag_i_write_enable = 1'b1;
        dag_i_write_address = 3'd0;
        dag_i_write_data = 14'h0456;
        dag_i_write_result_valid = 1'b1;
        #1;
        expect16(read_data, 16'h0123, "old DAG I0 read");
        tick();
        expect16(read_data, 16'h0456, "new DAG I0 read");

        // Same-I setup/update and same-AR move/ALU combinations fail closed.
        clear_actions();
        move_write = 1'b1;
        move_code = 6'h10;
        move_data = 16'h0777;
        dag_i_write_enable = 1'b1;
        dag_i_write_address = 3'd0;
        dag_i_write_data = 14'h0888;
        dag_i_write_result_valid = 1'b1;
        #1;
        if (internal_conflict !== 1'b1) begin
            $fatal(1, "same-I setup/update conflict was not detected");
        end
        tick();
        expect16(read_data, 16'h0456, "conflicting DAG write preservation");

        move_register(6'h0a, 16'h9999);
        read_code = 6'h0a;
        clear_actions();
        move_write = 1'b1;
        move_code = 6'h0a;
        move_data = 16'haaaa;
        alu_write_enable = 1'b1;
        alu_destination_feedback = 1'b0;
        alu_result = 16'hbbbb;
        #1;
        if (internal_conflict !== 1'b1) begin
            $fatal(1, "same-AR move/ALU conflict was not detected");
        end
        tick();
        expect16(read_data, 16'h9999, "conflicting AR write preservation");

        // Manual stack actions share this owner and commit from cycle-start
        // stack/status state at one active edge.
        move_register(6'h30, 16'h00a5);
        move_register(6'h31, 16'h0006);
        move_register(6'h33, 16'h0009);
        clear_actions();
        stack_status_operation = 2'b10;
        tick();
        if (sstat[4] !== 1'b0) begin
            $fatal(1, "status-stack push did not clear empty state");
        end
        move_register(6'h30, 16'h0012);
        move_register(6'h31, 16'h0003);
        move_register(6'h33, 16'h0004);
        clear_actions();
        stack_status_operation = 2'b11;
        tick();
        if (
            astat !== 8'ha5 || mstat !== 4'h6 || imask !== 4'h9
            || sstat[4] !== 1'b1
        ) begin
            $fatal(1, "status-stack pop/restore mismatch");
        end

        move_register(6'h35, 16'h0123);
        move_register(6'h35, 16'h0234);
        if (count_stack_depth !== 3'd1 || sstat[2] !== 1'b0) begin
            $fatal(1, "count-stack setup mismatch");
        end
        clear_actions();
        stack_count_pop = 1'b1;
        tick();
        if (
            cntr !== 14'h0123 || !cntr_valid
            || count_stack_depth !== 3'd0 || sstat[2] !== 1'b1
        ) begin
            $fatal(1, "count-stack pop/restore mismatch");
        end
        clear_actions();
        stack_pc_push = 1'b1;
        stack_pc_push_data = 14'h2345;
        tick();
        if (!pc_stack_top_valid || pc_stack_top !== 14'h2345 || sstat[0]) begin
            $fatal(1, "PC-stack push/top mismatch");
        end
        clear_actions();
        stack_pc_pop = 1'b1;
        stack_loop_pop = 1'b1;
        tick();
        if (internal_conflict || sstat[0] !== 1'b1 || sstat[6] !== 1'b1) begin
            $fatal(1, "PC pop or empty loop pop produced invalid state");
        end

        // Reset suppresses direct computational writes while retaining the
        // intentionally unspecified computational-register contents.
        clear_actions();
        reset = 1'b1;
        alu_write_enable = 1'b1;
        alu_destination_feedback = 1'b0;
        alu_result = 16'hdead;
        tick();
        reset = 1'b0;
        clear_actions();
        expect16(read_data, 16'h9999, "reset-suppressed AR write");
        if (mstat !== 4'h0 || alternate_bank !== 1'b0) begin
            $fatal(1, "reset did not restore primary bank selection");
        end

        assert (unused_observation == unused_observation);
        $display("PASS shared architectural-state action boundary");
        $finish;
    end
endmodule

`default_nettype wire
