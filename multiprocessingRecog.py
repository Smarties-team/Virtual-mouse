
import os
import multiprocessing
from ctypes import c_bool
import cv2
import numpy as np
import math

import HandTracking as htm
from HandTracking import FingerState
from HandTracking import getAngleABC
from HandTracking import radianToDegree
import time
import autopy
from pynput.mouse import Button, Controller

import mediapipe as mp
import winsound
from VideoCapture import VideoCapture
import TargetLocking



mouse = Controller()

##########################
wCam, hCam = 640, 480
frameR = 100  # Frame Reduction
smoothening = 3
user_handedness = 'Right'
#########################

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
prevX, prevY = 0, 0

injoo = 'http://192.168.1.32:8080/video'
mi8 = 'http://192.168.1.30:8080/video'

hand = 'hand1.m4a'

wScr, hScr = autopy.screen.size()
# wScr, hScr = pyautogui.size()


def handtrackTask(auth, face_rect):
    print("Hand tracking task")

    unlock_sound = 'sounds/isOn.wav'
    click_sound = 'sounds/click.wav'
    release_sound = 'sounds/release.wav'
    slide_sound = 'sounds/slide.wav'
    lock_sound = 'sounds/lock.wav'

    pTime = 0
    clickState = False
    movingState = False
    isIndexBent = False
    isMidBent = False
    prevIndexState = FingerState.Straight
    prevMidState = FingerState.Straight
    leftClickState = False
    rightClickState = False
    plocX, plocY = 0, 0
    clocX, clocY = 0, 0
    prevX, prevY = 0, 0
    wScr, hScr = autopy.screen.size()
    wCam, hCam = 640, 480

    frame_count = 0
    time_count = 0
    open_count = 0
    close_count = 0
    open_count_threshold = 3
    close_count_threshold = 2
    scroll_count = 0
    scroll_state = False
    scroll_count_threshold = 3
    click_state_count = 0
    click_state_count_threshold = 3
    auth_count = 0
    prev_fingers = []
    auth_count_threshold = 2
    is_auth = False
    isOn = False
    handedness_count = 0
    handedness_count_threshold = 6

    detector = htm.handDetector(trackCon=0.8, maxHands=1, detectionCon=0.9)
    cap = cv2.VideoCapture(mi8)

    wCam = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    hCam = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    ROI = frameR, frameR, wCam - frameR, hCam - frameR  # Initial virtual screen ROI
    user_ROI = 0, 0, wCam, hCam  # Initial user ROI

    # success, img = cap.read()

    # cut_ROI = []
    # if success:
    #     cut_ROI = cv2.selectROI('Select ROI', img)

    # print(cut_ROI)
    # cropped = img[top:bottom, left:right]
    success = True
    img = []
    success, img = cap.read()
    while cap.isOpened():
        if not success:
            continue
        # 12. Display
        cv2.imshow("Image", img)

        if cv2.waitKey(1) == ord('q'):
            break

        # 1. Find hand Landmarks
        success, img = cap.read()

        # Disable the mouse in case of consecutive frames of unrecognized user.
        if auth.value is True:
            is_auth = True
            # Find user's ROI
            user_ROI = TargetLocking.face_to_person_ROI(face_rect)
            auth_count = 0
        else:
            auth_count = auth_count + 1
            if auth_count >= auth_count_threshold:
                is_auth = False
                auth_count = 0
                # Check if mouse clicked, release it

        if not is_auth:
            continue


        # TODO Set Crop the image limits but inside unlocking mode
        # ROI rectangle
        # user_ROI = face_to_person_ROI(face_rect)
        ROI_left, ROI_top, ROI_right, ROI_bottom = user_ROI
        # ROI_right = int(ROI_right)
        # ROI_bottom = int(ROI_bottom)
        # cropped = img[ROI_top:ROI_bottom, ROI_left:ROI_right]
        img, handedness = detector.findHands(img)

        # Check user handedness, Mouse can only be controlled by the specified hand
        if handedness != user_handedness:
            handedness_count = handedness_count + 1
            if handedness_count >= handedness_count_threshold:
                continue
        else:
            handedness_count = 0

        lmList, bbox = detector.findPosition(img)



        # TODO Mouse disappears due to lm list not available, Use interpolation

        # print(auth.value,", face rect: ", face_rect[0])
        # Ignore mouse control if either authentication fails or hand tracking fails
        if len(lmList) != 0 and is_auth:
            # 2. Get the tip of the index and middle fingers
            # x1, y1 = lmList[8][1:]
            x1, y1 = lmList[0][1:]
            x2, y2 = lmList[12][1:]

            # left, top, width, height = cut_ROI
            # right = width + left
            # bottom = height + top
            # cv2.rectangle(img, (left, top), (right, bottom),
            #               (255, 0, 255), 2)

            # find ROI
            # ROI = virtual_screen_ROI(face_rect)
            # print(ROI)

            # 3. Check which fingers are up
            fingers = detector.fingersUp()
            # print(fingers)

            # All fingers open for open_count_threshold frames -> Unlock,
            # Use fingers open functions metric
            # Check x coordinates difference between middle and wrist
            # Check hand orientation (Angle between bottom of the mid-finger and wrist)
            x_diff = lmList[12][1] - lmList[0][1]
            wrist = lmList[0]
            MCP_of_middle_finger = lmList[9]

            ang_in_radian = getAngleABC(MCP_of_middle_finger[1], MCP_of_middle_finger[2], wrist[1], wrist[2],
                                        wrist[1] + 0.1, wrist[2])

            ang_in_degree = radianToDegree(ang_in_radian)

            # print(ang_in_degree)
            # 3 kinds of checks for robustness
            if fingers == [1, 1, 1, 1, 1] \
                    and 60 < ang_in_degree < 120 \
                    and -24 < x_diff < 24:
                movingState = False
                open_count = open_count + 1
                # print(open_count)
                # lmList[12], lmList[0]
                # print('x: ', lmList[12][1] - lmList[0][1], ', y: ', lmList[12][2] - lmList[0][2])
                # print(ang_in_degree)
                if open_count >= open_count_threshold:
                    if isOn is False:
                        # playsound(unlock_sound, False)
                        winsound.PlaySound(unlock_sound, winsound.SND_ASYNC | winsound.SND_ALIAS)
                    isOn = True
                    # Find ROI based on current hand position
                    ROI = TargetLocking.virtual_screen_ROI(x1, y1, face_rect, user_ROI)
                    plocX = x1  # Start mouse movement from center
                    plocY = y1  # Start mouse movement from center
                    open_count = 0
                    close_count = 0

            # All fingers closed for close_count_threshold frames -> lock
            elif fingers == [0, 0, 0, 0, 0]:
                movingState = False
                close_count = close_count + 1
                if close_count >= close_count_threshold:
                    if isOn is True:
                        winsound.PlaySound(lock_sound, winsound.SND_ASYNC | winsound.SND_ALIAS)
                    isOn = False
                    close_count = 0
                    open_count = 0
            else:
                open_count = 0
                close_count = 0

            # Reset mouse clicks when they happen by mistake
            if fingers == [1, 1, 1, 1, 1] or fingers == [0, 0, 0, 0, 0]:
            # Check if mouse is pressed, release it
                if leftClickState:
                    mouse.release(Button.left)
                    leftClickState = False
                if rightClickState:
                    mouse.release(Button.right)
                    rightClickState = True

            # print(fingers)
            # Slide back
            if fingers == [1, 0, 0, 0, 0] and prev_fingers == [0, 0, 0, 0, 0]:
                autopy.key.tap(autopy.key.Code.LEFT_ARROW)
                winsound.PlaySound(slide_sound, winsound.SND_ASYNC | winsound.SND_ALIAS)
                print('slide back')
            # Slide forward
            elif fingers == [0, 0, 0, 0, 1] and prev_fingers == [0, 0, 0, 0, 0]:
                autopy.key.tap(autopy.key.Code.RIGHT_ARROW)
                winsound.PlaySound(slide_sound, winsound.SND_ASYNC | winsound.SND_ALIAS)
                print('slide forward')

            # Virtual screen (ROI) mouse movement area
            left, top, right, bottom = ROI
            # cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
            #               (255, 0, 255), 2)
            right = int(right)
            bottom = int(bottom)
            # print(ROI)
            cv2.rectangle(img, (left, top), (right, bottom),
                          (255, 0, 255), 2)

            prev_fingers = fingers

            # click_distance = math.dist((lmList[8][1], lmList[8][2]),(lmList[4][1], lmList[4][2]))
            # print(click_distance, lmList[8][2] - lmList[4][2])
            # print(click_distance)
            if isOn:
                # Both fingers bent: Scroll
                if fingers == [0, 1, 1, 1, 0]:
                    movingState = False
                    scroll_count = scroll_count + 1
                    if scroll_count >= scroll_count_threshold:
                        scroll_state = True
                        scroll_count = 0

                    if scroll_state is True:
                        # y3 = np.interp(y1, (top, bottom), (0, hScr))
                        # # 6. Smoothen Values
                        # f = 10
                        #
                        # clocY = plocY + (y3 - plocY) / f
                        #
                        # # 7. Scroll
                        # # mouse.scroll(0, -(y3 - plocY) / f)
                        # mouse.scroll(0, -(y1 - prevY) / f)
                        #
                        # cv2.circle(img, (x1, y1), 10, (0, 0, 255), cv2.FILLED)
                        # plocX, plocY = clocX, clocY
                        # prevY = y1
                        print('scroll')
                        # mouse.scroll(0, 2)  # Scroll two steps down

                # 8. Index is bent: left click press
                elif lmList[8][2] - lmList[4][2] > -7 and prevIndexState is FingerState.Straight\
                        and movingState is True:

                    mouse.press(Button.left)
                    winsound.PlaySound(click_sound, winsound.SND_ASYNC | winsound.SND_ALIAS)
                    prevIndexState = FingerState.Bent
                    leftClickState = True
                    click_state_count = 0
                    movingState = False
                    print('press left')

                # Index finger stretched: release left click
                elif lmList[8][2] - lmList[4][2] < -15 and leftClickState is True:
                    mouse.release(Button.left)
                    leftClickState = False
                    prevIndexState = FingerState.Straight
                    print('release left')

                # Middle finger is bent: right click press
                elif lmList[12][2] - lmList[4][2] > -7 and prevMidState is FingerState.Straight\
                        and movingState is True:
                    mouse.press(Button.right)
                    winsound.PlaySound(click_sound, winsound.SND_ASYNC | winsound.SND_ALIAS)
                    rightClickState = True
                    click_state_count = 0
                    prevMidState = FingerState.Bent
                    movingState = False
                    print('press right')

                # Middle finger stretched: release right click
                elif lmList[12][2] - lmList[4][2] < -15 and prevMidState is FingerState.Bent:
                    mouse.release(Button.right)
                    rightClickState = False
                    prevMidState = FingerState.Straight
                    print('release right')

                # 4. Either Index and middle fingers up or only index, or during a click press
                if fingers == [0, 1, 1, 0, 0] or fingers == [1, 1, 1, 0, 0] \
                        or leftClickState or rightClickState:
                    if leftClickState or rightClickState:
                        click_state_count = click_state_count + 1

                    if click_state_count > click_state_count_threshold\
                            or (not leftClickState and not rightClickState):
                        # 5. Convert Coordinates
                        locX = np.interp(x1, (left, right), (0, wScr))
                        locY = np.interp(y1, (top, bottom), (0, hScr))
                        # print(top, bottom)
                        # print(x3)
                        # 6. Smoothen Values
                        # plocX, plocY = autopy.mouse.location()
                        # print(plocX, plocY)
                        dx = locX - plocX
                        dy = locY - plocY
                        distanceSquared = dx ** 2 + dy ** 2
                        # Ignore small movements for stability
                        if(distanceSquared <= 100):
                            clocX = plocX
                            clocY = plocY
                        else:
                            clocX = plocX + dx / smoothening
                            clocY = plocY + dy / smoothening
                        # print(y3 - plocY)

                        # print(y3)
                        if clocX >= wScr:
                            print('clocX', clocX)
                            clocX = wScr
                        elif clocX <= 0:
                            print('clocX', clocX)
                            clocX = 0

                        if clocY >= hScr:
                            print('clocY', clocY)
                            clocY = hScr
                        elif clocY <= 0:
                            print('clocY', clocY)
                            clocY = 0

                        # print(clocX, clocY)
                        # 7. Move Mouse
                        try:
                            autopy.mouse.move(wScr - clocX, clocY)
                        except:
                            print('Autopy mouse movement error')
                            print(clocX, clocY)

                        cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
                        plocX, plocY = clocX, clocY

                    movingState = True
                    scroll_state = False

        else:
            open_count = 0
            close_count = 0
            movingState = False
            scroll_state = False

        # 11. Frame Rate
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, str(int(fps)) + " FPS", (20, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 0), 2)

        # Face rectangle
        top, right, bottom, left = face_rect
        cv2.rectangle(img, (left, top), (right, bottom), (255, 0, 255), 2)

        # ROI rectangle
        ROI_left, ROI_top, ROI_right, ROI_bottom = user_ROI
        ROI_right = int(ROI_right)
        ROI_bottom = int(ROI_bottom)
        cv2.rectangle(img, (ROI_left, ROI_top), (ROI_right, ROI_bottom), (255, 0, 255), 2)

        # 12. Display
        # cv2.imshow("Image", img)
        #
        # if cv2.waitKey(1) == ord('q'):
        #     break
        # print(fps)
    cap.release()
    cv2.destroyAllWindows()


# TODO scroll doesn't reset after restarting it
# TODO Lag

if __name__ == "__main__":
    print("Main function start")

    # Interprocess communication variables
    auth = multiprocessing.Value(c_bool, False)
    face_rect = multiprocessing.Array('i', 4)

    # creating processes
    target_person_locking_t = multiprocessing.Process(target=TargetLocking.target_person_locking_task, args=(auth, face_rect))
    handtrackT = multiprocessing.Process(target=handtrackTask, args=(auth, face_rect))

    # starting threads
    target_person_locking_t.start()
    handtrackT.start()

    # wait until all threads finish
    target_person_locking_t.join()
    handtrackT.join()

    print("end")


