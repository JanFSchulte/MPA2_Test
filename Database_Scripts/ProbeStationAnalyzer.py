import ROOT
from ROOT import *
import csv

def ColorMatrix(a, name, title):
	print "Creating..."
	nY = len(a)
	nX = len(a[0])
	print "        ...   " + str(nX) + "x" + str(nY)
	Grid = TH2F(name, title, nX, 0, nX, nY, 0, nY)
	Grid.SetStats(0)
	ax = Grid.GetXaxis()
	ay = Grid.GetYaxis()
	for i in range(nY):
		for j in range(nX):
			B = Grid.GetBin(j+1,i+1)
			Grid.SetBinContent(B, a[i][j])
	ax.SetNdivisions(0)
	ay.SetNdivisions(0)
	C = TCanvas()
	C.cd()
	Grid.Draw("coltext")
	C.Print(name+".png")

def ReadVCALvals(loc, chipID):
	fullpath = loc + "CAL_VDACs.csv"
	with open(fullpath, 'rb') as F:
		R = csv.reader(F, delimiter=' ', quotechar='|')
		A = []
		for row in R:
			a = []
			for cell in row:
				a.append(int(cell.split(",")[1].split(')')[0]))
			A.append(a)
		A.reverse()
		print A
	ColorMatrix(A, chipID, "DAC values, (chip = "+chipID+")")
ReadVCALvals("", "test")