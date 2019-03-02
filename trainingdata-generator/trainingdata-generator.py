"""
Creates hierarchical data format files with complexe frequency spectrograms for audio files in a given folder.
"""

__author__ = 'david@flury.email'

import os
import sys
import glob
import h5py
import time
import librosa
import warnings
import argparse
import numpy as np
import multiprocessing
import skimage.io as io
from os.path import basename
from joblib import Parallel, delayed
from matplotlib.cm import get_cmap
import audioread

audio_extensions = ['.wav', '.mp3']


def generate_container(file, fft_window, target_sample_rate):
    try:
        audio, sample_rate = librosa.load(file, mono=False, sr=target_sample_rate if target_sample_rate > 0 else None)            
        left = generate_spectrogram(file, audio[0], '0-left', fft_window, sample_rate)
        right = generate_spectrogram(file, audio[1], '1-right', fft_window, sample_rate)
        file_name = '%s_spectrogram_fft-window[%d]_sample-rate[%d]' % (file, fft_window, sample_rate)
        save_spectrogram_data(stft_to_complex_spectrogram(left), stft_to_complex_spectrogram(right), file_name, fft_window, sample_rate)
        print('Generated spectrogram %s' % file_name)
    except (RuntimeError, TypeError, NameError, audioread.NoBackendError):
        print('Error while generating spectrogram for %s' % file)
        pass

def generate_spectrogram(file, audio, part, fft_window, sample_rate):
    file_name = '%s_spectrogram_%s_fft-window[%d]_sample-rate[%d]' % (file, part, fft_window, sample_rate)
    stft = librosa.stft(audio, fft_window)
    save_spectrogram_image(stft_to_real_spectrogram(stft), file_name)
    return stft


def stft_to_real_spectrogram(stft):
    spectrogram = np.log1p(np.abs(stft))
    return np.array(spectrogram)[:, :, np.newaxis]


def stft_to_complex_spectrogram(stft):
    real_part = np.real(stft)
    imag_part = np.imag(stft)
    spectrogram = np.zeros((stft.shape[0], stft.shape[1], 2))
    spectrogram[:, :, 0] = real_part
    spectrogram[:, :, 1] = imag_part
    return spectrogram


def save_spectrogram_image(spectrogram, file):
    real_part = spectrogram[:, :, 0]

    cm_hot = get_cmap('plasma')
    image = np.clip((real_part - np.min(real_part)) / (np.max(real_part) - np.min(real_part)), 0, 1)
 
    with warnings.catch_warnings():
        image = cm_hot(image)
        warnings.simplefilter('ignore')
        io.imsave(file + '.png', image)


def save_spectrogram_data(spectrogram_left, spectrogram_right, file, fft_window, sample_rate):
    h5f = h5py.File(file + '.h5', 'w')
    h5f.create_dataset('file', data=os.path.basename(file))
    h5f.create_dataset('spectrogram_left', data=spectrogram_left)
    h5f.create_dataset('spectrogram_right', data=spectrogram_right)
    h5f.create_dataset('fft_window', data=fft_window)
    h5f.create_dataset('sample_rate', data=sample_rate)
    h5f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates hierarchical data format files including complexe frequency spectrograms for audio files in a given folder.')
    parser.add_argument('--path', default='U:\\2_prepared\\musdb18\\', type=str, help='Working path')
    parser.add_argument('--fft_window', default=1536, type=int, help='Size [Samples] of FFT windows')
    parser.add_argument('--sample_rate', default=-1, type=int, help='Optional target samplerate [Hz] for the audiofiles')
    parser.add_argument('--job_count', default=int(multiprocessing.cpu_count()), type=int, help='Maximum number of concurrently running jobs')

    args = parser.parse_args()
    print('Arguments:', str(args))

    if not args.path.endswith('\\'):
        args.path += '\\'

    files = [] # Load all files into list
    print('Load all music files...')
    for file in glob.iglob(args.path + '**/*', recursive=True):
        extension = os.path.splitext(file)[1].lower()
        if extension in audio_extensions:
            files.append(file)
    print('Found %d music files' % len(files))

    start = time.time()
    print('Generate spectrograms with maximum %d jobs...' % args.job_count)
    Parallel(n_jobs=args.job_count)(delayed(generate_container)(file, args.fft_window, args.sample_rate) for file in files)
    end = time.time()
    
    print('Finished processing in %d [ms]', (end - start))
