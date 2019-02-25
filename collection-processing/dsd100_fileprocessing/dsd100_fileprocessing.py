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
sources_dev = unmix_server + "/1_sources/DSD100/Sources/Dev"
sources_test = unmix_server + "/1_sources/DSD100/Sources/Test"
sources_out = unmix_server + "/2_prepared/dsd100"


def copy_files(sourcedir, outputdir, maxCopy, override):
    src_files = listdir(sourcedir)
    for folder in src_files:
        if maxCopy == 0: break

        songfolder = join(sourcedir, folder)

        #Input files
        bass_track = join(songfolder, 'bass.wav')
        drums_track = join(songfolder, 'drums.wav')
        restinst_track = join(songfolder, 'other.wav')
        vocals_track = join(songfolder, 'vocals.wav')

        new_folder = join(outputdir, folder)
        new_songname_instr = 'instrumental_' + folder + '.wav'
        new_songname_vocals = 'vocals_' + folder + '.wav'
        new_songfile_instr = join(new_folder, new_songname_instr)
        new_songfile_vocals = join(new_folder, new_songname_vocals)

        cmd = "ffmpeg" + ' -i "' + bass_track + '" -i "' + drums_track + '" -i "' + restinst_track + '" -i "' + vocals_track + \
              "\" -filter_complex \"[0:0][1:0][2:0]amerge=inputs=3[instr]\" -map [instr] -ac 2 \"" + new_songfile_instr + \
              "\" -map 3:0 -ac 2 \"" + new_songfile_vocals + "\""

        if exists(bass_track) and exists(drums_track) and exists(restinst_track) and exists(vocals_track):
            if not exists(new_folder): makedirs(new_folder)

            if exists(new_songfile_instr) and override:
                remove(new_songfile_instr)
            if exists(new_songfile_vocals) and override:
                remove(new_songfile_vocals)
            if (not exists(new_songfile_vocals) and not exists(new_songfile_instr)) or override:
                subprocess.check_call(cmd, shell=True)  # cwd = cwd
                print("\n" + new_songname_vocals + " and " + new_songname_instr + " converted" + "\n")
            maxCopy -= 1


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

    copy_files(sources_test, sources_out, maxCopy, override)
    copy_files(sources_dev, sources_out, maxCopy, override)


    print('Finished converting files')

