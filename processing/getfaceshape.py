import cv2 as cv
import numpy as np
import dlib
from imutils import face_utils
import pickle


def getPoints(vName):

    v = cv.VideoCapture("videos/"+vName)

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    points = []

    frame = 0
    while (True):
        print(frame)
        frame+=1
        ret, srcColor = v.read()
        if(ret):
            cv.imshow("srccolor", srcColor)
            gray = cv.cvtColor(srcColor, cv.COLOR_BGR2GRAY)
            det = detector(gray, 1)

            if (len(det) == 0):
                print('no good match')
                points.append(np.asarray([]))
                continue
            det = det[0]

            shape = predictor(gray, det)
            shape = face_utils.shape_to_np(shape)

            points.append(shape)
        else:
            break

    pickle.dump(points, open("facepts/"+vName.split(".")[0]+".pkl", "wb"))



if(__name__=="__main__"):
    points = getPoints("example.mov")
    print(points)
