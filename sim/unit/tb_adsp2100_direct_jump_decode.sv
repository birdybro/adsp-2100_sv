`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_direct_jump_decode;
    logic [23:0] opcode;
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_call_ce;
    logic        call_action;
    logic [13:0] address;
    logic [3:0]  condition;
    logic        expected_class;
    logic        expected_unsupported;
    integer      word;
    integer      class_count;
    integer      supported_count;
    integer      unsupported_count;

    adsp2100_direct_jump_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_call_ce_o(unsupported_call_ce),
        .call_o(call_action),
        .address_o(address),
        .condition_o(condition)
    );

    initial begin
        opcode = 24'h000000;
        class_count = 0;
        supported_count = 0;
        unsupported_count = 0;
        for (word = 0; word < 16_777_216; word = word + 1) begin
            opcode = word[23:0];
            #1;
            expected_class = ((opcode & 24'hf80000) == 24'h180000);
            expected_unsupported = (
                expected_class && opcode[18] && opcode[3:0] == 4'he
            );
            if (class_valid !== expected_class
                || action_valid !== (expected_class && !expected_unsupported)
                || unsupported_call_ce !== expected_unsupported) begin
                $fatal(1, "classification mismatch word=%06x", word);
            end
            if (expected_class) begin
                if (call_action !== opcode[18]
                    || address !== opcode[17:4]
                    || condition !== opcode[3:0]) begin
                    $fatal(1, "field mismatch word=%06x", word);
                end
                class_count = class_count + 1;
                if (expected_unsupported) begin
                    unsupported_count = unsupported_count + 1;
                end else begin
                    supported_count = supported_count + 1;
                end
            end else if (call_action !== 1'b0
                || address !== 14'h0000 || condition !== 4'h0) begin
                $fatal(1, "nonclass field leakage word=%06x", word);
            end
        end
        if (class_count != 524_288 || supported_count != 507_904
            || unsupported_count != 16_384) begin
            $fatal(
                1,
                "counts class=%0d supported=%0d unsupported=%0d",
                class_count,
                supported_count,
                unsupported_count
            );
        end
        $display(
            "PASS Type 10 decode: %0d supported, %0d OQ-012 CALL NOT CE",
            supported_count,
            unsupported_count
        );
        $finish;
    end
endmodule

`default_nettype wire
