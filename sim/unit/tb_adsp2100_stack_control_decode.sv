`default_nettype none

module tb_adsp2100_stack_control_decode;
    logic [23:0] opcode;
    logic        valid;
    logic [1:0]  status_operation;
    logic        count_pop;
    logic        loop_pop;
    logic        pc_pop;
    logic        has_effect;
    integer unsigned opcode_index;
    integer unsigned valid_count;

    adsp2100_stack_control_decode dut (
        .opcode_i(opcode),
        .valid_o(valid),
        .status_operation_o(status_operation),
        .count_pop_o(count_pop),
        .loop_pop_o(loop_pop),
        .pc_pop_o(pc_pop),
        .has_effect_o(has_effect)
    );

    initial begin
        valid_count = 0;
        for (
            opcode_index = 0;
            opcode_index < 32'h01000000;
            opcode_index = opcode_index + 1
        ) begin
            opcode = opcode_index[23:0];
            #1;
            if (valid !== (opcode[23:5] == 19'b0000010000000000000)) begin
                $fatal(1, "valid mismatch at opcode=%06x", opcode);
            end
            if (valid) begin
                valid_count = valid_count + 1;
                if (
                    status_operation !== opcode[1:0]
                    || count_pop !== opcode[2]
                    || loop_pop !== opcode[3]
                    || pc_pop !== opcode[4]
                    || has_effect !== (|opcode[4:1])
                ) begin
                    $fatal(1, "action mismatch at opcode=%06x", opcode);
                end
            end else if (
                status_operation !== 2'b00
                || count_pop !== 1'b0
                || loop_pop !== 1'b0
                || pc_pop !== 1'b0
                || has_effect !== 1'b0
            ) begin
                $fatal(1, "invalid opcode emitted action: %06x", opcode);
            end
        end
        if (valid_count != 32) begin
            $fatal(1, "Type 26 encoding count mismatch: %0d", valid_count);
        end
        $display(
            "PASS stack-control decode: 32 encodings, invalid words fail closed"
        );
        $finish;
    end
endmodule

`default_nettype wire
