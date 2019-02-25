"""
Create complexe frequency spectrograms for wav files in a given folder.
"""

__author__ = 'david@flury.email'

import os
import sys
import glob
import h5py
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

unmix_server = '//192.168.1.29/unmix-server'
audio_extensions = ['.wav', '.mp3']
fft_window = 1536


def generate_spectrogram(file):
    try:
        audio, sample_rate = librosa.load(file)
        file_name = '%s_spectrogram_fft-window[%d]_sample-rate[%d]' % (file, fft_window, sample_rate)
        stft = librosa.stft(audio, fft_window)   
        save_spectrogram_image(stft_to_real_spectogram(stft), file_name)
        save_spectrogram_data(stft_to_complex_spectrogram(stft), file_name)
        print('Generated spectrogram %s' & file_name)
    except (RuntimeError, TypeError, NameError, audioread.NoBackendError):
        print('Error while generating spectrogram for %s' % file)
        pass

    
def stft_to_real_spectogram(stft):
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


def save_spectrogram_data(spectrogram, file):
    h5f = h5py.File(file + '.h5', 'w')
    h5f.create_dataset('imag_part', data=spectrogram[:, :, 0])
    h5f.create_dataset('real_part', data=spectrogram[:, :, 1])
    h5f.create_dataset('spectrogram', data=spectrogram)
    h5f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create complexe frequency spectrograms for wav files in a given folder.')
    parser.add_argument('--path', default='U:\\2_prepared\\musdb18\\', type=str, help='Working path')
    parser.add_argument('--fft_window', default=1536, type=int, help='Size of FFT windows')

    args = parser.parse_args()
    print('Arguments:', str(args))

    if args.fft_window:
        fft_window = args.fft_window

    files = [] # Load all files into list
    print('Load all music files...')
    for file in glob.iglob(args.path + '**/*', recursive=True):
        extension = os.path.splitext(file)[1].lower()
        if extension in audio_extensions:
            files.append(file)
    
    multiprocessing_cores = multiprocessing.cpu_count() / 2
    print('Generate spectrograms with %d cores...' % multiprocessing_cores)
    
    Parallel(n_jobs=multiprocessing_cores)(delayed(generate_spectrogram)(file) for file in files)

    print('Finished processing')
