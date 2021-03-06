"""
Reads a hierarchical data format (h5) file containing a complexe frequency spectrogram and generates the audio file.
"""

__author__ = 'David Flury'
__email__ = "david@flury.email"

import os
import h5py
import librosa
import argparse
import numpy as np

def generate_audiofile(spectrograms, name, path, fft_window, sample_rate):
    file = os.path.join(path, name + ".wav")
    data = [librosa.istft((generate_stft(spectrogram))) for spectrogram in spectrograms]
    audio = np.array(data)
    print('Output audio file: %s' % file)
    librosa.output.write_wav(file, audio[0] if len(data) == 1 else audio, sample_rate, norm=False)


def generate_stft(spectrogram):
    real_part = spectrogram[:, :, 0]
    imag_part = spectrogram[:, :, 1]
    stft = real_part + imag_part * 1j
    return stft

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reads h5 a file containing a complexe frequency spectrogram and generates the audio file.')
    parser.add_argument('--file', default='D:\\Data\\test_abs-angle-instrumental.h5', 
        type=str, help='Hierarhical data format container file')
    parser.add_argument('--path', default='', type=str, help='Optional output folder')

    args = parser.parse_args()
    print('Arguments:', str(args))

    if not args.path:
        args.path = os.path.dirname(args.file)


    h5f = h5py.File(args.file,'r')
    file = h5f['file'].value
    fft_window = h5f['fft_window'].value
    sample_rate = h5f['sample_rate'].value
    channels = h5f['channels'].value

    spectrograms = []
    if channels > 1:
        spectrograms.append(h5f['spectrogram_left'][:, :, :])
        spectrograms.append(h5f['spectrogram_right'][:, :, :])
    else:
        spectrograms.append(h5f['spectrogram'][:, :, :])
        
    generate_audiofile(spectrograms, file, args.path, fft_window, sample_rate)

    h5f.close()
    print('Finished processing')
