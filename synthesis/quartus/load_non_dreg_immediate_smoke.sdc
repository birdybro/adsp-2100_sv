# Bounded Type 7 register-state slice, not whole-core timing.
create_clock -name load_non_dreg_immediate_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock load_non_dreg_immediate_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock load_non_dreg_immediate_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock load_non_dreg_immediate_clock 0.000 [all_outputs]
