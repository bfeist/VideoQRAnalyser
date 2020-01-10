# Importing all necessary libraries
import cv2
from pyzbar import pyzbar
import os
import datetime

# Read the video from specified path
# cam = cv2.VideoCapture("../vid/IMG_0690.mov")
cam = cv2.VideoCapture("../vid/IMG_0690_1080p_trimmed.mov")

fps = round(cam.get(cv2.CAP_PROP_FPS))

currentframe = 0
decodedCodes = []
tempDict = {}

firstSeconds = 0

class BreakIt(Exception): pass

try:
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

                tempDict['framenum'] = currentframe
                tempDict['data'] = barcode.data
                decodedCodes.append(tempDict.copy())

                dataArray = barcode.data.decode('utf-8').split("/")

                timestring = dataArray[0] + " " + dataArray[1]
                # timestring.decode('UTF-8')
                timestring = timestring[:-3]
                currSeconds = timestring[-2:]
                # print(timestring)

                if firstSeconds == 0:
                    firstSeconds = int(currSeconds)

                if int(currSeconds) - firstSeconds == 1:
                    # if the first detected QR code in the next second is detected, then this frame should be used to determine time using framerate math
                    secondsIntoVideo = currentframe / fps
                    print("Time rollover detected " + str(secondsIntoVideo) + " seconds into the video")

                    currTimeDatetime = datetime.datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S')
                    print(currTimeDatetime)
                    videoStartTime = currTimeDatetime - datetime.timedelta(seconds=secondsIntoVideo)

                    print("Calculated video start time: " + str(videoStartTime))
                    raise BreakIt

            currentframe += 1
        else:
            break
except BreakIt:
    pass

# Release all space and windows once done
cam.release()
# cv2.destroyAllWindows()