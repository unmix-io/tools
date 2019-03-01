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

#Beispiel ffmpeg mp4 streams auftrennen und zusammenmergen: ffmpeg -i test.mp4 -filter_complex "[0:1][0:2]amerge=inputs=2[ab]" -map [ab] 1.wav
#Hier wurden streams 2 und 3 gemerged

def normalize(file, destination, db = -20.0):
    def match_target_amplitude(sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    sound = AudioSegment.from_file(file, "wav")
    normalized_sound = match_target_amplitude(sound, db)
    normalized_sound.export(destination, format="wav")

def calculate_ratio_instr_vocs():
    level1 = AudioSegment.from_file(join(temp_path, "line1.wav"), "wav").dBFS
    level2 = AudioSegment.from_file(join(temp_path, "line2.wav"), "wav").dBFS
    level3 = AudioSegment.from_file(join(temp_path, "line3.wav"), "wav").dBFS
    level4 = AudioSegment.from_file(join(temp_path, "line4.wav"), "wav").dBFS
    targetDB_VOC = -20 + (-20 * (level4 / ((level1+level2+level3)/3)-1))
    return targetDB_VOC

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
            cmd = "ffmpeg -i \"" + old_file + "\" -map 0:1 -ac 2 ./temp/line1.wav -map 0:2 -ac 2 ./temp/line2.wav -map 0:3 -ac 2 ./temp/line3.wav -map 0:4 -ac 2 ./temp/line4.wav"
            subprocess.check_call(cmd, shell=True)  # cwd = cwd

            # Find out normalization-level for voc tracks out of ratio vocals/instrumentals
            voclevel = calculate_ratio_instr_vocs()

            #Merge tracks and put back to temppath
            cmd2 = "ffmpeg -i " + join(temp_path, "line1.wav") + " -i " + join(temp_path, "line2.wav") + " -i " + join(temp_path, "line3.wav") + " -i " + join(temp_path, "line4.wav") + " -filter_complex \"[0:0][1:0][2:0]amix=inputs=3[instr]\" -map [instr] \"" + join(temp_path, new_songname_instr) + "\" -map 3:0 \"" + join(temp_path, new_songname_vocals) + "\""
            subprocess.check_call(cmd2, shell=True)
            remove(join(temp_path, "line1.wav"))
            remove(join(temp_path, "line2.wav"))
            remove(join(temp_path, "line3.wav"))
            remove(join(temp_path, "line4.wav"))

            #Normalize volumes
            normalize(join(temp_path, new_songname_instr), new_songfile_instr, -20)
            normalize(join(temp_path, new_songname_vocals), new_songfile_vocals, voclevel)
            remove(join(temp_path, new_songname_vocals))
            remove(join(temp_path, new_songname_instr))

            print("\n" + new_songname_vocals + " and " + new_songname_instr + " converted" + "\n")
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

