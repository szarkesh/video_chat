import readline
import socket
import struct
import sys
import threading
import math
from time import sleep

class mywrapper(object):
    def __init__(self):
        self.calling = True
        self.loading = True
        self.paused = False
        self.targetip = None
        self.targetport = None

    # When it asks to read a specific size, give it that many bytes, and
    # update our remaining data.
    # def read(self, size):
    #    result = self.data[:size]
    #    self.data = self.data[size:]
    #    self.playhead = self.playhead + (float(size) / CHUNK_SIZE)
    #    return result

def play_thread_func(wrap, cond_filled, dev):
    cond_filled.acquire()
    #wrap.mf = mad.MadFile(wrap)
    cond_filled.release()
    while True:
        """
        TODO
        example usage of dev and wrap (see mp3-example.py for a full example):
        buf = wrap.mf.read()
        dev.play(buffer(buf), len(buf))
        """
        cond_filled.acquire()
        if not wrap.playing:
            cond_filled.release()
            return
        if wrap.paused:
            sleep(0.1)
            cond_filled.release()
            continue
        if wrap.data != "":
            buf = wrap.mf.read()
            cond_filled.release()
            if buf is not None:
                # print("Playing song...")
                dev.play(buffer(buf), len(buf))
        else:
            cond_filled.release()


def request_thread_func(wrap, songId, sock, cond_filled):
    while True:
        if (not wrap.playing):
            return
        if (len(wrap.data) < 50000 and wrap.loading):
            cond_filled.acquire()
            chunk = str(wrap.loadhead).zfill(4)
            #print(chunk, wrap.recvhead, wrap.loadhead, wrap.playhead)
            wrap.loadhead += 1
            cond_filled.release()
            header = ("0G"+songId+"0"+chunk+"00000")
            totalSent = 0
            while totalSent < 14:
                bytes_sent = sock.send(header[totalSent:])
                totalSent += bytes_sent
        sleep(0.1)


def main():
    if len(sys.argv) < 3:
        print('Usage: %s <your ip> <your port>' % sys.argv[0])
        sys.exit(1)

    # Create a pseudo-file wrapper, condition variable, and socket.  These will
    # be passed to the thread we're about to create.
    wrap = mywrapper()
    # Create a condition variable to synchronize the receiver and player threads.
    # In python, this implicitly creates a mutex lock too.
    # See: https://docs.python.org/2/library/threading.html#condition-objects
    cond_filled = threading.Condition()
    # Create a TCP socket and try connecting to the server.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Starting client...")
    #sock.connect((sys.argv[1], int(sys.argv[2])))
    #print("Connected!")

    # Create a thread whose job is to receive messages from other clients
    recv_thread = threading.Thread(
        target=recv_thread_func,
        args=(wrap, cond_filled, sock)
    )
    recv_thread.daemon = True
    recv_thread.start()

    # Create a thread for video output
    #dev = ao.AudioDevice('pulse')

    # Enter our never-ending user I/O loop.  Because we imported the readline
    # module above, raw_input gives us nice shell-like behavior (up-arrow to
    # go backwards, etc.).

    query_thread = None
    play_thread = None

    while True:
        line = raw_input('>> ')

        if ' ' in line:
            cmd, argstring = line.split(' ', 1)
            args = argstring.split(' ')
        else:
            cmd = line

        # TODO: Send messages to the server when the user types things.
        # HEADER LENGTH = 14?
        # [Request/Response - 1char][Request Type - 1 char][SONG ID - 2 chars]
        # [STATUS - 1 char][Frame Number - 4 chars][Payload Length = 5 chars]
        if cmd in ['c', 'call']:
            if args.length < 3:
                print('Usage: call <targetip> <targetport> [freshrate] [resolution]')
            if args.length >= 3:
                cond_filled.acquire()
                wrap.calling = False
                wrap.loading = False
                wrap.targetip = str(args[1])
                wrap.targetport = int(str(args[2]))
                if args.length >= 4:
                    wrap.freshrate = int(str(args[3]))
                if args.length >= 5:
                    wrap.resolution = int(str(args[4]))
                cond_filled.release()
                while (query_thread != None and query_thread.is_alive()) or (play_thread != None and play_thread.is_alive()):
                    sleep(0.1)
                # reset wrapper object
                cond_filled.acquire()
                wrap.calling = True
                wrap.loading = True
                cond_filled.release()                
                

        if cmd in ['p', 'play']:
            # Begin sending chunks continuously
            try:
                songId = str(int(args[0])).zfill(2)

                cond_filled.acquire()
                wrap.paused = False
                wrap.playing = False
                cond_filled.release()

                # blocking wait until query and play threads kill themselves.
                while (query_thread != None and query_thread.is_alive()) or (play_thread != None and play_thread.is_alive()):
                    sleep(0.1)


                # reset wrapper object
                cond_filled.acquire()
                wrap.playing = True
                wrap.loading = True
                wrap.data = ""
                wrap.playhead = 0
                wrap.loadhead = 0
                wrap.recvhead = 0
                cond_filled.release()

                # Create a thread whose job is to query the current state of the wrapper, and potentially
                # make requests.

                query_thread = threading.Thread(
                    target=request_thread_func,
                    args=(wrap, songId, sock, cond_filled)
                )
                query_thread.daemon = True
                query_thread.start()

                # Create a thread to play the audio

                play_thread = threading.Thread(
                    target=play_thread_func,
                    args=(wrap, cond_filled, dev)
                )
                play_thread.daemon = True
                play_thread.start()

                # Both threads will return when the song is stopped.

            except (ValueError):
                print("Usage: play/p [songId]")

        if cmd in ['pause']:
            wrap.paused = True
        
        if cmd in ['resume']:
            wrap.paused = False

        if cmd in ['s', 'stop']:
            cond_filled.acquire()
            wrap.playing = False
            wrap.paused = False
            cond_filled.release()

        if cmd in ['ff']:
            cond_filled.acquire()
            wrap.playhead = int(math.floor(wrap.playhead + 8))
            wrap.loadhead = wrap.playhead
            wrap.recvhead = wrap.loadhead
            wrap.data = ""
            wrap.mf = mad.MadFile(wrap)
            cond_filled.release()
        
        if cmd in ['rw']:
            cond_filled.acquire()
            wrap.playhead = int(max(math.floor(wrap.playhead - 8), 0))
            wrap.loadhead = wrap.playhead
            wrap.recvhead = wrap.playhead
            wrap.loading = True
            wrap.data = ""
            wrap.mf = mad.MadFile(wrap)
            cond_filled.release()

        if cmd in ['status']:
            cond_filled.acquire()
            print("Next chunk to be requested: ", wrap.loadhead)
            print("Next chunk to be received: ", wrap.recvhead)
            print("Currently playing at chunk #", round(wrap.playhead, 2))
            cond_filled.release()

        if cmd in ['quit', 'q', 'exit']:
            sys.exit(0)


if __name__ == '__main__':
    main()
