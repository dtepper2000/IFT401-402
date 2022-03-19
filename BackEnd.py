import requests
from urllib.parse import urlencode
#import sqlite3

#Connecting to the SQL DB <<< NOT SURE HOW TO CONNECT, FULLY
#connection = sqlite3.connect('Capstone.db')


#Take User Input to Prepare the API Query   <<< GET RID OF INPUT MESSAGE... take input from Front-End
devInput = input("\nEnter a Valid Address Here: ")
api_key = "AIzaSyBzP4pcCXn8cELXQCWHP8mNkPh9TgPlWOQ"


#Performs the API query: Turn Address into Lat/Lon
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
    #latCoord = coords.get("lat")   << THESE DON'T WORK (not global)
    #lngCoord = coords.get("lng")   << THESE DON'T WORK (not global)
    return coords.get("lat"), coords.get("lng")

parse_result_coords(any_valid_address = devInput)


#EXECUTE the SQL query
#cursor.execute(    )