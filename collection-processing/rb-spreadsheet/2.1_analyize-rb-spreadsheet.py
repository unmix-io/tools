
from os import listdir, chdir, makedirs
from os.path import isfile, join, isdir, exists
import sys
import datetime
import re
import ntpath

# Format specs

# Format 0: ogg, several tracks, including one named "vocals.ogg"
c_0_ogg = 0

tempPath = "./temp"
eligible_simple_filetypes = ['.wav', '.ogg', '.mp3']



def isVocal(file):
    return re.search('voc', file, re.IGNORECASE) or re.search('vox', file, re.IGNORECASE)

def file_processing(sourcedir, destdir, maxCopy, override):

    #Create list of directories and songfiles (simple files stands for normal mono or stereo tracks, no containers)
    directories = [f for f in listdir(sourcedir) if isdir(join(sourcedir, f))]
    eligible_simple_files = [f for f in listdir(sourcedir) if isfile(join(sourcedir, f)) and eligible_simple_filetypes.__contains__(f[-4:])]

    for d in directories:
        directoryPath = join(sourcedir, d)
        file_processing(directoryPath, destdir, maxCopy, override)
        print(d + "")

    vocals = [f for f in eligible_simple_filetypes if isVocal(f)]
    instrumentals = [f for f in eligible_simple_filetypes if not isVocal(f)]

    # Abort process if there are no vocals or no instrumentals in folder
    if (len(vocals) == 0 or len(instrumentals) == 0):
        return

    # Add new folder in target directory if not yet existing
    if not exists(join(destdir, ntpath.basename(sourcedir))):
        makedirs(join(destdir, ntpath.basename(sourcedir)))


    #Next: 1. make filter complex, run fulter complex, run normalization with good ratio
    
    # for f in eligible_simple_files:
    #     file_path = join(sourcedir, f)
    #     print (file_path)




def setup_logfile(log_file_dir):
    if not exists(log_file_dir):
        makedirs(log_file_dir)

    log_file_path = join(log_file_dir, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_Logfile.txt")
    global log_file
    log_file = open(log_file_path, "w+")

def init():
    #Initialize logfile
    setup_logfile("./logfiles")

    #Create temp folder
    if not exists(tempPath):
        makedirs(tempPath)

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

    file_processing(sourcedir, destdir, maxCopy, override)

    log_file.close()

    print('Finished converting files')