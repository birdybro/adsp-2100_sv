create_clock -name compute_pm_halt_clock -period 25.000 [get_ports {clk_i}]
# Virtual controls represent same-clock, register-launched phase/event inputs.
set_input_delay -clock compute_pm_halt_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock compute_pm_halt_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock compute_pm_halt_clock 0.000 [all_outputs]
