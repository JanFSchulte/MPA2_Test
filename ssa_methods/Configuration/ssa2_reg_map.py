
#  import json
#  with open('ssa_methods/Configuration/ssa2_reg_map.json') as datafile:
#      ssa_reg_map = json.load(datafile)
#  print(json.dumps(ssa_reg_map, indent=4, sort

################# Strip register map #########################
ssa_strip_reg_map = {}

ssa_strip_reg_map['tmp']                = 0b00001


################# Periphery register map #####################
ssa_peri_reg_map = {}

ssa_peri_reg_map['tmp']            =  0


################# Analog MUX map #####################
analog_mux_map = {'highimpedence': 0x00}


print('- Loaded configuration for SSA v2')
