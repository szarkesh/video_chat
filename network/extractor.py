import threading
from time import sleep
from client_wrapper import client_wrapper 
from raw_wrapper import raw_wrapper
from fin_wrapper import fin_wrapper
import helper
import dlib
import pickle
from getfaceshape import getFrameInfo

def extractor_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, send_raw_wrap: raw_wrapper, send_raw_lock: threading.Condition, send_fin_wrap: fin_wrapper, send_fin_lock: threading.Condition):
    count = 0
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    while True:
        sleep(helper.SLEEP)
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
            points, bound_box = getFrameInfo(detector, predictor, frame)
            send_fin_lock.acquire()
            send_fin_wrap.framedata.append(f)
            send_fin_wrap.featuredata.append(points)
            send_fin_lock.release()
            helper.cprint("extracted frame: " + str(f.fid) + " ~ " + str(f.data)[1:5] + " | len: " + str(len(f.data)))
        else:
            send_raw_lock.release()