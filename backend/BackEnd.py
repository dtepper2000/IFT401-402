#!/usr/bin/env python
# 
#   File: BackEnd.py
#   Author: Ian Brown (ijbrown@asu.edu)
#   Date: 2022.04.19
#   Description: The combined "API/Geocoding" and "SQL" portions of the "Back-End" Programming for p51 (IFT402)
#   Notes:  [Reference] ODBC Driver info can be found in ODBC Data Source Admin (tool) > "Drivers" tab (if needed for different engine/connection type)
#           [Reference] ODBC DSN can be found at: HKEY_LOCAL_MACHINE\SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources
#           [Reference] Documentation to figure out how to connect Azure DB to the "ENGINE"
#               https://docs.sqlalchemy.org/en/14/dialects/mssql.html#:~:text=degrades%20performance%20significantly.-,PyODBC,-%C2%B6
#				https://docs.microsoft.com/en-us/sql/connect/python/pyodbc/step-3-proof-of-concept-connecting-to-sql-using-pyodbc?view=sql-server-ver15
#
########################################################################################

#!pip install requests
#!pip install pypyodbc
#!pip install pyodbc
#!pip install pandas
#!pip install sqlalchemy

import requests
from urllib.parse import urlencode
import pypyodbc
import pyodbc
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from dataclasses import dataclass
import xml.etree.ElementTree as ET


# ----------------------------------- XML ----------------------------------
# Setup the XML
Tree = ET.parse('FE-BE_Integration.xml')
Root = Tree.getroot()

FrontEnd = Root[0]
BackEnd = Root[1]
Results = Root[1][0]
Events = Root[1][1]

# FOR READING THE POI from the <FrontEnd>    
PoI = Root[0][0].text



# ----------------------------------- GEOCODING ----------------------------------

api_key = "AIzaSyBzP4pcCXn8cELXQCWHP8mNkPh9TgPlWOQ"
#          ^ NOTE: This API key is restricted to certain IP addresses.
#                  For production, I will add the Azure instance IP to this list.

#Defines the API query to be performed
def get_PoI_coords(any_valid_address, data_type = 'json'):
    
    endpoint = f"https://maps.googleapis.com/maps/api/geocode/{data_type}"
    params = {"address": any_valid_address, "key": api_key}
    url_params = urlencode(params)
    url = f"{endpoint}?{url_params}"
    
    r = requests.get(url)
    if r.status_code not in range(200, 299):
        return {}
    coords = {}
    try:
        return r.json()['results'][0]['geometry']['location']
    except:
        pass
    return coords.get("lat"), coords.get("lng")


# Executes the API request, as defined above
locDataDict = get_PoI_coords(PoI)

# These variables are used as param arguments at the end of the SQL query
latCoord=float(locDataDict['lat'])
lngCoord=float(locDataDict['lng'])

# USING THESE IN LIEU OF ABOVE API WORK
#latCoord=46.197532
#lngCoord=-122.188374



# ----------------------------------- SQL QUERY ----------------------------------
# Connection String to the Azure SQL Server


#engine = create_engine("mssql+pyodbc://p51admin:T2Y3Q327KP05W34D@IFT-Capstone")   <<< Format of DEV version (known to work locally)
engine = create_engine('Driver={ODBC Driver 13 for SQL Server};Server=tcp:project51.database.windows.net,1433;Database=IFT-Capstone;Uid=p51admin;Pwd={T2Y3Q327KP05W34D$};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
connection = engine.connect()


#cnxn = pyodbc.connect('Driver={ODBC Driver 13 for SQL Server};Server=tcp:project51.database.windows.net,1433;Database=IFT-Capstone;Uid=p51admin;Pwd={T2Y3Q327KP05W34D$};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
#cursor = cnxn.cursor()   <<< AZURE (option 2)


# Performs the SQL Query, specifying the connection and parameters (for ? marker values) at the end (line 130)
#SQLdataResults = cursor.execute("""   <<< AZURE (option 2)
SQLdataResults = pd.read_sql_query("""


DECLARE
	@PoI GEOGRAPHY,
	@LAT FLOAT(4),
	@LON FLOAT(4),
	@SEARCHRADIUS INT


-- SET a PoI (ie. the Address/location being searched) ----------------------------------------------------------------------
SET @LAT= ?
SET @LON= ?



-- Convert that PoI into a GEOGRAPHY data point -----------------------------------------------------------------------------
/*		NOTE .. Uses this EXTENDED STATIC METHOD: geography::Point
				Static value "4326" occupies the "SRID" argument which configures the data type you are creating.
				SRID 4326 is widely used, it represents spatial data using longitude and latitude coordinates on the Earth's
				surface as defined in the WGS84 standard, which is also used for the Global Positioning System (GPS).
*/
SET @PoI= geography::Point(@LAT, @LON, 4326)


-- SET a radius -------------------------------------------------------------------------------------------------------------
SET @SEARCHRADIUS=20	-- << THIS IS A STATIC SEARCH RADIUS, CAN be changed to take user input (change to ? and add param to variable list (above) and connection params (below))


-- SELECT all events WHERE within X radius (defined/set above) -------------------------------------------------------------- [in MILES]
SELECT
	[Event_Category] as Type,
	[Detail],
    [Locale],
    [Latitude],
    [Longitude],
    [DateTime],
	ROUND((@PoI.STDistance(geography::Point(ISNULL([Latitude],0),ISNULL([Longitude],0), 4326))/1609.344),2) 'Distance from PoI'
FROM
	[dbo].[DataMaster]
WHERE
	((@PoI.STDistance(geography::Point(ISNULL([Latitude],0),ISNULL([Longitude],0), 4326))/1609.344) <= @SEARCHRADIUS)
"""
,connection,params=(float(latCoord),float(lngCoord)))
#,cursor,params=(float(latCoord),float(lngCoord))) <<< AZURE (option 2)



# ----------------------------------- EVENT MANAGEMENT ----------------------------------
# The SQL query is now in a dataframe, need to get that to the XML

# Function creates a new instance of "event" in the "events" section (in the XML)
def AddEvent(fType,fDetail,fLoc,fLat,fLon,fDist,fDateTime): 

    newEvent = ET.Element("Event")
    newEvent.set("type",fType)
    Root[1][1].append(newEvent)

    newDetail = ET.SubElement(newEvent, "detail")
    newDetail.text = fDetail
    newLoc = ET.SubElement(newEvent, "loc")
    newLoc.text = fLoc
    newLat = ET.SubElement(newEvent, "lat")
    newLat.text = fLat
    newLon = ET.SubElement(newEvent, "lon")
    newLon.text = fLon
    newDist = ET.SubElement(newEvent, "dist")
    newDist.text = str(fDist)
    newDateTime = ET.SubElement(newEvent, "datetime")
    newDateTime.text = fDateTime   
    with open("SAMPLE.xml", "wb") as toFile:
        Tree.write(toFile)

# Function creates a new instance of "result" in the "results" section (in the XML)
def AddResult(fCategory,fType,fValue): 

    newResult = ET.Element("Result")
    newResult.set("category",fCategory)
    newResult.set("type",fType)
    newResult.text = str(fValue)
    Root[1][0].append(newResult)

    with open("SAMPLE.xml", "wb") as toFile:
        Tree.write(toFile)


# Function helps with result/score calc
BoomCount = 0
QuakeCount = 0
AlienCount = 0


for index, row in SQLdataResults.iterrows():
    #print(row['Detail'],row['Locale'])
    AddEvent(row['Type'],row['Detail'],row['Locale'],row['Latitude'],row['Longitude'],row['Distance from PoI'],row['DateTime'])
    
    if row['Type'] == 'Explosion':
        BoomCount += 1
    elif row['Type'] == 'Earthquake':
        QuakeCount += 1
    else:
        AlienCount += 1
        
AddResult("Count","Explosion",BoomCount)
AddResult("Count","Earthquake",QuakeCount)
AddResult("Count","UFO",AlienCount)



# ----------------------------------- RISK SCORE MANAGEMENT ----------------------------------

TotalEvents = BoomCount + QuakeCount + AlienCount
RiskScore = "None"
       
if TotalEvents == 1 or TotalEvents == 2:
    RiskScore = "Very Low"

elif TotalEvents == 3 or TotalEvents == 4:
    RiskScore = "Low"

elif TotalEvents == 5 or TotalEvents == 6:
    RiskScore = "Medium"
 
elif TotalEvents >= 6 and TotalEvents <= 15:
    RiskScore = "High"

elif TotalEvents >= 16 and TotalEvents <= 30:
    RiskScore = "Exceedingly High"

elif TotalEvents >= 31 and TotalEvents <= 50:
    RiskScore = "Excessively High"

elif TotalEvents > 50:
    RiskScore = "Unreasonably High"

else:
    RiskScore = "DANGEROUS"

AddResult("Score","Risk",RiskScore)