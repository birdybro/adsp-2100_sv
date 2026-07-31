`default_nettype none

module adsp2100_mr_saturation_slice_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        astat_write,
    input logic [7:0]  astat_write_data,
    input logic        mstat_write,
    input logic [3:0]  mstat_write_data,
    input logic        mr_setup_write,
    input logic [39:0] mr_setup_write_data
);
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic        condition_mv;
    logic        selected_bank_alternate;
    logic        mr_write;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic [39:0] mr;
    logic        setup_action;
    logic        type_25_valid;
    logic        past_valid;

    assign setup_action = (
        astat_write
        || mstat_write
        || mr_setup_write
    );
    assign type_25_valid = opcode == 24'h050000;

    adsp2100_mr_saturation_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .astat_write_i(astat_write),
        .astat_write_data_i(astat_write_data),
        .mstat_write_i(mstat_write),
        .mstat_write_data_i(mstat_write_data),
        .mr_setup_write_i(mr_setup_write),
        .mr_setup_write_data_i(mr_setup_write_data),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .condition_mv_o(condition_mv),
        .selected_bank_alternate_o(selected_bank_alternate),
        .mr_write_o(mr_write),
        .astat_o(astat),
        .mstat_o(mstat),
        .mr_o(mr)
    );

    always_comb begin
        assert (
            boundary_valid
            == (
                !reset
                && execute
                && type_25_valid
                && !setup_action
            )
        );
        assert (
            invalid_opcode
            == (!reset && execute && !type_25_valid)
        );
        assert (
            integration_conflict
            == (!reset && execute && setup_action)
        );
        assert (!internal_conflict);
        assert (condition_mv == astat[6]);
        assert (selected_bank_alternate == mstat[0]);
        assert (mr_write == (boundary_valid && condition_mv));

        cover (boundary_valid && !condition_mv);
        cover (boundary_valid && condition_mv && !mr[39]);
        cover (boundary_valid && condition_mv && mr[39]);
        cover (boundary_valid && selected_bank_alternate);
        cover (integration_conflict);
        cover (invalid_opcode);
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
        end else if ($past(boundary_valid)) begin
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
            if ($past(condition_mv)) begin
                assert (
                    mr
                    == (
                        $past(mr[39])
                        ? 40'hff80000000
                        : 40'h007fffffff
                    )
                );
            end else begin
                assert (mr == $past(mr));
            end
        end else if (
            $past(integration_conflict)
            || $past(invalid_opcode)
        ) begin
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
            assert (mr == $past(mr));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
