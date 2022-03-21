#!/usr/bin/env python
# 
#   File: BackEnd.py
#   Author: Ian Brown (ijbrown@asu.edu)
#   Date: 2022.03.20
#   Description: The combined "API/Geocoding" and "SQL" portions of the "Back-End" Programming for p51 (IFT402)
#   Notes:  1. [TO-DO] This works on my local machine, needs to be refactored for Azure SQL DB
#           2. [TO-DO] Will need to figure out how to manage "PIP INSTALL" requirements in an Azure Web Server
#           3. [TO-DO] Can we access "System DSN" (ie. Registry Key info) on Azure instance? If so, feed it to the "ENGINE"
#           4. [Reference] ODBC Driver info can be found in ODBC Data Source Admin (tool) > "Drivers" tab (if needed for different engine/connection type)
#           5. [Reference] ODBC DSN can be found at: HKEY_LOCAL_MACHINE\SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources
#           6. [Reference] Documentation to figure out how to connect Azure DB to the "ENGINE"
#               https://docs.sqlalchemy.org/en/14/dialects/mssql.html#:~:text=degrades%20performance%20significantly.-,PyODBC,-%C2%B6
#
########################################################################################


# IMPORTS for Geocoding
#!pip install requests
import requests # requires pip install requests
from urllib.parse import urlencode

# IMPORTS for SQL query
#!pip install pypyodbc
import pypyodbc # connects Python to SQL
#!pip install pyodbc
import pyodbc
#!pip install pandas
import pandas as pd # helps put SQL data into "data frames"
#!pip install sqlalchemy
import sqlalchemy
from sqlalchemy import create_engine
from dataclasses import dataclass


# ----------------------------------- GEOCODING ----------------------------------
# Converts plain-text address/location into latitude/longitude


# Take User Input to Prepare the API Query   <<< [TO-DO]: change devInput to User input from Front-End search bar
devInput = input("\nEnter a Valid Address Here: ")
api_key = "AIzaSyBzP4pcCXn8cELXQCWHP8mNkPh9TgPlWOQ"
#          ^ NOTE: This API key is restricted to certain IP addresses.
#                  For production, I will add the Azure instance IP to this list.


#Defines the API query to be performed
def parse_result_coords(any_valid_address, data_type = 'json'):
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

# Executes the API request, as defined above (currently prints the lat/lon for confirmation)
locDataDict = parse_result_coords(any_valid_address = devInput)
print('Latitude is:', locDataDict['lat'])
print('Longitude is:', locDataDict['lng'])


# These variables are used as param arguments at the end of the SQL query
latCoord=float(locDataDict['lat'])
lngCoord=float(locDataDict['lng'])


# ----------------------------------- SQL QUERY ----------------------------------

# [WORK NOTE]: Elements below connection string need to be replaced with AZURE SQL DB info {User Name}:{User's Pawwdord}@{ODBC DSN name}
# Connection String to the SQL Server
engine = create_engine("mssql+pyodbc://p51_SqlJob:p51_program_pwd_51@Capstone")
connection = engine.connect()

# ------- [EXPLOSIONS SQL Query]
# [WORK NOTE]: Query needs to be replicated x2 for UFO and EARTHQUATE tables
# Performs the SQL Query, specifying the connection and parameters (for ? marker values) at the end (line 127)
dataExplosions = pd.read_sql_query("""

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
SET @SEARCHRADIUS=100	-- << change to take user input


-- SELECT all events WHERE within X radius (defined/set above) -------------------------------------------------------------- [in MILES]
SELECT
	[type] 'Event Type',
	SUBSTRING(
        [place], 
        CHARINDEX('of ', [place])+3, 
        LEN([place])-CHARINDEX('of ', [place])
    ) 'Approx. Event Location',
	ROUND((@PoI.STDistance(geography::Point(ISNULL([latitude],0),ISNULL([longitude],0), 4326))/1609.344),2) 'Distance from PoI (Miles)'
FROM
	[dbo].[Explosions]
WHERE
	((@PoI.STDistance(geography::Point(ISNULL([latitude],0),ISNULL([longitude],0), 4326))/1609.344) <= @SEARCHRADIUS)
"""
,connection,params=(float(latCoord),float(lngCoord)))
print(dataExplosions)

# [WORK NOTE]: need to create a "counter" for number of results returned (feed that count to risk score)




# ------- [EARTHQUATE SQL Query]
# [WORK NOTE]: need to replicate Explosion query here - just change "FROM" TO [dbo].[Earthquakes]





# ------- [UFO SQL Query]
# [WORK NOTE]: need to replicate Explosion query here - REFACTOR SQL QUERY to work with the UFO table






# ----------------------------------- RISK SCORE ----------------------------------
# [WORK NOTE]: need to build