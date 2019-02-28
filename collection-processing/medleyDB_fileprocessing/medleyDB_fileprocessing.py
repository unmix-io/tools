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
        folders_with_stems = [join(directoyPath, folder) for folder in listdir(directoyPath) if "stem" in folder.lower() and isdir(join(directoyPath, folder))]
        dest_path = join(destdir, dir)

        if(len(vocal_stems) == 0 or len(instr_stems) == 0):
            continue

        if exists(dest_path) and not override:
            log_file.write("MEssage: Song with name " + dir + " already existing\n")
            continue

        if not exists(dest_path):
            makedirs(dest_path)

        mixdown(folders_with_stems, dest_path, vocal_stems, instr_stems, dir)

def normalize(file, destination, db = -20.0):
    def match_target_amplitude(sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    sound = AudioSegment.from_file(file, "wav")
    normalized_sound = match_target_amplitude(sound, db)
    normalized_sound.export(destination, format="wav")


def mixdown(folders_with_stems, destination, vocal_stems, instr_stems, songname):
    inpArgs = ""
    filter_complex_voc = ""
    filter_complex_instr = ""
    count_voc_tracks = 0
    count_instr_tracks = 0
    track_count = 0
    sum_volumes_voc = 0
    sum_volumes_instr = 0

    for folder_with_stems in folders_with_stems:
        for file in listdir(folder_with_stems):
            if any(map(lambda x: x in file, vocal_stems)):
                inpArgs += "-i \"" + join(folder_with_stems, file) + "\" "
                filter_complex_voc += "[" + str(track_count) + ":0]"
                sum_volumes_voc += AudioSegment.from_file(join(folder_with_stems, file), "wav").dBFS
                count_voc_tracks += 1
                track_count += 1
            elif any(map(lambda x: x in file, instr_stems)):
                inpArgs += "-i \"" + join(folder_with_stems, file) + "\" "
                filter_complex_instr += "[" + str(track_count) + ":0]"
                sum_volumes_instr += AudioSegment.from_file(join(folder_with_stems, file), "wav").dBFS
                count_instr_tracks += 1
                track_count += 1

    cmd = "ffmpeg " + inpArgs + " -filter_complex \"" + filter_complex_voc + "amix=inputs=" + str(count_voc_tracks) + ":dropout_transition=0[vocs];" + filter_complex_instr + "amix=inputs=" + str(count_instr_tracks) + ":dropout_transition=0[instr]\" -map [vocs] " + join(temp_path, "vocals_" + songname) + ".wav -map [instr] " + join(temp_path, "instrumental_" + songname) + ".wav"
    print(cmd)
    try:
        subprocess.check_call(cmd, shell=True)
        log_file.write("Message: " + songname + " was converted successfully\n")
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " conversion failed\n")
        return

    # Calculate ratio of volume of original vocals and volume of original instruments. Instruments will be normalized to
    # -20 DB, Vocals to -20 DB * Ratio
    try:
        targetDB_voc = -20 + (-20 * ((sum_volumes_voc/count_voc_tracks) / (sum_volumes_instr/count_instr_tracks) - 1))

        normalize(join(temp_path, "vocals_" + songname) + ".wav", join(destination, "vocals_" + songname) + ".wav", targetDB_voc)
        normalize(join(temp_path, "instrumental_" + songname) + ".wav", join(destination, "instrumental" + songname) + ".wav", -20)
        log_file.write("Message: " + songname + " was normalized successfully\n")
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " normalization failed\n")

    try:
        remove(join(temp_path, "vocals_" + songname) + ".wav")
        remove(join(temp_path, "instrumental_" + songname) + ".wav")
    except:
        log_file.write("Could not delete tempfile\n")

if __name__ == '__main__':
    # Call script with scriptname maxfiles override
    # Example call: dsd100_fileprocessing.py 20 True
    # This will convert the first twenty files in the source dir and override already existing files in the outputdir

    maxCopy = -1
    override = False
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
