import socket
import sys
import threading
from time import sleep
import uuid
from client_wrapper import client_wrapper
from fin_wrapper import fin_wrapper
from helper import send
from server_recv import server_client_recv_thread_func

from raw_wrapper import raw_wrapper
from server_recv import server_recv_thread_func

QUEUE_LENGTH = 10
PORT = 3000
IP = "localhost"

def main():
    if len(sys.argv) < 4:
        print('Usage: %s <server ip> <server port> <your first name> <your port>' % sys.argv[0])
        sys.exit(1)

    print("Starting client...")
    # Create a pseudo-file wrapper, condition variable, and socket.  These will
    # be passed to the thread we're about to create.
    wrap = client_wrapper()
    wrap.name = sys.argv[3]
    PORT = int(sys.argv[4])
    IP = socket.gethostbyname(socket.gethostname())
    recv_raw_wrap = raw_wrapper()
    recv_fin_wrap = fin_wrapper()
    send_raw_wrap = raw_wrapper()
    send_fin_wrap = fin_wrapper()
    # Create a condition variable to synchronize the receiver and player threads.
    # In python, this implicitly creates a mutex lock too.
    # See: https://docs.python.org/2/library/threading.html#condition-objects
    cond_filled = threading.Condition()
    recv_raw_lock = threading.Condition()
    recv_fin_lock = threading.Condition()
    send_raw_lock = threading.Condition()
    send_fin_lock = threading.Condition()
    #query_thread = None
    listen_thread = None
    capture_thread = None
    sender_thread = None
    render_thread = None
    print("Client Ready! [" + IP + ":" + str(PORT) + "]")
    
    # Create a TCP socket and try connecting to the server.
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to server... [" + sys.argv[1] + ":" + sys.argv[2] + "]")
    server_sock.connect((sys.argv[1], int(sys.argv[2])))
    server_recv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # may need to use socket.gethostname() instead of localhost once deploy to ec2
    server_recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #"localhost" if socket.gethostname() == "cis553" else socket.gethostname()
    server_recv_sock.bind((IP, PORT))
    server_recv_sock.listen()
    
    # Create a thread whose job is to receive messages from server
    server_recv_thread = threading.Thread(
        target=server_recv_thread_func,
        args=(wrap, cond_filled, server_sock)
    )
    server_recv_thread.daemon = True
    server_recv_thread.start()
    # Create a thread whose job is to listen on a port for incoming messages
    client_recv_thread = threading.Thread(
        target=server_client_recv_thread_func,
        args=(wrap, cond_filled, server_sock, server_recv_sock)
    )
    client_recv_thread.daemon = True
    client_recv_thread.start()
    print("Connected!")
    
    while True:
        line = input('>> ')

        if ' ' in line:
            cmd, argstring = line.split(' ', 1)
            args = argstring.split(' ')
        else:
            cmd = line
        
        if cmd in ['c', 'call']:
            try: 
                if args.__len__() < 2:
                    print('Usage: call <targetip> <targetport> [freshrate] [resolution]')
                if args.__len__() >= 2:
                    cond_filled.acquire()
                    wrap.calling = False
                    wrap.targetip = str(args[0])
                    wrap.targetport = int(str(args[1]))
                    if args.__len__() >= 3:
                        wrap.freshrate = int(str(args[2]))
                    if args.__len__() >= 4:
                        wrap.resolution = int(str(args[3]))
                    cond_filled.release()
                    #blocking wait until threads kill themselves and reset.
                    while (listen_thread != None and listen_thread.is_alive()) or (capture_thread != None and capture_thread.is_alive()) or (sender_thread != None and sender_thread.is_alive()) or (render_thread != None and render_thread.is_alive()):
                        sleep(0.1) 
                    #reset raw and fin data wrapper objects for sending and receiving (no need to lock since threads killed?)
                    recv_raw_wrap.headframeid = 0
                    recv_raw_wrap.tailframeid = 0
                    recv_raw_wrap.framedata = ""
                    recv_raw_wrap.featuredata = ""
                    send_raw_wrap.headframeid = 0
                    send_raw_wrap.tailframeid = 0
                    send_raw_wrap.framedata = ""
                    send_raw_wrap.featuredata = ""
                    recv_fin_wrap.headframeid = 0
                    recv_fin_wrap.tailframeid = 0
                    recv_fin_wrap.framedata = ""
                    recv_fin_wrap.featuredata = ""
                    send_fin_wrap.headframeid = 0
                    send_fin_wrap.tailframeid = 0
                    send_fin_wrap.framedata = ""
                    send_fin_wrap.featuredata = ""
                    # ping server to initiate call
                    cond_filled.acquire()
                    wrap.waiting = True
                    wrap.accepted = False
                    wrap.calling = False
                    call_id = uuid.uuid1().hex
                    payload = call_id + "," + wrap.name + "," + str(IP) + "," + str(PORT) + "," + str(wrap.targetip) + "," + str(wrap.targetport)
                    cond_filled.release()
                    header = "0C0" + str(payload.__len__()).zfill(3)
                    send(server_sock, header + payload)
                    # block until response from user through server
                    print("Calling " + str(args[0]) + ":" + str(args[1]) + " ...")
                    print("Call ID: " + call_id + " | Waiting on response...")
                    waiting = True
                    while waiting:
                        # Server Recv Thread will update wrap based on response
                        cond_filled.acquire()
                        waiting = wrap.waiting
                        cond_filled.release()
                        sleep(1)
                    cond_filled.acquire()
                    accepted = wrap.accepted
                    cond_filled.release()
                    if accepted:
                        # Spawn threads for call (timing with unix stamp)
                        print("Spawn Video Call")
                    # start listen and capture threads
                    #listen_thread = threading.Thread(
                    #    target=listen_thread_func,
                    #    args=()
                    #)
                    #capture_thread = threading.Thread(
                    #    target=listen_thread_func,
                    #    args=()
                    #)
            except (ValueError):
                print("Usage: call <targetip> <targetport> [freshrate] [resolution]")
            
        elif cmd in ['s', 'stop']:
            cond_filled.acquire()
            if wrap.calling:
                #send message to other client to end call
                print("Ended Call!")
            wrap.waiting
            wrap.accepted = False
            wrap.calling = False
            cond_filled.release()
            
        elif cmd in ['status']:
            cond_filled.acquire()
            # TODO
            cond_filled.release()

        elif cmd in ['quit', 'q', 'exit']:
            sys.exit(0)
        elif cmd in ['h', 'help']:
            #TODO
            print("General Command Help:")
            print("[c, call] - Accept call, begin video")
            print("[r, reject] - Reject call")
            print("[q, quit] - Exit & Shutdown client")
        else:
            print("Invalid command. ")


if __name__ == '__main__':
    main()
