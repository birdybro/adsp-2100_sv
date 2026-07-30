create_clock -name register_clock -period 20.000 [get_ports {clk_i}]
set_input_delay -clock register_clock 0.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock register_clock 0.000 [all_outputs]
