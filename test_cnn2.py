'''
GPU run command:
    THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python test_cnn.py
'''

from __future__ import print_function
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import SGD
from keras.preprocessing.image import ImageDataGenerator
from keras.utils import np_utils
from keras.callbacks import EarlyStopping
import numpy


import VIPerDS


batch_size = 32
# nb_classes = 1
nb_classes = 2
nb_epoch = 2

data_augmentation = True

# input image dimensions
img_rows, img_cols = 128, 48
# the VIPerDS images are RGB
img_channels = 3

# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = VIPerDS.load_data()
print('X_train shape:', X_train.shape)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)
# Y_train = numpy.reshape(y_train, (numpy.size(y_train), 1))
# Y_test = numpy.reshape(y_test, (numpy.size(y_test), 1))

# model = model_from_json(open('my_model_architecture.json').read())
# model.load_weights('my_model_weights.h5')

model = Sequential()

model.add(Convolution2D(32, 5, 5, border_mode='valid',
                        input_shape=(img_channels, img_rows, img_cols)))
model.add(Activation('relu'))
model.add(Convolution2D(32, 5, 5))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
# model.add(ZeroPadding2D(padding=(1, 1), dim_ordering='th'))
model.add(Dropout(0.25))

model.add(Convolution2D(64, 3, 3))
model.add(Activation('relu'))
model.add(Convolution2D(64, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Convolution2D(128, 3, 3))
model.add(Activation('relu'))
model.add(ZeroPadding2D(padding=(1, 1)))
model.add(Convolution2D(128, 3, 3))
model.add(Activation('relu'))
model.add(ZeroPadding2D(padding=(1, 1)))

# model.add(Convolution2D(16, 3, 3))
# model.add(Activation('relu'))
# model.add(ZeroPadding2D(padding=(1, 1)))
# model.add(Convolution2D(8, 3, 3))
# model.add(Activation('relu'))
# model.add(ZeroPadding2D(padding=(1, 1)))
# model.add(Convolution2D(8, 3, 3))
# model.add(Activation('relu'))
# model.add(ZeroPadding2D(padding=(1, 1)))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Convolution2D(64, 3, 3))
model.add(Activation('relu'))
model.add(ZeroPadding2D(padding=(1, 1)))
model.add(Convolution2D(64, 3, 3))
model.add(Activation('relu'))
model.add(ZeroPadding2D(padding=(1, 1)))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(256))
model.add(Activation('relu'))
model.add(Dropout(0.5))

model.add(Dense(32))
model.add(Activation('relu'))
model.add(Dropout(0.5))

model.add(Dense(nb_classes))
model.add(Activation('softmax'))


earlyStopping = EarlyStopping(monitor='val_loss', patience=1, verbose=0, mode='min')

# let's train the model using SGD + momentum
# stochastic gradient descent
sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd)

if not data_augmentation:
    print('Not using data augmentation.')
    model.fit(X_train, Y_train, batch_size=batch_size,
              nb_epoch=nb_epoch, show_accuracy=True,
              validation_data=(X_test, Y_test), shuffle=True,
              callbacks=[earlyStopping])
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
                        nb_worker=1,
                        callbacks=[earlyStopping])

json_string = model.to_json()
open('my_model_architecture.json', 'w').write(json_string)
model.save_weights('my_model_weights.h5'
                   # , overwrite=True
                   )

