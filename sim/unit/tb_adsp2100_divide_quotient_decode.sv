`default_nettype none
`timescale 1ns/1ps

module tb_adsp2100_divide_quotient_decode;
    logic [23:0] opcode;
    logic class_valid;
    logic action_valid;
    logic [2:0] xop;
    logic [3:0] divisor_source;
    logic expected_class;
    logic [3:0] expected_source;
    integer opcode_value;
    integer class_count;
    integer action_count;

    adsp2100_divide_quotient_decode dut (
        .opcode_i(opcode),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .xop_o(xop),
        .divisor_source_dreg_o(divisor_source)
    );

    always_comb begin
        unique case (opcode[10:8])
            3'd0: expected_source = 4'h0;
            3'd1: expected_source = 4'h1;
            3'd2: expected_source = 4'ha;
            3'd3: expected_source = 4'hb;
            3'd4: expected_source = 4'hc;
            3'd5: expected_source = 4'hd;
            3'd6: expected_source = 4'he;
            default: expected_source = 4'hf;
        endcase
    end

    initial begin
        class_count = 0;
        action_count = 0;
        for (opcode_value = 0; opcode_value < 24'hffffff; opcode_value++) begin
            opcode = opcode_value[23:0];
            #1;
            expected_class = ((opcode & 24'hfff8ff) == 24'h071000);
            if (class_valid !== expected_class) begin
                $fatal(1, "Type 23 class mismatch opcode=%06x", opcode);
            end
            if (action_valid !== expected_class) begin
                $fatal(1, "Type 23 action mismatch opcode=%06x", opcode);
            end
            if (expected_class) begin
                class_count = class_count + 1;
                action_count = action_count + 1;
                if (xop !== opcode[10:8] || divisor_source !== expected_source) begin
                    $fatal(1, "Type 23 field mismatch opcode=%06x", opcode);
                end
            end else if (xop !== 3'b000) begin
                $fatal(1, "nonclass Type 23 XOP is not zero opcode=%06x", opcode);
            end
        end
        opcode = 24'hffffff;
        #1;
        expected_class = ((opcode & 24'hfff8ff) == 24'h071000);
        if (class_valid !== expected_class || action_valid !== expected_class) begin
            $fatal(1, "Type 23 final opcode mismatch");
        end
        if (class_count != 8 || action_count != 8) begin
            $fatal(
                1,
                "Type 23 count mismatch class=%0d action=%0d",
                class_count,
                action_count
            );
        end
        $display("PASS Type 23 decode: 8 source-closed actions");
        $finish;
    end
endmodule

`default_nettype wire
