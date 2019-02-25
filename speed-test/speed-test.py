import time
import hashlib

start = time.time()
input = 'unmix.io is great!'
for x in range(10000000):
  hash_object = hashlib.sha1(input.encode())
  input = hash_object.hexdigest()
end = time.time()
print(end - start)