`default_nettype none

module adsp2100_sequencer_stacks (
    input  logic        clk_i,
    input  logic        reset_i,

    input  logic        pc_push_i,
    input  logic        pc_pop_i,
    input  logic [13:0] pc_push_data_i,
    output logic [13:0] pc_top_data_o,
    output logic        pc_top_valid_o,
    output logic        pc_pop_valid_o,
    output logic        pc_empty_o,
    output logic        pc_overflow_o,
    output logic [4:0]  pc_depth_o,
    output logic        pc_push_accepted_o,
    output logic        pc_overflow_event_o,
    output logic        pc_empty_pop_o,

    input  logic        count_push_i,
    input  logic        count_pop_i,
    input  logic [13:0] count_push_data_i,
    output logic [13:0] count_top_data_o,
    output logic        count_top_valid_o,
    output logic        count_pop_valid_o,
    output logic        count_empty_o,
    output logic        count_overflow_o,
    output logic [2:0]  count_depth_o,
    output logic        count_push_accepted_o,
    output logic        count_overflow_event_o,
    output logic        count_empty_pop_o,

    input  logic        loop_push_i,
    input  logic        loop_pop_i,
    input  logic [17:0] loop_push_data_i,
    output logic [17:0] loop_top_data_o,
    output logic        loop_top_valid_o,
    output logic        loop_pop_valid_o,
    output logic        loop_empty_o,
    output logic        loop_overflow_o,
    output logic [2:0]  loop_depth_o,
    output logic        loop_push_accepted_o,
    output logic        loop_overflow_event_o,
    output logic        loop_empty_pop_o,

    output logic [7:0]  sstat_fragment_o,
    output logic        write_conflict_o
);
    logic [13:0] pc_stack_q [0:15];
    logic [13:0] count_stack_q [0:3];
    logic [17:0] loop_stack_q [0:3];
    logic [4:0]  pc_depth_q;
    logic [2:0]  count_depth_q;
    logic [2:0]  loop_depth_q;
    logic        pc_overflow_q;
    logic        count_overflow_q;
    logic        loop_overflow_q;
    logic [3:0]  pc_top_index;
    logic [1:0]  count_top_index;
    logic [1:0]  loop_top_index;

    assign pc_empty_o = pc_depth_q == 5'd0;
    assign count_empty_o = count_depth_q == 3'd0;
    assign loop_empty_o = loop_depth_q == 3'd0;
    assign pc_overflow_o = pc_overflow_q;
    assign count_overflow_o = count_overflow_q;
    assign loop_overflow_o = loop_overflow_q;
    assign pc_depth_o = pc_depth_q;
    assign count_depth_o = count_depth_q;
    assign loop_depth_o = loop_depth_q;
    assign pc_top_valid_o = !pc_empty_o;
    assign count_top_valid_o = !count_empty_o;
    assign loop_top_valid_o = !loop_empty_o;
    assign pc_top_index = pc_depth_q[3:0] - 4'd1;
    assign count_top_index = count_depth_q[1:0] - 2'd1;
    assign loop_top_index = loop_depth_q[1:0] - 2'd1;

    assign write_conflict_o = !reset_i && (
        (pc_push_i && pc_pop_i)
        || (count_push_i && count_pop_i)
        || (loop_push_i && loop_pop_i)
    );

    assign pc_pop_valid_o = (
        pc_pop_i
        && !pc_empty_o
        && !reset_i
        && !write_conflict_o
    );
    assign count_pop_valid_o = (
        count_pop_i
        && !count_empty_o
        && !reset_i
        && !write_conflict_o
    );
    assign loop_pop_valid_o = (
        loop_pop_i
        && !loop_empty_o
        && !reset_i
        && !write_conflict_o
    );

    assign pc_push_accepted_o = (
        pc_push_i
        && (pc_depth_q < 5'd16)
        && !reset_i
        && !write_conflict_o
    );
    assign count_push_accepted_o = (
        count_push_i
        && (count_depth_q < 3'd4)
        && !reset_i
        && !write_conflict_o
    );
    assign loop_push_accepted_o = (
        loop_push_i
        && (loop_depth_q < 3'd4)
        && !reset_i
        && !write_conflict_o
    );

    assign pc_overflow_event_o = (
        pc_push_i
        && (pc_depth_q == 5'd16)
        && !reset_i
        && !write_conflict_o
    );
    assign count_overflow_event_o = (
        count_push_i
        && (count_depth_q == 3'd4)
        && !reset_i
        && !write_conflict_o
    );
    assign loop_overflow_event_o = (
        loop_push_i
        && (loop_depth_q == 3'd4)
        && !reset_i
        && !write_conflict_o
    );

    assign pc_empty_pop_o = (
        pc_pop_i
        && pc_empty_o
        && !reset_i
        && !write_conflict_o
    );
    assign count_empty_pop_o = (
        count_pop_i
        && count_empty_o
        && !reset_i
        && !write_conflict_o
    );
    assign loop_empty_pop_o = (
        loop_pop_i
        && loop_empty_o
        && !reset_i
        && !write_conflict_o
    );

    assign sstat_fragment_o = {
        loop_overflow_o,
        loop_empty_o,
        2'b00,
        count_overflow_o,
        count_empty_o,
        pc_overflow_o,
        pc_empty_o
    };

    // Empty top data is undocumented (OQ-013). Zero is an implementation
    // sentinel only; the corresponding valid outputs are false.
    always_comb begin
        pc_top_data_o = 14'h0000;
        if (pc_depth_q != 5'd0) begin
            pc_top_data_o = pc_stack_q[pc_top_index];
        end

        count_top_data_o = 14'h0000;
        if (count_depth_q != 3'd0) begin
            count_top_data_o = count_stack_q[count_top_index];
        end

        loop_top_data_o = 18'h00000;
        if (loop_depth_q != 3'd0) begin
            loop_top_data_o = loop_stack_q[loop_top_index];
        end
    end

    // RESET clears pointer/status state only. Stored data has no documented
    // reset value and is deliberately left uninitialized.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            pc_depth_q <= 5'd0;
            count_depth_q <= 3'd0;
            loop_depth_q <= 3'd0;
            pc_overflow_q <= 1'b0;
            count_overflow_q <= 1'b0;
            loop_overflow_q <= 1'b0;
        end else if (!write_conflict_o) begin
            if (pc_push_i) begin
                if (pc_depth_q < 5'd16) begin
                    pc_stack_q[pc_depth_q[3:0]] <= pc_push_data_i;
                    pc_depth_q <= pc_depth_q + 5'd1;
                end else begin
                    pc_overflow_q <= 1'b1;
                end
            end else if (pc_pop_i && (pc_depth_q != 5'd0)) begin
                pc_depth_q <= pc_depth_q - 5'd1;
            end

            if (count_push_i) begin
                if (count_depth_q < 3'd4) begin
                    count_stack_q[count_depth_q[1:0]] <= count_push_data_i;
                    count_depth_q <= count_depth_q + 3'd1;
                end else begin
                    count_overflow_q <= 1'b1;
                end
            end else if (count_pop_i && (count_depth_q != 3'd0)) begin
                count_depth_q <= count_depth_q - 3'd1;
            end

            if (loop_push_i) begin
                if (loop_depth_q < 3'd4) begin
                    loop_stack_q[loop_depth_q[1:0]] <= loop_push_data_i;
                    loop_depth_q <= loop_depth_q + 3'd1;
                end else begin
                    loop_overflow_q <= 1'b1;
                end
            end else if (loop_pop_i && (loop_depth_q != 3'd0)) begin
                loop_depth_q <= loop_depth_q - 3'd1;
            end
        end
    end
endmodule

`default_nettype wire
