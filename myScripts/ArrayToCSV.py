import numpy as np
import pandas as pd

class CSVutility:

	def ArrayToCSV(self, array, filename, index=None , columns=None, transpose = False):
		if (transpose == True):
			df = pd.DataFrame(array.transpose())
		else:
			df = pd.DataFrame(array)
		if index:
			df.index = index
		if columns:
			df.columns = columns
		df.to_csv(filename)

	def csv_to_array(self, filename):
		temp = pd.read_csv(filename)
		array = np.array(temp)
		return array

	def csv_to_array_en(self, filename):
		temp = pd.read_csv(filename, sep=',|;', engine='python')
		array = np.array(temp)
		return array

	def array_to_csv(self, array, filename, index=None , columns=None, transpose = False): #for compatibility
		self.ArrayToCSV(array, filename, index , columns, transpose)



	def CsvToArray(self, filename): #for compatibility
		return self.csv_to_array(filename)

CSV = CSVutility()
