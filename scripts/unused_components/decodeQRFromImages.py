# import the necessary packages
import os
from pyzbar import pyzbar

import cv2

imagePath = '../../tmp'

imageFilename = 'frame0241.jpg'
# for imageFilename in os.listdir(imagePath):
# load the input image
# image = cv2.imread(imagePath + '/' + imageFilename)
image = cv2.imread(imagePath + '/' + imageFilename)

# find the barcodes in the image and decode each of the barcodes
decodedBarcodes = pyzbar.decode(image)

# loop over the detected barcodes
print(imageFilename)
for barcode in decodedBarcodes:
    print('Type : ', barcode.type)
    print('Data : ', barcode.data.decode('utf-8'),'\n')

