"""
Filreader enriching files with synonyms out of wordnet
"""

import sys
from os import listdir, rename, makedirs, remove
from os.path import join, isfile, dirname, exists
import shutil
import subprocess

__author__ = "kaufmann-a@hotmail.ch"
unmix_server = '//192.168.1.29/unmix-server'
sources = unmix_server + "/1_sources/musdb18/songs"
destination = unmix_server + "/2_prepared/musdb18"

#Beispiel ffmpeg mp4 streams auftrennen und zusammenmergen: ffmpeg -i test.mp4 -filter_complex "[0:1][0:2]amerge=inputs=2[ab]" -map [ab] 1.wav
#Hier wurden streams 2 und 3 gemerged

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
            cmd = "ffmpeg -i \"" + old_file + "\" -filter_complex \"[0:1][0:2][0:3]amerge=inputs=3[instr]\" -map [instr] -ac 2 \"" + new_songfile_instr + "\" -map 0:4 -ac 2 \"" + new_songfile_vocals + "\""
            subprocess.check_call(cmd, shell=True)  # cwd = cwd
            print("\n" + new_songname_vocals + " and " + new_songname_instr + " converted" + "\n")
        maxCopy -= 1

if __name__ == '__main__':
    #Call script with scriptname maxfiles override
    #Example call: musdb18_fileprocessing.py 20 True
    #This will convert the first twenty files in the source dir and override already existing files in the outputdir

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
            exit ("Add a number as the first argument")
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

    copy_files(sources, destination, '.stem.wav', maxCopy, override)

    print('Finished converting')

