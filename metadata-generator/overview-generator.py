"""
Reads metadata files and generates an overview.
"""

__author__ = 'david@flury.email'

import os
import csv
import glob
import json
import argparse

metadata_suffix = '_metadata.json'
overview_filename = 'metadata_overview.csv'


def generate_csv_template(destination):
    csv_file = os.path.join(destination, overview_filename) 
    with open(csv_file, 'w', newline='', encoding='utf8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Name', 'File', 'Path', 'Extension', \
            'Channels', 'Sample Rate', 'Duration',  \
            'Title', 'Artists', 'Album', 'Genres', \
            'Explicit Content', 'Popularity', \
            'Danceability', 'Energy', 'Loudness', 'Speechiness', \
            'Acousticness', 'Instrumentalness', 'Liveness', \
            'Valence', 'Tempo', 'Spotify ID'])        
    return csv_file

def write_csv_row(file, csv_file):
    with open(file, 'r') as f:
        data = json.load(f)
    features = data.get('features', {})
    with open(csv_file, 'a', newline='', encoding='utf8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([data.get('name'), data.get('file'), data.get('path'), data.get('extension'), \
            data.get('channels'), data.get('sample_rate'), data.get('duration'), \
            data.get('title'), ', '.join(data.get('artists', [''])), data.get('album'), ', '.join(data.get('genres', [''])), \
            data.get('explicit_content'), data.get('spotify_popularity'), \
            features.get('danceability'), features.get('energy'), features.get('loudness'), features.get('speechiness'), \
            features.get('acousticness'), features.get('instrumentalness'), features.get('liveness'), \
            features.get('valence'), features.get('tempo'), data.get('spotify_id')])
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reads metadata files and generates an overview.')
    parser.add_argument('--path', default='U:\\2_prepared\\', type=str, help='Working and default destination path')
    parser.add_argument('--destination', default='', type=str, help='Optional destionation path')

    args = parser.parse_args()
    print('Arguments:', str(args))

    if not args.destination:
        args.destination = args.path

    csv_file = generate_csv_template(args.destination)

    print('Load all metadata files...')
    for file in glob.iglob(args.path + '**\\*%s' % metadata_suffix, recursive=True):
        write_csv_row(file, csv_file)
        print('Wrote metadata from file %s' % file)

    print('Finished processing')
