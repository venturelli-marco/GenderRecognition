from __future__ import print_function
from keras.models import Sequential, model_from_json
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import SGD
from keras.preprocessing.image import ImageDataGenerator
from keras.utils import np_utils
from keras.callbacks import EarlyStopping
import numpy
import os
import VIPerDS
import siamese
import random

random.seed(12345)

video_directory = "/home/cla/Downloads/CMD/CMD/CMD"

directory_list = []
for direct in os.listdir(video_directory):
    if not os.path.isdir(video_directory+'/'+direct):
        continue
    else:
        directory_list.append(video_directory+'/'+direct)

def load_pkl_video(dir):
    import cPickle as pickle
    import sys
    sys.setrecursionlimit(10000)

    file_load = open(dir + "/prova.pkl", 'rb')
    m = pickle.load(file_load)
    return m

def load_train_samples(x, y, dirs, maxsize=None):
    for d in random.sample(dirs,len(dirs)):
            (new_img, new_labels) = load_pkl_video(d)
            corrected_labels = map(lambda x: 0 if x < 0 else x, new_labels)
            labels = np_utils.to_categorical(corrected_labels, nb_classes)
            y = numpy.vstack([y, labels])
            x = numpy.vstack([x, new_img])
            if maxsize and y.shape[0] > maxsize:
                break
    return (x,y)

random.shuffle(directory_list)

val_list= directory_list[15:]
train_list = directory_list[:15]
# train_list = directory_list

#cambio il seed per caricare gli esempi in modi diversi
random.seed(56323)

batch_size = 32
# nb_classes = 1
nb_classes = 2
nb_epoch = 1

data_augmentation = True

# input image dimensions
img_rows, img_cols = 128, 48
# the VIPerDS images are RGB
img_channels = 3

# (X_train, y_train), (X_test, y_test) = VIPerDS.load_data()
# Y_train = np_utils.to_categorical(y_train, nb_classes)
# Y_test = np_utils.to_categorical(y_test, nb_classes)
X_test = numpy.empty([0, 3, 128, 48], dtype='float32')
Y_test = numpy.empty([0, 2])
X_train = numpy.empty([0, 3, 128, 48], dtype='float32')
Y_train = numpy.empty([0, 2])
(X_test, Y_test) = load_train_samples(X_test,Y_test, val_list)


# model_name = 'my_model_architecture.json'
# model_weights = 'my_model_weights.h5'
# # model_weights = None
#
# model = model_from_json(open(model_name).read())
# if model_weights:
#     model.load_weights(model_weights)


m = Sequential()

m.add(Convolution2D(32, 5, 5, border_mode='valid',
                        input_shape=(img_channels, img_rows, img_cols)))
m.add(Activation('relu'))
m.add(Convolution2D(32, 5, 5))
m.add(Activation('relu'))
m.add(MaxPooling2D(pool_size=(2, 2)))
# m.add(ZeroPadding2D(padding=(1, 1), dim_ordering='th'))
m.add(Dropout(0.25))

m.add(Convolution2D(64, 3, 3, border_mode='same'))
m.add(Activation('relu'))
m.add(Convolution2D(64, 3, 3))
m.add(Activation('relu'))
m.add(MaxPooling2D(pool_size=(2, 2)))
m.add(Dropout(0.25))

m.add(Convolution2D(128, 3, 3, border_mode='same'))
m.add(Activation('relu'))
m.add(Convolution2D(128, 3, 3))
m.add(Activation('relu'))
m.add(MaxPooling2D(pool_size=(2, 2)))
m.add(Dropout(0.25))

m.add(Flatten())
m.add(Dense(64))
m.add(Activation('relu'))
m.add(Dropout(0.5))

last_layer = 32
m.add(Dense(last_layer))
m.add(Activation('relu'))
m.add(Dropout(0.5))

# remove last layer
model = siamese.build_siamese(m, m, last_layer, nb_classes)

model.load_weights('my_model_weights.h5')


earlyStopping = EarlyStopping(monitor='val_loss', patience=1, verbose=0, mode='min')

sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd)


if not data_augmentation:
    print('Not using data augmentation.')

else:
    print('Using real-time data augmentation.')

# this will do preprocessing and realtime data augmentation
datagen = ImageDataGenerator(
    featurewise_center=False,  # set input mean to 0 over the dataset
    samplewise_center=False,  # set each sample mean to 0
    featurewise_std_normalization=False,  # divide inputs by std of the dataset
    samplewise_std_normalization=False,  # divide each input by its std
    zca_whitening=False,  # apply ZCA whitening
    rotation_range=20,  # randomly rotate images in the range (degrees, 0 to 180)
    width_shift_range=0.2,  # randomly shift images horizontally (fraction of total width)
    height_shift_range=0.2,  # randomly shift images vertically (fraction of total height)
    horizontal_flip=True,  # randomly flip images
    vertical_flip=False)  # randomly flip images




for i in range(1,10):
    if Y_train.shape[0] < 30000:
        (X_train, Y_train) = load_train_samples(X_train, Y_train, train_list, 30000)
    else:
        X_train = X_train[20000:, :]
        Y_train = Y_train[20000:, :]
        (X_train, Y_train) = load_train_samples(X_train, Y_train, train_list, 30000)

    if not data_augmentation:
        model.fit(X_train, Y_train, batch_size=batch_size,
              nb_epoch=nb_epoch, show_accuracy=True,
              validation_data=(X_test, Y_test), shuffle=True
              # ,callbacks=[earlyStopping]
              )

    else:
        # compute quantities required for featurewise normalization
        # (std, mean, and principal components if ZCA whitening is applied)
        datagen.fit(X_train)

        # fit the model on the batches generated by datagen.flow()
        model.fit_generator(datagen.flow(X_train, Y_train,
                                     batch_size=batch_size, shuffle=True,
                                     #save_to_dir='prova', save_format='png'
                                     ),
                        samples_per_epoch=X_train.shape[0],
                        nb_epoch=nb_epoch, show_accuracy=True,
                        validation_data=(X_test, Y_test),
                        nb_worker=1
                        # ,callbacks=[earlyStopping]
                        )





json_string = model.to_json()
open('my_model_architecture.json', 'w').write(json_string)
model.save_weights('my_model_weights.h5'
                   , overwrite=True
                   )
