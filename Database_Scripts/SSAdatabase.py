import mysql.connector
import numpy as np
import matplotlib.pyplot as plt
import sys
import pandas as pd
from CSVutility import *
from CreateDatabase import *

dbname = "SSA_WAFER"
tablename = "SSA"
path = '/home/david/cernbox/Wafer_Data/Wafer_W1_v2/'

DB = CreateDatabase(dbname, path)
DB.makeTable(tablename)
DB.fillTable(tablename)
# DB.printTable(tablename)
