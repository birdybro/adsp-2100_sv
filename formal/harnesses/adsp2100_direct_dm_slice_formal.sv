`default_nettype none

module adsp2100_direct_dm_slice_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        dm_ack,
    input logic [15:0] dm_read_data,
    input logic        dm_read_data_valid,
    input logic        setup_write,
    input logic [5:0]  setup_code,
    input logic [15:0] setup_data,
    input logic [5:0]  probe_code
);
    logic class_valid;
    logic action_valid;
    logic invalid_subencoding;
    logic write_direction;
    logic [13:0] direct_address;
    logic [5:0] register_code;
    logic boundary_valid;
    logic accepted;
    logic instruction_complete;
    logic transaction_active;
    logic stalled;
    logic busy;
    logic invalid_opcode;
    logic invalid_setup;
    logic integration_conflict;
    logic internal_conflict;
    logic dm_select;
    logic dm_read;
    logic dm_write;
    logic [13:0] dm_address;
    logic dm_address_valid;
    logic [15:0] dm_write_data;
    logic dm_write_data_valid;
    logic register_write;
    logic register_write_known;
    logic source_provisional;
    logic pm_access;
    logic dm_access;
    logic [15:0] probe_data;
    logic probe_data_valid;
    logic [7:0] astat;
    logic [3:0] mstat;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic [13:0] cntr;
    logic cntr_valid;
    logic [7:0] px;
    logic [7:0] sstat;
    logic count_push;
    logic [13:0] count_push_data;
    logic [2:0] count_depth;
    logic count_overflow;
    logic past_valid;
    logic unused_observation;

    adsp2100_direct_dm_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .dm_ack_i(dm_ack),
        .dm_read_data_i(dm_read_data),
        .dm_read_data_valid_i(dm_read_data_valid),
        .setup_write_i(setup_write),
        .setup_code_i(setup_code),
        .setup_data_i(setup_data),
        .probe_code_i(probe_code),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .invalid_subencoding_o(invalid_subencoding),
        .write_direction_o(write_direction),
        .direct_address_o(direct_address),
        .register_code_o(register_code),
        .boundary_valid_o(boundary_valid),
        .accepted_o(accepted),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active),
        .stalled_o(stalled),
        .busy_o(busy),
        .invalid_opcode_o(invalid_opcode),
        .invalid_setup_o(invalid_setup),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .dm_select_o(dm_select),
        .dm_read_o(dm_read),
        .dm_write_o(dm_write),
        .dm_address_o(dm_address),
        .dm_address_valid_o(dm_address_valid),
        .dm_write_data_o(dm_write_data),
        .dm_write_data_valid_o(dm_write_data_valid),
        .register_write_o(register_write),
        .register_write_known_o(register_write_known),
        .source_extension_provisional_o(source_provisional),
        .pm_data_access_o(pm_access),
        .dm_access_o(dm_access),
        .probe_data_o(probe_data),
        .probe_data_valid_o(probe_data_valid),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .px_o(px),
        .sstat_o(sstat),
        .count_stack_push_o(count_push),
        .count_stack_push_data_o(count_push_data),
        .count_stack_depth_o(count_depth),
        .count_stack_overflow_o(count_overflow)
    );

    assign unused_observation = ^{
        class_valid, action_valid, invalid_subencoding,
        write_direction, direct_address, register_code,
        invalid_opcode, invalid_setup, integration_conflict,
        internal_conflict, register_write_known, source_provisional,
        probe_data, probe_data_valid, astat, mstat, icntl, imask,
        cntr, cntr_valid, px, sstat, count_push, count_push_data,
        count_depth, count_overflow
    };

    initial past_valid = 1'b0;

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(dm_read && dm_write));
        assert (dm_select == (dm_read || dm_write));
        assert (dm_access == dm_select);
        assert (!pm_access);
        assert (boundary_valid == accepted);
        assert (instruction_complete == (transaction_active && dm_ack));
        assert (stalled == (transaction_active && !dm_ack));
        assert (busy == stalled);
        assert (register_write == (instruction_complete && dm_read));
        assert (dm_address_valid == transaction_active);
        if (!dm_address_valid) assert (dm_address == 14'h0000);
        if (!dm_write_data_valid) assert (dm_write_data == 16'h0000);
        if (source_provisional) assert (dm_write);
        if (stalled) assert (!instruction_complete && !register_write);
        if (reset) assert (!accepted && !transaction_active);
    end

    always_ff @(posedge clk) begin
        past_valid <= 1'b1;
        if (past_valid && $past(stalled) && stalled) begin
            assert (dm_address == $past(dm_address));
            assert (dm_read == $past(dm_read));
            assert (dm_write == $past(dm_write));
            assert (dm_write_data_valid == $past(dm_write_data_valid));
            if (dm_write_data_valid) begin
                assert (dm_write_data == $past(dm_write_data));
            end
            assert (!register_write);
        end
        cover (past_valid && $past(stalled) && instruction_complete);
        cover (accepted && dm_write && source_provisional);
    end
endmodule

`default_nettype wire
