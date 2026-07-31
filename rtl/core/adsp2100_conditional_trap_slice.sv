`default_nettype none

module adsp2100_conditional_trap_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [2:0]  phase_i,
    input  logic        phase_advance_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,
    input  logic        halt_recognized_i,

    input  logic        pc_setup_write_i,
    input  logic [13:0] pc_setup_data_i,
    input  logic        astat_setup_write_i,
    input  logic [7:0]  astat_setup_data_i,
    input  logic        counter_setup_write_i,
    input  logic [13:0] counter_setup_data_i,

    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic [3:0]  condition_o,
    output logic        instruction_accepted_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        invalid_condition_state_o,
    output logic        integration_conflict_o,
    output logic        phase_mismatch_o,
    output logic        condition_known_o,
    output logic        condition_true_o,
    output logic        pending_o,
    output logic        pending_taken_o,
    output logic [13:0] pc_o,
    output logic        pc_write_o,
    output logic [7:0]  astat_o,
    output logic        astat_valid_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic        counter_test_o,
    output logic        counter_decrement_o,
    output logic        trap_o,
    output logic        trap_event_o,
    output logic        halted_o,
    output logic        halt_handoff_o,
    output logic        resume_event_o,
    output logic        phase_hold_o,
    output logic [13:0] pma_observation_o,
    output logic        pma_observation_valid_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    localparam logic [2:0] PHASE_STATE_1 = 3'd0;
    localparam logic [2:0] PHASE_STATE_7 = 3'd6;

    logic [13:0] pc_q;
    logic [7:0]  astat_q;
    logic        astat_valid_q;
    logic [13:0] cntr_q;
    logic        cntr_valid_q;
    logic        pending_q;
    logic        pending_taken_q;
    logic        trap_q;
    logic        halted_q;
    logic        halt_handoff_q;
    logic [2:0]  setup_count;
    logic        raw_condition_true;
    logic        raw_condition_known;
    logic        not_counter_expired;
    logic        accept_window;
    logic        accept_condition;
    logic        boundary_window;

    adsp2100_conditional_trap_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .action_valid_o(action_valid_o),
        .condition_o(condition_o)
    );

    assign setup_count = (
        {2'b00, pc_setup_write_i}
        + {2'b00, astat_setup_write_i}
        + {2'b00, counter_setup_write_i}
    );
    assign integration_conflict_o = !reset_i && (
        (execute_i && setup_count != 3'd0) || setup_count > 3'd1
    );
    assign accept_window = (
        !reset_i && execute_i && !halted_q && phase_advance_i
        && phase_i == PHASE_STATE_1 && !integration_conflict_o
    );
    assign accept_condition = accept_window && action_valid_o;
    assign boundary_window = (
        !reset_i && pending_q && !halted_q && phase_advance_i
        && phase_i == PHASE_STATE_7
    );

    always_comb begin
        raw_condition_known = astat_valid_q;
        if (condition_o == 4'he) begin
            raw_condition_known = cntr_valid_q;
        end else if (condition_o == 4'hf) begin
            raw_condition_known = 1'b1;
        end
    end

    assign not_counter_expired = (cntr_q != 14'h0001);

    adsp2100_condition_logic condition_logic (
        .condition_i(condition_o),
        .az_i(astat_q[0]),
        .an_i(astat_q[1]),
        .av_i(astat_q[2]),
        .ac_i(astat_q[3]),
        .as_i(astat_q[4]),
        .mv_i(astat_q[6]),
        .not_counter_expired_i(not_counter_expired),
        .condition_true_o(raw_condition_true)
    );

    assign pc_o = pc_q;
    assign astat_o = astat_q;
    assign astat_valid_o = astat_valid_q;
    assign cntr_o = cntr_q;
    assign cntr_valid_o = cntr_valid_q;
    assign pending_o = pending_q;
    assign pending_taken_o = pending_taken_q;
    assign trap_o = trap_q;
    assign halted_o = halted_q;
    assign halt_handoff_o = halt_handoff_q;
    assign phase_hold_o = halted_q;
    assign pma_observation_o = pc_q;
    assign pma_observation_valid_o = halted_q;
    assign counter_test_o = 1'b0;
    assign counter_decrement_o = 1'b0;
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pc_q <= 14'h0004;
            astat_q <= 8'h00;
            astat_valid_q <= 1'b0;
            cntr_q <= 14'h0000;
            cntr_valid_q <= 1'b0;
            pending_q <= 1'b0;
            pending_taken_q <= 1'b0;
            trap_q <= 1'b0;
            halted_q <= 1'b0;
            halt_handoff_q <= 1'b0;
            instruction_accepted_o <= 1'b0;
            boundary_valid_o <= 1'b0;
            invalid_opcode_o <= 1'b0;
            invalid_condition_state_o <= 1'b0;
            phase_mismatch_o <= 1'b0;
            condition_known_o <= 1'b0;
            condition_true_o <= 1'b0;
            pc_write_o <= 1'b0;
            trap_event_o <= 1'b0;
            resume_event_o <= 1'b0;
        end else begin
            instruction_accepted_o <= 1'b0;
            boundary_valid_o <= 1'b0;
            invalid_opcode_o <= 1'b0;
            invalid_condition_state_o <= 1'b0;
            phase_mismatch_o <= 1'b0;
            condition_known_o <= 1'b0;
            condition_true_o <= 1'b0;
            pc_write_o <= 1'b0;
            trap_event_o <= 1'b0;
            resume_event_o <= 1'b0;

            if (!execute_i && setup_count == 3'd1) begin
                if (pc_setup_write_i) begin
                    pc_q <= pc_setup_data_i;
                end else if (astat_setup_write_i) begin
                    astat_q <= astat_setup_data_i;
                    astat_valid_q <= 1'b1;
                end else if (counter_setup_write_i) begin
                    cntr_q <= counter_setup_data_i;
                    cntr_valid_q <= 1'b1;
                end
            end

            if (trap_q && halt_recognized_i) begin
                trap_q <= 1'b0;
                halted_q <= 1'b1;
                halt_handoff_q <= 1'b1;
            end else if (halt_handoff_q && !halt_recognized_i) begin
                halted_q <= 1'b0;
                halt_handoff_q <= 1'b0;
                resume_event_o <= 1'b1;
            end

            if (
                execute_i && !halted_q && phase_advance_i
                && phase_i != PHASE_STATE_1 && !integration_conflict_o
            ) begin
                phase_mismatch_o <= 1'b1;
            end
            if (accept_window && !class_valid_o) begin
                invalid_opcode_o <= 1'b1;
            end
            if (accept_condition) begin
                condition_known_o <= raw_condition_known;
                if (raw_condition_known) begin
                    instruction_accepted_o <= 1'b1;
                    condition_true_o <= raw_condition_true;
                    pending_q <= 1'b1;
                    pending_taken_q <= raw_condition_true;
                end else begin
                    invalid_condition_state_o <= 1'b1;
                end
            end

            if (boundary_window) begin
                pc_q <= pc_q + 14'h0001;
                pc_write_o <= 1'b1;
                boundary_valid_o <= 1'b1;
                pending_q <= 1'b0;
                pending_taken_q <= 1'b0;
                if (pending_taken_q) begin
                    trap_q <= 1'b1;
                    halted_q <= 1'b1;
                    halt_handoff_q <= 1'b0;
                    trap_event_o <= 1'b1;
                end
            end
        end
    end
endmodule

`default_nettype wire
