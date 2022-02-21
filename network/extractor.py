import threading
import sys
sys.path.append('../processing')
import face_utils
from time import sleep
from frame import Frame
from client_wrapper import client_wrapper 
from raw_wrapper import raw_wrapper
from fin_wrapper import fin_wrapper
import helper
import pickle
import cv2
import mediapipe as mp
#from helper import FLAG_USE_ALL_LANDMARKS

mp_holistic = mp.solutions.holistic
def extractor_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, send_raw_wrap: raw_wrapper, send_raw_lock: threading.Condition, send_fin_wrap: fin_wrapper, send_fin_lock: threading.Condition):
    count = 0
    
    cond_filled.acquire()
    samplingrate = wrap.freshrate
    cond_filled.release()
    with mp_holistic.Holistic(static_image_mode=True, model_complexity=1, enable_segmentation=True, refine_face_landmarks=True) as holistic_detector:
        while True:
            sleep(helper.SLEEP / 5)
            count += 1
            if count > helper.CHECK:
                cond_filled.acquire()
                if not wrap.calling:
                    cond_filled.release()
                    print("Stopping extractor thread...")
                    break
                cond_filled.release()
                count = 0
            send_raw_lock.acquire()
            #Note: may need to insert into send_fin_wrap using some kind of insert function that sorts based on fid (or do this at render time?)
            if len(send_raw_wrap.framedata) > 0:
                f = send_raw_wrap.framedata.pop(0)
                send_raw_lock.release()
                frame = pickle.loads(f.data)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = holistic_detector.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                if results.face_landmarks:
                    mesh_points=face_utils.get_landmarks_to_np(results.face_landmarks, image.shape[1],image.shape[0], True)
                    #if results.pose_landmarks:
                        #body_points = face_utils.get_landmarks_to_np(results.pose_landmarks, image.shape[1],
                                                                        #image.shape[0], True)
                    #points, bound_box = getFrameInfo(detector, predictor, frame)
                    #ptsframe = Frame(pickle.dumps({mesh: mesh_points, body: body_points}, 0), f.fid, True)
                    ptsframe = Frame(pickle.dumps(mesh_points, 0), f.fid, True)
                    send_fin_lock.acquire()
                    #if f.fid % samplingrate == 0:
                    send_fin_wrap.framedata.append(f)
                    send_fin_wrap.featuredata.append(ptsframe)
                    send_fin_lock.release()
                    print("extracted frame: " + str(f.fid) + " ~ " + str(f.data)[1:5] + " | len: " + str(len(f.data)))
            else:
                send_raw_lock.release()