from os import listdir
from os.path import isfile, join, isdir
import re
import audiohelpers
import os
import uuid
import sys

unmix_server = "//192.168.1.29/unmix-server"
sourcedir = unmix_server + "/1_sources/cambridge-mt"
mixPath = unmix_server + "/2_prepared/cambridge-mt"
tempPath = "./temp"


def isVocal(file):
    return re.search('vox', file, re.IGNORECASE)

def isLead(file):
    return re.search('lead', file, re.IGNORECASE)

def mix(files, destPath):
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

    audiohelpers.mixdown(tempfiles, destPath)

    for f in tempfiles:
        os.remove(f[0])


def file_processing(sourcedir, destdir, maxCopy, override):

    if not os.path.exists(tempPath): os.makedirs(tempPath)

    directories = [f for f in listdir(sourcedir) if isdir(join(sourcedir, f))]

    for d in directories:
        directoryPath = join(sourcedir, d)
        wavFiles = [join(directoryPath, f) for f in listdir(directoryPath) if isfile(join(directoryPath, f)) and f.endswith(".wav")]

        voiceFilesNonLead = [f for f in wavFiles if isVocal(f) and not isLead(f)]
        voiceFilesLead = [f for f in wavFiles if isVocal(f) and isLead(f)]
        instrumentalFiles = [f for f in wavFiles if not isVocal(f)]

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

if __name__ == '__main__':
    # Call script with scriptname maxfiles override
    # Example call: dsd100_fileprocessing.py 20 True
    # This will convert the first twenty files in the source dir and override already existing files in the outputdir

    maxCopy = -1
    override = True

    print('Argument List:', str(sys.argv))

    if sys.argv.__len__() == 1:
        maxCopy = -1
        override = True
    if sys.argv.__len__() >= 2:
        try:
            int(sys.argv[1])
        except ValueError:
            exit("Add a number as the first argument")
        if int(sys.argv[1]) >= -1:
            maxCopy = int(sys.argv[1])
        else:
            exit("Enter a number equal or bigger than zero, if you enter -1, the function is disabled")
    if sys.argv.__len__() >= 3:
        if sys.argv[2].lower() == "true":
            override = True
        elif sys.argv[2].lower() == "false":
            override = False
        else:
            exit("Second argument not valid, enter true or false")

    file_processing(sourcedir, mixPath, maxCopy, override)


    print('Finished converting files')