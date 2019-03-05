import argparse
from correlation import correlate
from os import listdir, makedirs, remove
from os.path import isfile, join, isdir, exists
import csv
import sys

def initialize():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i ", "--source-file", help="source file")
    parser.add_argument("-o ", "--target-file", help="target file")
    args = parser.parse_args()

    SOURCE_FILE = args.source_file if args.source_file else None
    TARGET_FILE = args.target_file if args.target_file else None
    if not SOURCE_FILE or not TARGET_FILE:
        raise Exception("Source or Target files not specified.")
    return SOURCE_FILE, TARGET_FILE


if __name__ == "__main__":
    #SOURCE_FILE, TARGET_FILE = initialize()

    maxCopy = -1
    override = True
    unmix_server = '//192.168.1.29/unmix-server'

    print('Argument List:', str(sys.argv))

    if sys.argv.__len__() == 2:
        unmix_server = sys.argv[1]

    song_dir = unmix_server + "/2_prepared/RockBand-GuitarHero"
    csv_dir = unmix_server + "/2_prepared/RockBand-GuitarHero/_panninginfo"
    if not exists(csv_dir): makedirs(csv_dir)

    directories = [f for f in listdir(song_dir) if isdir(join(song_dir, f))]
    for dir in directories:
        songfolder = join(song_dir, dir)
        csv_filename = join(csv_dir, dir + '.csv')
        if exists(csv_filename): remove(csv_filename)
        csv_file = open(csv_filename, "w+", newline='')
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow(['ID', 'Pan'])


        wav_files = [(int(f[:-4]), join(songfolder, f)) for f in listdir(songfolder)]
        wav_files_dict = dict(wav_files)
        file1 = ''
        file2 = ''
        last_processed_index = 0
        for ind, file in enumerate(sorted(wav_files_dict)):
            file1 = file2
            file2 = wav_files_dict[file]
            max_corr, max_corr_offset = 0, 0
            if file1 and file2:
                max_corr, max_corr_offset = correlate(file1, file2)
            if max_corr > 0.62 and max_corr_offset == 0:
                writer.writerow([str(ind-1), 'L'])
                writer.writerow([str(ind), 'R'])
                last_processed_index = ind
            elif last_processed_index < (ind-1) or ind == 1:
                writer.writerow([str(ind-1), 'M'])
                last_processed_index = ind - 1
        print("finished " + dir + "\n")
        csv_file.close()
