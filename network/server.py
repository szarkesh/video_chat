#!/usr/bin/env python

import os
import socket
import struct
import sys
import shutil
import threading
from threading import Lock, Thread

from helper import send

QUEUE_LENGTH = 10
SEND_BUFFER = 32768

# per-client struct

class Client:
    def __init__(self, clientsocket: socket):
        self.lock = Lock()
        self.clientsocket = clientsocket


# Super simple thread that takes in requests from the client and immediately sends a response.
# There is one thread per client.

def client_read(client: Client, cond_filled: threading.Condition):
    print("")
    print("NEW CLIENT HAS JOINED")
    #print(client.clientsocket.gethostbyname(client.clientsocket.gethostname()))
    print("_____________________")
    try:
        while True:
            HDRLEN = 6
            chunks = []
            bytes_recd = 0
            response = ""
            while bytes_recd < HDRLEN:
                chunk = client.clientsocket.recv(HDRLEN - bytes_recd).decode("utf-8")
                if chunk == b'':
                    #raise RuntimeError("socket connection broken")
                    print("Connection from client closed")
                    sys.exit()
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            header = ''.join(chunks)
            print("Received message header ", header)
            length = int(header[3:6])
            payload = ""
            if length != 0:
                while (len(payload) < length):
                    payload += client.clientsocket.recv(length - len(payload)).decode("utf-8")
            print("Message Payload:\n" + payload)
            if header[0] == "0":
                if header[1] == "C":
                    callid, name, srcip, srcport, tgtip, tgtport = payload.split(',')
                    print("Call request " + callid + " from client")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((tgtip, int(tgtport)))
                    #payload = callid + ":" + name + ":" + src + ":" + port
                    #header = "0C0" + str(len(payload)).zfill(3)
                    send(sock, header + payload)
                    sock.close()
                    print("Call request forwarded to " + name + " at [" + tgtip + ":" + tgtport +"]")            
                elif header[1] == "A":
                    callid, name, ip, port, timestamp = payload.split(',')
                    print("Accept request for call: " + callid)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((ip, int(port)))
                    send(sock, header + payload)
                    sock.close()
                    print("Call accept forwarded to " + name + " at [" + ip + ":" + port +"] with timestamp: " + timestamp)    
                elif header[1] == "R":
                    callid, name, ip, port = payload.split(',')
                    print("Reject request for call: " + callid)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((ip, int(port)))
                    send(sock, header + payload)
                    sock.close()
                    print("Call reject forwarded to " + name + " at [" + ip + ":" + port +"]")    
                else:
                    print("Unexpected Operation")
            else:
                print("Request from Client - Unexpected Behaviour -- header was", header)
    except(ConnectionResetError):
        print("Client disconnected, closing thread...")

def server_thread(s: socket, cond_filled: threading.Condition, threads: list):
    while True:
        (clientsocket, address) = s.accept()
        client = Client(clientsocket)
        t = Thread(target=client_read, args=(client, cond_filled))
        t.daemon = True
        threads.append(t)
        t.start()

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python server.py <port>")

    port = int(sys.argv[1])

    cond_filled = threading.Condition()

    threads = []
    print("Starting Server on port {0}".format(port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # may need to use socket.gethostname() instead of localhost once deploy to ec2
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    name = '0.0.0.0'#name = 'localhost'#"localhost" if socket.gethostname() == "cis553" else socket.gethostname()
    s.bind((name, port))
    s.listen(QUEUE_LENGTH)
    server_main_thread = threading.Thread(target=server_thread, args=(s, cond_filled, threads))
    server_main_thread.daemon = True
    server_main_thread.start()
    while True:
        line = input('>> ')
        if ' ' in line:
            cmd, argstring = line.split(' ', 1)
            args = argstring.split(' ')
        else:
            cmd = line
        
        if cmd in ['q', 'quit']:
            sys.exit(0)
        # blocking call to accept, creates new socket to handle each client
        


if __name__ == "__main__":
    main()
