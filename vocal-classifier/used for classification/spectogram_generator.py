import os
import subprocess
from os import listdir
from os.path import isfile, join, isdir


if not os.path.isdir("./temp-spectrograms"):
    os.mkdir("./temp-spectrograms")

targetDir = "../../../2_prepared/RockBand-GuitarHero/"

folders = [f for f in listdir(targetDir) if isdir(join(targetDir, f))]

for f in folders:
    folder = join(targetDir, f)
    files = [f for f in listdir(folder) if isfile(join(folder, f)) and f.endswith(".wav")]

    if len(files) == 0:
        continue

    spectrogramFolder = "./temp-spectrograms/" + f
    if not os.path.isdir(spectrogramFolder):
        os.mkdir(spectrogramFolder)
    
    for file in files:
        file = join(folder, file)
        targetFile = spectrogramFolder + "/" + os.path.basename(file) + ".png"

        # Transform wav to spectogram if it does not exist yet
        if not os.path.exists(targetFile):
            subprocess.check_call("ffmpeg -i \"" + file + "\" -lavfi showspectrumpic=s=hd480:legend=0,format=yuv420p \"" + targetFile + "\"", shell=True)
        else:
            print("Skipped " + targetFile + ": already exists")
