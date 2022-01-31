import threading
from time import sleep
from client_wrapper import client_wrapper
from fin_wrapper import fin_wrapper
import cv2
import numpy as np
import pickle
import helper

def render_thread_func(wrap: client_wrapper, cond_filled:  threading.Condition, recv_fin_wrap: fin_wrapper, recv_fin_lock: threading.Condition):
    print("Creating Window...")
    cond_filled.acquire()
    windname = "video" + str(wrap.targetport)[3]
    cv2.namedWindow(windname, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(windname, 680 if wrap.resolution == 480 else (wrap.resolution * 16 / 9), wrap.resolution)
    cond_filled.release()
    count = 0
    while True:
        sleep(helper.SLEEP)
        helper.cprint("Waiting to render...")
        count += 1
        if count > 10000:
            cond_filled.acquire()
            if not wrap.calling:
                cond_filled.release()
                break
            cond_filled.release()
            count = 0
        recv_fin_lock.acquire()
        length = len(recv_fin_wrap.framedata)
        helper.cprint(str(length) + " frames ready")
        recv_fin_lock.release()
        if length > 0:
            recv_fin_lock.acquire()            
            f = recv_fin_wrap.framedata.pop(0)
            recv_fin_lock.release()
            helper.cprint("Rendering FID: " + str(f.fid))
            #nparr = np.fromstring(f.data, dtype=np.uint8)
            #frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            frame = pickle.loads(f.data)
            image = cv2.putText(frame, "Frame: " + str(f.fid), (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow(windname, image)
            #cv2.waitKey(0)
            cv2.waitKey(25)
            helper.cprint("rendered frame: " + str(f.fid))