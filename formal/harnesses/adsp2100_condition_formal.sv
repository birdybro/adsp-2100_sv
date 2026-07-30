`default_nettype none

module adsp2100_condition_formal (
    input logic [3:0] condition,
    input logic       az,
    input logic       an,
    input logic       av,
    input logic       ac,
    input logic       as_flag,
    input logic       mv,
    input logic       counter_nonzero
);
    logic                     condition_true;

    adsp2100_condition_logic dut (
        .condition_i(condition),
        .az_i(az),
        .an_i(an),
        .av_i(av),
        .ac_i(ac),
        .as_i(as_flag),
        .mv_i(mv),
        .counter_nonzero_i(counter_nonzero),
        .condition_true_o(condition_true)
    );

    always_comb begin
        unique case (condition)
            4'h0: assert (condition_true == az);
            4'h1: assert (condition_true == ~az);
            4'h2: assert (condition_true == ((an ^ av) | az));
            4'h3: assert (condition_true == ~((an ^ av) | az));
            4'h4: assert (condition_true == (an ^ av));
            4'h5: assert (condition_true == ~(an ^ av));
            4'h6: assert (condition_true == av);
            4'h7: assert (condition_true == ~av);
            4'h8: assert (condition_true == ac);
            4'h9: assert (condition_true == ~ac);
            4'ha: assert (condition_true == as_flag);
            4'hb: assert (condition_true == ~as_flag);
            4'hc: assert (condition_true == mv);
            4'hd: assert (condition_true == ~mv);
            4'he: assert (condition_true == counter_nonzero);
            4'hf: assert (condition_true);
        endcase
    end
endmodule

`default_nettype wire
