import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import os
import datetime
import dateutil.parser
from multiprocessing import Process, Value, Array, Pool


class BreakIt(Exception):
    pass


def f(thisFrame, currentFrame):
    if currentFrame % 100 == 0:
        print("Searching Frame# " + str(currentFrame), end="\r", flush=True)
    # find the barcodes in the frame and decode each of the barcodes
    decodedBarcodes = pyzbar.decode(thisFrame, symbols=[ZBarSymbol.QRCODE])

    # loop over the detected barcodes in the frame (there should only be one)
    for barcode in decodedBarcodes:
        print("\n")
        print("Type : ", barcode.type)

        print("Data : ", barcode.data)

        if barcode.type == "QRCODE":
            return barcode.data
    return 0


if __name__ == "__main__":
    # test video with CODA Clocksync ISO time QR code in it.
    cam = cv2.VideoCapture("../vid/IMG_1722.MOV")
    # cam = cv2.VideoCapture("N:\\Projects\\NASA_CODA\\CODA_data\\RockYard\\2021-05-13-QuadView-EVA_20.26.55.MP4")

    # get frames per second of video for use in start time calc
    fps = round(cam.get(cv2.CAP_PROP_FPS))

    currentframe = 0
    firstSeconds = 0

    with Pool(processes=16) as pool:
        # Loop through all of the frames in the video
        while True:
            # reading from frame
            ret, frame = cam.read()

            # if frames remaining, continue reading frames
            if ret:
                # send frame to pool worker process
                res = pool.apply_async(f, (frame, currentframe))  # runs in *only* one process
                result = res.get(timeout=1)
                try:
                    if result != 0:
                        # parse encoded time into date
                        qrTimestamp = dateutil.parser.isoparse(result.decode("utf-8"))
                        print(
                            "Frame# "
                            + str(currentframe)
                            + " QR Timestamp: "
                            + qrTimestamp.isoformat().replace("+00:00", "Z")
                            + "\n"
                        )
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
                            raise BreakIt()
                catch(e):
                    pass

                currentframe += 1
            else:
                break

    # Release all space once done
    cam.release()
