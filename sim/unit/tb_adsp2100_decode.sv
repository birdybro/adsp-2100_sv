`default_nettype none

module tb_adsp2100_decode;
    import adsp2100_pkg::*;
    import adsp2100_decode_pkg::*;

    program_word_t      opcode;
    instruction_class_t actual_class;
    instruction_class_t expected_class;
    integer unsigned    opcode_index;
    longint unsigned    shown_count;
    longint unsigned    reserved_unshown_count;

    adsp2100_class_decode dut (
        .opcode_i(opcode),
        .instruction_class_o(actual_class)
    );

    function automatic instruction_class_t independent_decode(
        input program_word_t word
    );
        // Hand-transcribed independently from ADI-UM-1989 printed A-1-A-5.
        casez (word)
            24'b11??????????????????????:
                return INSTRUCTION_TYPE_01;
            24'b101?????????????????????:
                return INSTRUCTION_TYPE_02;
            24'b100?????????????????????:
                return INSTRUCTION_TYPE_03;
            24'b011?????????????????????:
                return INSTRUCTION_TYPE_04;
            24'b0101????????????????????:
                return INSTRUCTION_TYPE_05;
            24'b0100????????????????????:
                return INSTRUCTION_TYPE_06;
            24'b0011????????????????????:
                return INSTRUCTION_TYPE_07;
            24'b00101???????????????????:
                return INSTRUCTION_TYPE_08;
            24'b00100???????????0000????:
                return INSTRUCTION_TYPE_09;
            24'b00011???????????????????:
                return INSTRUCTION_TYPE_10;
            24'b000101??????????????????:
                return INSTRUCTION_TYPE_11;
            24'b0001001?????????????????:
                return INSTRUCTION_TYPE_12;
            24'b00010001????????????????:
                return INSTRUCTION_TYPE_13;
            24'b00010000????????????????:
                return INSTRUCTION_TYPE_14;
            24'b000011110???????????????:
                return INSTRUCTION_TYPE_15;
            24'b000011100???????0000????:
                return INSTRUCTION_TYPE_16;
            24'b000011010000????????????:
                return INSTRUCTION_TYPE_17;
            24'b000011000000????????0000:
                return INSTRUCTION_TYPE_18;
            24'b0000101100000000??0?????:
                return INSTRUCTION_TYPE_19;
            24'b0000101000000000000?????:
                return INSTRUCTION_TYPE_20;
            24'b0000100100000000000?????:
                return INSTRUCTION_TYPE_21;
            24'b00001000000000000000????:
                return INSTRUCTION_TYPE_22;
            24'b0000011100010???00000000:
                return INSTRUCTION_TYPE_23;
            24'b00000110000?????00000000:
                return INSTRUCTION_TYPE_24;
            24'b000001010000000000000000:
                return INSTRUCTION_TYPE_25;
            24'b0000010000000000000?????:
                return INSTRUCTION_TYPE_26;
            24'b00000011????????????????:
                return INSTRUCTION_TYPE_27;
            24'b00000010????????????????:
                return INSTRUCTION_TYPE_28;
            24'b00000001????????????????:
                return INSTRUCTION_TYPE_29;
            24'b000000000000000000000000:
                return INSTRUCTION_TYPE_30;
            default:
                return INSTRUCTION_RESERVED_UNSHOWN;
        endcase
    endfunction

    initial begin
        shown_count = 64'd0;
        reserved_unshown_count = 64'd0;
        for (
            opcode_index = 0;
            opcode_index < 32'h01000000;
            opcode_index = opcode_index + 1
        ) begin
            opcode = opcode_index[23:0];
            #1;
            expected_class = independent_decode(opcode);
            if (actual_class !== expected_class) begin
                $fatal(
                    1,
                    "decode mismatch opcode=%06x actual=%0d expected=%0d",
                    opcode,
                    actual_class,
                    expected_class
                );
            end
            if (actual_class == INSTRUCTION_RESERVED_UNSHOWN) begin
                reserved_unshown_count = reserved_unshown_count + 64'd1;
            end else begin
                shown_count = shown_count + 64'd1;
            end
        end
        if (shown_count != 64'd15473178) begin
            $fatal(1, "shown count mismatch: %0d", shown_count);
        end
        if (reserved_unshown_count != 64'd1304038) begin
            $fatal(
                1,
                "reserved-unshown count mismatch: %0d",
                reserved_unshown_count
            );
        end
        $display(
            "PASS original ADSP-2100 decode: %0d shown, %0d reserved-unshown",
            shown_count,
            reserved_unshown_count
        );
        $finish;
    end
endmodule

`default_nettype wire
