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
from pydub import AudioSegment

__author__ = "kaufmann-a@hotmail.ch"
temp_path = "./temp"

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
            log_file.write(str(type(inst)) + ": Yaml-file for song " + songpath + "could not be loaded\n")
            return {}


def song_path_metadata(metadata_path, songname):
    for file in listdir(metadata_path):
        if songname in str(file):
            return join(metadata_path, file)

    log_file.write("Error - Metadata: Following song not found in Metadata: " + songname + "\n")
    return {}


def is_song_valid(metadata_path, songname):
    def is_instrumental(song_metadata):
        return not song_metadata['instrumental'] == 'no'

    def has_bleed(song_metadata):
        return not song_metadata['has_bleed'] == 'no'

    song_metadata = read_metadata_for_song(metadata_path, songname)

    if not song_metadata:
        log_file.write("Error: Metadata-file for song for " + songname + " doesn't contain proper yaml code\n")
        return False

    return not is_instrumental(song_metadata) and not has_bleed(song_metadata)


def is_vocal(file):
    return re.search('vox', file, re.IGNORECASE) or re.search('voc', file, re.IGNORECASE) or re.search('sing', file, re.IGNORECASE) or re.search('speak', file, re.IGNORECASE)


def is_fx(file):
    return re.search('room', file, re.IGNORECASE) or re.search('chamber', file, re.IGNORECASE) or re.search('fx', file, re.IGNORECASE)


def file_processing(sourcedir, destdir, override):
    # Create list of directories
    directories = [f for f in listdir(sourcedir) if isdir(join(sourcedir, f))]

    for dir in directories:
        directoyPath = join(sourcedir, dir)

        # Check if dir is a folder (all songs are in subfolders)
        if not isdir(directoyPath):
            log_file.write("Error Songdirectory: TopLevel Songdirectory detected dir which is not a folder with name " + directoyPath + "\n")
            continue

        # Check if song is valid
        if not is_song_valid(join(join(join(directoyPath, pardir), pardir), "Metadata"), dir):
            log_file.write("Error Songvalidation: Song with name " + dir + " is not valid\n")
            continue

        # Find tracks in metadata
        song_metadata = read_metadata_for_song(join(join(join(directoyPath, pardir), pardir), "Metadata"), dir)

        if not song_metadata:
            log_file.write("Error: Metadata-file for song for " + dir + " doesn't contaion proper yaml code\n")
            continue

        vocal_stems = [song_metadata['stems'][stem]['filename'] for stem in song_metadata['stems'] if is_vocal(song_metadata['stems'][stem]['instrument']) and not is_fx(song_metadata['stems'][stem]['instrument'])]
        instr_stems = [song_metadata['stems'][stem]['filename'] for stem in song_metadata['stems'] if not is_vocal(song_metadata['stems'][stem]['instrument']) and not is_fx(song_metadata['stems'][stem]['instrument'])]

        # Find stems-folder
        folders_with_stems = [join(directoyPath, folder) for folder in listdir(directoyPath) if (("stem" in folder.lower()) and isdir(join(directoyPath, folder)))]
        dest_path = join(destdir, dir)

        if(len(vocal_stems) == 0 or len(instr_stems) == 0):
            continue

        if exists(dest_path) and not override:
            log_file.write("MEssage: Song with name " + dir + " already existing\n")
            continue

        if not exists(dest_path):
            makedirs(dest_path)

        mixdown(folders_with_stems, dest_path, vocal_stems, instr_stems, dir)


def char_code_for_number(i):
    """ Returns a for 0, b for 1, etc. """
    char = ""
    while(i > 25):
        char += chr(97 + (i % 25))
        i = i - 25
    char += chr(97 + i)
    return char # 97 = a

def mixdown(folders_with_stems, destination, vocal_stems, instr_stems, songname):
    inpArgs = ""
    filter_complex_voc = ""
    filter_complex_instr = ""
    filter_complex_fullmix = ""
    chain_vocs = ""
    chain_instr = ""
    count_voc_tracks = 0
    count_instr_tracks = 0
    track_count = 0
    sum_volumes_voc = 0
    sum_volumes_instr = 0

    try:
        for folder_with_stems in folders_with_stems:
            for file in listdir(folder_with_stems):
                if any(map(lambda x: x in file, vocal_stems)):
                    inpArgs += "-i \"" + join(folder_with_stems, file) + "\" "
                    char = char_code_for_number(track_count)
                    filter_complex_voc += "[" + str(track_count) + ":0]volume=" + str(1/(len(vocal_stems) + len(instr_stems)) / (1/len(vocal_stems))) + "[" + char + "];"
                    filter_complex_fullmix += "[" + str(track_count) + ":0]"
                    chain_vocs += "[" + char + "]"
                    count_voc_tracks += 1
                    track_count += 1
                elif any(map(lambda x: x in file, instr_stems)):
                    inpArgs += "-i \"" + join(folder_with_stems, file) + "\" "
                    char = char_code_for_number(track_count)
                    filter_complex_instr += "[" + str(track_count) + ":0]volume=" + str(1/(len(vocal_stems) + len(instr_stems)) / (1/len(instr_stems))) + "[" + char + "];"
                    filter_complex_fullmix += "[" + str(track_count) + ":0]"
                    chain_instr += "[" + char + "]"
                    count_instr_tracks += 1
                    track_count += 1
    except Exception as inst:
        log_file.write("Message: Pydub could not read " + folder_with_stems)


    # Create a fullmix of all audio tracks
    try:
        cmd_fullmix = "ffmpeg " + inpArgs + " -filter_complex \"" + filter_complex_fullmix + "amix=inputs=" + str(track_count) + "[mix]\" -map [mix] -y -ar 44100 \"" + join(temp_path, "fullmix_" + songname + ".wav") + "\""
        subprocess.check_call(cmd_fullmix, shell=True)
    except Exception as inst:
        log_file.write(str(type(inst)) + ": ffmpeg fullmix creation failed " + songname + "\n")

    # Calculate the average volume of the fullmix and suptract it from the reference normalization volume
    try:
        avg_db = AudioSegment.from_file(join(temp_path, "fullmix_" + songname + ".wav")).dBFS
        differenz_db = -20 - avg_db
    except Exception as inst:
        log_file.write(str(type(inst)) + ": Audiosegment couldn't read audiofile " + songname + "\n")
        differenz_db = -20

    # Finally mix vocals and instrumentals separately and apply volume difference to the traacks
    try:
        cmd = "ffmpeg " + inpArgs + " -filter_complex \"" + filter_complex_voc + chain_vocs + "amix=inputs=" \
              + str(len(vocal_stems)) + ",volume=" + str(differenz_db) + "dB[vocs];" + filter_complex_instr + chain_instr + "amix=inputs=" \
              + str(len(instr_stems)) + ",volume=" + str(differenz_db) + "dB[instr]\" -map [vocs] -y -ar 44100 \"" \
              + join(destination, "vocals_" + songname + ".wav") + "\" -map [instr] -y -ar 44100 \"" + join(destination, "instrumental_" + songname + ".wav") + "\""
        print(cmd)
        subprocess.check_call(cmd, shell=True)
        log_file.write("Message: " + songname + " was converted successfully\n")
        # For testing purposes
        cmd_test = "ffmpeg -i \"" + join(temp_path,
                                         "fullmix_" + songname + ".wav") + "\" -filter_complex \"[0:0]volume=" + str(
            differenz_db) + "dB\" -y -ar 44100 \"" + join(temp_path, "fullmux_norm_" + songname + ".wav") + "\""
        subprocess.call(cmd_test, shell=True)
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " conversion failed\n")
        return
    finally:
        try:
            files = listdir(temp_path)
            for f in files:
                remove(join(temp_path, f))
        except:
            log_file.write("Could not delete tempfile\n")

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
    log_file_dir = "./logfiles"

    if not exists(log_file_dir):
        makedirs(log_file_dir)

    log_file_path = join(log_file_dir, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_Logfile.txt")
    global log_file
    log_file = open(log_file_path, "w+")

    #Setup Paths
    sourcedir_V1 = unmix_server + "/1_sources/MedleyDBs/V1"
    sourcedir_V2 = unmix_server + "/1_sources/MedleyDBs/V2"
    mixPath = unmix_server + "/2_prepared/MedleyDBs"
    if not exists(temp_path): makedirs(temp_path)

    #Start process
    try:
        file_processing(sourcedir_V1, mixPath, override)
        file_processing(sourcedir_V2, mixPath, override)
    finally:
        log_file.close()


    print("Processing finished")
