import threading
from client_wrapper import client_wrapper
from fin_wrapper import fin_wrapper
import cv2

def render_thread_func(wrap: client_wrapper, cond_filled:  threading.Condition, recv_fin_wrap: fin_wrapper, recv_fin_lock: threading.Condition):
    cv2.namedWindow("video", cv2.WINDOW_NORMAL)
    cond_filled.acquire()
    cv2.resizeWindow("video", 680 if wrap.resolution == 480 else (wrap.resolution * 16 / 9), wrap.resolution)
    cond_filled.release()
    count = 0
    while True:
        count += 1
        if count > 10000:
            cond_filled.acquire()
            if not wrap.calling:
                cond_filled.release()
                break
            cond_filled.release()
            count = 0
        recv_fin_lock.acquire()
        if len(recv_fin_wrap.framedata) > 0:
            f = recv_fin_wrap.framedata.pop(0)
            frame = f.data
            cv2.imshow("video", frame)