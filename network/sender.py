import socket
import threading
from time import sleep
from client_wrapper import client_wrapper
from fin_wrapper import fin_wrapper
import numpy as np

def sender_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, send_fin_wrap: fin_wrapper, send_fin_lock: threading.Condition):
    # Wait for listener thread on recipient to start
    sleep(1)
    count = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cond_filled.acquire()
    sock.connect((wrap.targetip, str(wrap.targetport)))
    cond_filled.release()
    while True:
        count += 1
        if count > 10000:
            cond_filled.acquire()
            if not wrap.calling:
                cond_filled.release()
                break
            cond_filled.release()
            count = 0
        send_fin_lock.acquire()
        if len(send_fin_wrap.framedata) > 0:
            f = send_fin_wrap.framedata.pop(0)
            send_fin_lock.release()
            payload = f.data
            header = "0F0" + str(f.fid).zfill(7) + '00000' + str(len(payload)).zfill(5)
            send(sock, header+payload)
            send_fin_lock.acquire()
        #if len(send_fin_wrap.featuredata) > 0:
            #f = send_fin_wrap.featuredata.pop(0)
            #send_fin_lock.release()
            #payload = ???
            #header = "0F0" + str(f.fid).zfill(7) + '00000' + str(len(payload)).zfill(5)
            #send(sock, header+payload)
        send_fin_lock.release()