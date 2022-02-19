import base64
import select
import socket
import threading
from time import sleep, time
import numpy as np
from client_wrapper import client_wrapper
from frame import Frame
from raw_wrapper import raw_wrapper
import helper
import pickle

HDRLEN = 25

def listen_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, recv_raw_wrap: raw_wrapper, recv_raw_lock: threading.Condition, IP: str, PORT: int):
        
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
        listen_thread_loop(wrap, cond_filled, recv_raw_wrap, recv_raw_lock, s)
                    
def listen_thread_loop(wrap: client_wrapper, cond_filled: threading.Condition, recv_raw_wrap: raw_wrapper, recv_raw_lock: threading.Condition, s: socket):
    count = 0
    samplingrate = wrap.freshrate
    while True:
            sleep(helper.SLEEP)
            count += 1
            if count > int(helper.CHECK):
                cond_filled.acquire()
                if not wrap.calling:
                    cond_filled.release()
                    print("Stopping listen thread...")
                    break
                cond_filled.release()
                count = 0
            header = ""
            r, _, _ = select.select([s], [], [])
            if r:
                helper.cprint("Receiving ")
                t = time()
                while (len(header) < HDRLEN):
                    t2 = time()
                    if t2 - t > 2:
                        cond_filled.acquire()
                        if not wrap.calling:
                            cond_filled.release()
                            print("Stopping listen thread...")
                            return
                        cond_filled.release()
                    header += s.recv(HDRLEN - len(header)).decode('utf-8')
                    helper.cprint(str(len(header)) + " / " + str(HDRLEN))
                helper.cprint(header)
                if len(header) > 0:
                    type = header[1]
                    status = int(header[2])
                    fid = int(header[3:10])
                    cnum = int(header[10:15])
                    length = int(header[15:25])
                    if (status != 0):
                        print("Error Status: " + str(status))
                    payload = b''
                    t = time()
                    while (len(payload) < length):
                        t2 = time()
                        if t2 - t > 2:
                            cond_filled.acquire()
                            if not wrap.calling:
                                cond_filled.release()
                                print("Stopping listen thread...")
                                return
                            cond_filled.release()
                        payload += s.recv(length - len(payload))
                        helper.cprint(str(len(payload)) + " / " + str(length))
                    if type == 'C':
                        recv_raw_lock.acquire()
                        recv_raw_wrap.calibration_frames = pickle.loads(payload)
                        recv_raw_lock.release()
                        print("Received Calibration Frames");
                    elif type == 'A':
                        recv_raw_lock.acquire()
                        recv_raw_wrap.calibration_masks = pickle.loads(payload)
                        recv_raw_lock.release()
                        print("Received Calibration Masks");
                    elif type == 'M':
                        recv_raw_lock.acquire()
                        recv_raw_wrap.calibration_meshes = pickle.loads(payload)
                        recv_raw_lock.release()
                        print("Received Calibration Meshes");
                    elif type == 'P':
                        recv_raw_lock.acquire()
                        recv_raw_wrap.calibration_poses = pickle.loads(payload)
                        recv_raw_lock.release()
                        print("Received Calibration Poses");
                    elif type == 'B':
                        recv_raw_lock.acquire()
                        recv_raw_wrap.background_frame = pickle.loads(payload)
                        recv_raw_lock.release()
                        print("Received Background Frame");
                    elif type == "F":
                        # Received frame
                        frame = Frame(payload, fid, True)
                        recv_raw_lock.acquire()
                        #recv_raw_wrap.framedata.append(frame)
                        recv_raw_wrap.lastGoodFrames[str(fid)] = frame
                        recv_raw_lock.release()
                        helper.cprint("listened frame: " + str(frame.fid))
                    elif type == "D":
                        # Received feature data
                        frame = Frame(payload, fid, True)
                        recv_raw_lock.acquire()
                        recv_raw_wrap.featuredata.append(frame)
                        #if fid % samplingrate:
                        #    recv_raw_wrap.lastGoodFramePoints[str(fid)] = frame
                        recv_raw_lock.release()
                        helper.cprint("listened feature data: " + str(frame.fid))
                    elif type == "E":
                        # Received end call
                        cond_filled.acquire()
                        print(wrap.oppositename + " ended the call.")
                        cond_filled.release()
                        helper.reset(wrap, cond_filled, False)
                    else:
                        print("Unsupported Operation: " + type)
                else:
                    sleep(helper.SLEEP)