import socket
import threading
import numpy as np
from client_wrapper import client_wrapper
from frame import Frame
from raw_wrapper import raw_wrapper

HDRLEN = 20

def listen_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, recv_raw_wrap: raw_wrapper, recv_raw_lock: threading.Condition, IP: str, PORT: int):
    try:
        count = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #"localhost" if socket.gethostname() == "cis553" else socket.gethostname()
        sock.bind((IP, str(PORT)))
        sock.listen(1)
        (s, address) = sock.accept() 
        cond_filled.acquire()
        height = wrap.resolution
        width = 680 if wrap.resolution == 480 else (wrap.resolution * 16 / 9)
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
            
            header = ""
            receive(s, header, HDRLEN)
            type = header[1]
            status = int(header[2])
            fid = int(header[3:10])
            cnum = int(header[10:15])
            length = int(header[15:20])
            if (status != 0):
                print("Error Status: " + str(status))
            payload = ""
            receive(s, payload, length)
            
            if type == "F":
                # Received frame
                data = np.frombuffer(payload, dtype="B").reshape((width, height, 1), )
                frame = Frame(data, fid, True)
                recv_raw_lock.acquire()
                recv_raw_wrap.framedata.append(frame)
                recv_raw_lock.release()
            elif type == "D":
                # Received feature data
                print("Data Features")
            elif type == "E":
                # Received end call
                reset(wrap, cond_filled, False)
            else:
                print("Unsupported Operation: " + type)
            
    except Exception as e:
        print(e)