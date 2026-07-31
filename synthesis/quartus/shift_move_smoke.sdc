create_clock -name core_clock -period 20.000 [get_ports {clk_i}]
set_input_delay -clock core_clock 0.000 [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock core_clock 0.000 [all_outputs]
