import threading
from client_wrapper import client_wrapper
from fin_wrapper import fin_wrapper
import cv2
import numpy as np

def render_thread_func(wrap: client_wrapper, cond_filled:  threading.Condition, recv_fin_wrap: fin_wrapper, recv_fin_lock: threading.Condition):
    print("Creating Window...")
    cond_filled.acquire()
    windname = "video" + str(wrap.targetport)[3]
    cv2.namedWindow(windname, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(windname, 680 if wrap.resolution == 480 else (wrap.resolution * 16 / 9), wrap.resolution)
    cond_filled.release()
    count = 0
    while True:
        print("Waiting to render...")
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
        print(str(length) + " frames ready")
        recv_fin_lock.release()
        if length > 0:            
            f = recv_fin_wrap.framedata.pop(0)
            print("Rendering: " + str(f.fid))
            nparr = np.fromstring(f.data, dtype=np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            cv2.imshow(windname, frame)
            cv2.waitKey(0)
            print("rendered frame: " + str(f.fid))