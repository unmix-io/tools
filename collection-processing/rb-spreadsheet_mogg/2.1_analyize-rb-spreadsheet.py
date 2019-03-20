
from os import listdir, chdir, makedirs, remove
from os.path import isfile, join, isdir, exists, basename, abspath, split
import ctypes
import sys
import datetime
import re
import ntpath
from pydub import AudioSegment
import pathlib
import is_vocal
import csv
import subprocess
import shutil
import glob
# Format specs

# Format 0: ogg, several tracks, including one named "vocals.ogg"
c_0_ogg = 0

temp_path = "./temp"
paninfo_path = ""
eligible_simple_filetypes = ['.wav', '.ogg', '.mp3', '.flac']
eligible_container_filetypes = ['.mogg']


def is_hidden(filepath):
    name = basename(abspath(filepath))
    return name.startswith('.') or has_hidden_attribute(filepath)


def has_hidden_attribute(filepath):
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(filepath)
        assert attrs != -1
        result = bool(attrs & 2)
    except (AttributeError, AssertionError):
        result = False
    return result


def char_code_for_number(i):
    """ Returns a for 0, b for 1, etc. """
    char = ""
    while(i > 25):
        char += chr(97 + (i % 25))
        i = i - 25
    char += chr(97 + i)
    return char # 97 = a


def mixdown(sourcefolder, destination, tracks_vocs, tracks_instr, songname, pandir):
    inp_args = ""
    filter_complex_vocs_L = ""
    filter_complex_instr_L = ""
    filter_complex_vocs_R = ""
    filter_complex_instr_R = ""
    filter_complex_fullmix_L = ""
    filter_complex_fullmix_R = ""
    chain_vocs_L = ""
    chain_vocs_R = ""
    chain_instr_L = ""
    chain_instr_R = ""

    track_count = 0

    #Read csv with panninginfo
    dict_panning = {}
    try:
        with open(join(pandir, songname) + ".csv") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            line_count = 0
            vocals_tracknmbrs = list(map(lambda x: x[:-4], tracks_vocs))
            instrumentl_tracknmbrs = list(map(lambda x: x[:-4], tracks_instr))

            for row in csv_reader:
                if not line_count == 0:
                    dict_panning[int(row[0])] = row[1]
                line_count += 1
            track_count_vocs_L = len([x for x in dict_panning if str(x) in vocals_tracknmbrs and (dict_panning[x] == 'L' or dict_panning[x] == 'M')])
            track_count_vocs_R = len([x for x in dict_panning if str(x) in vocals_tracknmbrs and (dict_panning[x] == 'R' or dict_panning[x] == 'M')])
            track_count_instr_L = len([x for x in dict_panning if str(x) in instrumentl_tracknmbrs and (dict_panning[x] == 'L' or dict_panning[x] == 'M')])
            track_count_instr_R = len([x for x in dict_panning if str(x) in instrumentl_tracknmbrs and (dict_panning[x] == 'R' or dict_panning[x] == 'M')])
    except Exception as inst:
        log_file.write(str(type(inst)) + ": Panningfile of song " + songname + "could not be found")
        log_file.flush()
        return

    try:
        for tracknr, track in enumerate(tracks_vocs):
            if dict_panning[int(track[:-4])] == "L":
                char = char_code_for_number(track_count)
                filter_complex_vocs_L += "[" + str(track_count) + ":0]volume=" + str(1/(track_count_vocs_L + track_count_instr_L) / (1/track_count_vocs_L)) + "[" + char + "];"
                filter_complex_fullmix_L += "[" + str(track_count) + ":0]"
                chain_vocs_L += "[" + char + "]"
            if dict_panning[int(track[:-4])] == "R":
                char = char_code_for_number(track_count)
                filter_complex_vocs_R += "[" + str(track_count) + ":0]volume=" + str(1/(track_count_vocs_R + track_count_instr_R) / (1/track_count_vocs_R)) + "[" + char + "];"
                filter_complex_fullmix_R += "[" + str(track_count) + ":0]"
                chain_vocs_R += "[" + char + "]"
            if dict_panning[int(track[:-4])] == "M":
                char_L = char_code_for_number(track_count)
                filter_complex_vocs_L += "[" + str(track_count) + ":0]volume=" + str(1 / (track_count_vocs_L + track_count_instr_L) / (1 / track_count_vocs_L)) + "[" + char_L + "];"
                filter_complex_fullmix_L += "[" + str(track_count) + ":0]"
                chain_vocs_L += "[" + char_L + "]"
                char_R = char_code_for_number(track_count)
                filter_complex_vocs_R += "[" + str(track_count) + ":0]volume=" + str(1 / (track_count_vocs_R + track_count_instr_R) / (1 / track_count_vocs_R)) + "[" + char_R + "];"
                filter_complex_fullmix_R += "[" + str(track_count) + ":0]"
                chain_vocs_R += "[" + char_R + "]"
            inp_args += "-i \"" + join(sourcefolder, track )+ "\" "
            track_count += 1
        for tracknr, track in enumerate(tracks_instr):
            if dict_panning[int(track[:-4])] == "L":
                char = char_code_for_number(track_count)
                filter_complex_instr_L += "[" + str(track_count) + ":0]volume=" + str(1/(track_count_vocs_L + track_count_instr_L) / (1/track_count_instr_L)) + "[" + char + "];"
                filter_complex_fullmix_L += "[" + str(track_count) + ":0]"
                chain_instr_L += "[" + char + "]"
            if dict_panning[int(track[:-4])] == "R":
                char = char_code_for_number(track_count)
                filter_complex_instr_R += "[" + str(track_count) + ":0]volume=" + str(1/(track_count_vocs_R + track_count_instr_R) / (1/track_count_instr_R)) + "[" + char + "];"
                filter_complex_fullmix_R += "[" + str(track_count) + ":0]"
                chain_instr_R += "[" + char + "]"
            if dict_panning[int(track[:-4])] == "M":
                char_L = char_code_for_number(track_count)
                filter_complex_instr_L += "[" + str(track_count) + ":0]volume=" + str(1 / (track_count_vocs_L + track_count_instr_L) / (1/track_count_instr_L)) + "[" + char_L + "];"
                filter_complex_fullmix_L += "[" + str(track_count) + ":0]"
                chain_instr_L += "[" + char_L + "]"
                char_R = char_code_for_number(track_count)
                filter_complex_instr_R += "[" + str(track_count) + ":0]volume=" + str(1 / (track_count_vocs_R + track_count_instr_R) / (1 /track_count_instr_R)) + "[" + char_R + "];"
                filter_complex_fullmix_R += "[" + str(track_count) + ":0]"
                chain_instr_R += "[" + char_R + "]"
            inp_args += "-i \"" + join(sourcefolder, track) + "\" "
            track_count += 1
    except Exception as inst:
            log_file.write(str(type(inst)) + ": Error in Panningfileprocessing of song" + songname + "\n")
            log_file.flush()

    # Create a fullmix of all audio tracks
    try:
        cmd_fullmix = "ffmpeg " + inp_args + " -filter_complex \"" + filter_complex_fullmix_L + "amix=inputs=" \
                      + str(track_count_vocs_L + track_count_instr_L) + "[mixL];" + filter_complex_fullmix_R + "amix=inputs=" + str(track_count_vocs_R + track_count_instr_R) \
                      + "[mixR];[mixL][mixR]join=inputs=2:channel_layout=stereo[mix]\" -map [mix] -y -ar 44100 \"" \
                      + join(temp_path, "fullmix_" + songname + ".wav") + "\""
        subprocess.check_call(cmd_fullmix, shell=True)
    except Exception as inst:
        log_file.write(str(type(inst)) + ": ffmpeg fullmix creation failed " + track + "\n")

    # Calculate the average volume of the fullmix and suptract it from the reference normalization volume
    try:
        avg_db = AudioSegment.from_file(join(temp_path, "fullmix_" + songname + ".wav")).dBFS
        differenz_db = -20 - avg_db
    except Exception as inst:
        log_file.write(str(type(inst)) + ": Audiosegment couldn't read audiofile " + track + "\n")
        differenz_db = -20

    # Finally mix vocals and instrumentals separately and apply volume difference to the traacks
    try:
        cmd = "ffmpeg " + inp_args + " -filter_complex \"" + filter_complex_vocs_L + chain_vocs_L \
              + "amix=inputs=" + str(track_count_vocs_L) + ",volume=" + str(differenz_db) + "dB[vocsL];" + filter_complex_vocs_R + chain_vocs_R \
              + "amix=inputs=" + str(track_count_vocs_R) + ",volume=" + str(differenz_db) + "dB[vocsR];" + filter_complex_instr_L + chain_instr_L \
              + "amix=inputs=" + str(track_count_instr_L) + ",volume=" + str(differenz_db) + "dB[instrL];" + filter_complex_instr_R + chain_instr_R \
              + "amix=inputs=" + str(track_count_instr_R) + ",volume=" + str(differenz_db) + "dB[instrR];" \
              + "[vocsL][vocsR]join=inputs=2:channel_layout=stereo[vocs];[instrL][instrR]join=inputs=2:channel_layout=stereo[instr]\" -map [vocs] -ac 2 -y -ar 44100 \"" \
              + join(destination, "vocals_" + songname + ".wav") + "\" -map [instr] -ac 2 -y -ar 44100 \"" + join(destination, "instrumental_" + songname + ".wav") + "\""
        print(cmd)
        subprocess.check_call(cmd, shell=True)
        log_file.write("Message: " + songname + " was converted successfully\n")
        log_file.flush()
        # For testing purposes
        cmd_test = "ffmpeg -i \"" + join(temp_path,
                                         "fullmix_" + songname + ".wav") + "\" -filter_complex \"[0:0]volume=" + str(
            differenz_db) + "dB\" -y -ar 44100 \"" + join(temp_path, "fullmux_norm_" + songname + ".wav") + "\""
        subprocess.call(cmd_test, shell=True)
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " conversion failed\n")
        log_file.flush()
        return
    finally:
        try:
            files = listdir(temp_path)
            for f in files:
                remove(join(temp_path, f))
        except:
            log_file.write("Could not delete tempfile\n")
            log_file.flush()


def file_processing(sourcedir, destdir, maxCopy, override, pandir):

    # Create list of directories and songfiles (simple files stands for normal mono or stereo tracks, no containers)
    directories = [f for f in listdir(sourcedir) if isdir(join(sourcedir, f))]
    eligible_simple_files = [f for f in listdir(sourcedir) if isfile(join(sourcedir, f)) and eligible_simple_filetypes.__contains__(pathlib.Path(f).suffix) and not is_hidden(f)]

    for d in directories:
        directory_path = join(sourcedir, d)
        file_processing(directory_path, destdir, maxCopy, override, pandir)

    #Process Simple File Types
    vocals = [f for f in eligible_simple_files if is_vocal.is_vocal(ntpath.basename(sourcedir), f)]
    instrumentals = [f for f in eligible_simple_files if not is_vocal.is_vocal(ntpath.basename(sourcedir), f)]

    # Abort process if there are no vocals or no instrumentals in folder
    if len(vocals) == 0 or len(instrumentals) == 0:
        return

    # Add new folder in target directory if not yet existing, if name to short parentfolder of source directory is added to name as well
    new_foldername = ""
    path = sourcedir
    while new_foldername.__len__() < 10:
        path, folder = split(path)

        if folder != "":
            temp = new_foldername
            if temp:
                temp = "_" + new_foldername
            else:
                temp = new_foldername
            new_foldername = folder + temp
        else:
            if path != "":
                temp = new_foldername
                new_foldername = folder + temp
            break


    if not exists(join(destdir, new_foldername)):
        makedirs(join(destdir, new_foldername))
    elif not override:
        return

    mixdown(sourcedir, join(destdir, new_foldername), vocals, instrumentals, new_foldername, pandir)



def setup_logfile(log_file_dir):
    if not exists(log_file_dir):
        makedirs(log_file_dir)

    log_file_path = join(log_file_dir, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_Logfile.txt")
    global log_file
    log_file = open(log_file_path, "w+")

def init():
    # Initialize logfile
    setup_logfile("./logfiles")

    # Create temp folder
    if not exists(temp_path):
        makedirs(temp_path)


if __name__ == '__main__':
    maxCopy = 3
    override = False
    unmix_server = "//192.168.1.29/unmix-server"

    print('Argument List:', str(sys.argv))

    if sys.argv.__len__() == 2:
        unmix_server = sys.argv[1]

    sourcedir = unmix_server + "/1_sources/RockBand-GuitarHero-moggs"
    destdir = unmix_server + "/2_prepared/RockBand-GuitarHero-moggs"
    pandir = unmix_server + "/1_sources/RockBand-GuitarHero/_panningInfo"
    init()

    try:
        file_processing(sourcedir, destdir, maxCopy, override, pandir)
    finally:
        log_file.close()

    print('Finished converting files')
