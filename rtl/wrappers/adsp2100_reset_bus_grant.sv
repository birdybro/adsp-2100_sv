`default_nettype none

// Native-pin-only RESET-time BR/BG path.
//
// The original path is asynchronous while RESET is active. Keeping this
// direct external-input/external-output mux in a wrapper prevents an
// asynchronous control path from entering architectural state.
module adsp2100_reset_bus_grant (
    input  logic reset_active_i,
    input  logic br_n_i,
    input  logic normal_bg_n_i,
    input  logic normal_bus_relinquished_i,
    output logic bg_n_o,
    output logic bus_relinquished_o
);
    always_comb begin
        if (reset_active_i) begin
            bg_n_o = br_n_i;
            bus_relinquished_o = !br_n_i;
        end else begin
            bg_n_o = normal_bg_n_i;
            bus_relinquished_o = normal_bus_relinquished_i;
        end
    end

`ifndef SYNTHESIS
    always_comb begin
        assert (bg_n_o == !bus_relinquished_o);
        if (reset_active_i) begin
            assert (bg_n_o == br_n_i);
        end
    end
`endif
endmodule

`default_nettype wire
