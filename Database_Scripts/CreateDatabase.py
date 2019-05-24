import mysql.connector
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from CSVutility import *

CSV = CSVutility()

class CreateDatabase():

	def __init__(self, dbname, path):
		self.dbname = dbname
		self.pathLogfile = path

		self.killDB()

		mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  passwd="password"
		)

		mycursor = mydb.cursor()

		try:
			sql_query = "CREATE DATABASE %s" %(self.dbname)
			mycursor.execute(sql_query)
			print("Successfully created new database: "+self.dbname)
		except:
			print("Failed to create database: "+self.dbname)

		sql_query = "SELECT @@datadir"
		mycursor.execute(sql_query)
		myresult = mycursor.fetchone()
		print("Data is being stored at: "+str(myresult[0])+dbname)

		mycursor.close()
		mydb.close()

	def killDB(self):
		
		mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  passwd="password"
		)

		mycursor = mydb.cursor()

		try:
			mycursor.execute("DROP DATABASE " + str(self.dbname))
			print("KILLED DATABASE: '" + str(self.dbname) + "' SINCE IT ALREADY EXISTED.")
		except:
			print("FAILED TO DROP: " + str(self.dbname) + " SINCE IT DID NOT EXIST.")

	def makeTable(self, tablename):
		mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  passwd="password",
		  database=self.dbname
		)

		mycursor = mydb.cursor()

		sql_query = "CREATE TABLE %s (ChipNumber INT AUTO_INCREMENT PRIMARY KEY)" %(tablename)
		mycursor.execute(sql_query)

		print("CREATED TABLE: "+tablename)

		array = CSV.csv_to_array(self.pathLogfile + 'Chip_N_1_v0/Logfile.csv')
		names = array[:,1]
		
		for i in names:
			sql_query = "ALTER TABLE %s ADD COLUMN %s DOUBLE(10,4)" %(tablename, i)
			mycursor.execute(sql_query)

		try:
			sql_query = "DESCRIBE %s" %(tablename)
			mycursor.execute(sql_query)
			myresult = mycursor.fetchall()
			print("Columns in "+tablename+": ")
			for x in myresult:
				print(x[0])
			print("Columns successfully added to table: "+tablename)
		except:
			print("Failed to create table.")

	def fillTable(self, tablename):

		mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  passwd="password",
		  database=self.dbname
		)

		mycursor = mydb.cursor()
		
		for z in range(1,91):

			k=1
			if(os.path.isfile(self.pathLogfile + 'Chip_N_'+str(z)+'_v'+str(k)+'/Logfile.csv')): continue
			else: k=0

			array = CSV.csv_to_array(self.pathLogfile + 'Chip_N_'+str(z)+'_v'+str(k)+'/Logfile.csv')
			names = array[:,1]
			values = array[:,2]
			snames = []
			
			for n in names:
				snames.append(n.strip())

			sql = "INSERT INTO {:s} ({:s}) VALUES ({:s})".format(tablename, ", ".join(map(str, snames)), ','.join(map(str, ["%s"]*len(snames))))
			val = tuple(values)
			# print(sql)
			try:
				mycursor.execute(sql,val)
				mydb.commit()
				print("Record for Chip Number: "+str(z)+" inserted successfully into table: "+tablename)
			except:
				mydb.rollback()
				print("Failed to insert record for Chip Number: "+str(z))

	def printTable(self, tablename):

		mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  passwd="password",
		  database=self.dbname
		)

		mycursor = mydb.cursor()

		try:
			sql_query = "SELECT * FROM %s" %tablename
			mycursor.execute(sql_query)
			myresult = mycursor.fetchall()
			for x in myresult:
				print(x)
		except:
			print("Failed to print table.")