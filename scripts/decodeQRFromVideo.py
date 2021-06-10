import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import os
import datetime
import dateutil.parser
from multiprocessing import Pool


class BreakIt(Exception):
    pass


class ReturnStatus(object):
    qrFound = False
    qrData = ""
    frameNumber = -1


def lookForQRcodes(thisFrame, currentFrameNumber):
    if currentFrameNumber % 10 == 0:
        print("Searching Frame# " + str(currentFrameNumber), end="\r", flush=True)
    # find the barcodes in the frame and decode each of the barcodes
    decodedBarcodes = pyzbar.decode(thisFrame, symbols=[ZBarSymbol.QRCODE])

    returnStatus = ReturnStatus()
    returnStatus.qrFound = False

    # loop over the detected barcodes in the frame (there should only be one)
    for barcode in decodedBarcodes:
        # If QR found, then return its data
        if barcode.type == "QRCODE":
            returnStatus.qrFound = True
            returnStatus.qrData = barcode.data
            returnStatus.frameNumber = currentFrameNumber

    return returnStatus


def QRcodeWorkerCallback(returnStatus: ReturnStatus):
    global startTimeFound
    global firstSeconds
    if returnStatus.qrFound != False and startTimeFound == False:
        # parse encoded time into date
        qrTimestamp = dateutil.parser.isoparse(returnStatus.qrData.decode("utf-8"))
        print(
            "Frame# "
            + str(returnStatus.frameNumber)
            + " QR Timestamp: "
            + qrTimestamp.isoformat().replace("+00:00", "Z")
        )
        # get seconds value
        currSeconds = qrTimestamp.second
        if firstSeconds == 0:
            firstSeconds = currSeconds

        # Detect if the QR time's second value has rolled over on this frame.
        # If so then this frame should be used to determine video start time using framerate math
        if currSeconds != firstSeconds:
            secondsIntoVideo = currentFrame / fps
            print("Time rollover detected " + str(secondsIntoVideo) + " seconds into the video")

            # subtract seconds since beginning of video of current frame from the QR time to determine video start time
            videoStartTime = qrTimestamp - datetime.timedelta(seconds=secondsIntoVideo)

            print("Calculated video start time: " + str(videoStartTime.isoformat().replace("+00:00", "Z")))
            startTimeFound = True


if __name__ == "__main__":
    startTimeFound = False
    currentFrame = 0
    firstSeconds = 0

    # test video with CODA Clocksync ISO time QR code in it.
    cam = cv2.VideoCapture("../vid/IMG_1722.MOV")
    # cam = cv2.VideoCapture("N:\\Projects\\NASA_CODA\\CODA_data\\RockYard\\2021-05-13-QuadView-EVA_20.26.55.MP4")

    # get frames per second of video for use in start time calc
    fps = round(cam.get(cv2.CAP_PROP_FPS))

    with Pool(processes=8) as pool:
        # Loop through all of the frames in the video

        try:
            while True:
                # reading from frame
                ret, frame = cam.read()

                # if frames remaining, continue reading frames
                if ret:
                    # send frame to pool worker process
                    res = pool.apply_async(lookForQRcodes, (frame, currentFrame), callback=QRcodeWorkerCallback)
                    currentFrame += 1
                else:
                    break
                if startTimeFound == True:
                    raise BreakIt
        except BreakIt:
            print(res.get(timeout=1))
            print("Search terminated")
            pass
    # Release all space once done
    cam.release()
