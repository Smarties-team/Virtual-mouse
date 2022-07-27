
# Lock on the targeted user, i.e. find it's rejoin of interest (ROI) if it exists

from VideoCapture import VideoCapture
import face_recognition
import time
import cv2
from ctypes import c_bool
import math
import autopy


wScr, hScr = autopy.screen.size()


injoo = 'http://192.168.1.32:8080/video'
mi8 = 'http://192.168.1.30:8080/video'

# target-person locking mechanism
def target_person_locking_task(auth, face_rect):
    print("Target-person-locking task started")

    my_photo = 'DiaaEldeen.jpg'
    pTime = 0
    cap = VideoCapture()

    no_detect_count = 0
    no_detect_count_threshold = 3

    my_img = face_recognition.load_image_file(my_photo)
    my_face_encodings = face_recognition.face_encodings(my_img, num_jitters=10)[0]

    # Update face rect every time and always
    # auth should work imed at the first time
    #

    while True:
        time.sleep(0.2)
        ret, img = cap.read()

        if not ret:
            print('none')
            continue

        # image = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(img)

        # Validate existence
        if len(face_locations) < 1:
            no_detect_count = no_detect_count + 1
            if no_detect_count >= no_detect_count_threshold:
                auth.value = False
                no_detect_count = 0
                print("No faces detected")

        else:
            no_detect_count = 0
            face_encodings = face_recognition.face_encodings(
                img, face_locations, num_jitters=1)

            # Iterate over each face in the captured image
            for face_location, face_encoding in zip(face_locations, face_encodings):
                # Extract the face in a separate image
                # top, right, bottom, left = face_location

                # face_image = image[top:bottom, left:right]

                # Compare the unknown face with my face
                matches = face_recognition.compare_faces(
                    [my_face_encodings], face_encoding, 0.7)

                # If match
                if True in matches:
                    first_match_index = matches.index(True)
                    # print('match: ', first_match_index)
                    auth.value = True
                    # face_recognition.face_landmarks(img, [face_location])
                    face_rect[0], face_rect[1], face_rect[2], face_rect[3] = face_location
                    # Draw rect
                    # locs = face_locations[first_match_index]
                    # cv2.rectangle(image, (left, top), (right, bottom),
                    #               (255, 0, 255), 2)
                else:
                    auth.value = False
                    print("Face doesn't match")

        # 11. Frame Rate
        # cTime = time.time()
        # fps = 1 / (cTime - pTime)
        # print(cTime-pTime)
        # pTime = cTime
        # cv2.putText(img, str(int(fps)) + " FPS", (20, 50), cv2.FONT_HERSHEY_PLAIN, 3,
        #             (255, 0, 0), 2)

        # cv2.imshow('task1', img)
        #
        # if cv2.waitKey(1) == ord('q'):
        #     break

    cap.cap.release()
    # cv2.destroyWindow('task1')





def face_to_person_ROI(face_rect):
    top, right, bottom, left = face_rect
    face_width = right - left
    face_height = bottom - top
    face_x_center = left + face_width / 2

    # Width / height ratio
    ratio = 1.2
    face_area = face_width * face_height
    ROI_area = face_area * 40
    ROI_height = int(math.sqrt(ROI_area / ratio))
    ROI_width = int(ROI_area / ROI_height)

    v_left = int(left - ROI_width  / 2)
    v_top = int(top - face_height)
    v_right = v_left + ROI_width
    v_bottom = v_top + ROI_height

    if v_left <= 0:
        v_left = 1

    if v_right >= wScr:
        v_right = wScr - 1

    if v_top <= 0:
        v_top = 1

    if v_bottom >= hScr:
        v_bottom = hScr - 1

    return int(v_left), int(v_top), int(v_right), int(v_bottom)

# Returns a rectangle centered around the wrist x, y position (Relative to face dimensions)
def virtual_screen_ROI(x, y, face_rect, user_ROI_rect):

    # left, top, right, bottom = face_rect
    top, right, bottom, left = face_rect
    user_ROI_left, user_ROI_top, user_ROI_right, user_ROI_bottom = user_ROI_rect
    face_width = right - left
    face_height = bottom - top

    ratio = wScr / hScr
    face_area = face_width * face_height
    vROI_area = face_area * 3.5


    vROI_height = int(math.sqrt(vROI_area / ratio))
    vROI_width = int(vROI_area / vROI_height)

    # ROI_height = int(face_height * 1.5)
    # ROI_width = face_width * 2

    v_left = int(x - vROI_width / 2)
    v_top = int(y - vROI_height / 2)
    v_right = v_left + vROI_width
    v_bottom = v_top + vROI_height

    # It cannot be outside user ROI
    if v_left <= user_ROI_left:
        v_left = user_ROI_left

    if v_right >= user_ROI_right:
        v_right = user_ROI_right-1

    if v_top <= user_ROI_top:
        v_top = user_ROI_top

    if v_bottom >= user_ROI_bottom:
        v_bottom = user_ROI_bottom-1

    return int(v_left), int(v_top), int(v_right), int(v_bottom)
