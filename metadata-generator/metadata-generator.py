"""
Creates metadata for audio files.
"""

__author__ = 'David Flury'
__email__ = "david@flury.email"

import os
import re
import glob
import json
import argparse
import requests
import audioread
import multiprocessing
from joblib import Parallel, delayed
from functools import reduce


audio_extensions = ['.wav', '.mp3']
file_prefix = 'vocals_'

replace_tokens = ['mogg_fixed', 'mogg_extract', 'mogg']

spotify_token = ''



def generate_metadata(file):
    extension = os.path.splitext(file)[1].lower()
    file_name = os.path.basename(file).replace(file_prefix, '')
    file_name = file_name.replace(extension, '')

    metadata = {}
    metadata['name'] = file_name
    metadata['file'] = file
    metadata['path'] = os.path.dirname(file)
    metadata['extension'] = extension
    metadata['folder'] = os.path.basename(os.path.dirname(file))
    metadata['collection'] = os.path.basename(os.path.dirname(os.path.dirname(file)))
    normalized_name = reduce((lambda x, y: x.replace(y, '')), [file_name] + replace_tokens)
    normalized_name = re.sub(r'[^a-zA-Z0-9]+', '', normalized_name).lower()
    metadata['normalized_name'] = normalized_name
    
    try:
        with audioread.audio_open(file) as f:
            metadata['channels'] = f.channels
            metadata['sample_rate'] = f.samplerate
            metadata['duration'] = f.duration
        metadata = spotify_metadata(file_name, metadata)
    except:
        pass
    metadata_file = os.path.join(os.path.dirname(file), '%s_metadata.json' % file_name) 
    with open(metadata_file, 'w') as fp:
        json.dump(metadata, fp)
        print('Generated metafile: %s' % metadata_file)


def spotify_metadata(song_name, metadata, retry=False):
    response_track = requests.get('https://api.spotify.com/v1/search?q=%s&type=track&limit=1' % song_name, \
        headers={'Authorization': 'Bearer %s' % spotify_token})
    data = json.loads(response_track.text)
    if 'error' in data:
        if retry:
            return metadata
        set_spotify_token()
        return spotify_metadata(song_name, metadata, True)
    track = data['tracks']['items'][0]
    metadata['title'] = track['name']
    metadata['artists'] = []
    for artist in track['artists']:
        metadata['artists'].append(artist['name'])
    metadata['album'] = track['album']['name']
    metadata['explicit_content'] = track['explicit']
    metadata['spotify_id'] = track['id']
    metadata['spotify_popularity'] = track['popularity']
    response_features = requests.get('https://api.spotify.com/v1/audio-features/%s' % track['id'], \
        headers={'Authorization': 'Bearer %s' % spotify_token})
    features = json.loads(response_features.text)
    if 'error' in features:
        if retry:
            return metadata
        set_spotify_token()
        return spotify_metadata(song_name, metadata, True)
    metadata['features'] = {}
    metadata['features']['danceability'] = features['danceability']
    metadata['features']['energy'] = features['danceability']
    metadata['features']['loudness'] = features['danceability']
    metadata['features']['speechiness'] = features['danceability']
    metadata['features']['acousticness'] = features['acousticness']
    metadata['features']['instrumentalness'] = features['instrumentalness']
    metadata['features']['liveness'] = features['liveness']
    metadata['features']['valence'] = features['valence']
    metadata['features']['tempo'] = features['tempo']
    response_artist = requests.get('https://api.spotify.com/v1/artists/%s' % track['artists'][0]['id'], \
        headers={'Authorization': 'Bearer %s' % spotify_token})
    artist = json.loads(response_artist.text)
    if 'error' in artist:
        if retry:
            return metadata
        set_spotify_token()
        return spotify_metadata(song_name, metadata, True)
    metadata['genres'] = artist['genres']
    return metadata


def set_spotify_token():
    global spotify_token
    response = requests.post('https://accounts.spotify.com/api/token', \
        data = {'grant_type': 'client_credentials'}, \
        headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic %s' % os.environ['SPOTIFY_SECRET']})
    data = json.loads(response.text) 
    spotify_token = data['access_token']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate and store meta data for audio files.')
    parser.add_argument('--path', default='\\\\192.168.1.29\\unmix-server\\3_filter\\', type=str, help='Working path')
    parser.add_argument('--job_count', default=int(multiprocessing.cpu_count() / 2), type=int, help='Maximum number of concurrently running jobs')

    args = parser.parse_args()
    print('Arguments:', str(args))

    files = [] # Load all files into list
    print('Load all music files...')
    for file in glob.iglob(args.path + '**/*', recursive=True):
        extension = os.path.splitext(file)[1].lower()
        file_name = os.path.basename(file)
        if extension in audio_extensions and file_name.startswith(file_prefix):
            files.append(file)
    print('Found %d music files' % len(files))
   
    set_spotify_token()

    print('Generate spectrograms with maximum %d jobs...' % args.job_count)
    Parallel(n_jobs=args.job_count)(delayed(generate_metadata)(file) for file in files)

    print('Finished processing')
