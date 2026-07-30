`default_nettype none

module adsp2100_sequencer_flow (
    input  logic [13:0] pc_i,
    input  logic [1:0]  explicit_flow_i,
    input  logic        explicit_taken_i,
    input  logic [13:0] explicit_target_i,
    input  logic        loop_active_i,
    input  logic [13:0] loop_end_i,
    input  logic [13:0] loop_start_i,
    input  logic        loop_termination_true_i,
    input  logic        loop_uses_counter_i,
    output logic [13:0] next_pc_o,
    output logic        pc_stack_push_o,
    output logic [13:0] pc_stack_push_value_o,
    output logic        pc_stack_pop_o,
    output logic        loop_stack_pop_o,
    output logic        count_stack_pop_o,
    output logic        loop_counter_test_o,
    output logic        loop_back_o,
    output logic        loop_exit_o,
    output logic        explicit_transfer_o
);
    localparam logic [1:0] FLOW_NONE = 2'b00;
    localparam logic [1:0] FLOW_JUMP = 2'b01;
    localparam logic [1:0] FLOW_CALL = 2'b10;
    localparam logic [1:0] FLOW_RETURN = 2'b11;

    logic [13:0] sequential_pc;
    logic        at_loop_end;

    always_comb begin
        sequential_pc = pc_i + 14'h0001;
        at_loop_end = loop_active_i && (pc_i == loop_end_i);

        next_pc_o = sequential_pc;
        pc_stack_push_o = 1'b0;
        pc_stack_push_value_o = sequential_pc;
        pc_stack_pop_o = 1'b0;
        loop_stack_pop_o = 1'b0;
        count_stack_pop_o = 1'b0;
        loop_counter_test_o = 1'b0;
        loop_back_o = 1'b0;
        loop_exit_o = 1'b0;
        explicit_transfer_o = 1'b0;

        if (explicit_taken_i && (explicit_flow_i != FLOW_NONE)) begin
            next_pc_o = explicit_target_i;
            explicit_transfer_o = 1'b1;
            unique case (explicit_flow_i)
                FLOW_JUMP: begin
                    pc_stack_push_o = 1'b0;
                end
                FLOW_CALL: begin
                    pc_stack_push_o = 1'b1;
                end
                FLOW_RETURN: begin
                    pc_stack_pop_o = 1'b1;
                end
                default: begin
                    explicit_transfer_o = 1'b0;
                end
            endcase
        end else if (at_loop_end) begin
            loop_counter_test_o = loop_uses_counter_i;
            if (loop_termination_true_i) begin
                pc_stack_pop_o = 1'b1;
                loop_stack_pop_o = 1'b1;
                count_stack_pop_o = loop_uses_counter_i;
                loop_exit_o = 1'b1;
            end else begin
                next_pc_o = loop_start_i;
                loop_back_o = 1'b1;
            end
        end
    end
endmodule

`default_nettype wire
