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


def copy_files(sourcedir, outputdir, maxCopy, override):
    src_files = listdir(sourcedir)
    for folder in src_files:

        if maxCopy == 0: break

        if exists(join(outputdir, folder)) and not override:
            continue

        songfolder = join(sourcedir, folder)

        #Input files
        bass_track = join(songfolder, 'bass.wav')
        drums_track = join(songfolder, 'drums.wav')
        restinst_track = join(songfolder, 'other.wav')
        vocals_track = join(songfolder, 'vocals.wav')

        # Create a fullmix of all audio tracks
        try:
            cmd = "ffmpeg" + ' -i "' + bass_track + '" -i "' + drums_track + '" -i "' + restinst_track + '" -i "' \
                  + vocals_track + "\" -filter_complex \"[0:0][1:0][2:0][3:0]amix=inputs=4[mix]\" -map [mix] -ac 2 \"" \
                  + join(temp_path, "fullmix_" + folder + ".wav")
            subprocess.check_call(cmd, shell=True)
        except Exception as stats:
            print(type(stats))

        # Calculate the average volume of the fullmix and suptract it from the reference normalization volume
        try:
            avg_db = AudioSegment.from_file(join(temp_path, "fullmix_" + folder + ".wav")).dBFS
            differenz_db = -20 - avg_db
        except Exception as inst:
            print(str(type(inst)) + ": Audiosegment couldn't read audiofile " + folder + "\n")
            differenz_db = -20

        new_folder = join(outputdir, folder)
        new_songname_instr = 'instrumental_' + folder + '.wav'
        new_songname_vocals = 'vocals_' + folder + '.wav'
        new_songfile_instr = join(new_folder, new_songname_instr)
        new_songfile_vocals = join(new_folder, new_songname_vocals)

        # Finally mix vocals and instrumentals separately and apply volume difference to the traacks
        try:
            cmd = "ffmpeg" + ' -i "' + bass_track + '" -i "' + drums_track + '" -i "' + restinst_track + '" -i "' + vocals_track + \
                  "\" -filter_complex \"[0:0]volume=0.75[bass];[1:0]volume=0.75[drums];[2:0]volume=0.75[restinst];[3:0]volume=0.25[vocals];" \
                  "[bass][drums][restinst]amix=inputs=3,volume=" + str(differenz_db) + "dB[instr];[vocals]volume=" + str(differenz_db) + "dB[vocs]\" " \
                  "-map [instr] -ac 2 \"" + new_songfile_instr + "\" -map [vocs] -ac 2 \"" + new_songfile_vocals + "\""
            subprocess.check_call(cmd, shell=True)

            # For testing purposes
            # cmd_test = "ffmpeg -i \"" + join(temp_path, "fullmix_" + folder + ".wav") + "\" -filter_complex \"[0:0]volume=" + str(
            #     differenz_db) + "dB\" -y -ar 44100 \"" + join(temp_path, "fullmix_norm_" + folder + ".wav") + "\""
            # subprocess.call(cmd_test, shell=True)
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
    # Call script with scriptname maxfiles override
    # Example call: dsd100_fileprocessing.py 20 True
    # This will convert the first twenty files in the source dir and override already existing files in the outputdir

    maxCopy = -1
    override = True
    unmix_server = '//192.168.1.29/unmix-server'

    print('Argument List:', str(sys.argv))

    if sys.argv.__len__() == 2:
        unmix_server = sys.argv[1]

    sources_dev = unmix_server + "/1_sources/DSD100/Sources/Dev"
    sources_test = unmix_server + "/1_sources/DSD100/Sources/Test"
    sources_out = unmix_server + "/2_prepared/dsd100"
    if not exists(temp_path): makedirs(temp_path)

    copy_files(sources_test, sources_out, maxCopy, override)
    copy_files(sources_dev, sources_out, maxCopy, override)


    print('Finished converting files')

