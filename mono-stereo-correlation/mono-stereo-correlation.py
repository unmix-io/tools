"""
Analysis of the correlation of mono and stereo tracks (left-right).
"""

__author__ = 'David Flury'
__email__ = "david@flury.email"

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


error_count = 0


def generate_difference(destination, vocals_file, instrumental_file):
    if not os.path.exists(destination):
        os.makedirs(destination)

    vocals_left, vocals_right = read_spectrogram(vocals_file)
    instrumental_left, instrumental_right = read_spectrogram(instrumental_file)

    mix_left = generate_stft(np.add(vocals_left, instrumental_left))
    mix_right = generate_stft(np.add(vocals_right, instrumental_right))
    librosa.output.write_wav(os.path.join(destination, "mix.wav"), y=np.array([librosa.istft(mix_left), librosa.istft(mix_right)]), sr=11025, norm=False)

    difference_amp_left = np.clip(np.abs(mix_left) - np.abs(mix_right), 0, None)
    difference_left = difference_amp_left * np.exp(np.angle(mix_left) * 1j)
    librosa.output.write_wav(os.path.join(destination, "difference_left.wav"), y=np.array(librosa.istft(difference_left)), sr=11025, norm=False)

    difference_amp_right = np.clip(np.abs(mix_right) - np.abs(mix_left), 0, None)
    difference_right = difference_amp_right * np.exp(np.angle(mix_right) * 1j)
    librosa.output.write_wav(os.path.join(destination, "difference_right.wav"), y=np.array(librosa.istft(difference_right)), sr=11025, norm=False)
    
    return


def generate_stft(spectrogram):
    real_part = spectrogram[:, :, 0]
    imag_part = spectrogram[:, :, 1]
    stft = real_part + imag_part * 1j
    return stft


def read_spectrogram(file):
    h5f = h5py.File(file,'r')
    return h5f['spectrogram_left'][:, :, :], h5f['spectrogram_right'][:, :, :]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates hierarchical data format files including complexe frequency spectrograms for audio files in a given folder.')
    parser.add_argument('--path', default='\\\\server.unmix.io\\unmix-server\\4_training\\fft-window=1536_sample-rate=11025_channels=2-stereo\\musdb18', type=str, help='Working path')
    parser.add_argument('--destination', default='D:\\Data\\unmix.io\\mono-stereo', type=str, help='Destination path')

    args = parser.parse_args()

    print('Arguments:', str(args))
    start = time.time()

    print('Load all music files...')
    for file in glob.iglob(os.path.join(args.path, '**/vocals_*.h5'), recursive=True):
        path = os.path.dirname(file)
        vocals_file = glob.glob(os.path.join(path, "vocals_*.h5"))[0]
        instrumental_file = glob.glob(os.path.join(path, "instrumental_*.h5"))[0]

        destination = os.path.join(args.destination, os.path.basename(path))

        generate_difference(destination, vocals_file, instrumental_file)

    end = time.time()
    
    print('Finished processing in %d [s] with %d errors.' % ((end - start), error_count))
