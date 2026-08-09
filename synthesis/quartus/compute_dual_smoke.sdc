# The bounded Type 1 slice qualifies logical atomic dual-read completion. It
# does not claim native DMACK/PM phase behavior, which remains OQ-023.
create_clock -name core_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock core_clock 0.000 [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock core_clock 0.000 [all_outputs]
