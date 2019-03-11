
srcDir = "/srv/unmix-server/1_sources/RockBand-GuitarHero/"
destDir = "/srv/unmix-server/1_sources/RockBand-GuitarHero-moggs/"

# Handle multitrackdownloads-alphanumeric
# This folder contains mogg files (sometimes directly in song folder, sometimes in subfolder).
# Take those and convert them with ffmpeg.


import subprocess
import glob, os
from shutil import copy, move
os.chdir(srcDir + "multitrackdownloads-alphanumeric")
for file in glob.glob("**/*.mogg"):
    print("Handling " + file)

    # Skip already existing files
    if(os.path.isfile(os.path.join(destDir, os.path.basename(file) + "_fixed.mogg"))):
        print("File " + file + "_fixed.mogg already exists - skipping file fix")
        file = destDir + os.path.basename(file)
    else:

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
    
    if(os.path.exists(file)):
        os.remove(file)

    file = file + "_fixed.mogg"

    extractFolder = destDir + os.path.basename(file) + "_extract/"

    if not os.path.isdir(extractFolder):
        os.mkdir(extractFolder)
    
    try:
        numChannels = subprocess.check_output("ffprobe -show_entries stream=channels -of compact=p=0:nk=1 -v 0 \"" + file + "\"", shell=True)
        
        
        print("Found " + str(numChannels) + " channels")

        for i in range(int(numChannels)):
            target = extractFolder + str(i) + ".wav"
            if os.path.isfile(target):
                print("Skipping wav track " + str(i) + ": already exists")
            else:
                subprocess.check_call("ffmpeg -i \"" + file + "\" -map_channel 0.0." + str(i) + " \"" + extractFolder + str(i) + ".wav\"", shell=True)
    except Exception as e:
        print("Error reading mogg file; break and moving to _error")
        errorsDir = os.path.join(destDir, "_errors")
        if not os.path.isdir(errorsDir):
            os.mkdir(errorsDir)
        move(extractFolder, errorsDir)
        move(file, errorsDir)