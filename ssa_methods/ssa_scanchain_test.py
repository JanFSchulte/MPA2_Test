import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import ctypes
from itertools import groupby
from operator import itemgetter

from utilities.tbsettings import *
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

class SSA_scanchain_test():


	##############################################################
	def __init__(self, ssa, I2C, FC7, pwr):
		self.ssa = ssa; self.I2C = I2C; self.fc7 = FC7; self.pwr = pwr;
		self.seu_check_time = -1; self.last_test_duration = 0;


	##############################################################
	def load_inputs_scan_test(self):

		fin = open ("/projects/TSMC65/CTPIX/SSA2.0/workAreas/gbergami/SSA_si_spera_finale/work_fsm/vector_shift" , "rt")
		lines = fin.readlines()
		input_vector = lines[0].rstrip()
		expected_response = lines[1].rstrip()
		input_mask = lines[2].rstrip()
		vector_list = []
		response_list = []
		mask_list = []
		### the list contains in position 0 the 24 lsb 23 : 0 , which are in position 5972: 5996 in the string in my file ). In position 249 i have the 20 msb (and 0000)
		for i in range(249):

			vector_list.append('{0:08b}'.format(i) + input_vector[(5996 - 24*i - 24) : (5996 - 24*i)])
			response_list.append( '{0:08b}'.format(i) + expected_response[(5996 - 24*i - 24) : (5996 - 24*i)])
			mask_list.append( '{0:08b}'.format(i) + input_mask[(5996 - 24*i - 24) : (5996 - 24*i)])

		vector_list.append( '{0:08b}'.format(249) + "0000" + input_vector[0:20] )
		mask_list.append('{0:08b}'.format(249) + "0000" + input_mask[0:20] )
		response_list.append('{0:08b}'.format(249) + "0000" + expected_response[0:20] )

		#for word in vector_list :
		#	self.fc7.write("cnfg_ssa_scanchain_vector",word)
		#	time.sleep(0.1)

		#for word in response_list :
		#	self.fc7.write("cnfg_ssa_scanchain_response",word)
		#	time.sleep(0.1)

		#for word in mask_list :
		#	self.fc7.write("cnfg_ssa_scanchain_mask",word)
		#	time.sleep(0.1)

## to check if the list it' s correct
##string = ""
##i= 249
### in the 249th position there are the bits 5996:5976, which are extended of 4 additional bits 0000 to become 24 bits
##while i >= 0:
##    print "%s" % vector_list[i][0:8]
##    if (i == 249) :
##parto da i = 249 per ricreare input_vector dal MSB
##        string = string + vector_list[i][12:32]
##    else :
##        string = string + vector_list[i][8:32]
##    i = i-1
##print "%s" % string == input_vector
###
###string = ""
###i= 249
#### in the 249th position there are the bits 5996:5976, which are extended of 4 additional bits 0000 to become 24 bits
###print "input vector is %s" % input_vector
###while i >= 0:
###    if (i == 249) :
###        string = string + vector_list[i][12:32]
###        print "%s" % vector_list[i][0:8]
###        print "%s" % vector_list[i][8:32]
###    else :
###        string = string + vector_list[i][8:32]
###        print "%s" % vector_list[i][0:8]
###        print "%s" % vector_list[i][8:32]
###    i = i-1
###print "%s" % string == input_vector
###

		###write registers : add write input_registers, expected_response, input_mask
		self.fc7.write("cnfg_ssa_scanchain_is_capture_test",0)
		time.sleep(0.1)
		self.fc7.write("cnfg_ssa_scanchain_is_reset_test",0)
		time.sleep(0.1)
		self.fc7.write("cnfg_ssa_scanchain_is_scanchain_test",1)
		print("Loaded inputs for scan test")

	##############################################################
	def load_inputs_capture_test(self):

		fin = open ("/projects/TSMC65/CTPIX/SSA2.0/workAreas/gbergami/SSA_si_spera_finale/work_fsm/first_vector_capture" , "rt")
		lines = fin.readlines()
		input_vector = lines[0].rstrip()
		expected_response = lines[1].rstrip()
		input_mask = lines[2].rstrip()
		vector_list = []
		response_list = []
		mask_list = []

		for i in range(249):

			vector_list.append('{0:08b}'.format(i) + input_vector[(5996 - 24*i - 24) : (5996 - 24*i)])
			response_list.append( '{0:08b}'.format(i) + expected_response[(5996 - 24*i - 24) : (5996 - 24*i)])
			mask_list.append( '{0:08b}'.format(i) + input_mask[(5996 - 24*i - 24) : (5996 - 24*i)])

		vector_list.append( '{0:08b}'.format(249) + "0000" + input_vector[0:20] )
		mask_list.append('{0:08b}'.format(249) + "0000" + input_mask[0:20] )
		response_list.append('{0:08b}'.format(249) + "0000" + expected_response[0:20] )


		#for word in vector_list :
		#	self.fc7.write("cnfg_ssa_scanchain_vector",word)
		#	time.sleep(0.1)

		#for word in response_list :
		#	self.fc7.write("cnfg_ssa_scanchain_response",word)
		#	time.sleep(0.1)

		#for word in mask_list :
		#	self.fc7.write("cnfg_ssa_scanchain_mask",word)
		#	time.sleep(0.1)

		###write registers : add write input_registers, expected_response, input_mask
		self.fc7.write("cnfg_ssa_scanchain_is_capture_test",1)
		time.sleep(0.1)
		self.fc7.write("cnfg_ssa_scanchain_is_reset_test",0)
		time.sleep(0.1)
		self.fc7.write("cnfg_ssa_scanchain_is_scanchain_test",0)
		print("Loaded inputs for capture test")

	##############################################################
	def load_inputs_reset_test(self):

		fin = open ("/projects/TSMC65/CTPIX/SSA2.0/workAreas/gbergami/SSA_si_spera_finale/work_fsm/vector_reset" , "rt")
		lines = fin.readlines()
		input_vector = lines[0].rstrip()
		expected_response = lines[1].rstrip()
		input_mask = lines[2].rstrip()
		vector_list = []
		response_list = []
		mask_list = []

		for i in range(249):
			vector_list.append('{0:08b}'.format(i) + input_vector[(5996 - 24*i - 24) : (5996 - 24*i)])
			response_list.append( '{0:08b}'.format(i) + expected_response[(5996 - 24*i - 24) : (5996 - 24*i)])
			mask_list.append( '{0:08b}'.format(i) + input_mask[(5996 - 24*i - 24) : (5996 - 24*i)])

		vector_list.append( '{0:08b}'.format(249) + "0000" + input_vector[0:20] )
		mask_list.append('{0:08b}'.format(249) + "0000" + input_mask[0:20] )
		response_list.append('{0:08b}'.format(249) + "0000" + expected_response[0:20] )


		#for word in vector_list :
		#	self.fc7.write("cnfg_ssa_scanchain_vector",word)
		#	time.sleep(0.1)

		#for word in response_list :
		#	self.fc7.write("cnfg_ssa_scanchain_response",word)
		#	time.sleep(0.1)

		#for word in mask_list :
		#	self.fc7.write("cnfg_ssa_scanchain_mask",word)
		#	time.sleep(0.1)

		###write registers : add write input_registers, expected_response, input_mask
		self.fc7.write("cnfg_ssa_scanchain_is_capture_test",0)
		time.sleep(0.1)
		self.fc7.write("cnfg_ssa_scanchain_is_reset_test",1)
		time.sleep(0.1)
		self.fc7.write("cnfg_ssa_scanchain_is_scanchain_test",0)
		time.sleep(0.1)
		print( "Loaded inputs for reset test")

	##############################################################
	def do_test(self):
		fc7.write("cnfg_ssa_scanchain_start_test",1)
		time.sleep(0.5)
		test_done = self.fc7.read("scanchain_test_done")
		comparator = self.fc7.read("scanchain_comparator")
		comparator_neg_pre = self.fc7.read("scanchain_comparator_negedge")
		comparator_neg_next = self.fc7.read("scanchain_comparator_negedge_next")
		miscompares = self.fc7.read("scanchain_comparator_miscompares")
		#response = ""
		#response = read from ddr3
		print("Test done is {:d} ".format(test_done))
		if (test_done == 0):
			return
		print("Comparator is %d " % comparator)
		print("Comparator neg pre is %d " % comparator_neg_pre)
		print("Comparator neg next is %d " % comparator_neg_next)
		if (comparator or comparator_neg_pre or comparator_neg_next ):
			print("Test successfull")
		else:
			print("Test failed")
			#print "%s" % response
			#for word in lateral_data:
			#utils.print_log(
			#    '    \t->' +
			#    '{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
			#    '{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
			#    '{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
			#    '{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )


##############################################################

	def restart_test(self):
		fc7.write("cnfg_ssa_scanchain_start_test",0)

	def enable_scanchain(self, val=1):
		fc7.write("cnfg_dio5_en" ,1)
		fc7.write("cnfg_dio5_ch1_out_en", 1)
		fc7.write("cnfg_dio5_ch2_out_en", 1)
		fc7.write("cnfg_dio5_ch3_out_en", 1)
		fc7.write("cnfg_dio5_ch4_out_en", 1)
		fc7.write("cnfg_dio5_ch5_out_en", 1)
		#fc7.write("cnfg_ddr3_scanchain_test_enable",1)
		#fc7.write("cnfg_ssa_scanchain_is_scanchain_test",1)

	def prova2(self):
		fc7.write("cnfg_ssa_scanchain_start_test",0)
		fc7.write("cnfg_ssa_scanchain_start_test",1)


	def prova1(self):

		self.fc7.write("cnfg_ssa_scanchain_is_capture_test",0)
		time.sleep(1)
		self.fc7.write("cnfg_ssa_scanchain_is_reset_test",0)
		time.sleep(1)
		self.fc7.write("cnfg_ssa_scanchain_is_scanchain_test",1)
		time.sleep(1)
		fc7.write("cnfg_ssa_scanchain_start_test",1)


#   cnfg_ddr3_scanchain_test_enable          40018000    00000002     1     1 *enable scanchain test mode
#   cnfg_ssa_scanchain_start_test            4001A000    00000001     1     1 * scanchain test start
#   cnfg_ssa_scanchain_is_scanchain_test     4001A000    00000002     1     1 * scanchain is_scan_test
#   cnfg_ssa_scanchain_is_reset_test         4001A000    00000004     1     1 * scanchain is_reset test
#   cnfg_ssa_scanchain_is_capture_test       4001A000    00000008     1     1 * scanchain is capture test
#   cnfg_ssa_scanchain_vector                4001A001    ffffffff     1     1 * scanchain input vector
#   cnfg_ssa_scanchain_response              4001A002    ffffffff     1     1 * scanchain input response
#   cnfg_ssa_scanchain_mask                  4001A003    ffffffff     1     1 * scanchain input mask

###################################################
