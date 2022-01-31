import base64
import threading
from time import sleep
from client_wrapper import client_wrapper
from raw_wrapper import raw_wrapper
from frame import Frame
import cv2
import numpy as np
import pickle
import helper

def capture_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, send_raw_wrap: raw_wrapper, send_raw_lock: threading.Condition):
    count = 0
    #cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
    cond_filled.acquire()
    cap = cv2.VideoCapture("../processing/videos/" + ("lower.mp4" if int(wrap.targetport) == 3001 else "lowercopy.mp4"))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, wrap.resolution)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 680 if wrap.resolution == 480 else (wrap.resolution * 16 / 9))
    cond_filled.release()
    fid = 0
    while True:
        sleep(helper.SLEEP)
        count += 1
        if count > 10000:
            cond_filled.acquire()
            if not wrap.calling:
                cond_filled.release()
                break
            cond_filled.release()
            count = 0
        ret, frame = cap.read()
        # if frame is read correctly ret is True
        
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        #print(type(frame))
        #encoded, buffer = cv2.imencode('.jpg', frame)
        #print(type(data))
        #data = base64.b64encode(buffer)
        data = pickle.dumps(frame, 0)
        f = Frame(data, fid, True)
        #print("captured frame ID: " + str(fid) + " ~ " + str(data)[1:5] + " | len: " + str(len(data)))
        send_raw_lock.acquire()
        send_raw_wrap.framedata.append(f)
        send_raw_lock.release()
        fid += 1