import base64
import socket
import threading
from time import sleep
import numpy as np
from client_wrapper import client_wrapper
from frame import Frame
from raw_wrapper import raw_wrapper
import helper

HDRLEN = 20

def listen_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, recv_raw_wrap: raw_wrapper, recv_raw_lock: threading.Condition, IP: str, PORT: int):
        count = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #"localhost" if socket.gethostname() == "cis553" else socket.gethostname()
        print("listening on: " + IP + ":" + str(PORT))
        sock.bind((IP, int("400" + str(PORT)[3])))
        sock.listen(10)
        cond_filled.acquire()
        height = wrap.resolution
        width = 680 if wrap.resolution == 480 else (wrap.resolution * 16 / 9)
        cond_filled.release()
        (s, address) = sock.accept()
        print("Connection Established: " + str(address)) 
        while True:
            sleep(1)
            count += 1
            if count > 10000:
                cond_filled.acquire()
                if not wrap.calling:
                    cond_filled.release()
                    break
                cond_filled.release()
                count = 0
            print("Receiving ")
            header = ""
            while (len(header) < HDRLEN):
                header += s.recv(HDRLEN - len(header)).decode('utf-8')
                print(str(len(header)) + " / " + str(HDRLEN))
            print(header)
            if len(header) > 0:
                type = header[1]
                status = int(header[2])
                fid = int(header[3:10])
                cnum = int(header[10:15])
                length = int(header[15:20])
                if (status != 0):
                    print("Error Status: " + str(status))
                payload = ""
                helper.datreceive(s, payload, length)
                print(payload[1:5])
                if type == "F":
                    # Received frame
                    data = base64.b64decode(payload)
                    frame = Frame(data, fid, True)
                    recv_raw_lock.acquire()
                    recv_raw_wrap.framedata.append(frame)
                    recv_raw_lock.release()
                    print("listened frame: " + str(frame.fid))
                elif type == "D":
                    # Received feature data
                    print("Data Features")
                elif type == "E":
                    # Received end call
                    helper.reset(wrap, cond_filled, False)
                else:
                    print("Unsupported Operation: " + type)