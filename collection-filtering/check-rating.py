from os import listdir, mkdir
from os.path import isfile, isdir, join, abspath
import csv
import re
import shutil
import unicodedata

baseFolder = "../../../../3_filter"
aqapFolder = "./AQAP/"
#collections = ["RockBand-GuitarHero_rb-spreadsheet"]
collections = ["RockBand-GuitarHero-moggs"]
categories = ["GOOD", "BAD", "PERFECT"]

"""Load all csv data for given collection"""
def getAqData(collectionName):
    
    aqData = []
    for aq in [f for f in listdir(aqapFolder) if isfile(join(aqapFolder, f)) and f.endswith(".txt") and f.startswith(collectionName)]:
        with open(join(aqapFolder, aq), "r", newline='') as aqFile:
            reader = csv.DictReader(aqFile, delimiter=';', quotechar='"')
            aqData.extend([l for l in reader])

    return aqData

for c in collections:
    print(f"Handling collection {c}")

    collectionFolder = join(baseFolder, c)
    if not isdir(collectionFolder):
        print(f"Collection {c} not found at {abspath(collectionFolder)}")
        continue
    
    aqData = getAqData(c)

    # Check folders - make sure every song directory has been rated by AQAP
    songFolders = [f for f in listdir(collectionFolder) if isdir(join(collectionFolder, f))]
    
    def getRating(f):
        f = unicodedata.normalize("NFC", f)
        aq = [x for x in aqData if x["FileName"] == f"vocals_{f}.wav"]

        return aq[0] if len(aq) > 0 else False

    foundSongs = [f for f in songFolders if getRating(f)]
    notFoundSongs = [f for f in songFolders if not getRating(f)]
    
    print(f"Found {len(foundSongs)} songs")
    print(f"Missing {len(notFoundSongs)} songs:")
    for n in notFoundSongs:
        print(f"- {n}")
    
    ratings = [getRating(f) for f in foundSongs]

    print("-------------")
    print(f"Songs with rating perfect: {len([r for r in ratings if r['Status'] == 'PERFECT'])}")
    print(f"Songs with rating good: {len([r for r in ratings if r['Status'] == 'GOOD'])}")
    print(f"Songs with rating bad: {len([r for r in ratings if r['Status'] == 'BAD'])}")

    #continue

    # Move songs to appropriate category directory
    for cat in categories:
        catDirectory = join(collectionFolder + '-' + cat)
        print(f"Create directory at {abspath(catDirectory)}")

        if not isdir(catDirectory):
            mkdir(catDirectory)

        for r in [r for r in ratings if r['Status'] == cat]:
            folderName = re.sub("^vocals_", "", r['FileName'])
            folderName = re.sub("\.wav$", "", folderName)
            sourceFolder = join(collectionFolder, folderName)

            if not isdir(sourceFolder):
                raise ValueError(f"Directory {sourceFolder} does not exist")

            print(f"Move {abspath(sourceFolder)} to {abspath(catDirectory)}")
            shutil.move(sourceFolder, catDirectory)

