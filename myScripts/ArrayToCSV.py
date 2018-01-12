import numpy as np
import pandas as pd

class CSVutility:
	
	def ArrayToCSV ( self, array, filename, index=None , columns=None):
		df = pd.DataFrame(array)
		if index:
			df.index = index
		if columns:
			df.columns = columns
		df.to_csv(filename)




