"""
Reads a hierarchical data format (h5) file containing a complexe frequency spectrogram.
"""

__author__ = 'david@flury.email'

import os
import h5py
import librosa
import argparse
import numpy as np

def generate_audiofile(spectrogram_left, spectrogram_right, name, path, fft_window, sample_rate):
    file = os.path.join(path, name + ".wav")

    stft_left = generate_stft(spectrogram_left)
    stft_right = generate_stft(spectrogram_right)
    audio_left = librosa.istft(stft_left)
    audio_right = librosa.istft(stft_right)
    audio = np.array([audio_left, audio_right])
    print('Output audio file: %s' % file)
    librosa.output.write_wav(file, audio, sample_rate, norm=False)


def generate_stft(spectrogram):
    real_part = spectrogram[:, :, 0]
    imag_part = spectrogram[:, :, 1]
    stft = real_part + imag_part * 1j
    return stft

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read h5 files containing a complexe frequency spectrogram.')
    parser.add_argument('--file', default='C:\\temp\\unmix.io\\test.h5', type=str, help='Hierarhical data format container file')
    parser.add_argument('--path', default='', type=str, help='Optional output folder')

    args = parser.parse_args()
    print('Arguments:', str(args))

    path = args.path
    if not path:
        path = os.path.dirname(args.file)


    h5f = h5py.File(args.file,'r')
    file = h5f['file'].value
    fft_window = h5f['fft_window'].value
    sample_rate = h5f['sample_rate'].value
    spectrogram_left = h5f['spectrogram_left'][:, :, :]
    spectrogram_right = h5f['spectrogram_right'][:, :, :]
    generate_audiofile(spectrogram_left, spectrogram_right, file, path, fft_window, sample_rate)

    h5f.close()
    print('Finished processing')
