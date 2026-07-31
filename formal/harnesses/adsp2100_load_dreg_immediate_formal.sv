`default_nettype none

module adsp2100_load_dreg_immediate_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        mstat_setup,
    input logic [3:0]  mstat_setup_data,
    input logic        dreg_setup,
    input logic [3:0]  dreg_setup_code,
    input logic [15:0] dreg_setup_data,
    input logic [3:0]  probe_code
);
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [3:0]  destination;
    logic [15:0] immediate;
    logic [15:0] probe_data;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        pm_data_access;
    logic        dm_access;
    logic        expected_valid;
    logic        expected_conflict;
    logic        past_valid;

    assign expected_valid = (opcode[23:20] == 4'h4);
    assign expected_conflict = (
        !reset
        && (
            (execute && (mstat_setup || dreg_setup))
            || (mstat_setup && dreg_setup)
        )
    );

    adsp2100_load_dreg_immediate_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .probe_code_i(probe_code),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .destination_dreg_o(destination),
        .immediate_data_o(immediate),
        .probe_data_o(probe_data),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (
            boundary_valid
            == (
                !reset
                && execute
                && expected_valid
                && !mstat_setup
                && !dreg_setup
            )
        );
        assert (invalid_opcode == (!reset && execute && !expected_valid));
        assert (integration_conflict == expected_conflict);
        assert (!internal_conflict);
        assert (!pm_data_access);
        assert (!dm_access);
        if (expected_valid) begin
            assert (destination == opcode[3:0]);
            assert (immediate == opcode[19:4]);
        end else begin
            assert (destination == 4'h0);
            assert (immediate == 16'h0000);
        end
        assert (alternate_bank == mstat[0]);
        cover (boundary_valid);
        cover (invalid_opcode);
        cover (integration_conflict);
        cover (boundary_valid && destination == 4'hc);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
        end else if ($past(invalid_opcode || integration_conflict)) begin
            assume (probe_code == $past(probe_code));
            assert (probe_data == $past(probe_data));
            assert (mstat == $past(mstat));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
