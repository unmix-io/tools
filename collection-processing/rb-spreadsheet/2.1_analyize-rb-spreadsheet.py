
from os import listdir, chdir, makedirs, remove
from os.path import isfile, join, isdir, exists
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


def is_vocal(file):
    return re.search('voc', file, re.IGNORECASE) or re.search('vox', file, re.IGNORECASE)


def normalize(file, destination, db = -20.0):
    def match_target_amplitude(sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    sound = AudioSegment.from_file(file, "wav")
    normalized_sound = match_target_amplitude(sound, db)
    normalized_sound.export(destination, format="wav")


def mixdown(sourcefolder, destination, tracks_vocs, tracks_instr, songname):
    inp_args = ""
    filter_complex_vocs = ""
    filter_complex_instr = ""
    sum_volumes_vocs = 0
    sum_volumes_instr = 0
    track_count = 0

    try:
        for tracknr, track in enumerate(tracks_vocs):
            inp_args += "-i \"" + join(sourcefolder, track )+ "\" "
            filter_complex_vocs += "[" + str(track_count) + ":0]"
            sum_volumes_vocs += AudioSegment.from_file(join(sourcefolder, track), pathlib.Path(track).suffix[1:]).dBFS
            track_count += 1
        for tracknr, track in enumerate(tracks_instr):
            inp_args += "-i \"" + join(sourcefolder, track) + "\" "
            filter_complex_instr += "[" + str(track_count) + ":0]"
            sum_volumes_instr += AudioSegment.from_file(join(sourcefolder, track), pathlib.Path(track).suffix[1:]).dBFS
            track_count += 1
    except Exception as inst:
            log_file.write(str(type(inst)) + ": Pydub could not read " + track)

    cmd = "ffmpeg " + inp_args + " -filter_complex \"" + filter_complex_vocs + "amix=inputs=" + str(tracks_vocs.__len__()) + "[vocs];" + filter_complex_instr \
          + "amix=inputs=" + str(tracks_instr.__len__()) + "[instr]\" -map [vocs] -ar 44100 \"" + join(temp_path, "vocals_" + songname + ".wav") \
          + "\" -map [instr] -ar 44100 \"" + join(temp_path, "instrumental_" + songname + ".wav") + "\""
    print(cmd)
    try:
        subprocess.check_call(cmd, shell=True)
        log_file.write("Message: " + songname + " was converted successfully\n")
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " conversion failed\n")
        return

    # Calculate ratio of volume of mixed vocals and volume of mixed instruments. Instruments will be normalized to
    # -20 DB, Vocals to -20 DB * Ratio
    try:
        target_db_voc = -20 + ( -20 * ((sum_volumes_vocs / tracks_vocs.__len__()) / (sum_volumes_instr / tracks_instr.__len__()) - 1))
        normalize(join(temp_path, "vocals_" + songname) + ".wav", join(destination, "vocals_" + songname) + ".wav", target_db_voc)
        normalize(join(temp_path, "instrumental_" + songname) + ".wav", join(destination, "instrumental" + songname) + ".wav", -20)
        log_file.write("Message: " + songname + " was normalized successfully\n")
    except Exception as inst:
        log_file.write(str(type(inst)) + ": " + songname + " normalization failed\n")
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
    eligible_simple_files = [f for f in listdir(sourcedir) if isfile(join(sourcedir, f)) and eligible_simple_filetypes.__contains__(f[-4:])]

    for d in directories:
        directory_path = join(sourcedir, d)
        file_processing(directory_path, destdir, maxCopy, override)

    vocals = [f for f in eligible_simple_files if is_vocal(f)]
    instrumentals = [f for f in eligible_simple_files if not is_vocal(f)]

    # Abort process if there are no vocals or no instrumentals in folder
    if len(vocals) == 0 or len(instrumentals) == 0:
        return

    # Add new folder in target directory if not yet existing
    if not exists(join(destdir, ntpath.basename(sourcedir))):
        makedirs(join(destdir, ntpath.basename(sourcedir)))
    elif not override:
        return

    mixdown(sourcedir, join(destdir, ntpath.basename(sourcedir)), vocals, instrumentals, ntpath.basename(sourcedir))


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

    sourcedir = unmix_server + "/1_sources/RockBand-GuitarHero/rb-spreadsheet"
    destdir = unmix_server + "/2_prepared/RockBand-GuitarHero_rb-spreadsheet"

    init()

    try:
        file_processing(sourcedir, destdir, maxCopy, override)
    finally:
        log_file.close()

    print('Finished converting files')