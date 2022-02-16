from scipy import spatial
from enum import IntEnum
import numpy as np
import cv2

class face_pts(IntEnum):
    NOSE_BOTTOM = 94
    FACE_TOP = 10
    LEFT_EYE_TOP = 159
    LEFT_EYE_BOTTOM = 145
    RIGHT_EYE_TOP = 386
    RIGHT_EYE_BOTTOM = 374
    MOUTH_LEFT = 61
    MOUTH_RIGHT = 291
    MOUTH_TOP = 0
    MOUTH_BOTTOM = 17
    FACE_LEFT = 234
    FACE_RIGHT = 454

LANDMARK_SUBSET = np.asarray(list(filter(lambda x: x % 3 == 0 or x >= 468, range(478))))


# relevant points for the body
BODY_SUBSET = [12,11,8,7]
FACE_POSE_SUBSET = [234, 54, 251, 356, 197, 107, 336, 296, 283]
def eye_openness(mesh):
    face_height = mesh[face_pts.NOSE_BOTTOM][1] - mesh[face_pts.FACE_TOP][1]
    left_openness = (mesh[face_pts.LEFT_EYE_BOTTOM][1] - mesh[face_pts.LEFT_EYE_TOP][1]) / face_height * 5
    right_openness = (mesh[face_pts.RIGHT_EYE_BOTTOM][1] - mesh[face_pts.RIGHT_EYE_TOP][1]) / face_height * 5
    return (left_openness + right_openness) / 2

def mouth_openness(mesh):
    face_height = mesh[face_pts.NOSE_BOTTOM][1] - mesh[face_pts.FACE_TOP][1]
    return (mesh[face_pts.MOUTH_BOTTOM][1] - mesh[face_pts.MOUTH_TOP][1]) / face_height

def mouth_width(mesh):
    face_width = mesh[face_pts.FACE_RIGHT][0] - mesh[face_pts.FACE_LEFT][0]
    return (mesh[face_pts.MOUTH_RIGHT][0] - mesh[face_pts.MOUTH_LEFT][0]) / face_width

def mesh_similarity(mesh1, mesh2):
    features1 = [eye_openness(mesh1), mouth_openness(mesh1), mouth_width(mesh1)]
    features2 = [eye_openness(mesh2), mouth_openness(mesh2), mouth_width(mesh2)]
    return 1 - spatial.distance.cosine(features1, features2)

def get_landmarks_to_np(landmarks, width, height, use_all = True):
    all_landmarks = np.array([np.multiply([p.x, p.y], [width, height]).astype(int) for p in
              landmarks.landmark])
    return all_landmarks