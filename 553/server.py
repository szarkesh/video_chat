#!/usr/bin/env python

import os
import socket
import struct
import sys
import shutil
import threading
from threading import Lock, Thread

QUEUE_LENGTH = 10
SEND_BUFFER = 32768

# per-client struct


class Client:
    def __init__(self, songs, musicdir, clientsocket):
        self.lock = Lock()
        self.songs = songs
        self.clientsocket = clientsocket
        self.musicdir = musicdir


# Super simple thread that takes in requests from the client and immediately sends a response.
# There is one thread per client.

def client_read(client, cond_filled):
    print("")
    print("NEW CLIENT HAS JOINED")
    print("_____________________")
    while True:
        HDRLEN = 14
        chunks = []
        bytes_recd = 0
        response = ""
        while bytes_recd < HDRLEN:
            chunk = client.clientsocket.recv(HDRLEN - bytes_recd)
            if chunk == b'':
                #raise RuntimeError("socket connection broken")
                print("Connection from client closed")
                sys.exit()
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        header = ''.join(chunks)
        print("Received message header ", header)
        if header[0] == "0":
            if header[1] == "L":
                print("Client requests song list...")
                resp_header = "1L0010000"
                payload = "\0"
                for i in range(len(client.songs)):
                    song = client.songs[i]
                    payload += (str(song['song_id'] + 1) +
                                ": " + song['name'] + "\0")
                resp_header = resp_header + str(len(payload)).zfill(5)
                response = resp_header+payload
            elif header[1] == "G":
                print("Client requests Get Chunk..." + header)
                songId = int(header[2:4]) - 1
                print(songId)
                if songId < 0 or songId >= len(client.songs):
                    response = "1G"+str(songId).zfill(2)+"3"+"0000"+"00000"
                else:
                    chunkNum = int(header[5:9])
                    songChunkNum = client.songs[songId]['total_chunks']
                    if chunkNum >= songChunkNum:
                        response = "1G"+str(songId).zfill(2)+"2"+"0000"+"00000"
                        print("sending response that song is over")
                    else:
                        file = open(
                            "chunks/" + client.songs[songId]['name'] + str(chunkNum))
                        response = file.read(SEND_BUFFER)
                        resp_header = (
                            "1G"+str(songId).zfill(2)+"1"+str(chunkNum).zfill(4)+str(len(response)).zfill(5))
                        response = resp_header + response
                        file.close()
                        # print(response)
            else:
                print("Unexpected Operation")

            print("SENDING TO CLIENT")

            totalSent = 0
            while totalSent < len(response):
                sent = client.clientsocket.send(response[totalSent:])
                if sent == 0:
                    print("Lost connection to Server...")
                totalSent += sent

            print("FINISHED SENDING TO CLIENT")

            # Send response to client
            # t = Thread(target=client_write, args=(
            #     client, response, cond_filled))
            # t.daemon = True
            # threads.append(t)
            # t.start()
        else:
            print("Request from Client - Unexpected Behaviour -- header was", header)

# function to compile the music directory into chunks


def get_mp3s(musicdir):
    print("Reading music files...")
    songs = []
    songList = []
    # Clear Existing Chunks
    if os.path.exists("chunks"):
        print("Deleting existing chunks...")
        shutil.rmtree("chunks")

    print("Creating new chunks directory")
    os.mkdir("chunks")
    id_num = 0
    for filename in os.listdir(musicdir):
        if filename.endswith(".mp3"):
            file = open(musicdir + "/" + filename, 'rb')
            name = filename.split('.')[0]
            chunk_num = 0
            bytes = file.read(SEND_BUFFER)
            f = 0
            while (bytes != ""):
                f = open("chunks/" + name + str(chunk_num), 'w')
                f.write(bytes)
                chunk_num += 1
                bytes = file.read(SEND_BUFFER)
            f.close()
            # TODO: Store song metadata for future use.  You may also want to build
            # the song list once and send to any clients that need it.
            name = filename.split('.')[0]
            songs.append({"song_id": id_num, "name": name,
                         "total_chunks": chunk_num})
            id_num += 1
    print(songs)
    print("Found {0} song(s)!".format(len(songs)))

    return songs, songList


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python server.py [port] [musicdir]")
    if not os.path.isdir(sys.argv[2]):
        sys.exit("Directory '{0}' does not exist".format(sys.argv[2]))

    port = int(sys.argv[1])

    cond_filled = threading.Condition()

    songs, songList = get_mp3s(sys.argv[2])

    threads = []
    print("Starting Server on port {0}".format(port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # may need to use socket.gethostname() instead of localhost once deploy to ec2
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    name = "localhost" if socket.gethostname() == "cis553" else socket.gethostname()
    s.bind((name, port))
    s.listen(QUEUE_LENGTH)
    # TODO: create a socket and accept incoming connections
    while True:
        (clientsocket, address) = s.accept()
        client = Client(songs, sys.argv[2], clientsocket)
        t = Thread(target=client_read, args=(client, cond_filled))
        t.daemon = True
        threads.append(t)
        t.start()
        #t = Thread(target=client_write, args=(client,))
        # threads.append(t)
        # t.start()
    # s.close()


if __name__ == "__main__":
    main()
