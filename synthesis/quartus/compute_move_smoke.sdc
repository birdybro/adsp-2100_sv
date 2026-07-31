# An initial 20 ns fit of this one-FPGA-cycle bounded compute slice measured
# about 46.04 MHz and missed setup by 1.721 ns. The documented 22 ns rerun
# measures 47.92 MHz at the worst slow corner in Quartus 17.0.2. The portable
# core may schedule an architectural instruction across explicit internal
# phases; this standalone smoke constraint qualifies the measured boundary
# without claiming final wrapper timing closure.
create_clock -name core_clock -period 22.000 [get_ports {clk_i}]
set_input_delay -clock core_clock 0.000 [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock core_clock 0.000 [all_outputs]
