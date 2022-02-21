import socket
import threading
import sys
sys.path.append('../processing')
import face_utils
from client_wrapper import client_wrapper
from capture import capture_thread_func
from constructor import constructor_thread_func
from listen import listen_thread_func
from extractor import extractor_thread_func
from util import image_resize
from render import render_thread_func
from sender import sender_thread_func
import mediapipe as mp
import cv2 

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
drawSpecCircle = mp.solutions.drawing_utils.DrawingSpec(thickness=0, circle_radius=0, color=(0, 0, 255))
mp_face_mesh = mp.solutions.face_mesh
mp_selfie_segmentation = mp.solutions.selfie_segmentation
mp_holistic = mp.solutions.holistic



SLEEP = 0.05
PRINT = False
CHECK = 1000
SKIPN = 2
EXTRACTOR_NUM = 1
CONSTRUCTOR_NUM = 1

TARGET_FRAME_RATE = 2
BEGIN_IMAGE_WIDTH = 720
IMAGE_WIDTH_OPTIONS = [240, 360, 720]
FLAG_AUTO_RESIZE = False
FLAG_USE_ALL_LANDMARKS = False
BODY_THRESH = 0.4
quality_index = IMAGE_WIDTH_OPTIONS.index(BEGIN_IMAGE_WIDTH)

def cprint(message: str):
    if PRINT:
        print(message)

def send(socket: socket.socket, data):
    totalSent = 0
    while totalSent < len(data):
        message = data[totalSent:].encode('utf-8') if type(data) == str else data[totalSent:]
        sent = socket.send(message)
        if sent == 0:
            print("Lost connection, retrying...")
        totalSent += sent
        #print(str(totalSent) + "/" + str(len(data)))
      
def datsend(socket: socket.socket, data):
    totalSent = 0
    while totalSent < len(data):
        message = data[totalSent:]
        sent = socket.send(message)
        if sent == 0:
            print("Lost connection, retrying...")
        totalSent += sent
        #print(str(totalSent) + "/" + str(len(data)))
       
def receive(sock: socket.socket, data, length: int):
    data = sock.recv(length).decode("utf-8")
    cprint(str(len(data)) + " / " + str(length))
    cprint(data)
    while (len(data) < length):
        data += sock.recv(length - len(data)).decode('utf-8')
        cprint(str(len(data)) + " / " + str(length))
        cprint(data)
     
def datreceive(sock: socket.socket, data, length: int):
    data = sock.recv(length)
    cprint(str(len(data)) + " / " + str(length))
    cprint(data)
    while (len(data) < length):
        data += sock.recv(length - len(data))
        cprint(str(len(data)) + " / " + str(length))
        cprint(data)

def start(wrap, cond_filled, prompts, IP, PORT, recv_raw_wrap, recv_raw_lock, recv_fin_wrap, recv_fin_lock, send_raw_wrap, send_raw_lock, send_fin_wrap, send_fin_lock, listen_thread, render_thread, capture_thread, sender_thread, constructor_threads, extractor_threads):
    print("Starting Calibration...")
    cond_filled.acquire()
    is_calibrating = True
    prompt_index = 0
    cap = cv2.VideoCapture('./rayvideo.mp4' if sys.argv[3] == 'raymond' else './rayvideo2.mp4')
    with mp_holistic.Holistic(static_image_mode=True, model_complexity=1, enable_segmentation=True, refine_face_landmarks=True) as holistic_detector:
        while cap.isOpened() and is_calibrating:
            ret, frame = cap.read()
            frame = image_resize(frame, width=720)
            if send_fin_wrap.background_frame is None:
                display_frame = frame.copy()
                cv2.putText(display_frame, "Leave the viewport and \n press N to continue.", (100, 100), fontFace=cv2.FONT_HERSHEY_PLAIN,
                            fontScale=1.2, color=(255, 255, 255))
                cv2.imshow('1', display_frame)

                if cv2.waitKey(1) & 0xFF == ord('n'):
                    send_fin_lock.acquire()
                    send_fin_wrap.background_frame = frame
                    send_fin_lock.release()
            else:
                if ret == True:
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
                    #else:
                    #    print('unable to find face')
                    cv2.putText(display_frame, prompts[prompt_index], (100,100), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1.2, color=(255,255,255))
                    cv2.imshow('1', display_frame)
                if cv2.waitKey(1) & 0xFF == ord('n'):
                    if results.face_landmarks:
                        prompt_index += 1
                        send_fin_wrap.calibration_frames.append(image)
                        face_pts = face_utils.get_landmarks_to_np(results.face_landmarks, image.shape[1], image.shape[0], True)
                        body_pts = face_utils.get_landmarks_to_np(results.pose_landmarks, image.shape[1],
                                                                image.shape[0], True)
                        print(body_pts)
                        send_fin_wrap.calibration_masks.append(thresh_mask)
                        send_fin_wrap.calibration_meshes.append(face_pts)
                        send_fin_wrap.calibration_poses.append(body_pts)
                        send_fin_wrap.calibration_masks.append(results.segmentation_mask)
                        print('face_pts have eye openness', face_utils.eye_openness(face_pts))
                        if prompt_index >= len(prompts):
                            print("Calibration Complete!")
                            cap.release()
                            is_calibrating = False
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    cond_filled.release()              
    print("Spawning Video Call Threads...")
    listen_thread = threading.Thread(
        target=listen_thread_func,
        args=(wrap, cond_filled, recv_raw_wrap, recv_raw_lock, IP, PORT)
    )
    listen_thread.daemon = True
    listen_thread.start()
    render_thread = threading.Thread(
        target=render_thread_func,
        args=(wrap, cond_filled, recv_fin_wrap, recv_fin_lock, prompts, recv_raw_wrap)
    )
    render_thread.daemon = True
    render_thread.start()
    capture_thread = threading.Thread(
        target=capture_thread_func,
        args=(wrap, cond_filled, send_raw_wrap, send_raw_lock, recv_raw_wrap, send_fin_wrap)
    )
    capture_thread.daemon = True
    capture_thread.start()
    sender_thread = threading.Thread(
        target=sender_thread_func,
        args=(wrap, cond_filled, send_fin_wrap, send_fin_lock)
    )
    sender_thread.daemon = True
    sender_thread.start()
    constructor_threads = []
    for i in range(0, CONSTRUCTOR_NUM):
        constructor_threads.append(threading.Thread(
            target=constructor_thread_func,
            args=(wrap, cond_filled, recv_raw_wrap, recv_raw_lock, recv_fin_wrap, recv_fin_lock)
        ))
        constructor_threads[i].daemon = True
        constructor_threads[i].start()
    extractor_threads = []
    for i in range(0, EXTRACTOR_NUM):
        extractor_threads.append(threading.Thread(
            target=extractor_thread_func,
            args=(wrap, cond_filled, send_raw_wrap, send_raw_lock, send_fin_wrap, send_fin_lock)
        ))
        extractor_threads[i].daemon = True
        extractor_threads[i].start()
    print("All Threads Spawned!")
   
def reset(wrap: client_wrapper, cond_filled: threading.Condition, stopOpp: bool):
    cond_filled.acquire()
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