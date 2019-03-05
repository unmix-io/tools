
srcDir = "/srv/unmix-server/1_sources/RockBand-GuitarHero/"
destDir = "/srv/unmix-server/2_prepared/RockBand-GuitarHero/"

# Handle multitrackdownloads-alphanumeric
# This folder contains mogg files (sometimes directly in song folder, sometimes in subfolder).
# Take those and convert them with ffmpeg.


import subprocess
import glob, os
from shutil import copy
os.chdir(srcDir + "multitrackdownloads-alphanumeric")
for file in glob.glob("**/*.mogg"):
    print(file)

    copy(file, destDir)
    file = destDir + os.path.basename(file)

    # The mogg files can't be processed with ffmpeg without this modification
    # Modify file: find occurrence of "OggS" in binary mogg file and remove everything before it
    with open(file, 'rb') as f:
        s = f.read()
        occurrenceOgg = s.find(b'\x4F\x67\x67\x53')
        s = s[occurrenceOgg:]
        with open(file + "_fixed.mogg", "wb") as f2:
            f2.write(s)
    
    os.remove(file)
    file = file + "_fixed.mogg"

    extractFolder = destDir + os.path.basename(file) + "_extract/"
    os.mkdir(extractFolder)

    numChannels = subprocess.check_output("ffprobe -show_entries stream=channels -of compact=p=0:nk=1 -v 0 \"" + file + "\"", shell=True)
    print(str(numChannels))

    for i in range(int(numChannels)):
        subprocess.check_call("ffmpeg -i \"" + file + "\" -map_channel 0.0." + str(i) + " \"" + extractFolder + str(i) + ".wav\"", shell=True)
