from os import listdir
from os.path import isfile, join, isdir, exists
import re
import globals
from typing import Union

import audiohelpers
import os
import uuid
import sys
import datetime

tempPath = "./temp"

def isVocal(file):
    return re.search('vox', file, re.IGNORECASE) or re.search('voc', file, re.IGNORECASE)

def isLead(file):
    return re.search('lead', file, re.IGNORECASE) and (re.search('voc', file, re.IGNORECASE) or re.search('vox', file, re.IGNORECASE))

def isRoom(file):
    return re.search('room', file, re.IGNORECASE)

def isChamber(file):
    return re.search('chamber', file, re.IGNORECASE)

def mix(files, destPath):
    if all(exists(f) for f in files):
        audiohelpers.mixdown([(w, 1) for w in files], destPath)

def normalizeAndMix(fArrWithVolume, destPath):

    tempfiles = []

    for a in fArrWithVolume:
        files = a[0]
        vol = a[1]
        mix_temp_file = join(tempPath, str(uuid.uuid4())) + ".wav"
        normalized_temp_file = join(tempPath, str(uuid.uuid4())) + ".wav"

        mix(files, mix_temp_file)
        audiohelpers.normalize(mix_temp_file, normalized_temp_file)
        os.remove(mix_temp_file)

        tempfiles.append((normalized_temp_file, vol))

    if all(exists(f[0]) for f in tempfiles):
        audiohelpers.mixdown(tempfiles, destPath)

    for f in tempfiles:
        os.remove(f[0])


def file_processing(sourcedir, destdir, maxCopy, override):

    #Create temp folder if not already existing
    if not os.path.exists(tempPath): os.makedirs(tempPath)

    #Create list of directories
    directories = [f for f in listdir(sourcedir) if isdir(join(sourcedir, f))]

    for d in directories:
        directoryPath = join(sourcedir, d)

        if not isdir(directoryPath):
            continue

        subdirectories = [join(directoryPath, f) for f in listdir(directoryPath) if isdir(join(directoryPath, f))]
        if subdirectories.__len__() >= 1:
            file_processing(directoryPath, destdir, maxCopy, override)
            continue


        wavFiles = [join(directoryPath, f) for f in listdir(directoryPath) if isfile(join(directoryPath, f)) and f.endswith(".wav")]

        voiceFilesNonLead = [f for f in wavFiles if isVocal(f) and not isLead(f)]
        voiceFilesLead = [f for f in wavFiles if isVocal(f) and isLead(f)]
        instrumentalFiles = [f for f in wavFiles if not isVocal(f) and not isRoom(f) and not isChamber(f)]

        destPath = join(destdir, d)

        # for now, skip tracks which do not have vocals
        if(len(voiceFilesLead) == 0 and len(voiceFilesNonLead) == 0):
            continue

        # only create new (continue) if option override disabled
        if os.path.exists(destPath) and not override:
            continue

        if not os.path.exists(destPath):
            os.makedirs(destPath)

        # Create voice-only mixdown
        if(len(voiceFilesNonLead) == 0):
            normalizeAndMix(
                [(voiceFilesLead, 1)],
                join(destPath, "vocals_" + d + ".wav")
            )
        elif(len(voiceFilesLead) == 0):
            normalizeAndMix(
                [(voiceFilesNonLead, 1)],
                join(destPath, "vocals_" + d + ".wav")
            )
        else:
            normalizeAndMix(
                [(voiceFilesLead, 0.7),
                 (voiceFilesNonLead, 0.3)],
                join(destPath, "vocals_" + d + ".wav")
            )

        # Create mixdown
        normalizeAndMix(
            [(instrumentalFiles, 1)],
            join(destPath, "instrumental_" + d + ".wav")
        )

def init():
    # Open Logfile
    log_file_name = join(join(sourcedir, "_log"),
                         datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_Logfile.txt")
    globals.log_file = open(log_file_name, "w+")

if __name__ == '__main__':
    # Call script with scriptname maxfiles override
    # Example call: dsd100_fileprocessing.py 20 True
    # This will convert the first twenty files in the source dir and override already existing files in the outputdir

    maxCopy = 3
    override = False
    unmix_server = "//192.168.1.29/unmix-server"

    print('Argument List:', str(sys.argv))

    if sys.argv.__len__() == 2:
        unmix_server = sys.argv[1]


    sourcedir = unmix_server + "/1_sources/cambridge-mt"
    mixPath = unmix_server + "/2_prepared/cambridge-mt"

    globals.initialize()
    init()

    file_processing(sourcedir, mixPath, maxCopy, override)

    globals.log_file.close()

    print('Finished converting files')