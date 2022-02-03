#   cnfg_dio5_en				40016005    00000001     1     1 *enable DIO5 block - disabled by default
#
#   cnfg_dio5_ch1_sel			40016000    ffffffff	 1     1 *Configuration of the channel 1
#        cnfg_dio5_ch1_out_en		40016000    00000001	 1     1 *1 - Output, 0 - Input
#        cnfg_dio5_ch1_term_en		40016000    00000002	 1     1 *Enable 50 Ohm termination
#        cnfg_dio5_ch1_threshold		40016000    0000ff00	 1     1 *0-255 threshold
#
#   cnfg_dio5_ch2_sel			40016001    ffffffff	 1     1 *Configuration of the channel 2
#        cnfg_dio5_ch2_out_en		40016001    00000001	 1     1 *1 - Output, 0 - Input
#        cnfg_dio5_ch2_term_en		40016001    00000002	 1     1 *Enable 50 Ohm termination
#        cnfg_dio5_ch2_threshold		40016001    0000ff00	 1     1 *0-255 threshold
#
#   cnfg_dio5_ch3_sel			40016002    ffffffff	 1     1 *Configuration of the channel 3
#        cnfg_dio5_ch3_out_en		40016002    00000001	 1     1 *1 - Output, 0 - Input
#        cnfg_dio5_ch3_term_en		40016002    00000002	 1     1 *Enable 50 Ohm termination
#        cnfg_dio5_ch3_threshold		40016002    0000ff00	 1     1 *0-255 threshold
#
#   cnfg_dio5_ch4_sel			40016003    ffffffff	 1     1 *Configuration of the channel 4
#        cnfg_dio5_ch4_out_en		40016003    00000001	 1     1 *1 - Output, 0 - Input
#        cnfg_dio5_ch4_term_en		40016003    00000002	 1     1 *Enable 50 Ohm termination
#        cnfg_dio5_ch4_threshold		40016003    0000ff00	 1     1 *0-255 threshold
#
#   cnfg_dio5_ch5_sel			40016004    ffffffff	 1     1 *Configuration of the channel 5
#        cnfg_dio5_ch5_out_en		40016004    00000001	 1     1 *1 - Output, 0 - Input
#        cnfg_dio5_ch5_term_en		40016004    00000002	 1     1 *Enable 50 Ohm termination
#        cnfg_dio5_ch5_threshold		40016004    0000ff00	 1     1 *0-255 threshold

from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import time
import sys
import inspect

class DIO5_control():
	def __init__(self, fc7_if):
		self.fc7 = fc7_if;

	def set_module_enable(self, en=1):
		self.fc7.write("cnfg_dio5_en", en)

	def set_lines_enable(self, d1=1, d2=1, d3=1, d4=1, d5=1):
		self.fc7.write("cnfg_dio5_ch1_out_en", d1)
		self.fc7.write("cnfg_dio5_ch2_out_en", d2)
		self.fc7.write("cnfg_dio5_ch3_out_en", d3)
		self.fc7.write("cnfg_dio5_ch4_out_en", d4)
		self.fc7.write("cnfg_dio5_ch5_out_en", d5)
