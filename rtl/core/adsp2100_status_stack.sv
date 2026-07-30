`default_nettype none

module adsp2100_status_stack (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic [1:0]  operation_i,
    input  logic [15:0] push_data_i,

    output logic [15:0] pop_data_o,
    output logic        pop_valid_o,
    output logic        empty_o,
    output logic        overflow_o,
    output logic [2:0]  depth_o,
    output logic        push_accepted_o,
    output logic        overflow_event_o,
    output logic        empty_pop_o
);
    localparam logic [1:0] OP_NO_CHANGE_ZERO = 2'b00;
    localparam logic [1:0] OP_NO_CHANGE_ONE = 2'b01;
    localparam logic [1:0] OP_PUSH = 2'b10;
    localparam logic [1:0] OP_POP = 2'b11;

    logic [15:0] stack_q [0:3];
    logic [2:0]  depth_q;
    logic        overflow_q;

    assign empty_o = depth_q == 3'd0;
    assign overflow_o = overflow_q;
    assign depth_o = depth_q;
    assign pop_valid_o = (
        (operation_i == OP_POP)
        && !empty_o
        && !reset_i
    );
    assign push_accepted_o = (
        (operation_i == OP_PUSH)
        && (depth_q < 3'd4)
        && !reset_i
    );
    assign overflow_event_o = (
        (operation_i == OP_PUSH)
        && (depth_q == 3'd4)
        && !reset_i
    );
    assign empty_pop_o = (
        (operation_i == OP_POP)
        && empty_o
        && !reset_i
    );

    // Empty-pop data is undocumented (OQ-013). Zero is an implementation
    // sentinel only; pop_valid_o is false and consumers must not use it.
    always_comb begin
        unique case (depth_q)
            3'd1: pop_data_o = stack_q[0];
            3'd2: pop_data_o = stack_q[1];
            3'd3: pop_data_o = stack_q[2];
            3'd4: pop_data_o = stack_q[3];
            default: pop_data_o = 16'h0000;
        endcase
    end

    // RESET clears only pointer/status state. Stack data has no architectural
    // reset value and is deliberately left uninitialized.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            depth_q <= 3'd0;
            overflow_q <= 1'b0;
        end else begin
            unique case (operation_i)
                OP_PUSH: begin
                    if (depth_q < 3'd4) begin
                        stack_q[depth_q[1:0]] <= push_data_i;
                        depth_q <= depth_q + 3'd1;
                    end else begin
                        overflow_q <= 1'b1;
                    end
                end
                OP_POP: begin
                    if (depth_q != 3'd0) begin
                        depth_q <= depth_q - 3'd1;
                    end
                end
                OP_NO_CHANGE_ZERO,
                OP_NO_CHANGE_ONE: begin
                    depth_q <= depth_q;
                end
                default: begin
                    depth_q <= depth_q;
                end
            endcase
        end
    end
endmodule

`default_nettype wire
