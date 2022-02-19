import socket
import threading
from time import sleep
from client_wrapper import client_wrapper
from fin_wrapper import fin_wrapper
import numpy as np
import pickle

import helper

def sender_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, send_fin_wrap: fin_wrapper, send_fin_lock: threading.Condition):
    # Wait for listener thread on recipient to start
    print("Sender Thread Started")
    sleep(1)
    count = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("connecting to " + wrap.targetip + ":" + "400" + str(wrap.targetport)[3])
    connected = False
    while not connected:
        try: 
            sock.connect((wrap.targetip, int("400" + str(wrap.targetport)[3])))
            connected = True
            print("Connection Established")
        except:
            print("Retrying connection...")
            sleep(1)
    #try:
    while True:
        sleep(helper.SLEEP)
        count += 1
        if count > int(helper.CHECK):
            cond_filled.acquire()
            if not wrap.calling:
                cond_filled.release()
                print("Sending End Call Message...")
                helper.send(sock, "0E0" + "0000000" + "00000" + "0000000000")
                print("Stopping sender thread...")
                break
            cond_filled.release()
            count = 0
        send_fin_lock.acquire()
        #print("Num Calibration Frames: " + str(len(send_fin_wrap.calibration_frames)))
        if len(send_fin_wrap.calibration_frames) > 0:
            frames = send_fin_wrap.calibration_frames
            payload = pickle.dumps(frames, 0)
            header = ("0C0" + '0000000' + '00000' + str(len(payload)).zfill(10)).encode('utf-8')
            helper.cprint("sending calibration frames: " + str(len(frames)) + " | len: " + str(len(frames)))
            helper.datsend(sock, header+payload)
            data = send_fin_wrap.calibration_meshes
            payload = pickle.dumps(data, 0)
            print(str(len(payload)))
            print(send_fin_wrap.calibration_meshes)
            header = ("0M0" + '0000000' + '00000' + str(len(payload)).zfill(10)).encode('utf-8')
            helper.cprint("sending calibration meshes: " + str(len(data)) + " | len: " + str(len(data)))
            helper.datsend(sock, header+payload)
            data = send_fin_wrap.calibration_poses
            payload = pickle.dumps(data, 0)
            header = ("0P0" + '0000000' + '00000' + str(len(payload)).zfill(10)).encode('utf-8')
            helper.cprint("sending calibration poses: " + str(len(data)) + " | len: " + str(len(data)))
            helper.datsend(sock, header+payload)
            data = send_fin_wrap.calibration_masks
            payload = pickle.dumps(data, 0)
            header = ("0A0" + '0000000' + '00000' + str(len(payload)).zfill(10)).encode('utf-8')
            helper.cprint("sending calibration masks: " + str(len(data)) + " | len: " + str(len(data)))
            helper.datsend(sock, header+payload)
            data = send_fin_wrap.background_frame
            payload = pickle.dumps(data, 0)
            header = ("0B0" + '0000000' + '00000' + str(len(payload)).zfill(10)).encode('utf-8')
            helper.cprint("sending background_frame: " + str(len(data)) + " | len: " + str(len(data)))
            helper.datsend(sock, header+payload)
            send_fin_wrap.calibration_frames = []
            send_fin_lock.release()
            print("All Calibration Data Sent!")
        else:
            send_fin_lock.release()
        send_fin_lock.acquire()
        if len(send_fin_wrap.framedata) > 0:
            f = send_fin_wrap.framedata.pop(0)
            send_fin_lock.release()
            payload = f.data
            header = ("0F0" + str(f.fid).zfill(7) + '00000' + str(len(payload)).zfill(10)).encode('utf-8')
            helper.cprint("sending frame id: " + str(f.fid) + " ~ " + str(f.data)[1:5] + " | len: " + str(len(f.data)))
            helper.datsend(sock, header+payload)
        else:
            send_fin_lock.release()
        send_fin_lock.acquire()
        if len(send_fin_wrap.featuredata) > 0:
            f = send_fin_wrap.featuredata.pop(0)
            send_fin_lock.release()
            payload = f.data
            header = ("0D0" + str(f.fid).zfill(7) + '00000' + str(len(payload)).zfill(10)).encode('utf-8')
            helper.cprint("sending feature data id: " + str(f.fid) + " ~ " + str(f.data)[1:5] + " | len: " + str(len(f.data)))
            helper.datsend(sock, header+payload)
        else:
            send_fin_lock.release()
    #except:
    #    print("Sender Error (Sender thread stopped...)")
    