# The initial 20 ns fit measured a 46.01 MHz worst slow-corner Fmax and missed
# setup by 1.735 ns. This 22 ns rerun qualifies that measured standalone
# boundary. It does not claim final integrated-core or MiSTer timing closure.
create_clock -name core_clock -period 22.000 [get_ports {clk_i}]
set_input_delay -clock core_clock 0.000 [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock core_clock 0.000 [all_outputs]
