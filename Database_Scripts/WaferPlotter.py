import ROOT
from ROOT import *

def OldPlotWafer(A, name, title):

	H = TH2F("W"+name, title, 12, 0, 12, 10, 0, 10)
	H.SetStats(0)
	Y = H.GetYaxis()
	X = H.GetXaxis()
	Y.SetLabelSize(0)
	Y.SetNdivisions(0)
	X.SetLabelSize(0)
	X.SetNdivisions(0)

	H.SetBinContent(H.GetBin(6,10), A[0])
	H.SetBinContent(H.GetBin(7,10), A[1])
	H.SetBinContent(H.GetBin(8,10), A[2])

	H.SetBinContent(H.GetBin(10,9), A[3])
	H.SetBinContent(H.GetBin(9,9), A[4])
	H.SetBinContent(H.GetBin(8,9), A[5])
	H.SetBinContent(H.GetBin(7,9), A[6])
	H.SetBinContent(H.GetBin(6,9), A[7])
	H.SetBinContent(H.GetBin(5,9), A[8])
	H.SetBinContent(H.GetBin(4,9), A[9])
	H.SetBinContent(H.GetBin(3,9), A[10])

	H.SetBinContent(H.GetBin(2,8), A[11])
	H.SetBinContent(H.GetBin(3,8), A[12])
	H.SetBinContent(H.GetBin(4,8), A[13])
	H.SetBinContent(H.GetBin(5,8), A[14])
	H.SetBinContent(H.GetBin(6,8), A[15])
	H.SetBinContent(H.GetBin(7,8), A[16])
	H.SetBinContent(H.GetBin(8,8), A[17])
	H.SetBinContent(H.GetBin(9,8), A[18])
	H.SetBinContent(H.GetBin(10,8), A[19])
	H.SetBinContent(H.GetBin(11,8), A[20])

	H.SetBinContent(H.GetBin(12,7), A[21])
	H.SetBinContent(H.GetBin(11,7), A[22])
	H.SetBinContent(H.GetBin(10,7), A[23])
	H.SetBinContent(H.GetBin(9,7), A[24])
	H.SetBinContent(H.GetBin(8,7), A[25])
	H.SetBinContent(H.GetBin(7,7), A[26])
	H.SetBinContent(H.GetBin(6,7), A[27])
	H.SetBinContent(H.GetBin(5,7), A[28])
	H.SetBinContent(H.GetBin(4,7), A[29])
	H.SetBinContent(H.GetBin(3,7), A[30])
	H.SetBinContent(H.GetBin(2,7), A[31])

	H.SetBinContent(H.GetBin(1,6), A[32])
	H.SetBinContent(H.GetBin(2,6), A[33])
	H.SetBinContent(H.GetBin(3,6), A[34])
	H.SetBinContent(H.GetBin(4,6), A[35])
	H.SetBinContent(H.GetBin(5,6), A[36])
	H.SetBinContent(H.GetBin(6,6), A[37])
	H.SetBinContent(H.GetBin(7,6), A[38])
	H.SetBinContent(H.GetBin(8,6), A[39])
	H.SetBinContent(H.GetBin(9,6), A[40])
	H.SetBinContent(H.GetBin(10,6), A[41])
	H.SetBinContent(H.GetBin(11,6), A[42])
	H.SetBinContent(H.GetBin(12,6), A[43])

	H.SetBinContent(H.GetBin(12,5), A[44])
	H.SetBinContent(H.GetBin(11,5), A[45])
	H.SetBinContent(H.GetBin(10,5), A[46])
	H.SetBinContent(H.GetBin(9,5), A[47])
	H.SetBinContent(H.GetBin(8,5), A[48])
	H.SetBinContent(H.GetBin(7,5), A[49])
	H.SetBinContent(H.GetBin(6,5), A[50])
	H.SetBinContent(H.GetBin(5,5), A[51])
	H.SetBinContent(H.GetBin(4,5), A[52])
	H.SetBinContent(H.GetBin(3,5), A[53])
	H.SetBinContent(H.GetBin(2,5), A[54])
	H.SetBinContent(H.GetBin(1,5), A[55])

	H.SetBinContent(H.GetBin(2,4), A[56])
	H.SetBinContent(H.GetBin(3,4), A[57])
	H.SetBinContent(H.GetBin(4,4), A[58])
	H.SetBinContent(H.GetBin(5,4), A[59])
	H.SetBinContent(H.GetBin(6,4), A[60])
	H.SetBinContent(H.GetBin(7,4), A[61])
	H.SetBinContent(H.GetBin(8,4), A[62])
	H.SetBinContent(H.GetBin(9,4), A[63])
	H.SetBinContent(H.GetBin(10,4), A[64])
	H.SetBinContent(H.GetBin(11,4), A[65])
	H.SetBinContent(H.GetBin(12,4), A[66])

	H.SetBinContent(H.GetBin(11,3), A[67])
	H.SetBinContent(H.GetBin(10,3), A[68])
	H.SetBinContent(H.GetBin(9,3), A[69])
	H.SetBinContent(H.GetBin(8,3), A[70])
	H.SetBinContent(H.GetBin(7,3), A[71])
	H.SetBinContent(H.GetBin(6,3), A[72])
	H.SetBinContent(H.GetBin(5,3), A[73])
	H.SetBinContent(H.GetBin(4,3), A[74])
	H.SetBinContent(H.GetBin(3,3), A[75])
	H.SetBinContent(H.GetBin(2,3), A[76])

	H.SetBinContent(H.GetBin(3,2), A[77])
	H.SetBinContent(H.GetBin(4,2), A[78])
	H.SetBinContent(H.GetBin(5,2), A[79])
	H.SetBinContent(H.GetBin(6,2), A[80])
	H.SetBinContent(H.GetBin(7,2), A[81])
	H.SetBinContent(H.GetBin(8,2), A[82])
	H.SetBinContent(H.GetBin(9,2), A[83])
	H.SetBinContent(H.GetBin(10,2), A[84])

	H.SetBinContent(H.GetBin(8,1), A[85])
	H.SetBinContent(H.GetBin(7,1), A[86])
	H.SetBinContent(H.GetBin(6,1), A[87])

	return H


A = []
for i in range(88):
	A.append(i+1)
print A

B = [0.1,1.,0.1,1.,0.1,0.1,0.1,0.1,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,0.1,0.1,1.,0.1,1.,1.,0.1,1.,1.,1.,1.,1.,1.,1.,0.1,1.,1.,0.1,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,0.1,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,1.,0.1,1.,1.]


H = PlotWafer(A, "test", "")
H1 = PlotWafer(B, "Quality", "Chip Quality, Wafer: N6T903-09A3")

Wafer = TEllipse(5.95, 5, 6.3, 5.25)
Wafer.SetFillColor(17)
Wafer.SetLineColor(17)
White = TEllipse(5, 6, 14, 14)
White.SetFillColor(0)
Notch = TEllipse(5.95, 10.26, 0.15, 0.15)
Notch.SetFillColor(0)
Notch.SetLineColor(0)

gStyle.SetPalette(kBlackBody)

C = TCanvas("C", "", 800, 800)
C.cd()
H1.Draw("text")
White.Draw("same")
Wafer.Draw("same")
H1.Draw("colsame")
Notch.Draw("same")
H.Draw("textsame")
C.Print("WaferMap.png")


