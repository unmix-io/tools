"""
Calculates the mean and variance over h5 audio trainings files.
"""

__author__ = 'David Flury'
__email__ = "david@flury.email"

import os
import glob
import json
import h5py
import time
import argparse
import numpy as np
import progressbar


def calculate_sum(file):    
    data = h5py.File(file,'r')
    stereo = data['stereo'][()]
    channels = None
    if stereo:
        channels = np.array(
            [np.abs(to_complex(data['spectrogram_left'][()])), 
             np.abs(to_complex(data['spectrogram_right'][()]))])
    else:
        channels = np.array([np.abs(to_complex(data['spectrogram'][()]))])
    return np.sum(np.sum(channels, axis=2), axis=0), np.size(channels[0])

def calculate_derivation(file, mean):    
    data = h5py.File(file,'r')
    stereo = data['stereo'][()]
    channels = None
    if stereo:
        channels = np.array(
            [np.abs(to_complex(data['spectrogram_left'][()])), 
             np.abs(to_complex(data['spectrogram_right'][()]))])
    else:
        channels = np.array([np.abs(to_complex(data['spectrogram'][()]))])
    return np.sum(np.sum(np.square(channels - np.repeat(np.reshape(mean, mean.shape + (1,)), channels.shape[-1], axis=1)), axis=2), axis=0)

def to_complex(realimag):
    'Converts the real-imag array of the training values to complex values'
    real = realimag[:, :, 0]
    imag = realimag[:, :, 1]
    return real + imag * 1j

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculates the mean and variance over h5 audio trainings files.')
    parser.add_argument('--path', default='D:\\Data\\unmix.io\\4_training\\fft-window=1536_sample-rate=11025_channels=1-mono\\mini',
         type=str, help='Working path.')
    parser.add_argument('--prefix', default='',
         type=str, help='Prefix for file names to pick only vocal or instrumental songs.')
    parser.add_argument('--fft_window', default=1536,
         type=int, help='FFT-Window size.')

    args = parser.parse_args()
    print('Arguments:', str(args))

    start = time.time()

    height = args.fft_window // 2 + 1

    print('Start calculating mean...')
    
    total_sum = np.zeros((height))
    total_elements = 0
    total_derivation = np.zeros((height))
    files = []

    with progressbar.ProgressBar(max_value=progressbar.UnknownLength) as bar:
        for file in glob.iglob(os.path.join(args.path, '**', '%s*.h5' % args.prefix), recursive=True):
            s, e = calculate_sum (file)
            total_sum += s
            total_elements +=  e
            files.append(file)
            bar.update(len(files))
        
    total_mean = total_sum / total_elements
    
    print('Start calculating variance...')
    with progressbar.ProgressBar(max_value=len(files)) as bar:
        for i in range(len(files)):
            file = files[i]
            total_derivation += calculate_derivation(file, total_mean)
            bar.update(i)

    total_variance = total_derivation / (total_elements - 1)

    result = {
        "mean": np.average(total_mean),
        "variance": np.average(total_variance),
        "bin_mean": total_variance.tolist(),
        "bin_variance": total_variance.tolist(),
        "files": len(files),
        "fft_window": args.fft_window,
        "prefix": args.prefix,
        "path": args.path
    }
    path = os.path.join(args.path, '%s%smean-derivation.json' % (args.prefix, '_' if args.prefix else ''))
    with open(path, 'w') as file:
        json.dump(result, file, indent=4)
    
    print("Wrote results to: %s" % path)

    end = time.time()
    
    print('Finished processing in %d [s].' % (end - start))
