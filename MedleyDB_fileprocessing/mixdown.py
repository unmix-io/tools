from os import listdir
from os.path import isfile, join, isdir
import re
import audiohelpers
import os
import uuid

sourcePath = "./sources"
mixPath = "./mixes"
tempPath = "./temp"
directories = [f for f in listdir(sourcePath) if isdir(join(sourcePath, f))]

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


for d in directories:
    directoryPath = join(sourcePath, d)
    wavFiles = [join(directoryPath, f) for f in listdir(directoryPath) if isfile(join(directoryPath, f)) and f.endswith(".wav")]

    voiceFilesNonLead = [f for f in wavFiles if isVocal(f) and not isLead(f)]
    voiceFilesLead = [f for f in wavFiles if isVocal(f) and isLead(f)]
    instrumentalFiles = [f for f in wavFiles if not isVocal(f)]

    destPath = join(mixPath, d)

    # for now, skip tracks which do not have vocals
    if(len(voiceFilesLead) == 0 and len(voiceFilesNonLead) == 0):
        continue

    # only create new (continue)
    if os.path.exists(destPath):
        continue

    if not os.path.exists(destPath):
        os.makedirs(destPath)

    # Create voice-only mixdown
    if(len(voiceFilesNonLead) == 0):
        normalizeAndMix(
            [(voiceFilesLead, 1)],
            join(destPath, "voice.wav")
        )
    elif(len(voiceFilesLead) == 0):
        normalizeAndMix(
            [(voiceFilesNonLead, 1)],
            join(destPath, "voice.wav")
        )
    else:
        normalizeAndMix(
            [(voiceFilesLead, 0.7),
             (voiceFilesNonLead, 0.3)],
            join(destPath, "voice.wav")
        )

    # Create mixdown
    normalizeAndMix(
        [([join(destPath, "voice.wav")], 0.5),
         (instrumentalFiles, 0.5)],
        join(destPath, "mix.wav")
    )
