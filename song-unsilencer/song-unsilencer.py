"""
Removes silent parts from songs.
"""

__author__ = 'David Flury'
__email__ = "david@flury.email"

import os
import glob
import argparse
import multiprocessing
from pydub import AudioSegment
from joblib import Parallel, delayed
from pydub.silence import split_on_silence

audio_extensions = ['.wav']
suffix = 'unsilenced'

def remove_silence(file, length=5000):
    sound = AudioSegment.from_file(file, format='wav', frame_rate=44100, channels=2, sample_width=2)
    chunks = split_on_silence(sound, min_silence_len=1000, silence_thresh=-30)
    combined = AudioSegment.empty()
    for chunk in chunks[:5]:
        combined += chunk
    result_file = '%s_%s.wav' % (file, suffix)
    chopped = combined[:length]
    chopped.export(result_file, format='wav')
    print('Removed silence from file: %s' % result_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Removes silent parts from songs.')
    parser.add_argument('--path', default='C:\\temp\\unmix.io\\real-test\\', type=str, help='Working path')
    parser.add_argument('--job_count', default=int(multiprocessing.cpu_count() / 2), type=int, help='Maximum number of concurrently running jobs')

    args = parser.parse_args()
    print('Arguments:', str(args))

    files = []  # Load all files into list
    print('Load all music files...')
    for file in glob.iglob(args.path + '**/*', recursive=True):
        extension = os.path.splitext(file)[1].lower()
        file_name = os.path.basename(file)
        if extension in audio_extensions and suffix not in file_name:
            files.append(file)
    print('Found %d music files' % len(files))

    print('Remove silence from files with maximum %d jobs...' % args.job_count)

    Parallel(n_jobs=args.job_count)(delayed(remove_silence)(file) for file in files)

    print('Finished processing')
