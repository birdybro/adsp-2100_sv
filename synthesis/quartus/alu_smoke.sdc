create_clock -name virtual_alu_clock -period 20.000
set_input_delay -clock virtual_alu_clock 0.000 [all_inputs]
set_output_delay -clock virtual_alu_clock 0.000 [all_outputs]
