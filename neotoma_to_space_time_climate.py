## This script gets data from the Neotoma Paleoecological database and gathers climate data from netCDFs
## downloads all of the datasets records from Neotoma that match a taxon query
## datasets downloaded and parsed
## essential metadata is maintained and written to an intermediate csv file
## The nearest value in a netCDF file is found for each space-time locus
## The values for monthly attributes are extracted from the NetCDF and written into the csv
## A csv is written to disk.

## Search terms follow the Neotoma API convention of wildcard characters

## Usage: python neotoma_to_space_time_climate.py Picea* C://Users/willlab/documents/myNeotomaFile.csv

import csv
import sys
import requests
import netCDF4
import numpy

def getMonthlyValuesFromNCFile(ncfile, variable, yearBP, lat, lng):
    ### get the all the values we have for a variable type and latitude, longitude, time
    ncfile = netCDF4.Dataset(ncfile, 'r')
    #array the lats and lngs of the file
    lon_array = numpy.array(ncfile.variables['lon'])
    lat_array = numpy.array(ncfile.variables['lat'])
    time_array = numpy.array(ncfile.variables['time'])
    time_array = numpy.multiply(time_array, -10) #convert from decades to year bp

    # find the nearest point for latitude and longitude
    nearest_lat = find_nearest(lat_array, lat)
    nearest_lng = find_nearest(lon_array, lng)
    nearest_time = find_nearest(time_array, yearBP)

    # ## find the index at those points in the ncdf file
    lat_idx = numpy.where(lat_array == nearest_lat)[0][0]
    lon_idx = numpy.where(lon_array == nearest_lng)[0][0]
    time_idx = numpy.where(time_array == nearest_time)[0][0]
    # ## get the values at that lat, lng pair for all times
    v = ncfile.variables[variable][time_idx, :, lat_idx, lon_idx]
    return v


taxonSearchKey = sys.argv[1] ## to search Neotoma --> gets from command line

neotomaLocationsFile = "NeotomaLocations.csv"
finsihedFile = sys.argv[2] ## where should I put the final file? get from command line
prcpNCDF = "W://Lab_Climate_Data/ModelData/TraCE/CCSM3/22k_monthly_avg/nc/ccsm3_22-0k_prcp.nc
tempNCDF = "W://Lab_Climate_Data/ModelData/TraCE/CCSM3/22k_monthly_avg/nc/ccsm3_22-0k_temp.nc",
prcpVar = "prcp"
tminVar = "tmin"
tmaxVar = "tmax"



## structure of each row
output = {
    'collectionUnitHandle' : None,
    'collectionUnitID' : None,
    'collectionUnitType' : None,
    'datasetType' : None,
    'datasetName' : None,
    'datasetID' : None,
    'siteName' : None,
    'siteLatitude' : None,
    'siteLongitude' : None,
    'siteAltitude' : None,
    'siteID' : None,
    'chronologyID' : None,
    'chronologyType' : None,
    'ageOld' : None,
    'ageYoung' : None,
    'age' : None,
    'depth' : None,
    'thickness' : None,
    'pollenSum' : None,
    'taxonSum' : None,
    'taxonPercent' : None,
    'countedInLevel' : None,
    'totalInLevel' : None
}

## column headers
outputkeys= ['siteName', 'siteLatitude', 'siteLongitude', 'siteAltitude', 'siteID', 'depth', 'thickness', 'age', 'ageOld', 'ageYoung',
             'ageType', 'chronologyID', 'taxonPercent',
             'taxonSum', 'pollenSum', 'countedInLevel', 'totalInLevel',
             'datasetID', 'datasetType', 'collectionUnitType', 'collectionUnitHandle', 'collectionUnitID']

## get set up to write a CSV file with the specified column headers
intermediateFile = open(neotomaLocationsFile, 'w')
writer = csv.DictWriter(intermediateFile, fieldnames=outputkeys)
writer.writeheader()

## for comparison within the counts
testString = ''.join(ch for ch in taxonSearchKey if ch.isalnum()) ## this is the searchstring without anything else
testString = taxonSearchKey.upper()


### download from Neotoma
searchEndpoint = "http://api.neotomadb.org/v1/data/datasets?"
bbox = '-167.2764,5.4995,-52.23204,83.162102' ## North America
searchString = searchEndpoint + 'taxonname=' + taxonSearchKey + "&loc=" + bbox
try:
    print "Searching NeotomaDB..."
    datasets = requests.get(searchString).json() ## this is the search
except Exception as e: ## you messed up
    print "Request error: " + str(e)
    print "Dying..."
    sys.exit(1) ## quit with an error

## check if Neotoma returned OK
if datasets['success']:
    numDatasets = len(datasets['data'])
    print "Found ", numDatasets, "datasets for", taxonSearchKey
    datasets = datasets['data'] ## just keep the data part
else:
    ## API didn't return successfully.
    print "API Server returned an error.  Cannot continue..."


downloadEndpoint = "http://api.neotomadb.org/v1/data/downloads/"

## iterate through all returned datasets
it = 0
for dataset in datasets:
    ## these are dataset metadata as JSON objects as documented in neotoma api
    ## iterate over all of them and get the properties.  Then download the raw data
    colUnitName = dataset['CollUnitName']
    colUnitType = dataset['CollUnitType']
    colUnitHandle = dataset['CollUnitHandle']
    colUnitID = dataset['CollectionUnitID']
    datasetID = dataset['DatasetID']
    datasetName = dataset['DatasetName']
    datasetType = dataset['DatasetType']
    siteName = dataset['Site']['SiteName']
    ## inform user of process
    print "Processing Dataset #", datasetID, "for site", siteName
    ## round site locations to average
    siteLat = (float(dataset['Site']['LatitudeNorth']) + float(dataset['Site']['LatitudeSouth']))/2
    siteLng = (float(dataset['Site']['LongitudeEast']) + float(dataset['Site']['LongitudeWest']))/2
    siteAlt = dataset['Site']['Altitude']
    siteID = dataset['Site']['SiteID']
    siteDesc = dataset['Site']['SiteDescription']
    downloadString = downloadEndpoint + str(datasetID)
    try:
        download = requests.get(downloadString).json() ## do the download request from Neotoma API
    except Exception as e:
        print "Request Error: " + str(e)
        print "Dying..."
        sys.exit(1) # quit with error
    if download['success']:
        ##OK
        pass
    else:## not okay, skip
        print "API Server returned an error.  Passing this dataset...."
        continue ## this dataset will not be returned in the final file
    download = download['data'][0] ## just keep the first item in the data array
    chronID = download['DefChronologyID'] ## default chronology ID
    samples = download['Samples'] ## this is an array
    print '\tDataset #', datasetID, "downloaded successfully with", len(samples), "samples."
    ## iterate through all of the samples (these are levels in a core)
    for sample in samples:
        depth = sample['AnalysisUnitDepth']
        thickness = sample['AnalysisUnitThickness']
        name = sample['AnalysisUnitName']
        ## get sample ages
        ## if there are multiple --> idk what to do
        ## so just use the default
        ages = sample['SampleAges']
        ## set default sample ages
        age = -9999
        ageOld = -9999
        ageYoung = -9999
        ageType = None
        for sampleage in ages:
            thisChronID = sampleage['ChronologyID']
            if thisChronID == chronID: ## only use this age if it is the dataset's default chronology
                age = sampleage['Age']
                ageType = sampleage['AgeType']
                ageOld = sampleage['AgeOlder']
                ageYoung = sampleage['AgeYounger']
        ## now get the sample data
        sampledata = sample['SampleData']
        taxonValue = 0
        levelTotal = 0
        countedInLevel = 0
        totalInLevel = 0
        for sd in sampledata: ## these are the actual counts
            taxon = sd['TaxonName'].upper()
            value = sd['Value']
            element = sd['VariableElement']
            if element == 'pollen':
                levelTotal += value
                countedInLevel += 1
            if testString in taxon:
                taxonValue += value
            totalInLevel += 1
        ## format the output
        try:
            output = {
                'collectionUnitHandle' : colUnitHandle,
                'collectionUnitID' : colUnitID,
                'collectionUnitType' : colUnitType,
                'datasetType' : datasetType,
                'datasetID' : datasetID,
                'siteName' : siteName.encode("utf-8", "replace"),
                'siteLatitude' : siteLat,
                'siteLongitude' : siteLng,
                'siteAltitude' : siteAlt,
                'siteID' : siteID,
                'chronologyID' : chronID,
                'ageType' : ageType,
                'ageOld' : ageOld,
                'ageYoung' : ageYoung,
                'age' : age,
                'depth' : depth,
                'thickness' : thickness,
                'pollenSum' : levelTotal,
                'taxonSum' : taxonValue,
                'taxonPercent' : (taxonValue / levelTotal) * 100,
                'countedInLevel' : countedInLevel,
                'totalInLevel': totalInLevel
            }
            writer.writerow(output)
            it += 1
        except Exception as e:
            print str(e)
            pass

intermediateFile.close()## close write mode
intermediateFile = open(neotomaLocationsFile, 'r') # open again in read mode
finalFile = open(finsihedFile, 'w')# this is where the climate data goes
reader = csv.reader(intermediateFile) ## read the locations from here
writer = csv.writer(outf, lineterminator='\n') ## write to final file with csv writer

## add the climate keys to the final file
newHeader = outputkeys + ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12',
             'tmin1', 'tmin2', 'tmin3', 'tmin4', 'tmin5', 'tmin6','tmin7', 'tmin8', 'tmin9', 'tmin10', 'tmin11', 'tmin12',
             'tmax1', 'tmax2', 'tmax3', 'tmax4', 'tmax5', 'tmax6', 'tmax7', 'tmax8', 'tmax9', 'tmax10', 'tmax11', 'tmax12']
writer.writerow(newHeader)
i = 0
for row in reader:
    try:
        lat = float(row[1])
        lon = float(row[2])
        alt = float(row[3])
        age = row[7]
        ageOld = row[8]
        ageYoung = row[9]
        ## make age the average of old and young if its missing
        if age == '':
            try:
                age = (float(ageOld) + float(ageYoung)) / 2
            except Exception as e:
                age = 0 ##modern
        age = float(age)
        ## get Precip
        p = getFromNCFile.getMonthlyValuesFromNCFile(prcpNCDF, prcpVar, age, lat, lon)
        P = list(p)
        tmin = getFromNCFile.getMonthlyValuesFromNCFile(tempNCDF, tminVar, age, lat, lon)
        tmin = list(tmin)
        tmax = getFromNCFile.getMonthlyValuesFromNCFile(tempNCDF, tmaxVar, age, lat, lon)
        tmax = list(tmax)
        clim = p + tmin + tmax
        output = row + clim
        writer.writerow(output)
    except Exception as e:
        ## pass any errors
        print str(e)
        continue
    if i % 100 == 0:
        print "Done: ", (i/it) * 100, "records"
    i += 1
finalFile.close()
