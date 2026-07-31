`default_nettype none

module adsp2100_mode_control_slice_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        setup_write,
    input logic [3:0]  setup_write_data
);
    logic       boundary_valid;
    logic       invalid_opcode;
    logic       integration_conflict;
    logic       internal_conflict;
    logic [1:0] decoded_sr;
    logic [1:0] decoded_br;
    logic [1:0] decoded_ol;
    logic [1:0] decoded_as;
    logic       decoded_has_effect;
    logic       decoded_has_alias;
    logic [3:0] mstat;
    logic       alternate_bank;
    logic       bit_reverse;
    logic       overflow_latch;
    logic       saturate_ar;
    logic       type_18_valid;
    logic       past_valid;

    function automatic logic updated_bit (
        input logic old_value,
        input logic [1:0] control
    );
        case (control)
            2'b10: updated_bit = 1'b0;
            2'b11: updated_bit = 1'b1;
            default: updated_bit = old_value;
        endcase
    endfunction

    assign type_18_valid = (
        (opcode & 24'hfff00f) == 24'h0c0000
    );

    adsp2100_mode_control_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .mstat_setup_write_i(setup_write),
        .mstat_setup_write_data_i(setup_write_data),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .decoded_mode_sr_o(decoded_sr),
        .decoded_mode_br_o(decoded_br),
        .decoded_mode_ol_o(decoded_ol),
        .decoded_mode_as_o(decoded_as),
        .decoded_has_effect_o(decoded_has_effect),
        .decoded_has_alias_o(decoded_has_alias),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .bit_reverse_o(bit_reverse),
        .overflow_latch_o(overflow_latch),
        .saturate_ar_o(saturate_ar)
    );

    always_comb begin
        assert (
            boundary_valid
            == (
                !reset
                && execute
                && type_18_valid
                && !setup_write
            )
        );
        assert (
            invalid_opcode
            == (!reset && execute && !type_18_valid)
        );
        assert (
            integration_conflict
            == (!reset && execute && setup_write)
        );
        assert (!internal_conflict);
        assert (alternate_bank == mstat[0]);
        assert (bit_reverse == mstat[1]);
        assert (overflow_latch == mstat[2]);
        assert (saturate_ar == mstat[3]);
        if (type_18_valid) begin
            assert (decoded_sr == opcode[5:4]);
            assert (decoded_br == opcode[7:6]);
            assert (decoded_ol == opcode[9:8]);
            assert (decoded_as == opcode[11:10]);
        end else begin
            assert (decoded_sr == 2'b00);
            assert (decoded_br == 2'b00);
            assert (decoded_ol == 2'b00);
            assert (decoded_as == 2'b00);
            assert (!decoded_has_effect);
            assert (!decoded_has_alias);
        end
        cover (boundary_valid && decoded_has_effect);
        cover (boundary_valid && !decoded_has_effect);
        cover (boundary_valid && decoded_has_alias);
        cover (integration_conflict);
        cover (invalid_opcode);
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
        end else if ($past(integration_conflict)) begin
            assert (mstat == $past(mstat));
        end else if ($past(setup_write)) begin
            assert (mstat == $past(setup_write_data));
        end else if ($past(boundary_valid)) begin
            assert (
                mstat[0]
                == updated_bit($past(mstat[0]), $past(decoded_sr))
            );
            assert (
                mstat[1]
                == updated_bit($past(mstat[1]), $past(decoded_br))
            );
            assert (
                mstat[2]
                == updated_bit($past(mstat[2]), $past(decoded_ol))
            );
            assert (
                mstat[3]
                == updated_bit($past(mstat[3]), $past(decoded_as))
            );
        end else begin
            assert (mstat == $past(mstat));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
