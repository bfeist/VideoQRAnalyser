# Importing all necessary libraries
import cv2
from pyzbar import pyzbar
import os
import datetime

# Read the video from specified path
# cam = cv2.VideoCapture("../vid/IMG_0690.mov")
cam = cv2.VideoCapture("../vid/IMG_0690_1080p_trimmed.mov")

#get frames per second of video for use in start time calc
fps = round(cam.get(cv2.CAP_PROP_FPS))

currentframe = 0

firstSeconds = 0

class BreakIt(Exception): pass

try:
    # Loop through all of the frames in the video
    while True:
        # reading from frame
        ret,frame = cam.read()

        # if frames remaining, continue reading frames
        if ret:
            print("Frame# " + str(currentframe))

            # find the barcodes in the frame and decode each of the barcodes
            decodedBarcodes = pyzbar.decode(frame)

            # loop over the detected barcodes in the frame (there should only be one)
            for barcode in decodedBarcodes:
                print('Type : ', barcode.type)
                print('Data : ', barcode.data,'\n')

                if barcode.type == 'QRCODE':
                    dataArray = barcode.data.decode('utf-8').split("/") #split the decoded string by / to get items
                    timestring = dataArray[0] + " " + dataArray[1][:-3] #assemble a proper Datetime out of items
                    currSeconds = int(timestring[-2:]) #get the seconds value out of the QR time

                    if firstSeconds == 0:
                        firstSeconds = currSeconds

                    # Detect if the QR time's second value has rolled over on this frame.
                    # If so then this frame should be used to determine time using framerate math
                    if currSeconds != firstSeconds:
                        secondsIntoVideo = currentframe / fps
                        print("Time rollover detected " + str(secondsIntoVideo) + " seconds into the video")

                        #create Datetime object out of decoded QR time
                        currTimeDatetime = datetime.datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S')

                        #subtract seconds since beginning of video of current frame from the QR time to determine video start time
                        videoStartTime = currTimeDatetime - datetime.timedelta(seconds=secondsIntoVideo)

                        print("Calculated video start time: " + str(videoStartTime))
                        raise BreakIt

            currentframe += 1
        else:
            break
except BreakIt:
    pass

# Release all space once done
cam.release()