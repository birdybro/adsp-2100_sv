`default_nettype none

module adsp2100_conditional_shift_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic [3:0]  sf_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  source_dreg_o,
    output logic [3:0]  condition_o
);
    assign class_valid_o = (
        (opcode_i & 24'hff80f0) == 24'h0e0000
    );
    assign sf_o = class_valid_o ? opcode_i[14:11] : 4'h0;
    assign xop_o = class_valid_o ? opcode_i[10:8] : 3'h0;
    assign condition_o = class_valid_o ? opcode_i[3:0] : 4'h0;
    assign action_valid_o = (
        class_valid_o
        && (opcode_i[10:8] != 3'b001)
    );
    assign unsupported_subencoding_o = class_valid_o && !action_valid_o;

    always_comb begin
        source_dreg_o = 4'h0;
        if (action_valid_o) begin
            unique case (xop_o)
                3'b000: source_dreg_o = 4'h8; // SI
                3'b010: source_dreg_o = 4'ha; // AR
                3'b011: source_dreg_o = 4'hb; // MR0
                3'b100: source_dreg_o = 4'hc; // MR1
                3'b101: source_dreg_o = 4'hd; // MR2
                3'b110: source_dreg_o = 4'he; // SR0
                3'b111: source_dreg_o = 4'hf; // SR1
                default: source_dreg_o = 4'h0;
            endcase
        end
    end
endmodule

`default_nettype wire
