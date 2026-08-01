`default_nettype none

module adsp2100_direct_dm_native_formal (
    input logic        clk,
    input logic        reset,
    input logic [2:0]  phase,
    input logic        phase_advance,
    input logic        bus_relinquished,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        dm_ack,
    input logic [15:0] read_data,
    input logic        read_data_valid,
    input logic        setup_write,
    input logic [5:0]  setup_code,
    input logic [15:0] setup_data,
    input logic [5:0]  probe_code
);
    import adsp2100_pkg::*;

    logic issue_boundary;
    logic phase_conflict;
    logic attachment_conflict;
    logic integration_conflict;
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
    logic internal_conflict;
    logic source_provisional;
    logic register_write;
    logic register_write_known;
    logic request_accepted;
    logic dmack_sample;
    logic dmack_accepted;
    logic wait_extension;
    logic completion;
    logic read_sample;
    logic bus_active;
    logic bus_waiting;
    logic address_oe;
    logic control_oe;
    logic data_oe;
    logic [13:0] dma;
    logic dma_valid;
    logic dms_n;
    logic dmrd_n;
    logic dmwr_n;
    logic [15:0] write_data;
    logic write_data_valid;
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
    logic controls_present;
    logic unused_observation;

    assign controls_present = execute || setup_write;
    assign unused_observation = ^{
        class_valid, action_valid, invalid_subencoding,
        write_direction, direct_address, register_code, boundary_valid,
        transaction_active, stalled, busy, invalid_opcode, invalid_setup,
        internal_conflict, source_provisional, register_write_known,
        dmack_sample, dmack_accepted, dma, dma_valid, write_data,
        write_data_valid, probe_data, probe_data_valid, astat, mstat,
        icntl, imask, cntr, cntr_valid, px, sstat, count_push,
        count_push_data, count_depth, count_overflow
    };

    adsp2100_direct_dm_native_slice dut (
        .clk_i(clk), .reset_i(reset), .phase_i(phase),
        .phase_advance_i(phase_advance),
        .bus_relinquished_i(bus_relinquished),
        .execute_i(execute), .opcode_i(opcode), .dm_ack_i(dm_ack),
        .dmd_read_data_i(read_data),
        .dmd_read_data_valid_i(read_data_valid),
        .setup_write_i(setup_write), .setup_code_i(setup_code),
        .setup_data_i(setup_data), .probe_code_i(probe_code),
        .issue_boundary_o(issue_boundary),
        .phase_conflict_o(phase_conflict),
        .attachment_conflict_o(attachment_conflict),
        .integration_conflict_o(integration_conflict),
        .class_valid_o(class_valid), .action_valid_o(action_valid),
        .invalid_subencoding_o(invalid_subencoding),
        .write_direction_o(write_direction),
        .direct_address_o(direct_address),
        .register_code_o(register_code),
        .boundary_valid_o(boundary_valid), .accepted_o(accepted),
        .instruction_complete_o(instruction_complete),
        .transaction_active_o(transaction_active), .stalled_o(stalled),
        .busy_o(busy), .invalid_opcode_o(invalid_opcode),
        .invalid_setup_o(invalid_setup),
        .internal_conflict_o(internal_conflict),
        .source_extension_provisional_o(source_provisional),
        .register_write_o(register_write),
        .register_write_known_o(register_write_known),
        .dm_request_accepted_o(request_accepted),
        .dmack_sample_event_o(dmack_sample),
        .dmack_accepted_o(dmack_accepted),
        .wait_extension_event_o(wait_extension),
        .dm_completion_event_o(completion),
        .dm_read_sample_event_o(read_sample),
        .dm_bus_active_o(bus_active), .dm_bus_waiting_o(bus_waiting),
        .dm_address_output_enable_o(address_oe),
        .dm_control_output_enable_o(control_oe),
        .dm_data_output_enable_o(data_oe),
        .dma_o(dma), .dma_valid_o(dma_valid), .dms_n_o(dms_n),
        .dmrd_n_o(dmrd_n), .dmwr_n_o(dmwr_n),
        .dmd_write_data_o(write_data),
        .dmd_write_data_valid_o(write_data_valid),
        .probe_data_o(probe_data), .probe_data_valid_o(probe_data_valid),
        .astat_o(astat), .mstat_o(mstat), .icntl_o(icntl),
        .imask_o(imask), .cntr_o(cntr), .cntr_valid_o(cntr_valid),
        .px_o(px), .sstat_o(sstat), .count_stack_push_o(count_push),
        .count_stack_push_data_o(count_push_data),
        .count_stack_depth_o(count_depth),
        .count_stack_overflow_o(count_overflow)
    );

    always_comb begin
        assert (unused_observation == unused_observation);
        assert (issue_boundary == (
            !reset && !bus_relinquished && phase_advance
            && phase == PHASE_STATE_8
        ));
        assert (phase_conflict
            == (!reset && controls_present && !issue_boundary));
        assert (!attachment_conflict);
        assert (integration_conflict
            == (phase_conflict || attachment_conflict
                || dut.core_integration_conflict));
        assert (accepted == request_accepted);
        assert (instruction_complete
            == (completion && dut.core_dm_select));
        assert (read_sample == (completion && dut.core_dm_read));
        assert (!(~dmrd_n && ~dmwr_n));
        assert (address_oe == control_oe);
        assert (dms_n == !control_oe);
        if (accepted) assert (issue_boundary && dut.core_dm_select);
        if (instruction_complete) begin
            assert (phase == PHASE_STATE_7 && phase_advance);
            assert (transaction_active && bus_active);
        end
        if (register_write) assert (read_sample);
        if (bus_waiting && !reset) begin
            assert (transaction_active && stalled);
            assert (!instruction_complete && !register_write);
        end
        if (bus_relinquished || reset) begin
            assert (!address_oe && !control_oe && !data_oe);
        end
    end

    always_ff @(posedge clk) begin
        cover (accepted && request_accepted);
        cover (wait_extension && bus_waiting);
        cover (instruction_complete && register_write);
    end
endmodule

`default_nettype wire
