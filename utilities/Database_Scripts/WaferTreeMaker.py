#####

import ROOT
import array
import scipy
from array import array
from ROOT import *
import csv
import scipy
import os


F = TFile("WaferData.root", "recreate")
F.cd()

T = TTree("TREE", "TREE")
# wafer number is difficult to acquire 
Wafer = array('I', [0])
T.Branch("WaferNumber", Wafer, "WaferNumber/I") # not necessarily number anymore?
Chip = array('I', [0])
T.Branch("ChipNumber", Chip, "ChipNumber/I")
Run = array('I', [0])
T.Branch("TestNumber", Run, "TestNumber/I")
MeanBiasDAC = array('f', [0])
T.Branch("MeanBiasDAC", MeanBiasDAC, "MeanBiasDAC/f")
Ground = array('f', [0])
T.Branch("Ground", Ground, "Ground/f")
VDDPST = array('f', [0])
T.Branch("VDDPST", VDDPST, "VDDPST/f")
DVDD = array('f', [0])
T.Branch("DVDD", DVDD, "DVDD/f")
AVDD = array('f', [0])
T.Branch("AVDD", AVDD, "AVDD/f")
StripLatency = array('f', [0])
T.Branch("StripLatency", StripLatency, "StripLatency/f")
StripLatencyMin = array('f', [0])
T.Branch("StripLatencyMin", StripLatencyMin, "StripLatencyMin/f")
nBadAnaPix = array('I', [0])
T.Branch("nBadAnaPix", nBadAnaPix, "nBadAnaPix/I")
BadAnaPixRow = array('I', [0]*1888)
T.Branch("BadAnaPixRow", BadAnaPixRow, "BadAnaPixRow[1904]/I")
BadAnaPixPix = array('I', [0]*1888)
T.Branch("BadAnaPixPix", BadAnaPixPix, "BadAnaPixPix[1904]/I")
#nBadDigPix = array('I', [0])
#no dig pixels anymore 
#T.Branch("nBadDigPix", nBadDigPix, "nBadDigPix/I")
#BadDigPixRow = array('I', [0]*1888)
#T.Branch("BadDigPixRow", BadDigPixRow, "BadDigPixRow[1904]/I")
#BadDigPixPix = array('I', [0]*1888)
#T.Branch("BadDigPixPix", BadDigPixPix, "BadDigPixPix[1904]/I")

#new 
#for BadPixelM_10.csv
nBadM_10Pix = array('I', [0])
T.Branch("nBadM_10Pix", nBadM_10Pix, "nBadM_10Pix/I")
BadM_10PixRow = array('I', [0]*1888)
T.Branch("BadM_10PixRow", BadM_10PixRow, "BadM_10PixRow[1904]/I")
BadM_10PixPix = array('I', [0]*1888)
T.Branch("BadM_10PixPix", BadM_10PixPix, "BadM_10PixPix[1904]/I")

#for BadPixelM_12.csv
nBadM_12Pix = array('I', [0])
T.Branch("nBadM_12Pix", nBadM_12Pix, "nBadM_12Pix/I")
BadM_12PixRow = array('I', [0]*1888)
T.Branch("BadM_12PixRow", BadM_12PixRow, "BadM_12PixRow[1904]/I")
BadM_12PixPix = array('I', [0]*1888)
T.Branch("BadM_12PixPix", BadM_12PixPix, "BadM_12PixPix[1904]/I")




Chips = []

for x in os.walk("ProbeStationResults"): #ProbeStationResults is file containing wafers, walks thorugh all subdirectories, no further (maybe options for that)
	if "ChipN" in x[0] and "wrong" not in x[0]: #if file is chip (with wafer before) 
		print x[0]
		Xw = x[0].split("/")[1] # This will be the file containing the wafer string
		W = Xw.split("_N6T903-")[1] # Wafer identification
		Xcv = x[0].split("/")[2]
		C = Xcv.split("N_")[1].split("_v")[0] # Chip identification
		V = Xcv.split("_v")[1] #version identification? pick greatest version (is wrong also no go?)
		Chips.append([W,C,V])

for c in Chips:#pick greatest version
	if int(c[2]) > 0:
		for cc in Chips:
			if cc[0] == c[0] and cc[1] == c[1] and int(cc[2]) < int(c[2]): Chips.remove(cc)

for c in Chips: 
	print c[0]

for i in Chips:
#	Wafer[0] = int(i[0]) #ignore wafer number for now 
	Wafer[0] = int("0x" + i[0], 0)
	print i[0]
	print Wafer[0]
	Chip[0] = int(i[1])
	Run[0] = int(i[2])
	Folder = "ProbeStationResults/Wafer_N6T903-"+i[0]+"/ChipN_"+i[1]+"_v"+i[2] #different identification, now is split into folders, keep note of this 
	#print "looking in " + Folder

	try:
		with open(Folder + "/LogFile.txt") as LOG: #look in LogFile and begin adding values to tree
			for line in LOG:
				if "GROUND IS " in line: 
					Ground[0] = float(line.split(" ")[2])
				if "VDDPST" in line:
					VDDPST[0] = float(line.split(" ")[2]) # multiple cases where these appear, take last one?
				if "DVDD" in line:
					DVDD[0] = float(line.split(" ")[2])
				if "AVDD" in line:
					AVDD[0] = float(line.split(" ")[2])
	except:
		Ground[0] = 0.
		VDDPST[0] = 0.
		DVDD[0] = 0.
		AVDD[0] = 0.

	try:
		with open(Folder + "/Bias_DAC.csv", 'rb') as CSV: # Open csv file
			BDCSV = csv.reader(CSV) #read the csv in rows 
			BDCSV.next() #get rid of first index row
			Tuple = map(tuple, BDCSV)# turn each row into a ntuple
			for l in Tuple:
				for i in l:
					if i != l[0]:
						MeanBiasDAC[0] += int(i)#go into each ntuple and add together all non index values
		MeanBiasDAC[0] = MeanBiasDAC[0]/24. #question, had 35 before, but now only 24 entries 
	except:
		MeanBiasDAC[0] = -1.#-1 when the file doesn't exist 
	try:
		with open(Folder + "/striptest_npulse_5.csv", 'rb') as SSALines:
			SCSV = csv.reader(SSALines) # get rows
			SCSV.next()  # remove index
			Tuple = map(tuple, SCSV) # ntuplize 
			keepline = [] # list of lines that are kept and analyzed
			for l in Tuple:
				L = list(l)	# make into list so can use all and append to list
				L.remove(l[0]) # remove the index
				if all(float(x) > 0.0 for x in L): keepline.append(L) #if all non-zero, good to keep, keep as single element of list
			if len(keepline) == 1:# if exactly one line is good, keep and calculate values from it?
				for n, i in enumerate(keepline[0]):
					keepline[0][n] = float(i)# change to float
				StripLatency[0] = scipy.mean(keepline[0])#average latency
				StripLatencyMin[0] = min(keepline[0])# find minimum 
			else: # if more than 1 line or 0 lines, no latency?
				StripLatency[0] = 0.
				StripLatencyMin[0] = 0.
	except:
		StripLatency[0] = -1.
		StripLatencyMin[0] = -1.
	try:
		with open(Folder + "/BadPixelsA.csv") as BPA:
			nBPA = 0
			for L in BPA:
				BadAnaPixPix[nBPA] = int(L.split(" ")[0])-1
				BadAnaPixRow[nBPA] = int(L.split(" ")[1])
				nBPA += 1
			nBadAnaPix[0] = nBPA
	except:
		nBadAnaPix[0] = 1888
	try:
		with open(Folder + "/BadPixelsM_10.csv") as BPA:
			nBPM_10 = 0
			for L in BPA:
				BadM_10PixPix[nBPA] = int(L.split(" ")[0])-1
				BadM_10PixRow[nBPA] = int(L.split(" ")[1])
				nBPM_10 += 1
			nBadM_10Pix[0] = nBPM_10
	except:
		nBadM_10Pix[0] = 1888
# no digital pixels anymore 
#	try:
#		with open(Folder + "/BadPixelsD.csv") as BPD:
#			nBPD = 0
#			for L in BPD:
#				BadDigPixPix[nBPD] = int(L.split(" ")[0])-1
#				BadDigPixRow[nBPD] = int(L.split(" ")[1])
#				nBPD += 1
#			nBadDigPix[0] = nBPD
#	except:
#		nBadDigPix[0] = 1888


	T.Fill()
	#Reset
F.Write()
F.Close()