# The bounded Type 4 slice includes compute, DAG, and logical DM capture/commit.
# Its standalone constraint qualifies this boundary, not a whole-core cycle.
create_clock -name core_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock core_clock 0.000 [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock core_clock 0.000 [all_outputs]
