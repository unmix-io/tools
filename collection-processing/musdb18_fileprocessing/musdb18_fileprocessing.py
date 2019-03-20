"""
Filreader enriching files with synonyms out of wordnet
"""

import sys
from os import listdir, rename, makedirs, remove
from os.path import join, isfile, dirname, exists
import shutil
from pydub import AudioSegment
import subprocess

__author__ = "kaufmann-a@hotmail.ch"


temp_path = "./temp"


def copy_files(sourcedir, outputdir, suffix, maxCopy, override):
    src_files= listdir(sourcedir)
    for file in src_files:
        if maxCopy == 0: break

        new_songname = file[:-suffix.__len__()]
        old_file = join(sourcedir, file)
        new_folder = join(outputdir, new_songname)
        new_songname_instr = 'instrumental_' + new_songname + '.wav'
        new_songname_vocals = 'vocals_' + new_songname + '.wav'
        new_songfile_instr = join(new_folder, new_songname_instr)
        new_songfile_vocals = join(new_folder, new_songname_vocals)
        if not exists(new_folder): makedirs(new_folder)
        if exists(new_songfile_instr) and override: remove(new_songfile_instr)
        if exists(new_songfile_vocals) and override: remove(new_songfile_vocals)
        if (not exists(new_songfile_vocals) and not exists(new_songfile_instr)) or override:

            # Extract wav files from mp4 and put to temp-path
            try:
                cmd = "ffmpeg -i \"" + old_file + "\" -map 0:1 -ac 2 ./temp/line1.wav -map 0:2 -ac 2 ./temp/line2.wav -map 0:3 -ac 2 ./temp/line3.wav -map 0:4 -ac 2 ./temp/line4.wav"
                subprocess.check_call(cmd, shell=True)  # cwd = cwd
            except Exception as stats:
                print(type(stats))

            # Create a fullmix of all audio tracks
            try:
                cmd = "ffmpeg" + ' -i "' + join(temp_path, "line1.wav") + '" -i "' + join(temp_path, "line2.wav") + '" -i "' + join(temp_path, "line3.wav") + '" -i "' \
                      + join(temp_path, "line4.wav") + "\" -filter_complex \"[0:0][1:0][2:0][3:0]amix=inputs=4[mix]\" -map [mix] -ac 2 \"" \
                      + join(temp_path, "fullmix_" + new_songname + ".wav") + "\""
                subprocess.check_call(cmd, shell=True)
            except Exception as stats:
                print(type(stats))

            # Calculate the average volume of the fullmix and suptract it from the reference normalization volume
            try:
                avg_db = AudioSegment.from_file(join(temp_path, "fullmix_" + new_songname + ".wav")).dBFS
                differenz_db = -20 - avg_db
            except Exception as inst:
                print(str(type(inst)) + ": Audiosegment couldn't read audiofile " + new_songname + "\n")
                differenz_db = -20

            # Finally mix vocals and instrumentals separately and apply volume difference to the traacks
            try:
                cmd = "ffmpeg" + ' -i "' + join(temp_path, "line1.wav") + '" -i "' + join(temp_path, "line2.wav") + '" -i "' + join(temp_path, "line3.wav") + '" -i "' + join(temp_path, "line4.wav") + \
                      "\" -filter_complex \"[0:0]volume=0.75[bass];[1:0]volume=0.75[drums];[2:0]volume=0.75[restinst];[3:0]volume=0.25[vocals];" \
                      "[bass][drums][restinst]amix=inputs=3,volume=" + str(differenz_db) + "dB[instr];[vocals]volume=" \
                      + str(differenz_db) + "dB[vocs]\" -map [instr] -ac 2 \"" + new_songfile_instr + "\" -map [vocs] -ac 2 \"" + new_songfile_vocals + "\""
                subprocess.check_call(cmd, shell=True)

                # For testing purposes
                cmd_test = "ffmpeg -i \"" + join(temp_path,
                                                 "fullmix_" + new_songname + ".wav") + "\" -filter_complex \"[0:0]volume=" + str(
                    differenz_db) + "dB\" -y -ar 44100 \"" + join(temp_path,
                                                                  "fullmix_norm_" + new_songname + ".wav") + "\""
                subprocess.call(cmd_test, shell=True)
            except Exception as inst:
                print(type(inst))
            try:
                files = listdir(temp_path)
                for f in files:
                    remove(join(temp_path, f))
            except:
                print("tempfolder could not be emptied")

        maxCopy -= 1

if __name__ == '__main__':
    #Call script with scriptname maxfiles override
    #Example call: musdb18_fileprocessing.py 20 True
    #This will convert the first twenty files in the source dir and override already existing files in the outputdir

    maxCopy = -1
    override = True
    unmix_server = '//192.168.1.29/unmix-server'

    print('Argument List:', str(sys.argv))

    if sys.argv.__len__() == 2:
        unmix_server = sys.argv[1]

    # Setup paths
    sources = unmix_server + "/1_sources/musdb18/songs"
    destination = unmix_server + "/2_prepared/musdb18"
    if not exists(temp_path): makedirs(temp_path)
    copy_files(sources, destination, '.stem.wav', maxCopy, override)

    print('Finished converting')

