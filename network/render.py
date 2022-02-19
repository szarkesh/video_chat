from multiprocessing import Array
import threading
from time import sleep, time
from client_wrapper import client_wrapper
from fin_wrapper import fin_wrapper
import cv2
import numpy as np
import pickle
import helper
from raw_wrapper import raw_wrapper

def render_thread_func(wrap: client_wrapper, cond_filled:  threading.Condition, recv_fin_wrap: fin_wrapper, recv_fin_lock: threading.Condition, prompts, recv_raw_wrap: raw_wrapper):
    print("Creating Window...")
    cond_filled.acquire()
    windname = "video" + str(wrap.targetport)[3]
    cv2.namedWindow(windname, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(windname, 680 if wrap.resolution == 480 else (wrap.resolution * 16 / 9), wrap.resolution)
    cond_filled.release()
    count = 0
    prev_frame_time = 0
    new_frame_time = 0
    start_time = 0
    started = False
    while True:
        #sleep(helper.SLEEP)
        helper.cprint("Waiting to render...")
        count += 1
        if count > int(helper.CHECK):
            cond_filled.acquire()
            if not wrap.calling:
                cond_filled.release()
                print("Stopping render thread...")
                cv2.destroyAllWindows()
                return
            cond_filled.release()
            count = 0
        recv_fin_lock.acquire()
        framelength = len(recv_fin_wrap.framedata)
        helper.cprint(str(framelength) + " frames ready")
        #datalength = len(recv_fin_wrap.featuredata)
        #helper.cprint(str(datalength) + " data frames ready")
        recv_fin_lock.release()
        #if framelength > 0 and datalength > 0:
        if framelength > 0:
            recv_fin_lock.acquire()            
            f = recv_fin_wrap.framedata.pop(0)
            #pts = recv_fin_wrap.featuredata.pop(0)
            recv_fin_lock.release()
            helper.cprint("Rendering FID: " + str(f.fid))
            #nparr = np.fromstring(f.data, dtype=np.uint8)
            #frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            #frame = pickle.loads(f.data)
            frame = f.data
            #points = pickle.loads(pts.data)
            # Could add lengths of the 4 buffers as the status dashboard
            recv_fin_lock.acquire()
            rdy = str(len(recv_fin_wrap.framedata))
            recv_fin_lock.release()
            new_frame_time = time()
            fps = str(int(1 / (new_frame_time - prev_frame_time)))
            prev_frame_time = new_frame_time
            if not started:
                start_time = time()
                started = True
            image = cv2.putText(frame, "FID: " + str(f.fid) + " FPS: " + fps + " TIME: " + str("{:.2f}".format(time() - start_time)) + " RDY: " + str(rdy), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1, cv2.LINE_AA)
            #for point in points:
            #    cv2.circle(frame, tuple(point), 2, color=(0, 0, 255), thickness=-1)
            cv2.imshow(windname, image)
            #cv2.waitKey(0)
            cv2.waitKey(50)
            helper.cprint("rendered frame: " + str(f.fid))