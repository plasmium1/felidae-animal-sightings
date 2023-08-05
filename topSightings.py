import os
import psycopg2
from collections import OrderedDict
import numpy as np

connect = psycopg2.connect(database="staging", user="app", password=os.environ.get("FELIDAEPASSWORD"), host="localhost", port="5440")

cur = connect.cursor()
cur.execute("SELECT x.id FROM public.locations_camerastation x")
cameraStations = [ str(i[0]) for i in cur.fetchall() ]

pumaSightingStations = dict.fromkeys(cameraStations, 0)
bobcatSightingStations = dict.fromkeys(cameraStations, 0)


def speciesAtStation(speciesName, stationSightingDict:dict): #Find all sightings of speciesName and obtain frequency list at each camera station
	#Get the species ID of speciesName
	stringSQL = "SELECT x.id FROM public.images_speciesname x WHERE name = '" + speciesName + "'"
	cur.execute(stringSQL)
	speciesID = cur.fetchone()[0]

	#Get the list of camera stations for every possible instance with the species in them.
	stringSQL = "SELECT x.camera_station_id FROM images_upload x WHERE id IN (SELECT x.upload_id FROM images_image x WHERE id IN (SELECT x.image_id FROM images_boundingbox x WHERE id IN (SELECT x.bounding_box_id FROM images_species x WHERE name_id = '" + str(speciesID) +  "')))"
	cur.execute(stringSQL)
	camID = [ str(i[0]) for i in cur.fetchall() ]
	
	#Record number of sightings per station in the station dictionary for speciesName
	for i in camID:
		stationSightingDict[i] += 1

def sortDict(dictionaryName):
	dictionaryKeys = list(dictionaryName.keys())
	dictionaryValues = list(dictionaryName.values())
	valuesSorted = reversed(np.argsort(dictionaryValues))
	dictionarySorted = {dictionaryKeys[i]:dictionaryValues[i] for i in valuesSorted}
	return dictionarySorted
	
def topStations(sortedStationDictionary, num):
	topL = list(sortedStationDictionary.keys())[:num]
	stations = []
	for i in topL:
		stringSQL = "SELECT x.station_id FROM locations_camerastation x WHERE id = '" + i + "'"
		cur.execute(stringSQL)
		val = cur.fetchall()[0][0]
		stations.append(val)
	return stations

speciesAtStation("Puma", pumaSightingStations)
speciesAtStation("Bobcat", bobcatSightingStations)
#Sort by the number of sightings per station

pumaStationsSorted = sortDict(pumaSightingStations)
print(pumaStationsSorted)
#Puma Stations have been sorted in descending order based on sightings.

bobcatStationsSorted = sortDict(bobcatSightingStations)
print(bobcatStationsSorted)
#Bobcat Stations get the same treatment

#topFivePumaStations = topStations(pumaStationsSorted, 5)
#topFiveBobcatStations = topStations(bobcatStationsSorted, 5)
topTenPumaStations = topStations(pumaStationsSorted, 10)
topTenBobcatStations = topStations(bobcatStationsSorted, 10)
print("Top Ten Puma Stations: ", topTenPumaStations)
print("Top Ten Bobcat Stations: ", topTenBobcatStations)
