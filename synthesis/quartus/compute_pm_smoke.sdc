# The Type 5 logical slice qualifies compute, DAG2, PX, and PM recovery state.
# This is a bounded attachment constraint, not whole-core timing closure.
create_clock -name compute_pm_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock compute_pm_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock compute_pm_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock compute_pm_clock 0.000 [all_outputs]
