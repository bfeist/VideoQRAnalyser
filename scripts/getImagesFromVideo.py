# Importing all necessary libraries
import cv2
import os

# Read the video from specified path
cam = cv2.VideoCapture("../vid/IMG_0690_1080p.mov")

imageOutputPath = '../tmp'

try:
    # creating a folder named data
    if not os.path.exists(imageOutputPath):
        os.makedirs(imageOutputPath)

    # if not created then raise error
except OSError:
    print ('Error: Creating output directory')

# frame
currentframe = 0

while(True):

    # reading from frame
    ret,frame = cam.read()

    if ret:
        # if video is still left continue creating images
        name = '/frame' + str(currentframe).rjust(4, '0') + '.jpg'
        print ('Creating...' + name)

        # writing the extracted images
        cv2.imwrite(imageOutputPath + name, frame)

        currentframe += 1
    else:
        break

# Release all space and windows once done
cam.release()
# cv2.destroyAllWindows()