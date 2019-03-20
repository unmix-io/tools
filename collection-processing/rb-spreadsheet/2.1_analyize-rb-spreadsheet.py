
from os import listdir, chdir, makedirs, remove
from os.path import isfile, join, isdir, exists, basename, abspath, split
import ctypes
import sys
import datetime
import re
import ntpath
from pydub import AudioSegment
import pathlib
import subprocess
import shutil
import glob
# Format specs

# Format 0: ogg, several tracks, including one named "vocals.ogg"
c_0_ogg = 0

temp_path = "./temp"
eligible_simple_filetypes = ['.wav', '.ogg', '.mp3']
eligible_container_filetypes = ['.mogg']

def is_vocal(file):
    return re.search('voc', file, re.IGNORECASE) or re.search('vox', file, re.IGNORECASE)


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


def normalize(file, destination, db = -20.0):
    def match_target_amplitude(sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    sound = AudioSegment.from_file(file, "wav")
    normalized_sound = match_target_amplitude(sound, db)
    normalized_sound.export(destination, format="wav")


def charCodeForNumber(i):
    """ Returns a for 0, b for 1, etc. """
    char = ""
    while(i > 25):
        char += chr(97 + (i % 25))
        i = i - 25
    char += chr(97 + i)
    return char # 97 = a


def mixdown(sourcefolder, destination, tracks_vocs, tracks_instr, songname):
    inp_args = ""
    filter_complex_vocs = ""
    filter_complex_instr = ""
    filter_complex_fullmix = ""
    track_count = 0
    chain_vocs = ""
    chain_instr = ""

    try:
        for tracknr, track in enumerate(tracks_vocs):
            inp_args += "-i \"" + join(sourcefolder, track )+ "\" "
            char = charCodeForNumber(track_count)
            filter_complex_vocs += "[" + str(track_count) + ":0]volume=" + str(1/(len(tracks_vocs) + len(tracks_instr)) / (1/len(tracks_vocs))) + ",aformat=channel_layouts=stereo[" + char + "];"
            filter_complex_fullmix += "[" + str(track_count) + ":0]"
            chain_vocs += "[" + char + "]"
            track_count += 1
        for tracknr, track in enumerate(tracks_instr):
            inp_args += "-i \"" + join(sourcefolder, track) + "\" "
            char = charCodeForNumber(track_count)
            filter_complex_instr += "[" + str(track_count) + ":0]volume=" + str(1/(len(tracks_vocs) + len(tracks_instr)) / (1/len(tracks_instr))) + ",aformat=channel_layouts=stereo[" + char + "];"
            filter_complex_fullmix += "[" + str(track_count) + ":0]"
            chain_instr += "[" + char + "]"
            track_count += 1
    except Exception as inst:
            log_file.write(str(type(inst)) + ": Pydub could not read " + track + "\n")

    # Create a fulmix of all audio tracks
    try:
        cmd_fullmix = "ffmpeg " + inp_args + " -filter_complex \"" + filter_complex_fullmix + "amix=inputs=" + str(track_count) + "[mix]\" -map [mix] -y -ar 44100 \"" + join(temp_path, "fullmix_" + songname + ".wav") + "\""
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
        cmd = "ffmpeg " + inp_args + " -filter_complex \"" + filter_complex_vocs + chain_vocs + "amix=inputs=" + str(len(tracks_vocs)) \
              + ",volume=" + str(differenz_db) + "dB[vocs];" + filter_complex_instr + chain_instr + "amix=inputs=" \
              + str(len(tracks_instr)) + ",volume=" + str(differenz_db) + "dB[instr]\" -map [vocs] -y -ar 44100 \"" \
              + join(destination,"vocals_" + songname + ".wav") + "\" -map [instr] -y -ar 44100 \"" + join(destination, "instrumental_"                                                                                             + songname + ".wav") + "\""
        print(cmd)
        subprocess.check_call(cmd, shell=True)
        log_file.write("Message: " + songname + " was converted successfully\n")
        # For testing purposes
        # cmd_test = "ffmpeg -i \"" + join(temp_path,
        #                                  "fullmix_" + songname + ".wav") + "\" -filter_complex \"[0:0]volume=" + str(
        #     differenz_db) + "dB\" -y -ar 44100 \"" + join(temp_path, "fullmux_norm_" + songname + ".wav") + "\""
        # subprocess.call(cmd_test, shell=True)
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


def file_processing(sourcedir, destdir, maxCopy, override):

    # Create list of directories and songfiles (simple files stands for normal mono or stereo tracks, no containers)
    directories = [f for f in listdir(sourcedir) if isdir(join(sourcedir, f))]
    eligible_simple_files = [f for f in listdir(sourcedir) if isfile(join(sourcedir, f)) and eligible_simple_filetypes.__contains__(pathlib.Path(f).suffix) and not is_hidden(f)]
    eligible_container_files = [f for f in listdir(sourcedir) if isfile(join(sourcedir, f)) and eligible_container_filetypes.__contains__(pathlib.Path(f).suffix) and not is_hidden(f)]

    for d in directories:
        directory_path = join(sourcedir, d)
        file_processing(directory_path, destdir, maxCopy, override)

    #Process Simple File Types
    vocals = [f for f in eligible_simple_files if is_vocal(f)]
    instrumentals = [f for f in eligible_simple_files if not is_vocal(f)]

    # Abort process if there are no vocals or no instrumentals in folder
    if len(vocals) == 0 or len(instrumentals) == 0:
        return

    # Add new folder in target directory if not yet existing, if name to short parentfolder of source directory is added to name as well
    new_foldername = ""
    path = sourcedir
    while len(new_foldername) < 10:
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

    mixdown(sourcedir, join(destdir, new_foldername), vocals, instrumentals, new_foldername)

    # TODO: Implement Container file type processing


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

    if len(sys.argv) == 2:
        unmix_server = sys.argv[1]

    sourcedir = unmix_server + "/1_sources/RockBand-GuitarHero"
    destdir = unmix_server + "/2_prepared/RockBand-GuitarHero_rb-spreadsheet"

    init()

    try:
        file_processing(sourcedir, destdir, maxCopy, override)
    finally:
        log_file.close()

    print('Finished converting files')