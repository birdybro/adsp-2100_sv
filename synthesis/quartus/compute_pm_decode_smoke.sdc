create_clock -name virtual_opcode_clock -period 20.000
set_input_delay -clock virtual_opcode_clock 2.000 [get_ports {opcode_i[*]}]
set_output_delay -clock virtual_opcode_clock 2.000 [get_ports {*_o*}]
