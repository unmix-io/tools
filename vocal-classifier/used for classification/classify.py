from os import listdir
import os
from os.path import isfile, join, isdir
import subprocess

# Run neural network for targetFile
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.optimizers import RMSprop
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense
from keras.callbacks import CSVLogger
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

#_____________________ Define model
# Model 5
IMAGE_WIDTH, IMAGE_HEIGHT = 852, 480
EPOCHS = 20
BATCH_SIZE = 8
TEST_SIZE = 149

input_shape = (IMAGE_WIDTH, IMAGE_HEIGHT, 3)

model = Sequential()

model.add(Conv2D(32, 3, 3, border_mode='same', input_shape=input_shape, activation='relu'))
model.add(Conv2D(32, 3, 3, border_mode='same', activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(64, 3, 3, border_mode='same', activation='relu'))
model.add(Conv2D(64, 3, 3, border_mode='same', activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(128, 3, 3, border_mode='same', activation='relu'))
model.add(Conv2D(128, 3, 3, border_mode='same', activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(256, 3, 3, border_mode='same', activation='relu'))
model.add(Conv2D(256, 3, 3, border_mode='same', activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(512, 3, 3, border_mode='same', activation='relu'))
model.add(Conv2D(512, 3, 3, border_mode='same', activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(1024, 3, 3, border_mode='same', activation='relu'))
model.add(Conv2D(1024, 3, 3, border_mode='same', activation='relu'))
model.add(MaxPooling2D(pool_size=(2,2)))

model.add(Flatten())
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.5))

model.add(Dense(512, activation='relu'))
model.add(Dropout(0.5))

model.add(Dense(512, activation='relu'))
model.add(Dropout(0.5))

model.add(Dense(1))
model.add(Activation('sigmoid'))
    
model.compile(loss='binary_crossentropy',
            optimizer=RMSprop(lr=0.0001),
            metrics=['accuracy'])

model.load_weights("model.h5")

test_data_generator = ImageDataGenerator(rescale=1./255)


test_generator = test_data_generator.flow_from_directory(
    "./temp-spectrograms",
    target_size=(IMAGE_WIDTH, IMAGE_HEIGHT),
    batch_size=1,
    class_mode="binary", 
    shuffle=False)

filenames = test_generator.filenames
nb_samples = len(filenames)

probabilities = model.predict_generator(test_generator, nb_samples)


with open("vocal-classifications.log.txt", 'w') as f:
    for index, probability in enumerate(probabilities):
        image_path = "./temp-spectrograms" + "/" +test_generator.filenames[index]
        label = "vocal" if probability > 0.99 else "nonvocal"
        print(label + ";" + str(probability[0]) + ";" + image_path)
