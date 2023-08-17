import os
import psycopg2
from collections import OrderedDict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

connect = psycopg2.connect(database="staging", user="app", password=os.environ.get("FELIDAEPASSWORD"), host="localhost", port="5440")

cur = connect.cursor()
cur.execute("SELECT x.id FROM public.locations_camerastation x")
cameraStations = [ str(i[0]) for i in cur.fetchall() ]

pumaSightingStations = dict.fromkeys(cameraStations, 0)
bobcatSightingStations = dict.fromkeys(cameraStations, 0)

pumaDict = {}
bobcatDict = {}

def speciesAtStation(speciesName, stationSightingDict:dict): #Find all sightings of speciesName and obtain frequency list at each camera station
	#Get the species ID of speciesName
	cur.execute("SELECT x.id FROM public.images_speciesname x WHERE name = %s", (speciesName,))
	speciesID = cur.fetchone()[0]

	#Get the list of camera stations for every possible instance with the species in them.
	cur.execute("SELECT x.camera_station_id FROM images_upload x WHERE id IN (SELECT x.upload_id FROM images_image x WHERE id IN (SELECT x.image_id FROM images_boundingbox x WHERE id IN (SELECT x.bounding_box_id FROM images_species x WHERE name_id = %s)))", (str(speciesID), ))
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
		cur.execute("SELECT x.station_id FROM locations_camerastation x WHERE id = %s", (i,))
		val = cur.fetchall()[0][0]
		stations.append(val)
	return stations

def getStationsDailyImages(stations, data):
	allCounts = np.array([])
	countOccurances = []
	for station in stations:
		cur.execute("SELECT COUNT(DATE(x.trigger_timestamp)), DATE(x.trigger_timestamp) AS trigger_date FROM images_image x WHERE upload_id IN (SELECT x.id FROM images_upload x WHERE camera_station_id IN (SELECT x.id FROM locations_camerastation x WHERE station_id = %s)) AND DATE(x.trigger_timestamp) IS NOT NULL GROUP BY trigger_date ORDER BY trigger_date", (station,))
		timestamps = cur.fetchall()
		counts = np.array([i[0] for i in timestamps])
		allCounts = np.insert(allCounts, 0, counts)
		allCounts = allCounts.flatten()
	
	uniqueCounts = np.unique(allCounts)
	uniqueCounts = np.sort(uniqueCounts, axis=None)
	countOccurances = [np.count_nonzero(uniqueCounts == i) for i in uniqueCounts]
	countsDict = dict(zip(uniqueCounts, countOccurances))
	countsDF = pd.DataFrame(countsDict, index=[0])
	return countsDF

#def 


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

pumaTimestampsDF = getStationsDailyImages(topTenPumaStations, pumaDict)
#bobcatTimestampsDF = getStationsDailyImages(topTenBobcatStations, bobcatDict)

print(pumaTimestampsDF)

pumaHist = pumaTimestampsDF.plot.hist(bins=5)
print(pumaHist)
pumaHist.figure.savefig("figure.png")
