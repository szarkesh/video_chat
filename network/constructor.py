import threading
from client_wrapper import client_wrapper 
from raw_wrapper import raw_wrapper
from fin_wrapper import fin_wrapper

def constructor_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, send_raw_wrap: raw_wrapper, send_raw_lock: threading.Condition, send_fin_wrap: fin_wrapper, send_fin_lock: threading.Condition):
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
        send_raw_lock.acquire()
        if len(send_raw_wrap.framedata) > 0:
            send_fin_lock.acquire()
            send_fin_wrap.framedata.append(send_raw_wrap.framedata.pop(0))
            send_fin_lock.release()
        send_raw_lock.release()