# Automated Time Sync Detector

This app looks for QR codes that contain timecodes embedded and returns the exact start time of the video. QR codes are generated via this app: https://apolloinrealtime.org/coda_clocksync/

# To Run
Tested on Python 3.8.2

Required pip packages:
- `pip install opencv-python` (https://pypi.org/project/opencv-python/)
- `pip install pyzbar`

To run
Open terminal in /scripts folder and run `python decodeQRFromVideo.py`  This will look for a hardcoded sample video file in a /vid subfolder. Your sample video should be of you holding up your phone running this page: https://apolloinrealtime.org/coda_clocksync/

