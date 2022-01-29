from socket import socket
import sys
import threading
from time import time

from client_wrapper import client_wrapper
from helper import send
from helper import start
from helper import receive

HDRLEN = 6

def server_recv_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, sock: socket):
    #try:
        while True:
            payload = ""
            header = sock.recv(HDRLEN).decode("utf-8")
            while (len(header) < HDRLEN):
                header += sock.recv(HDRLEN - len(header)).decode('utf-8')
            length = int(header[3:6]) #strip('\0')?
            t = header[1:2]
            status = int(header[2:3])
            if status != 0:
                print ("Error Status: " + status)
            if length != 0:
                while (len(payload) < length):
                    payload += sock.recv(length - len(payload)).decode('utf-8')
            data = payload.split(',')
            callid = data[0]
            name = data[1]
            if t == 'C':                
                cond_filled.acquire()
                ip = data[2]
                port = data[3]
                wrap.waiting = True
                wrap.targetip = ip
                wrap.targetport = port
                cond_filled.release()
                print("Incoming call (" + callid + ") from " + name + "[" + ip + ":" + port + "]")
                print("Please respond: [accept] or [reject]:")
                waiting = True
                while waiting:
                    line = input('>> ')
                    if ' ' in line:
                        cmd, argstring = line.split(' ', 1)
                        args = argstring.split(' ')
                    else:
                        cmd = line
                    print(cmd)
                    if cmd in ['a', 'accept']:
                        cond_filled.acquire()
                        wrap.waiting = False
                        wrap.accepted = True
                        # Send Accept Response to other client
                        payload = callid + "," + name
                        print("Informing opposite to start call...")
                        send(sock, "0A0" + str(len(payload)).zfill(3) + payload)
                        print("Call Accepted! Starting video call...")
                        # Logic to spawn threads (timing with unix stamp)
                        wrap.calling = True
                        waiting = False
                        cond_filled.release()
                    elif cmd in ['r', 'reject']:
                        cond_filled.acquire()
                        wrap.waiting = False
                        wrap.accepted = False
                        # Send  reject response to other client
                        payload = callid + "," + name
                        send(sock, "0R0" + str(len(payload)).zfill(3) + payload)
                        print("Call Rejected!")
                        waiting = False
                        cond_filled.release()
                    elif cmd in ['q', 'quit']:
                        sys.exit(0)
                    elif cmd in ['h', 'help']:
                        print("Incoming Call Command Help:")
                        print("[a, accept] - Accept call, begin video")
                        print("[r, reject] - Reject call")
                        print("[q, quit] - Exit & Shutdown client")
                    else:
                        print("Invalid command. ")
                    
            elif t == 'A':
                cond_filled.acquire()
                wrap.waiting = False
                wrap.accepted = True
                print(name + " accepted your call! Starting video...")
                cond_filled.release()
            elif t == 'R':
                cond_filled.acquire()
                wrap.waiting = False
                wrap.accepted = False
                print(name + " rejected your call!")
                cond_filled.release()
    #except:
    #    print("Error occured in receive thread. Client shutting down.")
    #    wrap.playing = False
    #    sys.exit()
        
def server_client_recv_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, IP, PORT, recv_raw_wrap, recv_raw_lock, recv_fin_wrap, recv_fin_lock, send_raw_wrap, send_raw_lock, send_fin_wrap, send_fin_lock, listen_thread, render_thread, capture_thread, sender_thread, constructor_threads, extractor_threads,
                                   server_sock: socket, supersocket: socket):
    (sock, address) = supersocket.accept()
    print("Server connected via listener")
    #server_recv_thread_func(wrap, cond_filled, sock)
    while True:
            payload = ""
            header = sock.recv(HDRLEN).decode("utf-8")
            while (len(header) < HDRLEN):
                header += sock.recv(HDRLEN - len(header)).decode('utf-8')
            length = int(header[3:6]) #strip('\0')?
            t = header[1:2]
            status = int(header[2:3])
            if status != 0:
                print ("Error Status: " + status)
            if length != 0:
                while (len(payload) < length):
                    payload += sock.recv(length - len(payload)).decode('utf-8')
            data = payload.split(',')
            callid = data[0]
            name = data[1]
            ip = data[2]
            port = data[3]
            if t == 'C':                
                cond_filled.acquire()    
                wrap.waiting = True
                wrap.targetip = ip
                wrap.targetport = port
                wrap.oppname = name
                cond_filled.release()
                print("Incoming call (" + callid + ") from " + name + "[" + ip + ":" + port + "]")
                print("Please respond: [accept] or [reject]:")
                waiting = True
                while waiting:
                    line = input('>>> ')
                    if ' ' in line:
                        cmd, argstring = line.split(' ', 1)
                        args = argstring.split(' ')
                    else:
                        cmd = line
                    if cmd in ['a', 'accept']:
                        cond_filled.acquire()
                        wrap.waiting = False
                        wrap.accepted = True
                        # Send Accept Response to other client
                        timestamp = int(time()) + 3000
                        payload = callid + "," + wrap.name + "," + ip + "," + str(port) + "," + str(timestamp)
                        print("Informing opposite to start call...")
                        send(server_sock, "0A0" + str(len(payload)).zfill(3) + payload)
                        print("Call Accepted! Starting video call...")
                        # Logic to spawn threads (timing with unix stamp)
                        wrap.calling = True
                        waiting = False
                        start(wrap, cond_filled, IP, PORT, recv_raw_wrap, recv_raw_lock, recv_fin_wrap, recv_fin_lock, send_raw_wrap, send_raw_lock, send_fin_wrap, send_fin_lock, listen_thread, render_thread, capture_thread, sender_thread, constructor_threads, extractor_threads)
                        cond_filled.release()
                    elif cmd in ['r', 'reject']:
                        cond_filled.acquire()
                        wrap.waiting = False
                        wrap.accepted = False
                        # Send  reject response to other client
                        payload = callid + "," + wrap.name + "," + ip + "," + str(port) 
                        send(server_sock, "0R0" + str(len(payload)).zfill(3) + payload)
                        print("Call Rejected!")
                        waiting = False
                        cond_filled.release()
                    elif cmd in ['q', 'quit']:
                        sys.exit(0)
                    elif cmd in ['h', 'help']:
                        print("Incoming Call Command Help:")
                        print("[a, accept] - Accept call, begin video")
                        print("[r, reject] - Reject call")
                        print("[q, quit] - Exit & Shutdown client")
                    else:
                        print("Invalid command. ")
                    
            elif t == 'A':
                timestamp = data[4]
                cond_filled.acquire()
                wrap.waiting = False
                wrap.accepted = True
                print(name + " [" + ip + ":" + port +"] accepted your call! Starting video... (@" + timestamp + ")")
                cond_filled.release()
            elif t == 'R':
                cond_filled.acquire()
                wrap.waiting = False
                wrap.accepted = False
                print(name + " [" + ip + ":" + port +"] rejected your call!")
                cond_filled.release()  
