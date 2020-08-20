from PyChipsUser import *
fc7AddrTable = AddressTable("./fc7AddrTable.dat")
from time import sleep
import sys
import os
import visa
from fc7_lib import *

#########################
# console arguments
#########################
debug_str=""
arguments = len(sys.argv)
if (arguments>1):
	if sys.argv[1]=="debug": debug_str="debug"
	
os.system((' '.join(['fc7_test_gtx_enable.py', debug_str])))
os.system((' '.join(['fc7_test_gtx_ber.py', debug_str])))
os.system((' '.join(['fc7_test_gtx_disable.py', debug_str])))


