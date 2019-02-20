"""
Filreader enriching files with synonyms out of wordnet
"""

import sys
from os import listdir, rename, makedirs, remove
from os.path import join, isfile, dirname, exists
import shutil

__author__ = "kaufmann-a@hotmail.ch"
unmix_server = '//192.168.1.29/unmix-server'
sources = unmix_server + "/musdb18/splitedToWav"
destination = unmix_server + "/Trainingdata/musdb18"

#Beispiel ffmpeg mp4 streams auftrennen und zusammenmergen: ffmpeg -i test.mp4 -filter_complex "[0:1][0:2]amerge=inputs=2[ab]" -map [ab] 1.wav
#Hier wurden streams 2 und 3 gemerged

def copy_files(sourcedir, outputdir, suffix, type, maxCopy):
    src_files= listdir(sourcedir)
    for file in src_files:
        if maxCopy <= 0: break
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
            maxCopy -= 1


if __name__ == '__main__':
    print('Argument List:', str(sys.argv))
    print('Loading data', file=sys.stderr)

    maxCopy = 10

    copy_files(sources, destination, '.stem_audio_track_00.wav', 'mixture', maxCopy)
    copy_files(sources, destination, '.stem_audio_track_04.wav', 'vocals', maxCopy)

    print('Finished google files')

