import pickle
import time
import morph
import cv2
import cProfile
import re
import numpy as np
from enum import Enum
from collections import deque
import face_utils

#from getfaceshape import getFrameInfo, getPoints

import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
drawSpecCircle = mp.solutions.drawing_utils.DrawingSpec(thickness=0, circle_radius=0, color=(0, 0, 255))
mp_face_mesh = mp.solutions.face_mesh
mp_selfie_segmentation = mp.solutions.selfie_segmentation
mp_holistic = mp.solutions.holistic




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



def get_most_similar_frame_idx(meshes, curr_mesh):
    similarities = [face_utils.mesh_similarity(mesh, curr_mesh) for mesh in meshes]
    return max((x, i) for i, x in enumerate(similarities))[1] # position of highest similarity


def main():
    srcFile = "example.mov"

    #cap = cv2.VideoCapture("videos/" + srcFile)
    #cap = cv2.VideoCapture(0)
    cap = cv2.VideoCapture('../network/rayvideo.mp4')
    frameIdx = 0
    samplingRate = 60  # sample every x frames
    TARGET_FRAME_RATE = 2
    BEGIN_IMAGE_WIDTH = 720
    IMAGE_WIDTH_OPTIONS = [240, 360, 720]
    FLAG_AUTO_RESIZE = False
    FLAG_USE_ALL_LANDMARKS = False

    BODY_THRESH = 0.4 # affects what pieces of the body you think are real.


    quality_index = IMAGE_WIDTH_OPTIONS.index(BEGIN_IMAGE_WIDTH)

    if (quality_index == -1):
        raise ValueError('Beginning image size not in list of sizes')



    lastGoodFrame = None
    lastGoodFramePoints = None

    cv2.namedWindow("1", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("2", cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow("1", -200, 0)
    cv2.moveWindow("2", 600, 0)

    prev_box = None

    last_frame_time_elapsed = 0

    calibration_frames = []
    calibration_meshes = []
    calibration_poses = []
    calibration_masks = []
    background_frame = None
    prompts = ['Show a neutral face'] #,'Now show a smile', 'Now show us your eyes closed','Now show your mouth half open', 'Now open your mouth more!', 'Now do a half smile', 'Now purse your lips']

    is_calibrating = True
    prompt_index = 0
    first = True
    t = time.time()
    with mp_holistic.Holistic(static_image_mode=True, model_complexity=1, enable_segmentation=True, refine_face_landmarks=True) as holistic_detector:
        while cap.isOpened():
            ret, frame = cap.read()
            frame = image_resize(frame, width=IMAGE_WIDTH_OPTIONS[quality_index])
            if is_calibrating:
                if background_frame is None:
                    display_frame = frame.copy()
                    cv2.putText(display_frame, "Leave the viewport and \n press N to continue.", (100, 100), fontFace=cv2.FONT_HERSHEY_PLAIN,
                                fontScale=1.2, color=(255, 255, 255))
                    cv2.imshow('1', display_frame)

                    if cv2.waitKey(1) & 0xFF == ord('n'):
                        background_frame = frame
                else:
                    if ret == True:
                        display_frame = frame.copy()
                        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        image.flags.writeable = False
                        results = holistic_detector.process(image)
                        image.flags.writeable = True
                        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                        if results.face_landmarks:
                            mp_drawing.draw_landmarks(image=display_frame, landmark_list=results.face_landmarks, landmark_drawing_spec=drawSpecCircle)
                            thresh_mask = (results.segmentation_mask > BODY_THRESH).astype('uint8')
                        if results.pose_landmarks:
                            mp_drawing.draw_landmarks(
                                display_frame,
                                results.pose_landmarks,
                                mp_holistic.POSE_CONNECTIONS,
                                landmark_drawing_spec=mp_drawing_styles.
                                    get_default_pose_landmarks_style())
                        else:
                            print('unable to find face')
                        cv2.putText(display_frame, prompts[prompt_index], (100,100), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1.2, color=(255,255,255))
                        cv2.imshow('1', display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('n'):
                        if results.face_landmarks:
                            prompt_index += 1
                            calibration_frames.append(image)
                            face_pts = face_utils.get_landmarks_to_np(results.face_landmarks, image.shape[1], image.shape[0], FLAG_USE_ALL_LANDMARKS)
                            body_pts = face_utils.get_landmarks_to_np(results.pose_landmarks, image.shape[1],
                                                                      image.shape[0], FLAG_USE_ALL_LANDMARKS)
                            print(body_pts)
                            calibration_masks.append(thresh_mask)
                            calibration_meshes.append(face_pts)
                            calibration_poses.append(body_pts)
                            calibration_masks.append(results.segmentation_mask)
                            print('face_pts have eye openness', face_utils.eye_openness(face_pts))
                            if prompt_index >= len(prompts):
                                is_calibrating = False
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            else:
                temp = time.time()
                last_frame_time_elapsed = temp - t
                t = temp
                if (FLAG_AUTO_RESIZE and 1 / last_frame_time_elapsed < TARGET_FRAME_RATE and quality_index > 0):
                    print('resizing to ', IMAGE_WIDTH_OPTIONS[quality_index-1])
                    resize_factor = IMAGE_WIDTH_OPTIONS[quality_index] / IMAGE_WIDTH_OPTIONS[quality_index - 1]
                    quality_index -= 1
                    lastGoodFrame = image_resize(lastGoodFrame, IMAGE_WIDTH_OPTIONS[quality_index])
                    lastGoodFramePoints = (lastGoodFramePoints / resize_factor).astype(int)
                    prev_box = (prev_box / resize_factor).astype(int)
                    t = time.time()
                if ret == True:
                    # append local context of frame instead
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image.flags.writeable = False
                    results = holistic_detector.process(image)
                    image.flags.writeable = True
                    image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    if results.face_landmarks:
                        mesh_points=face_utils.get_landmarks_to_np(results.face_landmarks, image.shape[1],image.shape[0],FLAG_USE_ALL_LANDMARKS)
                    if results.pose_landmarks:
                        body_points = face_utils.get_landmarks_to_np(results.pose_landmarks, image.shape[1],
                                                                     image.shape[0], FLAG_USE_ALL_LANDMARKS)
                    else:
                        print('results no workie')
                        continue
                    if mesh_points is not None:
                        calibration_img_idx = get_most_similar_frame_idx(calibration_meshes, mesh_points)
                        pasted_body = morph.PasteBody(background_frame, calibration_frames[0], calibration_meshes[0], calibration_masks[0], mesh_points)
                        # print("Calibration Img IDX: " + str(calibration_img_idx))
                        # print("Calibration Frame: ")
                        # print(type(calibration_frames[calibration_img_idx]))
                        # print(calibration_frames[calibration_img_idx].shape)
                        # print("--------------------------------------------------")
                        # print("Calibration mesh:")
                        # print(type(calibration_meshes[calibration_img_idx]))
                        # print(calibration_meshes[calibration_img_idx].shape)
                        # print("--------------------------------------------------")
                        # print("Current Mesh: ")
                        # print(type(mesh_points))
                        # print(mesh_points)
                        output_image = morph.ImageMorphingTriangulation(
                                calibration_frames[calibration_img_idx], calibration_meshes[calibration_img_idx], mesh_points, 1, pasted_body, FLAG_USE_ALL_LANDMARKS
                        )

                        #output_image = frame
                        cv2.putText(output_image, "FPS: " + str(int(1/last_frame_time_elapsed)), (100, 100), fontFace=cv2.FONT_HERSHEY_PLAIN,
                                    fontScale=1.2, color=(255, 255, 255))

                    cv2.imshow('1', output_image)
                    #cv2.imshow('2', image_resize(frame, width=500))

                    frameIdx += 1
                    # Press Q on keyboard to  exit
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                # Break the loop
                else:
                    break


if __name__ == "__main__":
    #cProfile.run("main")
    main()
