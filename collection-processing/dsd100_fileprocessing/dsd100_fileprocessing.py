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

def normalize(file, destination, db = -20.0):
    def match_target_amplitude(sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    sound = AudioSegment.from_file(file, "wav")
    normalized_sound = match_target_amplitude(sound, db)
    normalized_sound.export(destination, format="wav")

def calculate_ratio_instr_vocs(bass, drums_track, restinst_track, vocals_track):
    level1 = AudioSegment.from_file(bass, "wav").dBFS
    level2 = AudioSegment.from_file(drums_track, "wav").dBFS
    level3 = AudioSegment.from_file(restinst_track, "wav").dBFS
    level4 = AudioSegment.from_file(vocals_track, "wav").dBFS
    targetDB_VOC = -20 + (-20 * (level4 / ((level1+level2+level3)/3)-1))
    return targetDB_VOC

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
        #Calculate ratio instrumentals/vocals and return nromalizationlevel for vocals
        targetVoc_level = calculate_ratio_instr_vocs(bass_track, drums_track, restinst_track, vocals_track)

        new_folder = join(outputdir, folder)
        new_songname_instr = 'instrumental_' + folder + '.wav'
        new_songname_vocals = 'vocals_' + folder + '.wav'
        new_songfile_instr = join(new_folder, new_songname_instr)
        new_songfile_vocals = join(new_folder, new_songname_vocals)

        cmd = "ffmpeg" + ' -i "' + bass_track + '" -i "' + drums_track + '" -i "' + restinst_track + '" -i "' + vocals_track + \
              "\" -filter_complex \"[0:0][1:0][2:0]amix=inputs=3[instr]\" -map [instr] -ac 2 \"" + join(temp_path, new_songname_instr) + \
              "\" -map 3:0 -ac 2 \"" + join(temp_path, new_songname_vocals) + "\""
        subprocess.check_call(cmd, shell=True)

        if exists(bass_track) and exists(drums_track) and exists(restinst_track) and exists(vocals_track):
            if not exists(new_folder): makedirs(new_folder)

            if exists(new_songfile_instr) and override:
                remove(new_songfile_instr)
            if exists(new_songfile_vocals) and override:
                remove(new_songfile_vocals)
            if (not exists(new_songfile_vocals) and not exists(new_songfile_instr)) or override:
                normalize(join(temp_path, new_songname_instr), new_songfile_instr, -20)
                normalize(join(temp_path, new_songname_vocals), new_songfile_vocals, targetVoc_level)
                print("\n" + new_songname_vocals + " and " + new_songname_instr + " converted" + "\n")
                remove(join(temp_path, new_songname_vocals))
                remove(join(temp_path, new_songname_instr))
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

