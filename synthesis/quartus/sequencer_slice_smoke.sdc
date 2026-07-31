create_clock -name sequencer_slice_clock -period 20.000 [get_ports {clk_i}]
# Virtual ports model same-clock, register-launched core controls. Five
# nanoseconds includes launch clock-tree and source-register clock-to-Q delay
# in this isolated integration-slice fit.
set_input_delay -clock sequencer_slice_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock sequencer_slice_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock sequencer_slice_clock 0.000 [all_outputs]
