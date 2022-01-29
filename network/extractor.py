import threading
from client_wrapper import client_wrapper 
from raw_wrapper import raw_wrapper
from fin_wrapper import fin_wrapper

def extractor_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, recv_raw_wrap: raw_wrapper, recv_raw_lock: threading.Condition, recv_fin_wrap: fin_wrapper, recv_fin_lock: threading.Condition):
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
        recv_raw_lock.acquire()
        if len(recv_raw_wrap.framedata) > 0:
            recv_fin_lock.acquire()
            recv_fin_wrap.framedata.append(recv_raw_wrap.framedata.pop(0))
            recv_fin_lock.release()
        recv_raw_lock.release()