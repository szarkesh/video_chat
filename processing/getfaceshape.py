from time import time
import cv2 as cv
import numpy as np
import dlib
from imutils import face_utils
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh
import pickle


def getPoints(vName):
    start = time()
    v = cv.VideoCapture("videos/" + vName)

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    points = []

    frame = 0
    while True:
        print(frame)
        frame += 1
        ret, srcColor = v.read()
        if ret:
            cv.imshow("srccolor", srcColor)
            frame_points, bound_box = getFrameInfo(detector, predictor, srcColor)
            points.append(frame_points)
        else:
            break
    end = time()
    print(end - start)
    # pickle.dump(points, open("facepts/"+vName.split(".")[0]+".pkl", "wb"))
    return points


def getFrameInfo(detector, predictor, srcColor, prev_box = None):
    left = 0
    top = 0
    if prev_box is not None: # hint for where to look for the face
        prev_width = prev_box[1][1] - prev_box[1][0]
        prev_height = prev_box[0][1] - prev_box[0][0]

        left = prev_box[0][0] - int(prev_width / 10)
        right = prev_box[0][1] + int(prev_width / 10)
        top = prev_box[1][0] - int(prev_height / 10)
        bottom = prev_box[1][1] + int(prev_height / 10)
        gray = cv.cvtColor(srcColor[top:bottom,left:right], cv.COLOR_RGB2GRAY)
    else:
        gray = cv.cvtColor(srcColor, cv.COLOR_RGB2GRAY)

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
    )
    #det = detector(gray, 1)
    # if len(det) == 0:
    #     print("no good match")
    #     return None, None
    #det = det[0]

    #shape = predictor(gray, det)
    shape = face_utils.shape_to_np(shape)
    shape = shape + np.asarray([left, top])
    bounding_box = np.asarray([[det.left() + left, det.right() + left], [det.top() + top, det.bottom() + top]])

    return shape, bounding_box


if __name__ == "__main__":
    points = getPoints("lower.mp4")
    print(points)
