from socket import socket
import threading

from client_wrapper import client_wrapper
from capture import capture_thread_func
from constructor import constructor_thread_func
from listen import listen_thread_func
from extractor import extractor_thread_func
from render import render_thread_func
from sender import sender_thread_func

def send(socket: socket, data):
    totalSent = 0
    while totalSent < len(data):
        message = data[totalSent:].encode('utf-8') if type(data) == str else data[totalSent:]
        sent = socket.send(message)
        if sent == 0:
            print("Lost connection, retrying...")
        totalSent += sent
        #print(str(totalSent) + "/" + str(len(data)))
      
def datsend(socket: socket, data):
    totalSent = 0
    while totalSent < len(data):
        message = data[totalSent:]
        sent = socket.send(message)
        if sent == 0:
            print("Lost connection, retrying...")
        totalSent += sent
        print(str(totalSent) + "/" + str(len(data)))
       
def receive(sock: socket, data, length: int):
    data = sock.recv(length).decode("utf-8")
    print(str(len(data)) + " / " + str(length))
    print(data)
    while (len(data) < length):
        data += sock.recv(length - len(data)).decode('utf-8')
        print(str(len(data)) + " / " + str(length))
        print(data)
     
def datreceive(sock: socket, data, length: int):
    data = sock.recv(length)
    print(str(len(data)) + " / " + str(length))
    print(data)
    while (len(data) < length):
        data += sock.recv(length - len(data))
        print(str(len(data)) + " / " + str(length))
        print(data)

def start(wrap, cond_filled, IP, PORT, recv_raw_wrap, recv_raw_lock, recv_fin_wrap, recv_fin_lock, send_raw_wrap, send_raw_lock, send_fin_wrap, send_fin_lock, listen_thread, render_thread, capture_thread, sender_thread, constructor_threads, extractor_threads):
    print("Spawning Video Call Threads...")
    listen_thread = threading.Thread(
        target=listen_thread_func,
        args=(wrap, cond_filled, recv_raw_wrap, recv_raw_lock, IP, PORT)
    )
    listen_thread.daemon = True
    listen_thread.start()
    render_thread = threading.Thread(
        target=render_thread_func,
        args=(wrap, cond_filled, recv_fin_wrap, recv_fin_lock)
    )
    render_thread.daemon = True
    render_thread.start()
    capture_thread = threading.Thread(
        target=capture_thread_func,
        args=(wrap, cond_filled, send_raw_wrap, send_raw_lock)
    )
    capture_thread.daemon = True
    capture_thread.start()
    sender_thread = threading.Thread(
        target=sender_thread_func,
        args=(wrap, cond_filled, send_fin_wrap, send_fin_lock)
    )
    sender_thread.daemon = True
    sender_thread.start()
    constructor_threads.append(threading.Thread(
        target=constructor_thread_func,
        args=(wrap, cond_filled, recv_raw_wrap, recv_raw_lock, recv_fin_wrap, recv_fin_lock)
    ))
    constructor_threads[0].daemon = True
    constructor_threads[0].start()
    extractor_threads.append(threading.Thread(
        target=extractor_thread_func,
        args=(wrap, cond_filled, send_raw_wrap, send_raw_lock, send_fin_wrap, send_fin_lock)
    ))
    extractor_threads[0].daemon = True
    extractor_threads[0].start()
    print("All Threads Spawned!")
   
def reset(wrap: client_wrapper, cond_filled: threading.Condition, stopOpp: bool):
    cond_filled.acquire()
    if stopOpp:
        if wrap.calling:
            #send message to other client to end call
            print("Informed Opposite to end call...")
    wrap.waiting = False
    wrap.accepted = None
    wrap.calling = False
    wrap.timestamp = 0
    wrap.callid = ""
    wrap.oppositename = ""
    wrap.targetip = None
    wrap.targetport = None
    wrap.freshrate = 30
    wrap.resolution = 480
    wrap.oppname = ""
    cond_filled.release()