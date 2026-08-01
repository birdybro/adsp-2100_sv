create_clock -name shifter_pm_clock -period 21.000 [get_ports {clk_i}]
set_input_delay -clock shifter_pm_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock shifter_pm_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock shifter_pm_clock 0.000 [all_outputs]
