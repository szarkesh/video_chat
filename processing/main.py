import pickle
import time
import morph
import cv2
import dlib
import cProfile
import re
import numpy as np
from collections import deque


from getfaceshape import getFrameInfo, getPoints


def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    # return the resized image
    return resized


def main():
    srcFile = "example.mov"

    #cap = cv2.VideoCapture("videos/" + srcFile)
    cap = cv2.VideoCapture(0)

    frameIdx = 0
    samplingRate = 60  # sample every x frames
    TARGET_FRAME_RATE = 2
    BEGIN_IMAGE_WIDTH = 720
    IMAGE_WIDTH_OPTIONS = [240, 360, 720]


    quality_index = IMAGE_WIDTH_OPTIONS.index(BEGIN_IMAGE_WIDTH)

    if (quality_index == -1):
        raise ValueError('Beginning image size not in list of sizes')



    lastGoodFrame = None
    lastGoodFramePoints = None

    cv2.namedWindow("1", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("2", cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow("1", -200, 0)
    cv2.moveWindow("2", 600, 0)

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    prev_box = None

    last_frame_time_elapsed = 0

    t = time.time()
    while cap.isOpened():
        temp = time.time()
        last_frame_time_elapsed = temp - t
        t = temp
        if (1 / last_frame_time_elapsed < TARGET_FRAME_RATE and quality_index > 0):
            print('resizing to ', IMAGE_WIDTH_OPTIONS[quality_index-1])
            resize_factor = IMAGE_WIDTH_OPTIONS[quality_index] / IMAGE_WIDTH_OPTIONS[quality_index - 1]
            quality_index -= 1
            lastGoodFrame = image_resize(lastGoodFrame, IMAGE_WIDTH_OPTIONS[quality_index])
            lastGoodFramePoints = (lastGoodFramePoints / resize_factor).astype(int)
            prev_box = (prev_box / resize_factor).astype(int)
            t = time.time()
        # Capture frame-by-frame
        ret, frame = cap.read()
        frame = image_resize(frame, width=IMAGE_WIDTH_OPTIONS[quality_index])
        if ret == True:
            # append local context of frame instead
            points, prev_box = getFrameInfo(detector, predictor, frame, prev_box)
            if frameIdx % samplingRate == 0:
                # only save bounding box of frame here
                lastGoodFrame = frame
                lastGoodFramePoints = points
                print("last good frame face is ", np.mean(lastGoodFramePoints))
            # Display the resulting frame

            # for point in points:
            #     cv2.circle(frame, tuple(point), 2, color=(0, 0, 255), thickness=-1)
            if points is not None:
                output_image = morph.ImageMorphingTriangulation(
                        lastGoodFrame, lastGoodFramePoints, points, 1, 0
                )

            cv2.imshow('1', image_resize(output_image, width=500))

            frameIdx += 1
            # Press Q on keyboard to  exit
            if cv2.waitKey(25) & 0xFF == ord("q"):
                break

        # Break the loop
        else:
            break


if __name__ == "__main__":
    #cProfile.run("main")
    main()
