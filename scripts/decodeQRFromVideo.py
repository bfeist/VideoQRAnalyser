# Importing all necessary libraries
import cv2
from pyzbar import pyzbar
import os

# Read the video from specified path
cam = cv2.VideoCapture("../vid/IMG_0690_1080p.mov")

currentframe = 0

while(True):

    # reading from frame
    ret,frame = cam.read()

    if ret:
        # if video is still left continue reading frames

        # find the barcodes in the image and decode each of the barcodes
        decodedBarcodes = pyzbar.decode(frame)

        # loop over the detected barcodes
        print("Frame# " + str(currentframe))
        for barcode in decodedBarcodes:
            print('Type : ', barcode.type)
            print('Data : ', barcode.data,'\n')

        currentframe += 1
    else:
        break

# Release all space and windows once done
cam.release()
# cv2.destroyAllWindows()