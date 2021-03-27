import cv2
from pyzbar import pyzbar
import os
import datetime
import dateutil.parser

# test video with CODA Clocksync ISO time QR code in it.
cam = cv2.VideoCapture("../vid/IMG_1722.MOV")

# get frames per second of video for use in start time calc
fps = round(cam.get(cv2.CAP_PROP_FPS))

currentframe = 0
firstSeconds = 0


class BreakIt(Exception):
    pass


try:
    # Loop through all of the frames in the video
    while True:
        # reading from frame
        ret, frame = cam.read()

        # if frames remaining, continue reading frames
        if ret:
            print("Searching Frame# " + str(currentframe))

            # find the barcodes in the frame and decode each of the barcodes
            decodedBarcodes = pyzbar.decode(frame)

            # loop over the detected barcodes in the frame (there should only be one)
            for barcode in decodedBarcodes:
                print("Type : ", barcode.type)
                print("Data : ", barcode.data)

                if barcode.type == "QRCODE":
                    # parse encoded time into date
                    qrTimestamp = dateutil.parser.isoparse(barcode.data.decode("utf-8"))
                    print("QR Timestamp: " + qrTimestamp.isoformat().replace("+00:00", "Z") + "\n")

                    # get seconds value
                    currSeconds = qrTimestamp.second

                    if firstSeconds == 0:
                        firstSeconds = currSeconds

                    # Detect if the QR time's second value has rolled over on this frame.
                    # If so then this frame should be used to determine video start time using framerate math
                    if currSeconds != firstSeconds:
                        secondsIntoVideo = currentframe / fps
                        print("Time rollover detected " + str(secondsIntoVideo) + " seconds into the video")

                        # subtract seconds since beginning of video of current frame from the QR time to determine video start time
                        videoStartTime = qrTimestamp - datetime.timedelta(seconds=secondsIntoVideo)

                        print("Calculated video start time: " + str(videoStartTime.isoformat().replace("+00:00", "Z")))
                        raise BreakIt

            currentframe += 1
        else:
            break
except BreakIt:
    pass

# Release all space once done
cam.release()
