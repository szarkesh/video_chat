from concurrent.futures import thread
import socket
import sys
sys.path.append('../processing')
import face_utils
import threading
from time import sleep
import uuid
from client_wrapper import client_wrapper
from fin_wrapper import fin_wrapper
from helper import send
from helper import reset
from helper import start
from util import image_resize
from server_recv import server_client_recv_thread_func

from raw_wrapper import raw_wrapper
from cal_wrapper import cal_wrapper
from server_recv import server_recv_thread_func
import mediapipe as mp
import cv2 

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
drawSpecCircle = mp.solutions.drawing_utils.DrawingSpec(thickness=0, circle_radius=0, color=(0, 0, 255))
mp_face_mesh = mp.solutions.face_mesh
mp_selfie_segmentation = mp.solutions.selfie_segmentation
mp_holistic = mp.solutions.holistic

QUEUE_LENGTH = 10
PORT = 3000
IP = "localhost"
TARGET_FRAME_RATE = 2
BEGIN_IMAGE_WIDTH = 720
IMAGE_WIDTH_OPTIONS = [240, 360, 720]
FLAG_AUTO_RESIZE = False
FLAG_USE_ALL_LANDMARKS = False
BODY_THRESH = 0.4
quality_index = IMAGE_WIDTH_OPTIONS.index(BEGIN_IMAGE_WIDTH)
prompts = ['Show a neutral face'] #,'Now show a smile', 'Now show us your eyes closed','Now show your mouth half open', 'Now open your mouth more!', 'Now do a half smile', 'Now purse your lips']

if (quality_index == -1):
        raise ValueError('Beginning image size not in list of sizes')
    


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
    constructor_threads = []
    extractor_threads = []
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
        args=(wrap, cond_filled, IP, PORT, recv_raw_wrap, recv_raw_lock, recv_fin_wrap, recv_fin_lock, send_raw_wrap, send_raw_lock, send_fin_wrap, send_fin_lock, listen_thread, render_thread, capture_thread, sender_thread, constructor_threads, extractor_threads,
            server_sock, server_recv_sock)
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
                    recv_raw_wrap.framedata = []
                    recv_raw_wrap.featuredata = []
                    send_raw_wrap.headframeid = 0
                    send_raw_wrap.tailframeid = 0
                    send_raw_wrap.framedata = []
                    send_raw_wrap.featuredata = []
                    recv_fin_wrap.headframeid = 0
                    recv_fin_wrap.tailframeid = 0
                    recv_fin_wrap.framedata = []
                    recv_fin_wrap.featuredata = []
                    send_fin_wrap.headframeid = 0
                    send_fin_wrap.tailframeid = 0
                    send_fin_wrap.framedata = []
                    send_fin_wrap.featuredata = []
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
                    wrap.calling = True
                    cond_filled.release()
                    if accepted:
                         # Send Calibration
                        cond_filled.acquire()
                        is_calibrating = True
                        prompt_index = 0
                        cap = cv2.VideoCapture(0)
                        with mp_holistic.Holistic(static_image_mode=True, model_complexity=1, enable_segmentation=True, refine_face_landmarks=True) as holistic_detector:
                            while cap.isOpened() and is_calibrating:
                                ret, frame = cap.read()
                                frame = image_resize(frame, width=IMAGE_WIDTH_OPTIONS[quality_index])
                                if background_frame is None:
                                    display_frame = frame.copy()
                                    cv2.putText(display_frame, "Leave the viewport and \n press N to continue.", (100, 100), fontFace=cv2.FONT_HERSHEY_PLAIN,
                                                fontScale=1.2, color=(255, 255, 255))
                                    cv2.imshow('1', display_frame)

                                    if cv2.waitKey(1) & 0xFF == ord('n'):
                                        background_frame = frame
                                else:
                                    if prompt_index > prompts.__len__():
                                        print("Calibration Complete! Sending...")
                                        break
                                    elif ret == True:
                                        display_frame = frame.copy()
                                        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                        image.flags.writeable = False
                                        results = holistic_detector.process(image)
                                        image.flags.writeable = True
                                        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                                        if results.face_landmarks:
                                            mp_drawing.draw_landmarks(image=display_frame, landmark_list=results.face_landmarks, landmark_drawing_spec=drawSpecCircle)
                                            thresh_mask = (results.segmentation_mask > BODY_THRESH).astype('uint8')
                                        if results.pose_landmarks:
                                            mp_drawing.draw_landmarks(
                                                display_frame,
                                                results.pose_landmarks,
                                                mp_holistic.POSE_CONNECTIONS,
                                                landmark_drawing_spec=mp_drawing_styles.
                                                    get_default_pose_landmarks_style())
                                        else:
                                            print('unable to find face')
                                        cv2.putText(display_frame, prompts[prompt_index], (100,100), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1.2, color=(255,255,255))
                                        cv2.imshow('1', display_frame)
                                    if cv2.waitKey(1) & 0xFF == ord('n'):
                                        if results.face_landmarks:
                                            prompt_index += 1
                                            send_fin_wrap.calibration_frames.append(image)
                                            face_pts = face_utils.get_landmarks_to_np(results.face_landmarks, image.shape[1], image.shape[0], FLAG_USE_ALL_LANDMARKS)
                                            body_pts = face_utils.get_landmarks_to_np(results.pose_landmarks, image.shape[1],
                                                                                    image.shape[0], FLAG_USE_ALL_LANDMARKS)
                                            print(body_pts)
                                            send_fin_wrap.calibration_masks.append(thresh_mask)
                                            send_fin_wrap.calibration_meshes.append(face_pts)
                                            send_fin_wrap.calibration_poses.append(body_pts)
                                            send_fin_wrap.calibration_masks.append(results.segmentation_mask)
                                            print('face_pts have eye openness', face_utils.eye_openness(face_pts))
                                            if prompt_index >= len(prompts):
                                                is_calibrating = False
                                    if cv2.waitKey(1) & 0xFF == ord('q'):
                                        break
                                        
                        # Spawn threads for call (timing with unix stamp)
                        start(wrap, cond_filled, prompts, IP, PORT, recv_raw_wrap, recv_raw_lock, recv_fin_wrap, recv_fin_lock, send_raw_wrap, send_raw_lock, send_fin_wrap, send_fin_lock, listen_thread, render_thread, capture_thread, sender_thread, constructor_threads, extractor_threads)
                        #while True:
                        #    sleep(3)
                        #    recv_raw_lock.acquire()
                        #    recv_fin_lock.acquire()
                        #    send_raw_lock.acquire()
                        #    send_fin_lock.acquire()
                        #    print("RECV RAW: " + str(len(recv_raw_wrap.framedata)))
                        #    print("RECV FIN: " + str(len(recv_fin_wrap.framedata)))
                        #    print("SEND RAW: " + str(len(send_raw_wrap.framedata)))
                        #    print("SEND FIN: " + str(len(send_fin_wrap.framedata)))
                        #    recv_raw_lock.release()
                        #    recv_fin_lock.release()
                        #    send_raw_lock.release()
                        #    send_fin_lock.release()
            except (ValueError):
                print("Usage: call <targetip> <targetport> [freshrate] [resolution]")
            
        elif cmd in ['s', 'stop']:
            reset(wrap, cond_filled, True)
            
        elif cmd in ['status']:
            cond_filled.acquire()
            # TODO
            cond_filled.release()

        elif cmd in ['quit', 'q', 'exit']:
            sys.exit(0)
        elif cmd in ['h', 'help']:
            #TODO
            print("General Command Help:")
            print("[c/call <tgtip> <tgtport>] -")
            print("[s, stop] Stop current call")
            print("[status] - Data Dashboard")
            print("[q, quit] - Exit & Shutdown client")
        else:
            print("Invalid command. ")


if __name__ == '__main__':
    main()
