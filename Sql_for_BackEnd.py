
import pypyodbc # requires pip install pypyodbc - connects Python to SQL
import pyodbc
import pandas as pd # requires pip install pandas - helps parse SQL data
import sqlalchemy
from sqlalchemy import create_engine


#USR = 'p51_SqlJob'
#PWD = 'p51_program_pwd_51'
#Sys_DSN = 'Capstone'
#engine = create_engine("mssql+pyodbc://{USR}:{PWD}@{Sys_DSN}")
# ^ Note: System DSN info can be found at HKEY_LOCAL_MACHINE\SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources

engine = create_engine("mssql+pyodbc://p51_SqlJob:p51_program_pwd_51@Capstone")



connection = engine.connect()

data = pd.read_sql_query("""

DECLARE
	@PoI GEOGRAPHY,
	@LAT FLOAT(4),
	@LON FLOAT(4),
	@SEARCHRADIUS INT


-- SET a PoI (ie. the Address/location being searched) ----------------------------------------------------------------------
SET @LAT=30.0852		-- << change to take user input <<<<< WORK TO BE DONE HERE
SET @LON=-79.3251		-- << change to take user input <<<<< WORK TO BE DONE HERE


-- Convert that PoI into a GEOGRAPHY data point -----------------------------------------------------------------------------
/*		NOTE .. Uses this EXTENDED STATIC METHOD: geography::Point
				Static value "4326" occupies the "SRID" argument which configures the data type you are creating.
				SRID 4326 is widely used, it represents spatial data using longitude and latitude coordinates on the Earth's
				surface as defined in the WGS84 standard, which is also used for the Global Positioning System (GPS).
*/
SET @PoI= geography::Point(@LAT, @LON, 4326)


-- SET a radius -------------------------------------------------------------------------------------------------------------
SET @SEARCHRADIUS=50	-- << change to take user input


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
""",
connection)

print(data)

