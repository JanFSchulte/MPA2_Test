#
import os
import csv
import numpy as np
import time
import sys
from d19cScripts import *
from myScripts import *
from mpa_methods.mpa_main import *
import time

class mpa_probe_test:
	def __init__(self, DIR):
		# Classes
		self.DIR = DIR
		exists = False
		version = 0
		while not exists:
			if not os.path.exists(self.DIR+"_v"+str(version)):
				print(self.DIR)
				self.DIR = self.DIR+"_v"+str(version)
				os.makedirs(self.DIR)
				exists = True
			version += 1
		print(self.DIR + "<<< USING THIS")
		self.mpa = mpa;
		self.I2C = I2C;
		self.fc7 = fc7;
		self.cal = cal;
		self.test = test;
		self.bias = bias;
		# Variables
		self.GlobalSummary = []
		self.LogFile = open(self.DIR+"/LogFile.txt", "w")
		self.Legend = ["Chip_N", "I/O pwr reset" , "Digital pwr reset", "Analog pwr reset", "I/O pwr " , "Digital pwr ", "Analog pwr ", "Shift Test", "Ground Value", "Bias Average Cal", "Gain", "Threshold LSB", "Calibration LSB", "Noise [Cal LSB]", "Threshold Spread [Cal LSB]", "Pixel test", "Strip input test", "Memory @ 1.2 test", "Memory @ 1.0 test"]
		self.LogFileCSV = open(self.DIR+"/LogFile.txt", "w")
		self.GeneralLogFile = open(self.DIR+"/../LogFile.txt", "a")
		self.colprint("Creating new chip measurement: "+self.DIR)
		self.Flag = 1
		# Current Limits
		self.current_limit_pads_high = 25
		self.current_limit_pads_low = 5
		self.current_limit_digital_high = 200
		self.current_limit_digital_low = 100
		self.current_limit_digital_high_leakage = 20
		self.current_limit_digital_low_leakage = 5
		self.current_limit_analog_high = 100
		self.current_limit_analog_low = 50
		# Analog Paramters
		self.ideal_th_LSB = 1.456
		self.ideal_cl_LSB = 0.035
		self.high_th_DAC = 250
		self.high_cl_DAC = 90
		self.trim_th_DAC = 150
		self.trim_cl_DAC = 40
		self.low_th_DAC = 100
		self.low_cl_DAC = 15
		self.high_cl_ofs = 30
		self.trim_amplitude = 20
		# Digital Paramters
		self.signal_integrity_limit = 0.99


	def RUN(self, chipinfo, N = 99):
		self.colprint(chipinfo)
		self.colprint_general(chipinfo)
		self.GlobalSummary = [-1000]*19
		self.GlobalSummary[0] = N
		self.start = time.time()
		PowerFlag1 = 1
		PowerFlag2 = 1
		try:
			self.mpa.pwr.set_supply(mode = 'on', d = 1.00, a = 1.2, p = 1.2, bg = 0.270, measure = False, display = False)
			self.mpa.pwr._disable()
			PowerStatus, PowerFlag1 = self.power_on_check(leakage = 1)
			self.colprint(PowerStatus)
			self.colprint_general(PowerStatus)
			if PowerFlag1:
				PST1 = self.PVALS[0]; self.GlobalSummary[1] = PST1; DP1  = self.PVALS[1]; self.GlobalSummary[2] = DP1; AN1  = self.PVALS[2]; self.GlobalSummary[3] = AN1
				self.colprint("Enabling MPA")
				self.mpa.pwr._enable()
				PowerStatus, PowerFlag2 = self.power_on_check(leakage = 0)
				self.colprint(PowerStatus)
				self.colprint_general(PowerStatus)
				if PowerFlag2:
					PST2 = self.PVALS[0]; self.GlobalSummary[4] = PST2; DP2  = self.PVALS[1]; self.GlobalSummary[5] = DP2; AN2  = self.PVALS[2]; self.GlobalSummary[6] = AN2
					self.mpa.init_probe()
					with open(self.DIR+'/PowerMeasurement.csv', 'wb') as csvfile:
						CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
						DigP = [DP1, DP2, AN1, AN2, PST1, PST2]
						CVwriter.writerow(DigP)
					if self.test.shift(verbose = 0):
						self.colprint("Shift Test Passed")
						self.GlobalSummary[7] = 1
					else:
						self.colprint("Shift Test Failed")
						self.GlobalSummary[7] = 0
					self.analog_measurement()
					self.digital_test()
					self.colprint("DONE!")
		except:
			self.colprint("WE MESSED UP!!!")
			sys.stdout.write("\033[1;31m")
			print("WE MESSED UP!!!")
			sys.stdout.write("\033[0;0m")
			self.Flag = 0
		self.mpa.pwr.set_supply(mode = 'off', measure = False)
		if (PowerFlag1 == 0) or (PowerFlag2 == 0):
			self.colprint("Power Error")
			self.colprint_general("Power Error")
			sys.stdout.write("\033[1;31m")
			print("Power Error!!!")
			sys.stdout.write("\033[0;0m")
		if (os.path.isfile(self.DIR+'/../GlobalSummary.csv')):
			with open(self.DIR+'/../GlobalSummary.csv', 'a') as csvfile:
				CVwriter = csv.writer(csvfile, delimiter=',',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
				CVwriter.writerow(self.GlobalSummary)
		else:
			with open(self.DIR+'/../GlobalSummary.csv', 'w') as csvfile:
				CVwriter = csv.writer(csvfile, delimiter=',',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
				CVwriter.writerow(self.Legend)
				CVwriter.writerow(self.GlobalSummary)
		with open(self.DIR+'/LogFile.csv', 'w') as csvfile:
			CVwriter = csv.writer(csvfile, delimiter=',',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for i in range(0,19):
				CVwriter.writerow([self.Legend[i], self.GlobalSummary[i]])
		self.end = time.time()
		self.colprint("TOTAL TIME:")
		self.colprint(str(round(self.end - self.start)) + "sec")
		self.colprint_general("TOTAL TIME:")
		self.colprint_general(str(round(self.end - self.start)) + "sec")
		return self.Flag
	def colprint(self, text):
		sys.stdout.write("\033[1;34m")
		print((str(text)))
		sys.stdout.write("\033[0;0m")
		self.LogFile.write(str(text)+"\n")
	def colprint_general(self, text):
		self.GeneralLogFile.write(str(text)+"\n")
	def analog_measurement(self, calibrate = 1, plot = 0):
		start_time = time.time()
		self.colprint("Doing Analog Measurement:")
		if calibrate:
			gnd = self.bias.measure_gnd()
			message = "Measured Analog Ground: " + str(round(np.mean(gnd),3))
			self.colprint(message)
			self.colprint_general(message)
			cal = self.bias.calibrate_chip(gnd_corr = gnd, print_file = 1, filename = self.DIR+"/bias_calibration")
			self.GlobalSummary[8] = round(np.mean(gnd),3)
			self.GlobalSummary[9] = round(np.mean(cal),1)
			message = "Average Analog Bias: " + str(round(np.mean(cal),1))
			self.colprint(message)
			self.colprint_general(message)
		self.bias.trimDAC_amplitude(self.trim_amplitude)
		thDAC = self.bias.measure_DAC_testblocks(point = 5, bit = 8, step = 127, plot = plot, print_file = 1, filename = self.DIR+"/Th_DAC", verbose = 0)
		calDAC = self.bias.measure_DAC_testblocks(point = 6, bit = 8, step = 127, plot = plot, print_file = 1, filename = self.DIR+"/Cal_DAC", verbose = 0)
		thLSB = np.mean((thDAC[:,127] - thDAC[:,0])/127)*1000 #LSB Threshold DAC in mV
		calLSB = np.mean((calDAC[:,127] - calDAC[:,0])/127)*0.035/1.768*1000 #LSB Calibration DAC in fC
		#thLSB = 1.456
		#calLSB = 0.035
		self.colprint("S curve measurement")
		self.colprint_general("S curve measurement")
		th_H = int(round(self.high_th_DAC*thLSB/self.ideal_th_LSB))
		th_T = int(round(self.trim_th_DAC*thLSB/self.ideal_th_LSB))
		th_L = int(round(self.low_th_DAC*thLSB/self.ideal_th_LSB))
		cal_H = int(round(self.high_cl_DAC*self.ideal_cl_LSB/calLSB))
		cal_T = int(round(self.trim_cl_DAC*self.ideal_cl_LSB/calLSB))
		cal_L = int(round(self.low_cl_DAC*self.ideal_cl_LSB/calLSB))
		try:
			self.mpa.ctrl_base.disable_test()
			data_array,cal_A, noise_A, trim, pix_out = self.cal.trimming_probe(ref = th_H, low = cal_H - self.high_cl_ofs, req = cal_H, high = cal_H + self.high_cl_ofs, nominal_ref = th_T, nominal_req = cal_T, trim_ampl = self.trim_amplitude, rbr = 0, plot = plot)
			scurve, cal_B, noise_B  = self.cal.s_curve( n_pulse = 1000, s_type = "CAL", rbr = 0, ref_val = th_L, row = list(range(1,17)), step = 1, start = 0, stop = 100, pulse_delay = 500, extract_val = cal_L, extract = 1, plot = plot, print_file = 1, filename = self.DIR+ "/Scurve15")
			gain = (th_T-th_L)/(np.mean(cal_A[1:1920]) - np.mean(cal_B[1:1920])) * thLSB / calLSB # Average
			self.colprint("The average gain is: " + str(round(gain,1))); self.GlobalSummary[10] = round(gain,1)
			self.colprint("The thLSB is: " + str(round(thLSB,3))); self.GlobalSummary[11] = round(thLSB,3)
			self.colprint("The calLSB is: " + str(round(calLSB,3)));  self.GlobalSummary[12] = round(calLSB,3)
			self.colprint("The noise is: " + str(round(np.mean(noise_B[1:1919]),2))); self.GlobalSummary[13] = round(np.mean(noise_B[1:1919]),2)
			self.colprint("The threshold spread is: " + str(round(np.std(cal_B[1:1919]),2))); self.GlobalSummary[14] = round(np.std(cal_B[1:1919]),2)
			self.colprint_general("successfull!")
			with open(self.DIR+'/AnalogMeasurement.csv', 'wb') as csvfile:
				CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
				AnalogValues = [thLSB, calLSB, np.mean(noise_B), np.std(cal_B), gain]
				CVwriter.writerow(AnalogValues)
			print("Analog measurement Elapsed Time: " + str(time.time() - start_time))
			return 1
		except TypeError:
			self.colprint("SCURVE EXTRACTION FAILED")
			self.colprint_general("SCURVE EXTRACTION FAILED")
			return 0
	def digital_test(self):
		# Analog Injection pixel test
		self.colprint("Doing digital test")
		anapix = []
		#self.mpa.init_probe()
		self.mpa.ctrl_pix.disable_pixel(0,0)
		anapix.append(self.test.analog_pixel_test(print_log=0, verbose = 0))
		if ((len(anapix[0]) > 0) & (len(anapix[0]) < 50)) :
			anapix.append(self.test.analog_pixel_test(print_log=0, verbose = 0))
			BadPixA = self.GetActualBadPixels(anapix)
		else: BadPixA = anapix[0]
		self.colprint(str(np.size(BadPixA)) + " << Bad Pixels (Ana)")
		self.GlobalSummary[15] = np.size(BadPixA)
		self.colprint_general(str(np.size(BadPixA)) + " << Bad Pixels (Ana)")
		Analog = 1
		if (BadPixA == []): Analog = 0
		with open(self.DIR+'/BadPixelsA.csv', 'wb') as csvfile:
			CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for i in BadPixA: CVwriter.writerow(i)
		# Input Strip Test:
		strip_in = self.test.strip_in_scan(print_file = 1, filename = self.DIR + "/striptest", probe=1, verbose = 0)
		good_si = 0
		for i in range(0,8):
			if (strip_in[i,:].all() > self.signal_integrity_limit): good_si = 1
		if good_si:
			self.colprint("Strip Input scan passed");
			self.colprint_general("Strip Input scan passed")
			StripIn = 0
		else:
			self.colprint("Changing edge")
			strip_in = self.test.strip_in_scan(print_file = 1, edge = "rising", filename = self.DIR + "/striptest", probe=1, verbose = 0)
			good_si = 0
			for i in range(0,8):
				if (strip_in[i,:].all() > self.signal_integrity_limit): good_si = 1
			if good_si:
				self.colprint("Strip Input scan passed (changing edge)")
				self.colprint_general("Strip Input scan passed (changing edge)")
				StripIn = 0
			else:
				self.colprint("Strip Input scan failed")
				self.colprint_general("Strip Input scan failed")
				StripIn = 1
		self.GlobalSummary[16] = StripIn
		## MEMORY Test
		self.colprint("Memory test at 1.2 V")
		self.colprint_general("Memory test at 1.2 V")
		Mem12 = self.memory_test(125)
		if Mem12:
			self.colprint("Fail at 1.2 V. Not running test at 1 V")
			self.colprint_general("Fail at 1.2 V. Not running test at 1 V")
			Mem10 = 1;
		else:
			self.colprint("Memory test at 1.0 V")
			self.colprint_general("Memory test at 1.0 V")
			Mem10 = self.memory_test(105)
		# Digital Summary filename
		self.GlobalSummary[17] = Mem12
		self.GlobalSummary[18] = Mem10
		with open(self.DIR+'/DigitalSummary.csv', 'wb') as csvfile:
			CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
			DigitalFlags = [Analog, StripIn, Mem12, Mem10]
			CVwriter.writerow(DigitalFlags)

	def memory_test(self, voltage):
		self.mpa.pwr.set_dvdd(voltage/100.0)
		self.mpa.init_probe()
		bad_pix, error, stuck, i2c_issue, missing = self.test.mem_test(print_log=1, filename = self.DIR + "/LogMemTest_" + str(voltage) + ".txt", verbose = 0)
		mempix = []
		mempix.append(bad_pix)
		if ((len(mempix[0]) > 0) & (len(mempix[0]) < 20)):
			bad_pix, error, stuck, i2c_issue, missing = self.test.mem_test(print_log=1, filename = self.DIR + "/LogMemTest_" + str(voltage) + "_bis.txt", verbose = 0)
			mempix.append(bad_pix)
			BadPixM = self.GetActualBadPixels(mempix)
		BadPixM = mempix[0]
		self.colprint(str(len(BadPixM)) + " << Bad Pixels (Mem)")
		self.colprint_general(str(len(BadPixM)) + " << Bad Pixels (Mem)")
		# Write Failing Pixel
		with open(self.DIR+"/BadPixelsM_" + str(voltage) + ".csv", 'wb') as csvfile:
			CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for i in BadPixM: CVwriter.writerow(i)
		# Save Statistics
		with open(self.DIR+"/Mem" + str(voltage) + "_Summary.csv", 'wb') as csvfile:
			CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
			Memory12Flags = [len(BadPixM), stuck, i2c_issue, missing]
			CVwriter.writerow(Memory12Flags)
		# Set Flags for final summary
		if ((len(BadPixM)<10) and (stuck <10) and (i2c_issue < 10) and (missing <10)): 	return 0
		else: return  1

	def GetActualBadPixels(self, BPA):
		#print BPA
		badpix = BPA[0]
		goodpix = []
		for i in range(1, len(BPA)):
			for j in badpix:
				if j not in BPA[i]:
					goodpix.append(j)
		for i in goodpix:
			badpix.remove(i)
		return badpix

	def power_on_check(self, leakage):
		self.PVALS = ["0","0","0"]
		self.colprint("Checking Power-On...")
		PowerMessage = ""
		flag = 1
		self.PVALS[0] = self.mpa.pwr.get_power_pads()
		self.PVALS[1] = self.mpa.pwr.get_power_digital()
		self.PVALS[2] = self.mpa.pwr.get_power_analog()
		if (self.PVALS[0] > self.current_limit_pads_high): PowerMessage += "Pad power too high! ("+str(self.PVALS[0])+")"; flag = 0
		elif (self.PVALS[0] < self.current_limit_pads_low): PowerMessage += "Pad power too low! ("+str(self.PVALS[0])+")"; flag = 0
		else: PowerMessage += "Pad power OK! ("+str(self.PVALS[0])+")  "
		if leakage:
			if (self.PVALS[1] > self.current_limit_digital_high_leakage): PowerMessage += "Digital power too high! ("+str(self.PVALS[1])+")"; flag = 0
			elif (self.PVALS[1] < self.current_limit_digital_low_leakage):  PowerMessage += "Digital power too low!  ("+str(self.PVALS[1])+")"; flag = 0
			else: PowerMessage += "Digital power OK! ("+str(self.PVALS[1])+")  "
		else:
			if (self.PVALS[1] > self.current_limit_digital_high): PowerMessage += "Digital power too high! ("+str(self.PVALS[1])+")"; flag = 0
			elif (self.PVALS[1] < self.current_limit_digital_low):  PowerMessage += "Digital power too low!  ("+str(self.PVALS[1])+")"; flag = 0
			else: PowerMessage += "Digital power OK! ("+str(self.PVALS[1])+")  "
		if (self.PVALS[2] > self.current_limit_analog_high): PowerMessage += "Analog power too high! ("+str(self.PVALS[2])+")"; flag = 0
		elif (self.PVALS[2] < self.current_limit_analog_low):  PowerMessage += "Analog power too low!  ("+str(self.PVALS[2])+")"; flag = 0
		else: PowerMessage += "Analog power OK! ("+str(self.PVALS[2])+")  "
		return PowerMessage, flag
