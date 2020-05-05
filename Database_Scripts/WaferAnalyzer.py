# Wafer Analyzer
import ROOT
from ROOT import *
import sys

def DrawWafer(Title):
	H = TH2F("Wafer"+Title, Title, 12, 0, 12, 10, 0, 10)
	H.SetStats(0)
	Y = H.GetYaxis()
	X = H.GetXaxis()
	Y.SetLabelSize(0)
	Y.SetNdivisions(0)
	X.SetLabelSize(0)
	X.SetNdivisions(0)
	Wafer = TEllipse(5.95, 5, 6.3, 5.25)
	Wafer.SetFillColor(17)
	Wafer.SetLineColor(17)
	White = TEllipse(5, 6, 14, 14)
	White.SetFillColor(0)
	Notch = TEllipse(5.95, 10.26, 0.15, 0.15)
	Notch.SetFillColor(0)
	Notch.SetLineColor(0)
	return (H, White, Wafer, Notch)

def PlotWafer(Wafer, Boxes, Title):
	C = TCanvas("C"+Title, "", 800, 800)
	C.cd()
	Wafer[0].Draw()
	Wafer[1].Draw("same")
	Wafer[2].Draw("same")
	Wafer[3].Draw("same")
	try:
		for i in Boxes:
			i.Draw("same")
	except:
		for i in Boxes:
			for j in i:
				for k in j:
					k.Draw("same")
	C.Print(Title + ".pdf")

def AssignDyeColor(D, n, c, t):
	D[n-1].Clear()
	D[n-1].SetFillColor(c)
	D[n-1].AddText("   " + t + "   ")
def AssignPixelColor(D, i, j, k, c, t):
	print i,j,k
	P = D[i-1][j-1][k-1]
	P.Clear()
	P.SetFillColor(c)
	P.AddText("   " + t + "   ")
def AssignChipNum(D,c,t):
	D[c-1].AddText(" " + t + " ")
def DrawDyes():
	Dyes = []
	Pixels = []
	#for i in range(0,13):
	#	for j in range(0,10):
	#		b = TPaveText(i,j,1+1,j+1)
	#		b.SetFillColor(kRed)
	#		b.SetLineColor(kRed)
	#		Boxes.append(b)
	for i in range(1,89):
		subpix = []
		if i < 4:
			cord = [4+i, 9, 5+i, 10]
		elif i < 12:
			cord = [13-i, 8, 14-i, 9]
		elif i < 22:
			cord = [1+(i-12), 7, 2+(i-12), 8]
		elif i < 33:
			cord = [33-i, 6, 34-i, 7]
		elif i < 45:
			cord = [0+(i-33), 5, 1+(i-33), 6]
		elif i < 57:
			cord = [56-i, 4, 57-i, 5]
		elif i < 68:
			cord = [1+(i-57), 3, 2+(i-57), 4]
		elif i < 78:
			cord = [78-i, 2, 79-i, 3]
		elif i < 86:
			cord = [1+(i-77), 1, 2+(i-77), 2]
		elif i < 89:
			cord = [93-i, 0, 94-i, 1]
		else: print "There is a serious problem here..."

		b = TPaveText(cord[0],cord[1],cord[2],cord[3])
		b.SetFillColor(kRed)
		b.AddText(str(i))
		for r in range(16):
			row = []
			for p in range(118):
				pcord = [
						cord[2] - 1/118.*(p+1),
						cord[3] - 1/16.*(r+1),
						cord[2] - 1/118.*(p),
						cord[3] - 1/16.*(r)
				]
				pix = TPaveText(pcord[0],pcord[1],pcord[2],pcord[3])
				pix.SetFillColor(kTeal)
				row.append(pix)
			subpix.append(row)
		Dyes.append(b)
		Pixels.append(subpix)
	return [Dyes, Pixels]

def GetColorYtoG(V, l, h):
	C = (V-l)/(h-l)
	return 1000 + int(C*150)



if __name__ == "__main__":


	
	W1 = DrawWafer("1^{st} Wafer")
	gB1 = DrawDyes()
	bB1 = DrawDyes()
	cB1 = DrawDyes()
	BanaPix1 = DrawDyes()
	W2 = DrawWafer("2^{st} Wafer")
	gB2 = DrawDyes()
	bB2 = DrawDyes()
	cB2 = DrawDyes()
	BanaPix2 = DrawDyes()

	for i in range(0,88):
		AssignDyeColor(BanaPix1[0],i+1,kGreen,str(i+1))
		AssignDyeColor(BanaPix2[0],i+1,kGreen,str(i+1))


	F = TFile("WaferData.root")
	T = F.Get("TREE")
	n = T.GetEntries()
	for j in range(0, n):# Here is where we loop over all events. This program only looks at 2 wafers at a time. You can modify that 
		T.GetEntry(j) #get information about each of the events
		Wafer = T.WaferNumber
		Chip = T.ChipNumber
		BiasDAC = T.MeanBiasDAC
		GRND = T.Ground
		if BiasDAC < 0: # this section is for the Bias and ground plots
			bC = kRed
			bp = ""
		else: 
			bC = GetColorYtoG(BiasDAC, 13, 17)
			bp = '%2.2f' % (BiasDAC)
		gp = '%1.3f' % (GRND)
		gC = GetColorYtoG(GRND, 0.01, 0.14)


		BadAnaPix = [] # this section is for the bad analog pixels
		nBAP = T.nBadAnaPix
		print nBAP # first we look at bad chips
		if nBAP > 0 and Wafer == int("0x07B5", 0):
			AssignDyeColor(BanaPix1[0],Chip,kRed,str(Chip)) #0 index is for the plot that shows bad cips 
			print "Chip" + str(Chip)
			print nBAP
		if nBAP > 0 and Wafer == int("0x11A3", 0):
			AssignDyeColor(BanaPix2[0],Chip,kRed,str(Chip))
			print "Wafer 07B5 Chip" + str(Chip)
			print nBAP			
		for i in range(nBAP): # then we look at bad pixels
			r = T.BadAnaPixRow[i]
			p = T.BadAnaPixPix[i]
			#print r,p
			BadAnaPix.append([r,p])
			if Wafer == int("0x07B5", 0): # note that you should change the name here for different wafers
				AssignPixelColor(BanaPix1[1], Chip, r, p, kRed, "") # 1 index is for the pixel plots

			if Wafer == int("0x11A3",0): # same as above
				AssignPixelColor(BanaPix2[1], Chip, r, p, kRed, "")
				


		if Wafer == int("0x07B5", 0):
			AssignDyeColor(bB1[0], Chip, bC, bp)
			AssignDyeColor(gB1[0], Chip, gC, gp)
		if Wafer == int("0x11A3",0):
			AssignDyeColor(bB2[0], Chip, bC, bp)
			AssignDyeColor(gB2[0], Chip, gC, gp)


	PlotWafer(W1, bB1[0], "W1Bias") # plotting bias and ground
	PlotWafer(W2, bB2[0], "W2Bias")
	PlotWafer(W1, gB1[0], "W1Ground")
	PlotWafer(W2, gB2[0], "W2Ground")
	PlotWafer(W1, BanaPix1[1], "AnaPix_07B5") # plotting pixels
	PlotWafer(W2, BanaPix2[1], "AnaPix_11A3")
	PlotWafer(W1, BanaPix1[0], "Ana_07B5") # plotting chips
	PlotWafer(W2, BanaPix2[0], "Ana_11A3")










