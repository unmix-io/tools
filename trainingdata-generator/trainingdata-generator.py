"""
Creates hierarchical data format files with complexe frequency spectrograms for audio files in a given folder.
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

audio_extensions = ['.wav', '.mp3']


def generate_container(file, destination, fft_window, target_sample_rate, channels, generate_image):
    try:
        stereo = channels > 1
        audio, sample_rate = librosa.load(file, mono=not stereo, sr=target_sample_rate if target_sample_rate > 0 else None)
        spectrograms = []
        real_stereo = isinstance(audio[0], (np.ndarray))
        if stereo and real_stereo:
            spectrograms.append(stft_to_complex_spectrogram(generate_spectrogram(destination, audio[0], '0-stereo_left', fft_window, sample_rate, generate_image)))
            spectrograms.append(stft_to_complex_spectrogram(generate_spectrogram(destination, audio[1], '1-stereo_right', fft_window, sample_rate, generate_image)))
        else:
            spectrograms.append(stft_to_complex_spectrogram(generate_spectrogram(file, audio, '0-mono', fft_window, sample_rate, generate_image)))

        configuration = 'fft-window[%d]_sample-rate[%d]_channels[%d-%s]' % (fft_window, sample_rate, channels, "stereo" if stereo else "mono")

        song = os.path.basename(os.path.dirname(file))
        collection = os.path.basename(os.path.dirname(os.path.dirname(file)))
        
        folder = os.path.join(destination, configuration, collection, song)
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except:
                pass
        path = os.path.join(folder, "%s-spectrogram_%s" % (os.path.basename(file), configuration))

        save_spectrogram_data(spectrograms, path, fft_window, sample_rate, channels, real_stereo, song, collection)
        print('Generated spectrogram %s' % path)
    except Exception as e:
        print('Error while generating spectrogram for %s: %s' % (file, str(e)))
        pass

def generate_spectrogram(file, audio, part, fft_window, sample_rate, generate_image):
    stft = librosa.stft(audio, fft_window)
    if generate_image:        
        save_spectrogram_image(stft_to_real_spectrogram(stft), file, part, fft_window, sample_rate)
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

def save_spectrogram_image(spectrogram, file, part, fft_window, sample_rate):
    file_name = '%s_spectrogram_%s_fft-window[%d]_sample-rate[%d].png' % (file, part, fft_window, sample_rate)
    real_part = spectrogram[:, :, 0]
    cm_hot = get_cmap('plasma')
    image = np.clip((real_part - np.min(real_part)) / (np.max(real_part) - np.min(real_part)), 0, 1) 
    with warnings.catch_warnings():
        image = cm_hot(image)
        warnings.simplefilter('ignore')
        io.imsave(file_name, image)

def save_spectrogram_data(spectrograms, file, fft_window, sample_rate, channels, real_stereo, song, collection):
    h5f = h5py.File(file + '.h5', 'w')
    if len(spectrograms) > 1:
        h5f.create_dataset('spectrogram_left', data=spectrograms[0])
        h5f.create_dataset('spectrogram_right', data=spectrograms[1])
    else:
        h5f.create_dataset('spectrogram', data=spectrograms[0])
    dimensions = spectrograms[0].shape
    h5f.create_dataset('height', data=dimensions[0])
    h5f.create_dataset('width', data=dimensions[1])
    h5f.create_dataset('depth', data=dimensions[2])
    h5f.create_dataset('fft_window', data=fft_window)
    h5f.create_dataset('sample_rate', data=sample_rate)    
    h5f.create_dataset('channels', data=channels)    
    h5f.create_dataset('stereo', data=real_stereo)
    h5f.create_dataset('song', data=song)
    h5f.create_dataset('collection', data=collection)
    h5f.create_dataset('file', data=os.path.basename(file))
    h5f.close()

def build_destination(file, path, destination):
    return file.replace(path, destination)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates hierarchical data format files including complexe frequency spectrograms for audio files in a given folder.')
    parser.add_argument('--path', default='U:\\3_filter\\musdb18\\', type=str, help='Working path')
    parser.add_argument('--destination', default='D:\\Data\\unmix.io\\4_training\\', type=str, help='Destination path')
    parser.add_argument('--fft_window', default=1536, type=int, help='Size [Samples] of FFT windows')
    parser.add_argument('--sample_rate', default=11025, type=int, help='Optional target samplerate [Hz] for the audiofiles')
    parser.add_argument('--channels', default=1, type=int, help='1 (Mono) or 2 (Stereo)')
    parser.add_argument('--generate_image', default='true', type=str, help='If spectrogram image should be generated and saved')
    parser.add_argument('--job_count', default=int(multiprocessing.cpu_count()), type=int, help='Maximum number of concurrently running jobs')

    args = parser.parse_args()

    # Arguments cleanup
    if args.channels > 2:
        args.channels = 2
    if args.channels < 1:
        args.channels = 1

    if args.generate_image.lower() in ('no', 'false', 'f', 'n', '0'):
        args.generate_image = False
    else:
        args.generate_image = True

    print('Arguments:', str(args))

    files = [] # Load all files into list
    print('Load all music files...')
    for file in glob.iglob(args.path + '**/*', recursive=True):
        extension = os.path.splitext(file)[1].lower()
        if extension in audio_extensions:
            files.append(file)
    print('Found %d music files' % len(files))

    start = time.time()
    print('Generate spectrograms with maximum %d jobs...' % args.job_count)
    #generate_container(files[0], args.destination, args.fft_window, args.sample_rate, args.channels, args.generate_image)
    Parallel(n_jobs=args.job_count)(delayed(generate_container)(file, args.destination, args.fft_window, args.sample_rate, args.channels, args.generate_image) for file in files)
    end = time.time()
    
    print('Finished processing in %d [ms]', (end - start))
