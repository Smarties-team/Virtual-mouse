import cv2
import mediapipe as mp
import time
import math
import numpy as np
from enum import Enum

injoo = 'http://192.168.1.32:8080/video'
mi8 = 'http://192.168.1.30:8080/video'

lion_video = 'lion.mp4'
people_video = 'people.mp4'
basket_video = 'basket.mp4'
hand = 'hand1.m4a'


class FingerState(Enum):
    Bent = 1
    Straight = 2


# Measure angle between two lines
def getAngleABC(a_x, a_y, b_x, b_y, c_x, c_y):

    ab_x = b_x - a_x;
    ab_y = b_y - a_y;
    cb_x = b_x - c_x;
    cb_y = b_y - c_y;

    dot = (ab_x * cb_x + ab_y * cb_y)   # dot product
    cross = (ab_x * cb_y - ab_y * cb_x) # cross product
    alpha = math.atan2(cross, dot)

    return alpha


def radianToDegree(radian):
    M_PI = math.pi
    return int (math.floor(radian * 180. / M_PI + 0.5))


class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.6):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = float(detectionCon)
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(bool(self.mode), int(self.maxHands), 1,
                                        detectionCon, trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img.flags.writeable = False # For faster processing ?!
        self.results = self.hands.process(imgRGB)
        img.flags.writeable = True
        # print(results.multi_hand_landmarks)

        handedness = ''
        if self.results.multi_hand_landmarks:
            # Check handedness (It's inverted !)
            handed = self.results.multi_handedness[0]
            if handed.classification[0].label == 'Left':
                handedness = 'Right'
            else:
                handedness = 'Left'

            # Draw on landmarks
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)

        return img, handedness

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        bbox = []
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                # print(id, lm)
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                # print(id, cx, cy)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 2, (255, 0, 255), cv2.FILLED)

            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax

            if draw:
                cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20),
                              (0, 255, 0), 2)

        return self.lmList, bbox


    def fingersUp(self):
        fingers = []
        # Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Fingers
        for id in range(1, 5):
            # The tip minus  the point under it
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 1][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        # totalFingers = fingers.count(1)

        return fingers

    # def fingersUp(self):
    #     fingers = []
    #     # Thumb
    #     if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
    #         fingers.append(1)
    #     else:
    #         fingers.append(0)
    #
    #     # Fingers
    #     for id in range(1, 5):
    #         # The tip minus  the point under it
    #         if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 1][2]:
    #             fingers.append(1)
    #         else:
    #             fingers.append(0)
    #
    #     # totalFingers = fingers.count(1)
    #
    #     return fingers

    def is_fingers_open(self):
        fingers = []
        # Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Fingers
        for id in range(1, 5):

            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        # totalFingers = fingers.count(1)

        return fingers

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        length = math.hypot(x2 - x1, y2 - y1)

        return length, img, [x1, y1, x2, y2, cx, cy]


def main():
    pTime = 0
    cTime = 0
    cap = cv2.VideoCapture(mi8)
    detector = handDetector()
    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        if len(lmList) != 0:
            print(lmList[4])

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 255), 3)

        cv2.imshow("Image", img)
        if cv2.waitKey(1) == ord('q'):
            break


if __name__ == "__main__":
    main()

