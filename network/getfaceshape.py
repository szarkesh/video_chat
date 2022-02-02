from time import time
import cv2 as cv
import numpy as np
import dlib
from imutils import face_utils
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


def getFrameInfo(detector, predictor, srcColor):
    gray = cv.cvtColor(srcColor, cv.COLOR_BGR2GRAY)
    det = detector(gray, 1)
    if len(det) == 0:
        print("no good match")
        return np.asarray([]), None
    det = det[0]

    shape = predictor(gray, det)
    shape = face_utils.shape_to_np(shape)

    bounding_box = [[det.left(), det.right()], [det.top(), det.bottom()]]

    return shape, bounding_box


if __name__ == "__main__":
    points = getPoints("lower.mp4")
    print(points)
