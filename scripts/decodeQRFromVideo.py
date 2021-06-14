import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import os
from datetime import timedelta
import dateutil.parser
from multiprocessing import Pool
import sys


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
    global firstQRFoundFrameNumber
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
    global firstQRFoundFrameNumber
    if returnStatus.qrFound != False and firstQRFoundFrameNumber == 0:
        # parse encoded time into date
        qrTimestamp = dateutil.parser.isoparse(returnStatus.qrData.decode("utf-8"))
        print(
            "Frame# "
            + str(returnStatus.frameNumber)
            + " Pool worker found QR Timestamp: "
            + qrTimestamp.isoformat().replace("+00:00", "Z")
        )
        firstQRFoundFrameNumber = returnStatus.frameNumber


if __name__ == "__main__":
    firstQRFoundFrameNumber = 0
    currentFrame = 0
    firstSeconds = 0

    # get video file path argument
    if get_arg(1) == "":
        # test video with CODA Clocksync ISO time QR code in it.
        # cam = cv2.VideoCapture("../vid/IMG_1722.MOV")
        print("Video file path argument missing. Using default.")
        vidPath = "N:\\Projects\\NASA_CODA\\CODA_data\\RockYard\\2021-05-13-QuadView-EVA_20.26.55.MP4"
    else:
        vidPath = str(get_arg(1))

    cam = cv2.VideoCapture(vidPath)

    # get frames per second of video for use in start time calc
    fps = round(cam.get(cv2.CAP_PROP_FPS))

    print("Searching video file for QR code UTC timestamps.")
    print(
        "Your CPU has "
        + str(os.cpu_count())
        + " processors. Spinning up worker pool of "
        + str(os.cpu_count())
        + " QR searchers"
    )

    # Step 1: Use pool of workers to look for QRs in frames of video.
    # When a QR is found, save the frame number where it would found for use in Step 2 below
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
            if firstQRFoundFrameNumber != 0:
                break

    # Step 2: Starting at the frame number where the first QR code image was found using the parallel processing method above
    # Use single-thread method to step through frames of video looking for when the second ticks over
    # and use that frame number to determine precise video start time

    # start reading at frame number where the first QR code was found
    currentFrame = firstQRFoundFrameNumber
    cam.set(cv2.CAP_PROP_POS_FRAMES, currentFrame)

    try:
        while True:
            # reading from frame
            ret, frame = cam.read()

            # if frames remaining, continue reading frames
            if ret:
                if currentFrame % 10 == 0:
                    print("Single thread - searching Frame# " + str(currentFrame), end="\r", flush=True)
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

                            # subtract seconds since beginning of video of current frame from the QR time to determine video start time
                            videoStartTime = qrTimestamp - timedelta(seconds=secondsIntoVideo)

                            print(
                                "Calculated video start time: " + str(videoStartTime.isoformat().replace("+00:00", "Z"))
                            )
                            raise BreakIt

                currentFrame += 1
    except BreakIt:
        print("Search terminated")
        pass

    # Release all space once done
    cam.release()
