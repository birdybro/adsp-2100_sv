`default_nettype none

module adsp2100_condition_logic (
    input  logic [3:0] condition_i,
    input  logic       az_i,
    input  logic       an_i,
    input  logic       av_i,
    input  logic       ac_i,
    input  logic       as_i,
    input  logic       mv_i,
    input  logic       counter_nonzero_i,
    output logic       condition_true_o
);
    logic signed_less;

    always_comb begin
        signed_less = an_i ^ av_i;

        unique case (condition_i)
            4'h0: condition_true_o = az_i;
            4'h1: condition_true_o = ~az_i;
            4'h2: condition_true_o = ~(signed_less | az_i);
            4'h3: condition_true_o = signed_less | az_i;
            4'h4: condition_true_o = signed_less;
            4'h5: condition_true_o = ~signed_less;
            4'h6: condition_true_o = av_i;
            4'h7: condition_true_o = ~av_i;
            4'h8: condition_true_o = ac_i;
            4'h9: condition_true_o = ~ac_i;
            4'ha: condition_true_o = as_i;
            4'hb: condition_true_o = ~as_i;
            4'hc: condition_true_o = mv_i;
            4'hd: condition_true_o = ~mv_i;
            4'he: condition_true_o = counter_nonzero_i;
            4'hf: condition_true_o = 1'b1;
            default: condition_true_o = 1'b0;
        endcase
    end
endmodule

`default_nettype wire
