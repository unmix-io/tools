"""
Filreader enriching files with synonyms out of wordnet
"""

import sys
from os import listdir, rename, makedirs, remove
from os.path import join, isfile, dirname, exists
import shutil

__author__ = "kaufmann-a@hotmail.ch"
unmix_server = '//192.168.1.16'
sources_dev = unmix_server + "/RawAudio/DSD100/Sources/Dev"
sources_test = unmix_server + "/RawAudio/DSD100/Sources/Test"
mixtures_dev = unmix_server + "/RawAudio/DSD100/Mixtures/Dev"
mixtures_test = unmix_server + "/RawAudio/DSD100/Mixtures/Test"
sources_out = unmix_server + "/Trainingsdata/dsd100"
mixtures_out = unmix_server + "/Trainingsdata/dsd100"

def copy_files(sourcedir, outputdir, type, maxCopy):
    src_files= listdir(sourcedir)
    for folder in src_files:
        if maxCopy <= 0: break
        songfolder = join(sourcedir, folder)
        filename_before = type + '.wav'
        filename = join(songfolder, filename_before)
        if isfile(filename):
            new_folder = join(outputdir, folder)
            if not exists(new_folder): makedirs(new_folder)
            shutil.copy(filename, new_folder)
            filename_after = type + '_' + folder + '.wav'
            new_filename = join(new_folder, filename_after)
            old_filename = join(new_folder, filename_before)
            if exists(new_filename): remove(new_filename)
            rename(old_filename, new_filename)
            maxCopy -= 1

if __name__ == '__main__':
    print('Argument List:', str(sys.argv))
    print('Loading data', file=sys.stderr)

    maxCopy = 10

    copy_files(sources_dev, sources_out, 'vocals', maxCopy)
    copy_files(mixtures_dev, mixtures_out, 'mixture', maxCopy)
    copy_files(sources_test, sources_out, 'vocals', maxCopy)
    copy_files(mixtures_test, mixtures_out, 'mixture', maxCopy)

    print('Finished google files')

