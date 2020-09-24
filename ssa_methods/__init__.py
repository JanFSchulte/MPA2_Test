from ssa_methods.main import *
try:
    from ssa_methods.main_ssa_test_2 import *
except:
    pass

ssa  = ssa0

try:
    ssa_main_measure = SSA_Measurements_All()
    wp = ssa_main_measure
except:
    pass
