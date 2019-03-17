import os
import subprocess

rootFolder = "./temp"

from os import listdir
from os.path import isfile, join, isdir
folders = [f for f in listdir(rootFolder) if isdir(join(rootFolder, f))]

i = 0

for f in folders:
    folder = join(rootFolder, f)
    files = [f2 for f2 in listdir(folder) if isfile(join(folder, f2))]

    for file in files:
        file = join(folder, file)
        isvocal = file.__contains__("vocals")
        label = "vocal" if isvocal else "novocal"
        print(file)
        print(isvocal)

        subprocess.check_call("ffmpeg -i \"" + file + "\" -lavfi showspectrumpic=s=hd480:legend=0,format=yuv420p " + "./data-new/" + label + "/" + str(i+1000) + ".png", shell=True)

        i = i + 1
    