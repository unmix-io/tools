import csv
from os.path import isfile, join, isdir, exists
from os import listdir, remove
import shutil

def clean_dir(prepared_dir, blacklist_path):
    black_list = []
    with open(blacklist_path) as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        for row in csvReader:
            black_list.append(row)

    #irectories = [f for f in listdir(prepared_dir) if isdir(join(sourcedir, f))]

    for d in listdir(prepared_dir):
        if 'full' in d.lower():
            d.replace('full', '')
        d_short = d[0:-5]

        counter = 0
        full_session_path = ''
        not_full_session = ''
        for dd in listdir(prepared_dir):
            if d_short in dd:
                counter += 1
                if 'full' in dd.lower():
                    full_session_path = dd
                else:
                    not_full_session = dd
        if full_session_path.__len__() >= 1 and not_full_session.__len__() >= 1:
            shutil.rmtree(join(prepared_dir, not_full_session))

        for black in black_list:
            if black[0] in d:
                if exists(join(prepared_dir, d)):
                    shutil.rmtree(join(prepared_dir, d))
                    break

