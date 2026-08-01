`default_nettype none

// Stateless Type 25 action producer for attachment to a shared architectural
// state owner. The exact instruction samples MV and selected-bank MR from
// cycle-start state; the caller qualifies the optional MR write at retirement.
module adsp2100_mr_saturation_action (
    input  logic [23:0] opcode_i,
    input  logic [39:0] mr_i,
    input  logic        mv_i,

    output logic        action_valid_o,
    output logic        condition_mv_o,
    output logic        mr_write_o,
    output logic [39:0] mr_result_o
);
    adsp2100_mr_saturation_decode decode (
        .opcode_i(opcode_i),
        .valid_o(action_valid_o)
    );

    adsp2100_mr_saturate saturation (
        .mr_i(mr_i),
        .mv_i(mv_i),
        .result_o(mr_result_o)
    );

    assign condition_mv_o = mv_i;
    assign mr_write_o = action_valid_o && condition_mv_o;

`ifndef SYNTHESIS
    always_comb begin
        if (!action_valid_o) begin
            assert (!mr_write_o);
        end
        if (mr_write_o) begin
            assert (action_valid_o && condition_mv_o);
            assert (
                mr_result_o == (
                    mr_i[39] ? 40'hff80000000 : 40'h007fffffff
                )
            );
        end
    end
`endif
endmodule

`default_nettype wire
