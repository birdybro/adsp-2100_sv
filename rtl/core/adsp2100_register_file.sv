`default_nettype none

module adsp2100_register_file (
    input  logic        clk_i,
    input  logic        alternate_bank_i,

    input  logic [3:0]  read_address_0_i,
    input  logic [3:0]  read_address_1_i,
    input  logic [3:0]  read_address_2_i,
    input  logic [3:0]  read_address_3_i,
    output logic [15:0] read_data_0_o,
    output logic [15:0] read_data_1_o,
    output logic [15:0] read_data_2_o,
    output logic [15:0] read_data_3_o,

    input  logic        write_enable_0_i,
    input  logic [3:0]  write_address_0_i,
    input  logic [15:0] write_data_0_i,
    input  logic        write_enable_1_i,
    input  logic [3:0]  write_address_1_i,
    input  logic [15:0] write_data_1_i,
    input  logic        write_enable_2_i,
    input  logic [3:0]  write_address_2_i,
    input  logic [15:0] write_data_2_i,

    input  logic        sb_move_write_enable_i,
    input  logic [4:0]  sb_move_write_data_i,

    input  logic        alu_write_enable_i,
    input  logic        alu_destination_feedback_i,
    input  logic [15:0] alu_result_i,

    input  logic        mac_write_enable_i,
    input  logic        mac_destination_feedback_i,
    input  logic [39:0] mac_result_i,

    input  logic        shifter_sr_write_enable_i,
    input  logic [31:0] shifter_sr_result_i,
    input  logic        shifter_se_write_enable_i,
    input  logic [7:0]  shifter_se_result_i,
    input  logic        shifter_sb_write_enable_i,
    input  logic [4:0]  shifter_sb_result_i,

    output logic [15:0] af_o,
    output logic [15:0] mf_o,
    output logic [39:0] mr_o,
    output logic [7:0]  se_o,
    output logic [4:0]  sb_o,
    output logic [31:0] sr_o,
    output logic        write_conflict_o
);
    import adsp2100_register_pkg::*;

    // Fourteen DREGs are 16 bits. SE and MR2 retain their documented 8-bit
    // physical widths and are sign-extended only at the read boundary.
    logic [15:0] wide_register_q [0:1][0:13];
    logic [7:0]  se_q [0:1];
    logic [7:0]  mr2_q [0:1];
    logic [15:0] af_q [0:1];
    logic [15:0] mf_q [0:1];
    logic [4:0]  sb_q [0:1];
    logic [15:0] read_value [0:1][0:15];

    logic [2:0]  write_enable;
    logic [3:0]  write_address [0:2];
    logic [15:0] write_data [0:2];
    logic        shifter_write_enable;
    integer      conflict_port;
    integer      read_bank;
    integer      write_port;

    function automatic logic destinations_overlap(
        input logic [3:0] left,
        input logic [3:0] right
    );
        destinations_overlap = (
            (left == right)
            || ((left == DREG_MR1) && (right == DREG_MR2))
            || ((left == DREG_MR2) && (right == DREG_MR1))
        );
    endfunction

    assign write_enable[0] = write_enable_0_i;
    assign write_enable[1] = write_enable_1_i;
    assign write_enable[2] = write_enable_2_i;
    assign write_address[0] = write_address_0_i;
    assign write_address[1] = write_address_1_i;
    assign write_address[2] = write_address_2_i;
    assign write_data[0] = write_data_0_i;
    assign write_data[1] = write_data_1_i;
    assign write_data[2] = write_data_2_i;
    assign shifter_write_enable = (
        shifter_sr_write_enable_i
        || shifter_se_write_enable_i
        || shifter_sb_write_enable_i
    );

    always_comb begin
        for (read_bank = 0; read_bank < 2; read_bank = read_bank + 1) begin
            read_value[read_bank][DREG_AX0] = wide_register_q[read_bank][0];
            read_value[read_bank][DREG_AX1] = wide_register_q[read_bank][1];
            read_value[read_bank][DREG_MX0] = wide_register_q[read_bank][2];
            read_value[read_bank][DREG_MX1] = wide_register_q[read_bank][3];
            read_value[read_bank][DREG_AY0] = wide_register_q[read_bank][4];
            read_value[read_bank][DREG_AY1] = wide_register_q[read_bank][5];
            read_value[read_bank][DREG_MY0] = wide_register_q[read_bank][6];
            read_value[read_bank][DREG_MY1] = wide_register_q[read_bank][7];
            read_value[read_bank][DREG_SI] = wide_register_q[read_bank][8];
            read_value[read_bank][DREG_SE] = {
                {8{se_q[read_bank][7]}},
                se_q[read_bank]
            };
            read_value[read_bank][DREG_AR] = wide_register_q[read_bank][9];
            read_value[read_bank][DREG_MR0] = wide_register_q[read_bank][10];
            read_value[read_bank][DREG_MR1] = wide_register_q[read_bank][11];
            read_value[read_bank][DREG_MR2] = {
                {8{mr2_q[read_bank][7]}},
                mr2_q[read_bank]
            };
            read_value[read_bank][DREG_SR0] = wide_register_q[read_bank][12];
            read_value[read_bank][DREG_SR1] = wide_register_q[read_bank][13];
        end
        read_data_0_o = read_value[alternate_bank_i][read_address_0_i];
        read_data_1_o = read_value[alternate_bank_i][read_address_1_i];
        read_data_2_o = read_value[alternate_bank_i][read_address_2_i];
        read_data_3_o = read_value[alternate_bank_i][read_address_3_i];
        af_o = af_q[alternate_bank_i];
        mf_o = mf_q[alternate_bank_i];
        mr_o = {
            mr2_q[alternate_bank_i],
            wide_register_q[alternate_bank_i][11],
            wide_register_q[alternate_bank_i][10]
        };
        se_o = se_q[alternate_bank_i];
        sb_o = sb_q[alternate_bank_i];
        sr_o = {
            wide_register_q[alternate_bank_i][13],
            wide_register_q[alternate_bank_i][12]
        };
        write_conflict_o = (
            (
                write_enable[0]
                && write_enable[1]
                && destinations_overlap(write_address[0], write_address[1])
            )
            || (
                write_enable[0]
                && write_enable[2]
                && destinations_overlap(write_address[0], write_address[2])
            )
            || (
                write_enable[1]
                && write_enable[2]
                && destinations_overlap(write_address[1], write_address[2])
            )
        );

        if (
            (alu_write_enable_i && mac_write_enable_i)
            || (alu_write_enable_i && shifter_write_enable)
            || (mac_write_enable_i && shifter_write_enable)
        ) begin
            write_conflict_o = 1'b1;
        end
        if (
            (shifter_sr_write_enable_i && shifter_se_write_enable_i)
            || (shifter_sr_write_enable_i && shifter_sb_write_enable_i)
            || (shifter_se_write_enable_i && shifter_sb_write_enable_i)
            || (sb_move_write_enable_i && shifter_sb_write_enable_i)
        ) begin
            write_conflict_o = 1'b1;
        end
        for (
            conflict_port = 0;
            conflict_port < 3;
            conflict_port = conflict_port + 1
        ) begin
            if (write_enable[conflict_port]) begin
                if (
                    alu_write_enable_i
                    && !alu_destination_feedback_i
                    && (write_address[conflict_port] == DREG_AR)
                ) begin
                    write_conflict_o = 1'b1;
                end
                if (
                    mac_write_enable_i
                    && !mac_destination_feedback_i
                    && (
                        (write_address[conflict_port] == DREG_MR0)
                        || (write_address[conflict_port] == DREG_MR1)
                        || (write_address[conflict_port] == DREG_MR2)
                    )
                ) begin
                    write_conflict_o = 1'b1;
                end
                if (
                    shifter_sr_write_enable_i
                    && (
                        (write_address[conflict_port] == DREG_SR0)
                        || (write_address[conflict_port] == DREG_SR1)
                    )
                ) begin
                    write_conflict_o = 1'b1;
                end
                if (
                    shifter_se_write_enable_i
                    && (write_address[conflict_port] == DREG_SE)
                ) begin
                    write_conflict_o = 1'b1;
                end
            end
        end
    end

    // There is deliberately no reset assignment. The original manual does
    // not define computational-register contents after reset. Reads are
    // combinational and writes occur only at the active edge, reproducing
    // cycle-start read/cycle-end write visibility.
    always_ff @(posedge clk_i) begin
        if (!write_conflict_o) begin
            for (
                write_port = 0;
                write_port < 3;
                write_port = write_port + 1
            ) begin
                if (write_enable[write_port]) begin
                    case (write_address[write_port])
                        DREG_AX0: wide_register_q[alternate_bank_i][0]
                            <= write_data[write_port];
                        DREG_AX1: wide_register_q[alternate_bank_i][1]
                            <= write_data[write_port];
                        DREG_MX0: wide_register_q[alternate_bank_i][2]
                            <= write_data[write_port];
                        DREG_MX1: wide_register_q[alternate_bank_i][3]
                            <= write_data[write_port];
                        DREG_AY0: wide_register_q[alternate_bank_i][4]
                            <= write_data[write_port];
                        DREG_AY1: wide_register_q[alternate_bank_i][5]
                            <= write_data[write_port];
                        DREG_MY0: wide_register_q[alternate_bank_i][6]
                            <= write_data[write_port];
                        DREG_MY1: wide_register_q[alternate_bank_i][7]
                            <= write_data[write_port];
                        DREG_SI: wide_register_q[alternate_bank_i][8]
                            <= write_data[write_port];
                        DREG_SE: se_q[alternate_bank_i]
                            <= write_data[write_port][7:0];
                        DREG_AR: wide_register_q[alternate_bank_i][9]
                            <= write_data[write_port];
                        DREG_MR0: wide_register_q[alternate_bank_i][10]
                            <= write_data[write_port];
                        DREG_MR1: begin
                            wide_register_q[alternate_bank_i][11]
                                <= write_data[write_port];
                            mr2_q[alternate_bank_i]
                                <= {8{write_data[write_port][15]}};
                        end
                        DREG_MR2: mr2_q[alternate_bank_i]
                            <= write_data[write_port][7:0];
                        DREG_SR0: wide_register_q[alternate_bank_i][12]
                            <= write_data[write_port];
                        DREG_SR1: wide_register_q[alternate_bank_i][13]
                            <= write_data[write_port];
                        default: begin
                        end
                    endcase
                end
            end

            if (sb_move_write_enable_i) begin
                sb_q[alternate_bank_i] <= sb_move_write_data_i;
            end

            if (alu_write_enable_i) begin
                if (alu_destination_feedback_i) begin
                    af_q[alternate_bank_i] <= alu_result_i;
                end else begin
                    wide_register_q[alternate_bank_i][9] <= alu_result_i;
                end
            end

            if (mac_write_enable_i) begin
                if (mac_destination_feedback_i) begin
                    mf_q[alternate_bank_i] <= mac_result_i[31:16];
                end else begin
                    wide_register_q[alternate_bank_i][10]
                        <= mac_result_i[15:0];
                    wide_register_q[alternate_bank_i][11]
                        <= mac_result_i[31:16];
                    mr2_q[alternate_bank_i] <= mac_result_i[39:32];
                end
            end

            if (shifter_sr_write_enable_i) begin
                wide_register_q[alternate_bank_i][12]
                    <= shifter_sr_result_i[15:0];
                wide_register_q[alternate_bank_i][13]
                    <= shifter_sr_result_i[31:16];
            end
            if (shifter_se_write_enable_i) begin
                se_q[alternate_bank_i] <= shifter_se_result_i;
            end
            if (shifter_sb_write_enable_i) begin
                sb_q[alternate_bank_i] <= shifter_sb_result_i;
            end
        end
    end
endmodule

`default_nettype wire
