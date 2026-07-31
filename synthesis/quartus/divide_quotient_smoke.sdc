create_clock -name divide_quotient_clock -period 20.000 [get_ports {clk_i}]
# Virtual ports model same-clock, register-launched core controls.
set_input_delay -clock divide_quotient_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock divide_quotient_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock divide_quotient_clock 0.000 [all_outputs]
