
# This module uses multithreading to read the image frames from the video capture continuously
# in the background, so the that it provides the latest frame to the user

import threading
import queue
import cv2

injoo = 'http://192.168.1.32:8080/video'
mi8 = 'http://192.168.1.30:8080/video'
laptop_camera = 0       # or 1
streaming_device = mi8



# cap.set(3, wCam)
# cap.set(4, hCam)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, wCam)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hCam)

class VideoCapture:

    def __init__(self, name=streaming_device):
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()

    def _reader(self):
        while self.cap.isOpened():
            # Append new frame to the queue (Remove old one if exists)
            # print('thread read')
            ret, frame = self.cap.read()
            if not ret:
                continue
            if not self.q.empty():
                try:
                    self.q.get_nowait() # discard previous unprocessed frame
                except queue.Empty:
                    pass

            self.q.put(frame)

    def read(self):
        if self.q.empty():
            return False, None
        else:
            return True, self.q.get()