#
import csv
import numpy
import time
import sys
from d19cScripts import *
from myScripts import *
import time


class mpa_probe_test:
	def __init__(self, DIR, mpa, I2C, fc7, cal, test, bias):
		# Classes
		self.mpa = mpa;
		self.I2C = I2C;
		self.fc7 = fc7;
		self.cal = cal;
		self.test = test;
		self.bias = bias;
		# Variables
		self.DIR = DIR
		self.LogFile = open(self.DIR+"/LogFile.txt", "w")
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

	def RUN(self, chipinfo):
		self.colprint(chipinfo)
		self.colprint_general(chipinfo)
		self.start = time.time()
		try:
			self.mpa.pwr.set_supply(mode = 'on', d = 1.00, a = 1.2, p = 1.2, bg = 0.270, display = False)
			self.mpa.pwr._disable()
			PowerStatus = self.power_on_check(leakage = 1)
			self.colprint_general(PowerStatus)
			PST1 = self.PVALS[0]; DP1  = self.PVALS[1]; AN1  = self.PVALS[2]
			self.colprint("Enabling MPA")
			self.mpa.pwr._enable()
			PowerStatus = self.power_on_check(leakage = 0)
			self.colprint_general(PowerStatus)
			PST2 = self.PVALS[0]; DP2  = self.PVALS[1]; AN2  = self.PVALS[2]
			self.mpa.init_probe()
			#PowerStatus = self.power_on_check(leakage = 0)
			#self.colprint_general(PowerStatus)
			#PST3 = self.PVALS[0]; DP3  = self.PVALS[1]; AN3  = self.PVALS[2]
			with open(self.DIR+'/PowerMeasurement.csv', 'wb') as csvfile:
				CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
				#DigP = [DP1, DP2, DP3, AN1, AN2, AN3, PST1, PST2, PST3]
				DigP = [DP1, DP2, AN1, AN2, PST1, PST2]
				CVwriter.writerow(DigP)
			if self.test.shift(verbose = 0): self.colprint("Shift Test Passed")
			else: self.colprint("Shift Test Failed")
			self.Flag = self.analog_measurement()
			self.digital_test()
			self.colprint("DONE!")
			sleep(0.1)
		except:
			self.colprint("WE MESSED UP!!!")
			self.Flag = 0
			self.mpa.pwr.off()
		self.end = time.time()
		self.colprint("TOTAL TIME:")
		self.colprint(str((self.end - self.start)/60.))
		self.colprint_general("TOTAL TIME:")
		self.colprint_general(str((self.end - self.start)/60.))
		return self.Flag

	def colprint(self, text):
		sys.stdout.write("\033[1;31m")
		print(str(text))
		sys.stdout.write("\033[0;0m")
		self.LogFile.write(str(text)+"\n")
	def colprint_general(self, text):
		self.GeneralLogFile.write(str(text)+"\n")
	def analog_measurement(self, calibrate = 1, plot = 0):
		start_time = time.time()
		self.colprint("Doing Analog Measurement:")
		if calibrate:
			gnd = self.bias.measure_gnd()
			self.bias.calibrate_chip(gnd_corr = gnd)
		self.bias.trimDAC_amplitude(self.trim_amplitude)
		thDAC = self.bias.measure_DAC_testblocks(point = 5, bit = 8, step = 127, plot = plot, print_file = 1, filename = self.DIR+"/Th_DAC")
		calDAC = self.bias.measure_DAC_testblocks(point = 6, bit = 8, step = 127, plot = plot, print_file = 1, filename = self.DIR+"/Cal_DAC")
		thLSB = np.mean((thDAC[:,127] - thDAC[:,0])/127)*1000 #LSB Threshold DAC in mV
		calLSB = np.mean((calDAC[:,127] - calDAC[:,0])/127)*0.035/1.768*1000 #LSB Calibration DAC in fC
		#thLSB = 1.456
		#calLSB = 0.035
		self.colprint("S curve measurement")
		th_H = int(round(self.high_th_DAC*thLSB/self.ideal_th_LSB))
		th_T = int(round(self.trim_th_DAC*thLSB/self.ideal_th_LSB))
		th_L = int(round(self.low_th_DAC*thLSB/self.ideal_th_LSB))
		cal_H = int(round(self.high_cl_DAC*self.ideal_cl_LSB/calLSB))
		cal_T = int(round(self.trim_cl_DAC*self.ideal_cl_LSB/calLSB))
		cal_L = int(round(self.low_cl_DAC*self.ideal_cl_LSB/calLSB))
		try:
			self.mpa.ctrl_base.disable_test()
			data_array,cal_A, noise_A, trim, pix_out = self.cal.trimming_probe(ref = th_H, low = cal_H - self.high_cl_ofs, req = cal_H, high = cal_H + self.high_cl_ofs, nominal_ref = th_T, nominal_req = cal_T, trim_ampl = self.trim_amplitude, rbr = 0, plot = plot)
			scurve, cal_B, noise_B  = self.cal.s_curve( n_pulse = 1000, s_type = "CAL", rbr = 0, ref_val = th_L, row = range(1,17), step = 1, start = 0, stop = 100, pulse_delay = 500, extract_val = cal_L, extract = 1, plot = plot, print_file = 1, filename = self.DIR+ "/Scurve15")
			gain = (th_T-th_L)/(np.mean(cal_A[1:1920]) - np.mean(cal_B[1:1920])) * thLSB / calLSB # Average
			self.colprint("The average gain is: " + str(gain))
			self.colprint("The thLSB is: " + str(thLSB))
			self.colprint("The calLSB is: " + str(calLSB))
			self.colprint("The noise is: " + str(np.mean(noise_B[1:1919])))
			self.colprint("The threshold spread is: " + str(np.std(cal_B[1:1919])))
			self.colprint_general("SCURVE EXTRACTION SUCCESSFUL")
			with open(self.DIR+'/AnalogMeasurement.csv', 'wb') as csvfile:
				CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
				AnalogValues = [thLSB, calLSB, np.mean(noise_A), np.std(cal_A), gain]
				CVwriter.writerow(AnalogValues)
			print "Analog measurement Elapsed Time: " + str(time.time() - start_time)
			return 1

		except TypeError:
			self.colprint("SCURVE EXTRACTION FAILED")
			self.colprint_general("SCURVE EXTRACTION FAILED")
			return 0
	def digital_test(self):
		# Analog Injection pixel test
		self.colprint("Doing digital test")
		anapix = []
		self.mpa.init_probe()
		self.mpa.ctrl_pix.disable_pixel(0,0)
		anapix.append(self.test.analog_pixel_test(print_log=0))
		if len(anapix[0]) > 0:
			anapix.append(analog_pixel_test(print_log=0))
		BadPixA = self.GetActualBadPixels(anapix)
		self.colprint(str(BadPixA) + " << Bad Pixels (Ana)")
		self.colprint_general(str(BadPixA) + " << Bad Pixels (Ana)")
		Analog = 1
		if (BadPixA == []): Analog = 0
		with open(self.DIR+'/BadPixelsA.csv', 'wb') as csvfile:
			CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for i in BadPixA: CVwriter.writerow(i)
		# Input Strip Test:
		strip_in = self.test.strip_in_scan(print_file = 1, filename = self.DIR + "/striptest", probe=0)
		good_si = 0
		for i in range(0,8):
			if (strip_in[i,:].all() > self.signal_integrity_limit): good_si = 1
		if good_si:
			self.colprint("Strip Input scan passed")
			self.colprint_general("Strip Input scan passed")
			StripIn = 0
		else:
			self.colprint("Changing edge")
			strip_in = self.test.strip_in_scan(print_file = 1, edge = "rising", filename = self.DIR + "/striptest", probe=0)
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
		## MEMORY Test
		Mem12 = self.memory_test(125)
		if Mem12: 	Mem10 = 1;
		else: 		Mem10 = self.memory_test(105)
		# Digital Summary filename
		with open(self.DIR+'/DigitalSummary.csv', 'wb') as csvfile:
			CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
			DigitalFlags = [Analog, StripIn, Mem12, Mem10]
			CVwriter.writerow(DigitalFlags)


	def memory_test(self, voltage):
		self.mpa.pwr.set_dvdd(voltage/10)
		self.mpa.init_probe()
		bad_pix, error, stuck, i2c_issue, missing = self.test.mem_test(print_log=1, filename = self.DIR + "/LogMemTest_" + str(voltage) + ".txt", verbose = 0)
		mempix = []
		mempix.append(bad_pix)
		if len(mempix[0]) > 0:
			bad_pix, error, stuck, i2c_issue, missing = self.test.mem_test(print_log=1, filename = self.DIR + "/LogMemTest_" + str(voltage) + "_bis.txt", verbose = 0)
			mempix.append(bad_pix)
		BadPixM = self.GetActualBadPixels(mempix)
		self.colprint(str(len(BadPixM)) + " << Bad Pixels (Mem)")
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
		print BPA
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
		self.PVALS[0] = self.mpa.pwr.get_power_pads()
		self.PVALS[1] = self.mpa.pwr.get_power_digital()
		self.PVALS[2] = self.mpa.pwr.get_power_analog()
		if (self.PVALS[0] > self.current_limit_pads_high): return "Pad power too high! ("+str(self.PVALS[0])+")"
		elif (self.PVALS[0] < self.current_limit_pads_low): return "Pad power too low! ("+str(self.PVALS[0])+")"
		else: PowerMessage += "Pad power OK! ("+str(self.PVALS[0])+")  "
		if leakage:
			if (self.PVALS[1] > self.current_limit_digital_high_leakage): return "Digital power too high! ("+str(self.PVALS[1])+")"
			elif (self.PVALS[1] < self.current_limit_digital_low_leakage):  return "Digital power too low!  ("+str(self.PVALS[1])+")"
			else: PowerMessage += "Digital power OK! ("+str(self.PVALS[1])+")  "
		else:
			if (self.PVALS[1] > self.current_limit_digital_high): return "Digital power too high! ("+str(self.PVALS[1])+")"
			elif (self.PVALS[1] < self.current_limit_digital_low):  return "Digital power too low!  ("+str(self.PVALS[1])+")"
			else: PowerMessage += "Digital power OK! ("+str(self.PVALS[1])+")  "
		if (self.PVALS[2] > self.current_limit_analog_high): return "Analog power too high! ("+str(self.PVALS[2])+")"
		elif (self.PVALS[2] < self.current_limit_analog_low):  return "Analog power too low!  ("+str(self.PVALS[2])+")"
		else: PowerMessage += "Analog power OK! ("+str(self.PVALS[2])+")  "
		return PowerMessage
