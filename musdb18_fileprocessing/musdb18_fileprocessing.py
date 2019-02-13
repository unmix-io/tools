"""
Filreader enriching files with synonyms out of wordnet
"""

import sys
from os import listdir, rename, makedirs, remove
from os.path import join, isfile, dirname, exists
import shutil

__author__ = "kaufmann-a@hotmail.ch"
davidsIP = '//192.168.1.16'
sources = davidsIP + "/Data/unmix.io/musdb18/splitedToWav"
destination = davidsIP + "/Data/unmix.io/Trainingsdata/musdb18"

def copy_files(sourcedir, outputdir, suffix, type):
    src_files= listdir(sourcedir)
    for file in src_files:
        if file.endswith(suffix):
            new_songname = file[:-suffix.__len__()]
            new_songname_with_type = type + '_' + new_songname + '.wav'
            old_file = join(sourcedir, file)
            new_folder = join(outputdir, new_songname)
            new_songfile = join(new_folder, new_songname_with_type)
            copied_songfile = join(new_folder, file)
            if not exists(new_folder): makedirs(new_folder)
            shutil.copy(old_file, new_folder)
            if exists(new_songfile): remove(new_songfile)
            rename(copied_songfile, new_songfile)


if __name__ == '__main__':
    print('Argument List:', str(sys.argv))
    print('Loading data', file=sys.stderr)

    copy_files(sources, destination, '.stem_audio_track_00.wav', 'mixture')
    copy_files(sources, destination, '.stem_audio_track_04.wav', 'vocals')

    print('Finished google files')

