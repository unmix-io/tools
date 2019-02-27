"""
Filreader enriching files with synonyms out of wordnet
"""

import sys
from os import listdir, rename, makedirs, remove
from os.path import join, isfile, dirname, exists, isdir, pardir
import yaml
import subprocess
import datetime
import re

__author__ = "kaufmann-a@hotmail.ch"

#Beispiel ffmpeg mp4 streams auftrennen und zusammenmergen: ffmpeg -i test.mp4 -filter_complex "[0:1][0:2]amerge=inputs=2[ab]" -map [ab] 1.wav
#Hier wurden streams 2 und 3 gemerged


def read_metadata_for_song(metadata_path, songname):
    songpath = song_path_metadata(metadata_path, songname)

    if not isfile(songpath):
        return {}

    with open(songpath, 'r') as fhandle:
        try:
            return yaml.load(fhandle)
        except Exception as inst:
            log_file.write(str(type(inst)) + ": Yaml-file for song " + songpath + "could not be loaded")
            return {}


def song_path_metadata(metadata_path, songname):
    for file in listdir(metadata_path):
        if songname in str(file):
            return join(metadata_path, file)

    log_file.write("Error - Metadata: Following song not found in Metadata: " + songname)
    return {}


def is_song_valid(metadata_path, songname):
    def is_instrumental(song_metadata):
        return not song_metadata['instrumental'] == 'no'

    def has_bleed(song_metadata):
        return not song_metadata['has_bleed'] == 'no'

    song_metadata = read_metadata_for_song(metadata_path, songname)

    if not song_metadata:
        log_file.write("Error: Metadata-file for song for " + songname + " doesn't contain proper yaml code")
        return False

    return not is_instrumental(song_metadata) and not has_bleed(song_metadata)


def is_vocal(file):
    return re.search('vox', file, re.IGNORECASE) or re.search('voc', file, re.IGNORECASE) or re.search('sing', file, re.IGNORECASE) or re.search('speak', file, re.IGNORECASE)


def is_fx(file):
    return re.search('room', file, re.IGNORECASE) or re.search('chamber', file, re.IGNORECASE) or re.search('fx', file, re.IGNORECASE)


def file_processing(sourcedir, destdir, override, l=[]):
    # Create list of directories
    directories = [f for f in listdir(sourcedir) if isdir(join(sourcedir, f))]

    for dir in directories:
        directoyPath = join(sourcedir, dir)

        # Check if dir is a folder (all songs are in subfolders)
        if not isdir(directoyPath):
            log_file.write("Error Songdirectory: TopLevel Songdirectory detected dir which is not a folder with name " + directoyPath)
            continue

        # Check if song is valid
        if not is_song_valid(join(join(join(directoyPath, pardir), pardir), "Metadata"), dir):
            log_file.write("Error Songvalidation: Song with name " + dir + " is not valid")
            continue

        # Find tracks in metadata
        song_metadata = read_metadata_for_song(join(join(join(directoyPath, pardir), pardir), "Metadata"), dir)

        if not song_metadata:
            log_file.write("Error: Metadata-file for song for " + dir + " doesn't contaion proper yaml code")
            continue

        vocal_stems = [song_metadata['stems'][stem]['filename'] for stem in song_metadata['stems'] if is_vocal(song_metadata['stems'][stem]['instrument']) and not is_fx(song_metadata['stems'][stem]['instrument'])]
        instr_stems = [song_metadata['stems'][stem]['filename'] for stem in song_metadata['stems'] if not is_vocal(song_metadata['stems'][stem]['instrument']) and not is_fx(song_metadata['stems'][stem]['instrument'])]

        # Find stems-folder
        folders_with_stems = [join(directoyPath, folder) for folder in listdir(directoyPath) if "stem" in folder.lower()]
        dest_path = join(destdir, dir)

        if(len(vocal_stems) == 0 or len(instr_stems) == 0):
            continue

        if exists(dest_path) and not override:
            continue

        if not exists(dest_path):
            makedirs(dest_path)

        mixdown(folders_with_stems, dest_path, vocal_stems, instr_stems, dir)


def mixdown(folders_with_stems, destination, vocal_stems, instr_stems, songname):
    inpArgs = ""
    filter_complex_voc = ""
    filter_complex_instr = ""
    count_voc_tracks = 0
    count_instr_tracks = 0
    track_count = 0

    for folder_with_stems in folders_with_stems:
        for file in listdir(folder_with_stems):
            if any(map(lambda x: x in file, vocal_stems)):
                inpArgs += "-i \"" + join(folder_with_stems, file) + "\" "
                filter_complex_voc += "[" + str(track_count) + ":0]"
                count_voc_tracks += 1
                track_count += 1
            elif any(map(lambda x: x in file, instr_stems)):
                inpArgs += "-i \"" + join(folder_with_stems, file) + "\" "
                filter_complex_instr += "[" + str(track_count) + ":0]"
                count_instr_tracks += 1
                track_count += 1

    cmd = "ffmpeg " + inpArgs + " -filter_complex \"" + filter_complex_voc + "amix=inputs=" + str(count_voc_tracks) + ":dropout_transition=0[vocs];" + filter_complex_instr + "amix=inputs=" + str(count_instr_tracks) + ":dropout_transition=0[instr]\" -map [vocs] " + join(destination, "vocals_" + songname) + ".wav -map [instr] " + join(destination, "instrumental_" + songname) + ".wav"
    print(cmd)
    try:
        subprocess.check_call(cmd, shell=True)
        log_file.write("Message: " + songname + " was converted successfully")
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " conversion failed")


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
    # Call script with scriptname maxfiles override
    # Example call: dsd100_fileprocessing.py 20 True
    # This will convert the first twenty files in the source dir and override already existing files in the outputdir

    maxCopy = -1
    override = True
    unmix_server = "//192.168.1.29/unmix-server"

    print('Argument List:', str(sys.argv))

    if sys.argv.__len__() == 2:
        unmix_server = sys.argv[1]

    #Setup Logfile
    log_file_dir = "./temp"

    if not exists(log_file_dir):
        makedirs(log_file_dir)

    log_file_path = join(log_file_dir, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_Logfile.txt")
    global log_file
    log_file = open(log_file_path, "w+")

    #Setup Paths
    sourcedir_V1 = unmix_server + "/1_sources/MedleyDBs/V1"
    sourcedir_V2 = unmix_server + "/1_sources/MedleyDBs/V2"
    mixPath = unmix_server + "/2_prepared/MedleyDBs"

    #Start process
    try:
        file_processing(sourcedir_V1, mixPath, override)
        file_processing(sourcedir_V2, mixPath, override)
    finally:
        log_file.close()


    print("Processing finished")
