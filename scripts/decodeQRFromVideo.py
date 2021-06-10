import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import os
import datetime
import dateutil.parser
from multiprocessing import Pool


class BreakIt(Exception):
    pass


# worker process that searches a frame of video for a QR code
def lookForQRcodes(thisFrame, currentFrameNumber):
    global firstQRFoundFrameNumber
    if currentFrameNumber % 100 == 0:
        print("Searching Frame# " + str(currentFrameNumber), end="\r", flush=True)
    # find the barcodes in the frame and decode each of the barcodes
    decodedBarcodes = pyzbar.decode(thisFrame, symbols=[ZBarSymbol.QRCODE])

    # loop over the detected barcodes in the frame (there should only be one)
    for barcode in decodedBarcodes:
        # If QR found, then set the global frame number where it was found
        if barcode.type == "QRCODE":
            # TODO: make this ignore QR codes that aren't UTC timestamps
            firstQRFoundFrameNumber = currentFrameNumber


if __name__ == "__main__":
    firstQRFoundFrameNumber = 0
    currentFrame = 0
    firstSeconds = 0

    # test video with CODA Clocksync ISO time QR code in it.
    cam = cv2.VideoCapture("../vid/IMG_1722.MOV")
    # cam = cv2.VideoCapture("N:\\Projects\\NASA_CODA\\CODA_data\\RockYard\\2021-05-13-QuadView-EVA_20.26.55.MP4")

    # get frames per second of video for use in start time calc
    fps = round(cam.get(cv2.CAP_PROP_FPS))

    print(
        "Your CPU has "
        + str(os.cpu_count())
        + " processors. Spinning up worker pool of "
        + str(os.cpu_count())
        + " QR searchers"
    )

    # Step 1: Use pool of workers to look for QRs in frames of video.
    # When a QR is found, save the frame number where it would found for use in Step 2 below
    with Pool() as pool:
        # Loop through all of the frames in the video
        while True:
            # reading from frame
            ret, frame = cam.read()

            # if frames remaining, continue reading frames
            if ret:
                # send frame to pool worker process
                res = pool.apply_async(lookForQRcodes, (frame, currentFrame))
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
                            videoStartTime = qrTimestamp - datetime.timedelta(seconds=secondsIntoVideo)

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
