import mysql.connector
import csv
import numpy as np
import matplotlib.pyplot as plt
import sys

dbname = "WAFER_TYPE_AND_NUMBER"
tablename = "MPA_OR_SSA"

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="password"
)

#PASSWORD: MPA-SSA_Testing19

mycursor = mydb.cursor()

try:
	sql_query = "CREATE DATABASE %s" %(dbname)
	mycursor.execute(sql_query)
	print("Successfully created database: "+dbname)
except:
	print("Failed to create database: "+dbname)

sql_query = "SELECT @@datadir"
mycursor.execute(sql_query)
myresult = mycursor.fetchone()
print("Data is being stored at: "+str(myresult[0])+dbname)

mycursor.close()
mydb.close()

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="password",
  database=dbname
)

mycursor = mydb.cursor()

sql_query = "CREATE TABLE %s (ChipNumber INT AUTO_INCREMENT PRIMARY KEY)" %(tablename)
mycursor.execute(sql_query)

print("CREATED TABLE: "+tablename)

sql_query = "ALTER TABLE %s ADD COLUMN Digital_Leakage DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Digital_Initial DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Digital_Config DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Analog_Leakage DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Analog_Initial DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Analog_Config DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN IO_Leakage DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN IO_Initial DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN IO_Config DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN DigitalTest_Analog_Injection INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN DigitalTest_Strip_Input INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN DigitalTest_Memory12 INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN DigitalTest_Memory10 INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN AnalogMeasurement_ThLSB DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN AnalogMeasurement_CalLSB DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN AnalogMeasurement_Noise DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN AnalogMeasurement_ThSpread DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN AnalogMeasurement_Gain DOUBLE(10,4)" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Memory12_Error INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Memory12_Stuck INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Memory12_I2C INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Memory12_Missing INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Memory10_Error INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Memory10_Stuck INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Memory10_I2C INT" %(tablename)
mycursor.execute(sql_query)
sql_query = "ALTER TABLE %s ADD COLUMN Memory10_Missing INT" %(tablename)
mycursor.execute(sql_query)

try:
	sql_query = "DESCRIBE %s" %(tablename)
	mycursor.execute(sql_query)
	myresult = mycursor.fetchall()
	for x in myresult:
		for st in x: 
			sys.stdout.write("{:32s}".format(str(st)))
		sys.stdout.write('\n')
	print("Columns successfully added to table: "+tablename)
except:
	print("Failed to create table.")

for z in range(1,89):

	pathPowerMeasurement = '/home/david/Documents/Google_Drive/Wafer_Probing/MySQL_Testing/Wafer_N6T903-11A3/ChipN_'+str(z)+'_v0/PowerMeasurement.csv'
	pathDigitalSummary = '/home/david/Documents/Google_Drive/Wafer_Probing/MySQL_Testing/Wafer_N6T903-11A3/ChipN_'+str(z)+'_v0/DigitalSummary.csv'
	pathAnalogMeasurement = '/home/david/Documents/Google_Drive/Wafer_Probing/MySQL_Testing/Wafer_N6T903-11A3/ChipN_'+str(z)+'_v0/AnalogMeasurement.csv'
	pathMem12_Summary = '/home/david/Documents/Google_Drive/Wafer_Probing/MySQL_Testing/Wafer_N6T903-11A3/ChipN_'+str(z)+'_v0/Mem12_Summary.csv'
	pathMem10_Summary = '/home/david/Documents/Google_Drive/Wafer_Probing/MySQL_Testing/Wafer_N6T903-11A3/ChipN_'+str(z)+'_v0/Mem10_Summary.csv'

	with open(pathPowerMeasurement) as csvfile:
		PowerMeasurementValues = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for row in PowerMeasurementValues:
			Digital_Leakage = row[0]
			Digital_Initial = row[1]
			Digital_Config = row[2]
			Analog_Leakage = row[3]
			Analog_Initial = row[4]
			Analog_Config = row[5]
			IO_Leakage = row[6]
			IO_Initial = row[7]
			IO_Config = row[8]

	with open(pathDigitalSummary) as csvfile:
		DigitalSummaryValues = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for row in DigitalSummaryValues:
			DigitalTest_Analog_Injection = row[0]
			DigitalTest_Strip_Input = row[1]
			DigitalTest_Memory12 = row[2]
			DigitalTest_Memory10 = row[3]

	with open(pathAnalogMeasurement) as csvfile:
		AnalogMeasurementValues = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for row in AnalogMeasurementValues:
			AnalogMeasurement_ThLSB = row[0]
			AnalogMeasurement_CalLSB = row[1]
			AnalogMeasurement_Noise = row[2]
			AnalogMeasurement_ThSpread = row[3]
			AnalogMeasurement_Gain = row[4]

	with open(pathMem12_Summary) as csvfile:
		Mem12_SummaryValues = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for row in Mem12_SummaryValues:
			Memory12_Error = row[0]
			Memory12_Stuck = row[1]
			Memory12_I2C = row[2]
			Memory12_Missing = row[3]

	with open(pathMem10_Summary) as csvfile:
		Mem10_SummaryValues = csv.reader(csvfile, delimiter=' ', quotechar='|')
		for row in Mem10_SummaryValues:
			Memory10_Error = row[0]
			Memory10_Stuck = row[1]
			Memory10_I2C = row[2]
			Memory10_Missing = row[3]

	try:
		sql = "INSERT INTO "+tablename+" (Digital_Leakage, Digital_Initial, Digital_Config, Analog_Leakage, Analog_Initial, Analog_Config, IO_Leakage, IO_Initial, IO_Config, DigitalTest_Analog_Injection, DigitalTest_Strip_Input, DigitalTest_Memory12, DigitalTest_Memory10, AnalogMeasurement_ThLSB, AnalogMeasurement_CalLSB, AnalogMeasurement_Noise, AnalogMeasurement_ThSpread, AnalogMeasurement_Gain, Memory12_Error, Memory12_Stuck, Memory12_I2C, Memory12_Missing, Memory10_Error, Memory10_Stuck, Memory10_I2C, Memory10_Missing) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
		val = (Digital_Leakage, Digital_Initial, Digital_Config, Analog_Leakage, Analog_Initial, Analog_Config, IO_Leakage, IO_Initial, IO_Config, DigitalTest_Analog_Injection, DigitalTest_Strip_Input, DigitalTest_Memory12, DigitalTest_Memory10, AnalogMeasurement_ThLSB, AnalogMeasurement_CalLSB, AnalogMeasurement_Noise, AnalogMeasurement_ThSpread, AnalogMeasurement_Gain, Memory12_Error, Memory12_Stuck, Memory12_I2C, Memory12_Missing, Memory10_Error, Memory10_Stuck, Memory10_I2C, Memory10_Missing)
		mycursor.execute(sql,val)
		mydb.commit()
		print("Record for Chip Number: "+str(z)+" inserted successfully into table: "+tablename)
	except:
	 	mydb.rollback()
	 	print("Failed to insert record for Chip Number: "+str(z))

sql_query = "SELECT * FROM %s" %tablename
mycursor.execute(sql_query)
myresult = mycursor.fetchall()
for x in myresult:
	print(x)

def CheckValues(tablename='',TestType=0,PlotFlag=0):

	if(TestType==0) or (dbname=='') or (tablename==''):
		print("Please use format: CheckValues(Table_Name, Test_Type, Plot)")
		return
	elif(TestType==1):
		sql_query = "SELECT Digital_Leakage FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0 or x>15):
				sql_query = "SELECT ChipNumber FROM %s WHERE Digital_Leakage='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Digital Leakage Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==2):
		sql_query = "SELECT Digital_Initial FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<90 or x>130):
				sql_query = "SELECT ChipNumber FROM %s WHERE Digital_Initial='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Digital_Initial Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==3):
		sql_query = "SELECT Digital_Config FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<70 or x>110):
				sql_query = "SELECT ChipNumber FROM %s WHERE Digital_Config='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Digital_Config Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==4):
		sql_query = "SELECT Analog_Leakage FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<20 or x>50):
				sql_query = "SELECT ChipNumber FROM %s WHERE Analog_Leakage='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Analog_Leakage Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==5):
		sql_query = "SELECT Analog_Initial FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<45 or x>75):
				sql_query = "SELECT ChipNumber FROM %s WHERE Analog_Initial='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Analog_Initial Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==6):
		sql_query = "SELECT Analog_Config FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<45 or x>75):
				sql_query = "SELECT ChipNumber FROM %s WHERE Analog_Config='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Analog_Config Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==7):
		sql_query = "SELECT IO_Leakage FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<10 or x>20):
				sql_query = "SELECT ChipNumber FROM %s WHERE IO_Leakage='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad IO_Leakage Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==8):
		sql_query = "SELECT IO_Initial FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<10 or x>20):
				sql_query = "SELECT ChipNumber FROM %s WHERE IO_Initial='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad IO_Initial Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==9):
		sql_query = "SELECT IO_Config FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<10 or x>20):
				sql_query = "SELECT ChipNumber FROM %s WHERE IO_Config='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad IO_Config Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==10):
		sql_query = "SELECT DigitalTest_Analog_Injection FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0 or x>1):
				sql_query = "SELECT ChipNumber FROM %s WHERE DigitalTest_Analog_Injection='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad DigitalTest_Analog_Injection Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==11):
		sql_query = "SELECT DigitalTest_Strip_Input FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0 or x>1):
				sql_query = "SELECT ChipNumber FROM %s WHERE DigitalTest_Strip_Input='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad DigitalTest_Strip_Input Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==12):
		sql_query = "SELECT DigitalTest_Memory12 FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0 or x>1):
				sql_query = "SELECT ChipNumber FROM %s WHERE DigitalTest_Memory12='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad DigitalTest_Memory12 Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==13):
		sql_query = "SELECT DigitalTest_Memory10 FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0 or x>1):
				sql_query = "SELECT ChipNumber FROM %s WHERE DigitalTest_Memory10='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad DigitalTest_Memory10 Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==14):
		sql_query = "SELECT AnalogMeasurement_ThLSB FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<1.25 or x>1.70):
				sql_query = "SELECT ChipNumber FROM %s WHERE AnalogMeasurement_ThLSB='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad AnalogMeasurement_ThLSB Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==15):
		sql_query = "SELECT AnalogMeasurement_CalLSB FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0.030 or x>0.040):
				sql_query = "SELECT ChipNumber FROM %s WHERE AnalogMeasurement_CalLSB='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad AnalogMeasurement_CalLSB Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==16):
		sql_query = "SELECT AnalogMeasurement_Noise FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<1.00 or x>2.00):
				sql_query = "SELECT ChipNumber FROM %s WHERE AnalogMeasurement_Noise='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad AnalogMeasurement_Noise Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==17):
		sql_query = "SELECT AnalogMeasurement_ThSpread FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<3.0 or x>10.0):
				sql_query = "SELECT ChipNumber FROM %s WHERE AnalogMeasurement_ThSpread='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad AnalogMeasurement_ThSpread Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==18):
		sql_query = "SELECT AnalogMeasurement_Gain FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<60 or x>100):
				sql_query = "SELECT ChipNumber FROM %s WHERE AnalogMeasurement_Gain='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad AnalogMeasurement_Gain Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==19):
		sql_query = "SELECT Memory12_Error FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		ListOfMem12Errors = []
		# i=0
		for x in RESULT:
			# i += 1
			if(x!=0):
				# print("Bad Memory12_Error Value: "+str(x[0])+" at Chip Number: "+str(i))
				if x not in ListOfMem12Errors:
					ListOfMem12Errors.append(x[0])
					sql_query = "SELECT ChipNumber FROM %s WHERE Memory12_Error='%s'" %(tablename,float(x[0]))
					mycursor.execute(sql_query)
					myChipNumber = mycursor.fetchall()
					for row in myChipNumber:
						BadChipNumber = row[0]
						print("Bad Memory12_Error Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==20):
		sql_query = "SELECT Memory12_Stuck FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0):
				sql_query = "SELECT ChipNumber FROM %s WHERE Memory12_Stuck='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Memory12_Stuck Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==21):
		sql_query = "SELECT Memory12_I2C FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0):
				sql_query = "SELECT ChipNumber FROM %s WHERE Memory12_I2C='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Memory12_I2C Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==22):
		sql_query = "SELECT Memory12_Missing FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0):
				sql_query = "SELECT ChipNumber FROM %s WHERE Memory12_Missing='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Memory12_Missing Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==23):
		sql_query = "SELECT Memory10_Error FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		ListOfMem10Errors = []
		# i=0
		for x in RESULT:
			# i += 1
			if(x!=0):
				# print("Bad Memory10_Error Value: "+str(x[0])+" at Chip Number: "+str(i))
				if x not in ListOfMem10Errors:
					ListOfMem10Errors.append(x[0])
					sql_query = "SELECT ChipNumber FROM %s WHERE Memory10_Error='%s'" %(tablename,float(x[0]))
					mycursor.execute(sql_query)
					myChipNumber = mycursor.fetchall()
					for row in myChipNumber:
						BadChipNumber = row[0]
						print("Bad Memory10_Error Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==24):
		sql_query = "SELECT Memory10_Stuck FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0):
				sql_query = "SELECT ChipNumber FROM %s WHERE Memory10_Stuck='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Memory10_Stuck Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==25):
		sql_query = "SELECT Memory10_I2C FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0):
				sql_query = "SELECT ChipNumber FROM %s WHERE Memory10_I2C='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Memory10_I2C Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))
	elif(TestType==26):
		sql_query = "SELECT Memory10_Missing FROM %s" %tablename
		mycursor.execute(sql_query)
		myresult = mycursor.fetchall()
		RESULT = np.array(myresult)
		for x in RESULT:
			if(x<0):
				sql_query = "SELECT ChipNumber FROM %s WHERE Memory10_Missing='%s'" %(tablename,float(x[0]))
				mycursor.execute(sql_query)
				myChipNumber = mycursor.fetchone()
				BadChipNumber = myChipNumber[0]
				print("Bad Memory10_Missing Value: "+str(x[0])+" at Chip Number: "+str(BadChipNumber))

	if(PlotFlag==1):
		plt.hist(RESULT)
		plt.show()

for x in range(1,27):
	CheckValues(tablename,x,0)