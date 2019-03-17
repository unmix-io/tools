
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
eligible_simple_filetypes = ['.wav', '.ogg', '.mp3']
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


def normalize(file, destination, db = -20.0):
    def match_target_amplitude(sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    sound = AudioSegment.from_file(file, "wav")
    normalized_sound = match_target_amplitude(sound, db)
    normalized_sound.export(destination, format="wav")


def mixdown(sourcefolder, destination, tracks_vocs, tracks_instr, songname, pandir):
    inp_args = ""
    filter_complex_vocs_L = ""
    filter_complex_instr_L = ""
    filter_complex_vocs_R = ""
    filter_complex_instr_R = ""
    sum_volumes_vocs = 0
    sum_volumes_instr = 0
    track_count_vocs_L = 0
    track_count_vocs_R = 0
    track_count_instr_L = 0
    track_count_instr_R = 0

    track_count = 0

    #Read csv with panninginfo
    dict_panning = {}
    try:
        with open(join(pandir, songname) + ".csv") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            line_count = 0
            for row in csv_reader:
                if not line_count == 0:
                    dict_panning[int(row[0])] = row[1]
                line_count += 1
    except Exception as inst:
        log_file.write(str(type(inst)) + ": Panningfile of song " + songname + "could not be found")
        log_file.flush()
        return

    try:
        for tracknr, track in enumerate(tracks_vocs):
            if dict_panning[int(track[:-4])] == "L":
                filter_complex_vocs_L += "[" + str(track_count) + ":0]"
                track_count_vocs_L += 1
            if dict_panning[int(track[:-4])] == "R":
                filter_complex_vocs_R += "[" + str(track_count) + ":0]"
                track_count_vocs_R += 1
            if dict_panning[int(track[:-4])] == "M":
                filter_complex_vocs_L += "[" + str(track_count) + ":0]"
                filter_complex_vocs_R += "[" + str(track_count) + ":0]"
                track_count_vocs_L += 1
                track_count_vocs_R += 1
            inp_args += "-i \"" + join(sourcefolder, track )+ "\" "
            sum_volumes_vocs += AudioSegment.from_file(join(sourcefolder, track), pathlib.Path(track).suffix[1:]).dBFS
            track_count += 1
        for tracknr, track in enumerate(tracks_instr):
            if dict_panning[int(track[:-4])] == "L":
                filter_complex_instr_L += "[" + str(track_count) + ":0]"
                track_count_instr_L += 1
            if dict_panning[int(track[:-4])] == "R":
                filter_complex_instr_R += "[" + str(track_count) + ":0]"
                track_count_instr_R += 1
            if dict_panning[int(track[:-4])] == "M":
                filter_complex_instr_L += "[" + str(track_count) + ":0]"
                filter_complex_instr_R += "[" + str(track_count) + ":0]"
                track_count_instr_L += 1
                track_count_instr_R += 1
            inp_args += "-i \"" + join(sourcefolder, track) + "\" "
            sum_volumes_instr += AudioSegment.from_file(join(sourcefolder, track), pathlib.Path(track).suffix[1:]).dBFS
            track_count += 1
    except Exception as inst:
            log_file.write(str(type(inst)) + ": Pydub could not read " + track)
            log_file.flush()

    cmd = "ffmpeg " + inp_args + " -filter_complex \"" + filter_complex_vocs_L + "amix=inputs=" + str(track_count_vocs_L) + "[vocsL];" + filter_complex_vocs_R + "amix=inputs=" + str(track_count_vocs_R) + "[vocsR];" + filter_complex_instr_L \
          + "amix=inputs=" + str(track_count_instr_L) + "[instrL];" + filter_complex_instr_R + "amix=inputs=" + str(track_count_instr_R) + "[instrR];[vocsL][vocsR]join=inputs=2:channel_layout=stereo[vocs];[instrL][instrR]join=inputs=2:channel_layout=stereo[instr]\" -map [vocs] -ac 2 -y -ar 44100 \"" + join(temp_path, "vocals_" + songname + ".wav") \
          + "\" -map [instr] -ac 2 -y -ar 44100 \"" + join(temp_path, "instrumental_" + songname + ".wav") + "\""
    print(cmd)
    try:
        subprocess.check_call(cmd, shell=True)
        log_file.write("Message: " + songname + " was converted successfully\n")
        log_file.flush()
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " conversion failed\n")
        log_file.flush()
        return

    # Calculate ratio of volume of mixed vocals and volume of mixed instruments. Instruments will be normalized to
    # -20 DB, Vocals to -20 DB * Ratio
    try:
        target_db_voc = -20 + ( -20 * ((sum_volumes_vocs / tracks_vocs.__len__()) / (sum_volumes_instr / tracks_instr.__len__()) - 1))
        normalize(join(temp_path, "vocals_" + songname) + ".wav", join(destination, "vocals_" + songname) + ".wav", target_db_voc)
        normalize(join(temp_path, "instrumental_" + songname) + ".wav", join(destination, "instrumental" + songname) + ".wav", -20)
        log_file.write("Message: " + songname + " was normalized successfully\n")
        log_file.flush()
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " normalization failed\n")
        log_file.flush()
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

    mixdown(sourcedir, join(destdir, ntpath.basename(sourcedir)), vocals, instrumentals, ntpath.basename(sourcedir), pandir)



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
    override = True
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