import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import os
from datetime import timedelta
import dateutil.parser
from multiprocessing import Pool
import sys
import json


class BreakIt(Exception):
    pass


class ReturnStatus(object):
    qrFound = False
    qrData = ""
    frameNumber = -1


def secondsToText(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%02d:%02d:%02d" % (hour, minutes, seconds)


def get_arg(index):
    try:
        sys.argv[index]
    except IndexError:
        return ""
    else:
        return sys.argv[index]


# worker process that searches a frame of video for a QR code
def lookForQRcodes(thisFrame, currentFrameNumber, fps):
    if currentFrameNumber % 100 == 0:
        print(
            "Searching: " + secondsToText(currentFrameNumber / fps) + " (hh:mm:ss) - frame# " + str(currentFrameNumber),
            end="\r",
            flush=True,
        )

    returnStatus = ReturnStatus()
    returnStatus.qrFound = False

    # find the barcodes in the frame and decode each of the barcodes
    decodedBarcodes = pyzbar.decode(thisFrame, symbols=[ZBarSymbol.QRCODE])

    # loop over the detected barcodes in the frame (there should only be one)
    for barcode in decodedBarcodes:
        # If QR found, then set the global frame number where it was found
        if barcode.type == "QRCODE":
            returnStatus.qrFound = True
            returnStatus.qrData = barcode.data
            returnStatus.frameNumber = currentFrameNumber

    return returnStatus


def QRcodeWorkerCallback(returnStatus: ReturnStatus):
    global QRFoundFrameNumber
    global QRFoundTimestamp
    if returnStatus.qrFound != False and QRFoundFrameNumber == 0:
        # parse encoded time into date
        qrTimestamp = dateutil.parser.isoparse(returnStatus.qrData.decode("utf-8"))
        print(
            "Frame# "
            + str(returnStatus.frameNumber)
            + " Pool worker found QR Timestamp: "
            + qrTimestamp.isoformat().replace("+00:00", "Z")
        )
        QRFoundFrameNumber = returnStatus.frameNumber
        QRFoundTimestamp = qrTimestamp


def searchSingleThreaded():
    global QRFoundFrameNumber
    global QRFoundTimestamp
    global videoStartTime
    global currentFrame

    firstSeconds = 0

    # Step 2: Starting at the frame number where the first QR code image was found in step 1 above
    # Use single-thread method to step through frames of video looking for when the second ticks over
    # and use that frame number to determine precise video start time

    # start reading at frame number where the first QR code was found
    currentFrame = QRFoundFrameNumber
    cam.set(cv2.CAP_PROP_POS_FRAMES, currentFrame)

    try:
        # Loop through the next 100 frames looking frame rollover start time
        print("Single thread search next 100 frames for rollover")
        while currentFrame - QRFoundFrameNumber < 100:
            # reading from frame
            ret, frame = cam.read()

            # if frames remaining, continue reading frames
            if ret:
                if currentFrame % 10 == 0:
                    print("- searching Frame# " + str(currentFrame), end="\r", flush=True)
                # find the barcodes in the frame and decode each of the barcodes
                decodedBarcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])

                # loop over the detected barcodes in the frame (there should only be one)
                for barcode in decodedBarcodes:
                    # If QR found, then return its data
                    if barcode.type == "QRCODE":
                        qrTimestamp = dateutil.parser.isoparse(barcode.data.decode("utf-8"))
                        print(
                            "Frame# "
                            + str(currentFrame)
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

                            QRFoundFrameNumber = currentFrame
                            QRFoundTimestamp = qrTimestamp
                            raise BreakIt

                currentFrame += 1
    except BreakIt:
        print("Search terminated")
        pass

    secondsIntoVideo = QRFoundFrameNumber / fps
    # subtract seconds since beginning of video of current frame from the QR time to determine video start time
    videoStartTime = QRFoundTimestamp - timedelta(seconds=secondsIntoVideo)

    print("Calculated video start time: " + str(videoStartTime.isoformat().replace("+00:00", "Z")) + "\n")


if __name__ == "__main__":
    QRFoundFrameNumber = 0
    QRFoundTimestamp = None
    videoStartTime = None
    currentFrame = 0

    videoFeedsPath = r"N:\Projects\NASA_CODA\CODA_Box_data\box_mirror\CODA\DRATS\2021-10-22\Video-No-Audio\\"
    videoFilesWithDir = []
    for videoFilename in os.listdir(videoFeedsPath):
        if videoFilename.lower().endswith(".mp4") or videoFilename.lower().endswith(".mov"):
            videoFilesWithDir.append(videoFilename)

    print(
        "Your CPU has "
        + str(os.cpu_count())
        + " logical cores. Spinning up worker pool of "
        + str(os.cpu_count())
        + " QR searchers"
    )

    videoList = []
    for videoFilename in videoFilesWithDir:
        videoFullPath = videoFeedsPath + videoFilename

        QRFoundFrameNumber = 0
        QRFoundTimestamp = None
        videoStartTime = None
        currentFrame = 0
        tempDict = {}

        # test video with CODA Clocksync ISO time QR code in it.
        cam = cv2.VideoCapture(videoFullPath)  # open the video file

        # get frames per second of video for use in start time calc
        fps = round(cam.get(cv2.CAP_PROP_FPS))

        print("Searching " + videoFilename + " for QR code UTC timestamps.")

        # Step 1: Use pool of workers to look for QRs in frames of video in parallel
        # When a QR is found, save the frame number where it was found for use in Step 2 below
        with Pool(processes=os.cpu_count()) as pool:
            # Loop through all of the frames in the video

            while True:
                # reading from frame
                ret, frame = cam.read()

                # if frames remaining, continue reading frames
                if ret:
                    # send frame to pool worker process
                    res = pool.apply_async(lookForQRcodes, (frame, currentFrame, fps), callback=QRcodeWorkerCallback)
                    currentFrame += 1
                else:
                    break
                if QRFoundFrameNumber != 0:
                    break

        if QRFoundFrameNumber != 0:
            searchSingleThreaded()

        # Release all space once done
        cam.release()

        tempDict["videoFilename"] = videoFilename
        tempDict["FrameNumberQRFound"] = QRFoundFrameNumber
        tempDict["TimestampInQR"] = (
            QRFoundTimestamp.isoformat().replace("+00:00", "Z") if QRFoundTimestamp != None else ""
        )
        tempDict["videoStartTime"] = videoStartTime.isoformat().replace("+00:00", "Z") if videoStartTime != None else ""
        videoList.append(tempDict)

    with open(videoFeedsPath + "videoStartTimes.json", "w") as outfile:
        json.dump(videoList, outfile, indent=4, default=str)
