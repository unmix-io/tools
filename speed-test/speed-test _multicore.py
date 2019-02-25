import time
import hashlib
import argparse
import multiprocessing
from joblib import Parallel, delayed

def calculate_hash():
  input = 'unmix.io is great!'
  hash_object = hashlib.sha1(input.encode())

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='CPU speed test with multiple cores.')
  parser.add_argument('--calculations', default=1000000, type=int, help='Count of calculations')
  parser.add_argument('--cores', default=multiprocessing.cpu_count(), type=int, help='Size of FFT windows')

  args = parser.parse_args()
  print('Arguments:', str(args))
  
  print('speed-test with %d cores and %d calculations...' % (args.cores, args.calculations))
  
  start = time.time() 
  Parallel(n_jobs=args.cores)(delayed(calculate_hash)() for x in range(args.calculations))  
  end = time.time()
  print(end - start)
