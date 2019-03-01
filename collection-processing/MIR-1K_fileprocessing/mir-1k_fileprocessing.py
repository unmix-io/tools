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

def calculate_ratio_instr_vocs(instr, voc):
    instrlevel = AudioSegment.from_file(instr, "wav").dBFS
    voclevel = AudioSegment.from_file(voc, "wav").dBFS
    targetDB_VOC = -20 + (-20 * (voclevel / instrlevel - 1))
    return targetDB_VOC

def copy_files(sourcedir, outputdir, maxCopy, override):
    src_files= listdir(sourcedir)
    for file in src_files:
        if maxCopy == 0: break
        old_file = join(sourcedir, file)
        new_folder = join(outputdir, file)
        new_songname_instr = 'instrumental_' + file
        new_songname_vocals = 'vocals_' + file
        new_songfile_instr = join(new_folder, new_songname_instr)
        new_songfile_vocals = join(new_folder, new_songname_vocals)
        if not exists(new_folder): makedirs(new_folder)
        if exists(new_songfile_instr) and override: remove(new_songfile_instr)
        if exists(new_songfile_vocals) and override: remove(new_songfile_vocals)
        if (not exists(new_songfile_vocals) and not exists(new_songfile_instr)) or override:
            cmd = "ffmpeg -i \"" + old_file + "\" -filter_complex \"[0:a]channelsplit=channel_layout=stereo[l][r]\" -map [l] -ac 2 -ar 44100 \"" + join(temp_path, new_songname_instr) + "\" -map [r] -ac 2 -ar 44100 \"" + join(temp_path, new_songname_vocals) + "\""
            subprocess.check_call(cmd, shell=True)  # cwd = cwd

            vocal_volume = calculate_ratio_instr_vocs(join(temp_path, new_songname_instr), join(temp_path, new_songname_vocals))

            normalize(join(temp_path, new_songname_instr), new_songfile_instr, -20)
            normalize(join(temp_path, new_songname_vocals), new_songfile_vocals, vocal_volume)
            print("\n" + new_songname_vocals + " and " + new_songname_instr + " converted" + "\n")
            remove(join(temp_path, new_songname_vocals))
            remove(join(temp_path, new_songname_instr))
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

    sources = unmix_server + "/1_sources/MIR-1K/UndividedWavfile"
    destination = unmix_server + "/2_prepared/MIR-1K"
    if not exists(temp_path): makedirs(temp_path)

    copy_files(sources, destination, maxCopy, override)

    print('Finished converting')

