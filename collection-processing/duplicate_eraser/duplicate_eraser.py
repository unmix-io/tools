
from os import makedirs
from os.path import join, exists, dirname
import sys
import datetime
import shutil
import csv

def setup_logfile(log_file_dir):
    if not exists(log_file_dir):
        makedirs(log_file_dir)

    log_file_path = join(log_file_dir, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_Logfile.txt")
    global log_file
    log_file = open(log_file_path, "w+")


def read_csv(metadata_csv):
    collection_priorities = {'cambridge-mt': 4, 'dsd100': 2, 'MedleyDBs': 3, 'MIR-1K': 7, 'musdb18': 1, 'RockBand-GuitarHero-moggs': 6, 'RockBand-GuitarHero_rb-spreadsheet': 5}

    entries = []
    duplicate_entries = []
    with open(metadata_csv, 'r') as my_file:
        csvreader = csv.reader(my_file, delimiter=';')
        next(csvreader)
        for line in csvreader:
            if line[2] not in entries:
                entries.append(line[2])
            else:
                duplicate_entries.append(line[2])
    removed_files = 0
    if len(duplicate_entries) > 0:
        for duplicate in duplicate_entries:
            with open(metadata_csv, 'r') as my_file:
                csvreader = csv.reader(my_file, delimiter=';')
                next(csvreader)
                duplicates = []
                for line in csvreader:
                    if line[2] == duplicate:
                        duplicates.append(line)
                print(duplicates[0][9] + " - " + duplicates[1][9] + " = " + str(float(duplicates[0][9]) - float(duplicates[1][9])))
                priority = -1
                file_to_delete = ''
                for dupl in duplicates:
                    if priority == -1 or collection_priorities[dupl[4]] > priority:
                        priority = collection_priorities[dupl[4]]
                        file_to_delete = dupl[1]
                try:
                    shutil.rmtree(dirname(file_to_delete))
                    print("Removed: " + dirname(file_to_delete))
                    log_file.write("Removed: " + dirname(file_to_delete) + "\n")
                    log_file.flush()
                    removed_files += 1
                except Exception as inst:
                    print("Error: " + str(type(inst)) + "could not remove " + dirname(file_to_delete))
                    log_file.write("Error: " + str(type(inst)) + "could not remove " + dirname(file_to_delete) + "\n")
                    log_file.flush()

    else:
        print("No repetitions")
    log_file.write("Totaly removed folders: " + str(removed_files) + "\n")
    print("Totaly removed folders: " + str(removed_files))


def init():
    # Initialize logfile
    setup_logfile("./logfiles")


if __name__ == '__main__':
    maxCopy = 3
    override = True
    unmix_server = "//192.168.1.29/unmix-server"

    print('Argument List:', str(sys.argv))

    if sys.argv.__len__() == 2:
        unmix_server = sys.argv[1]

    metadata_csv = unmix_server + "/3_filter/metadata_overview.csv"
    init()

    try:
        read_csv(metadata_csv)
    finally:
        log_file.close()

    print('Finished converting files')
