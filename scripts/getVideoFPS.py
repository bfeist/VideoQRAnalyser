import cv2

cam = cv2.VideoCapture("../vid/IMG_0690.mov")
fps = cam.get(cv2.CAP_PROP_FPS)
print(fps)