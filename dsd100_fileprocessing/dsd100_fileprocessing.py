"""
Filreader enriching files with synonyms out of wordnet
"""

import sys
from os import listdir, rename, makedirs
from os.path import join, isfile, dirname, exists
import shutil

__author__ = "kaufmann-a@hotmail.ch"
davidsIP = '//192.168.1.16'
sources_dev = davidsIP + "/Data/unmix.io/DSD100/Sources/Dev"
sources_test = davidsIP + "/Data/unmix.io/DSD100/Sources/Test"
mixtures_dev = davidsIP + "/Data/unmix.io/DSD100/Mixtures/Dev"
mixtures_test = davidsIP + "/Data/unmix.io/DSD100/Mixtures/Test"
sources_out = davidsIP + "/Data/unmix.io/Trainingsdata/dsd100"
mixtures_out = davidsIP + "/Data/unmix.io/Trainingsdata/dsd100"

def copy_files(sourcedir, outputdir, type):
    src_files= listdir(sourcedir)
    for folder in src_files:
        songfolder = join(sourcedir, folder)
        filename_before = type + '.wav'
        filename = join(songfolder, filename_before)
        if(isfile(filename)):
            new_folder = join(outputdir, folder)
            if not exists(new_folder): makedirs(new_folder)
            shutil.copy(filename, new_folder)
            filename_after = type + '_' + folder + '.wav'
            new_filename = join(new_folder, filename_after)
            old_filename = join(new_folder, filename_before)
            rename(old_filename, new_filename)

if __name__ == '__main__':
    print('Argument List:', str(sys.argv))
    print('Loading data', file=sys.stderr)

    copy_files(sources_dev, sources_out, 'vocals')
    copy_files(mixtures_dev, mixtures_out, 'mixture')
    copy_files(sources_test, sources_out, 'vocals')
    copy_files(mixtures_test, mixtures_out, 'mixture')

    print('Finished google files')

