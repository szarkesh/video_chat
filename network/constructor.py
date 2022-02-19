import threading
from time import sleep
from frame import Frame
from client_wrapper import client_wrapper
from util import get_most_similar_frame_idx
from raw_wrapper import raw_wrapper
from fin_wrapper import fin_wrapper
import helper
import sys
sys.path.append('../processing')
import morph
import bisect
#from helper import FLAG_USE_ALL_LANDMARKS

def constructor_thread_func(wrap: client_wrapper, cond_filled: threading.Condition, recv_raw_wrap: raw_wrapper, recv_raw_lock: threading.Condition, recv_fin_wrap: fin_wrapper, recv_fin_lock: threading.Condition):
    count = 0
    # Insert raw frames from listen as dict not array based on fid, then access them using lock and construct frames using warping
    currfid = 0
    samplingrate = wrap.freshrate
    while True:
        sleep(helper.SLEEP)
        count += 1
        if count > int(helper.CHECK):
            cond_filled.acquire()
            if not wrap.calling:
                cond_filled.release()
                print("Stopping constructor thread...")
                return
            cond_filled.release()
            count = 0
        recv_raw_lock.acquire()
        framelength = len(recv_raw_wrap.framedata)
        recv_raw_lock.release()
        if framelength > 0:
            recv_raw_lock.acquire()
            f = recv_raw_wrap.framedata.pop(0)
            recv_raw_lock.release()
            recv_fin_lock.acquire()
            bisect.insort_left(recv_fin_wrap.framedata, f)
            #recv_fin_wrap.framedata.append(f)
            helper.cprint("constructed frame: " + str(f.fid))
            recv_fin_lock.release()
        
        recv_raw_lock.acquire()
        datalength = len(recv_raw_wrap.featuredata)
        recv_raw_lock.release()
        if datalength > 0:
            recv_raw_lock.acquire()
            pts = recv_raw_wrap.featuredata.pop(0)
            recv_raw_lock.release()
            recv_fin_lock.acquire()
            bisect.insort_left(recv_fin_wrap.featuredata, pts)
            #recv_fin_wrap.featuredata.append(pts)
            helper.cprint("constructed data: " + str(pts.fid))
            recv_fin_lock.release()
            #if not pts.fid % samplingrate == 0:
                # Need to create frame using delaunay triangulation
                # First, check if last frame is present
            if pts.data.mesh is not None:
                calibration_img_idx = get_most_similar_frame_idx(recv_raw_wrap.calibration_meshes, pts.data.mesh)
                pasted_body = morph.PasteBody(recv_raw_wrap.background_frame, recv_raw_wrap.calibration_frames[0], recv_raw_wrap.calibration_meshes[0], recv_raw_wrap.calibration_masks[0], pts.data.mesh)
                output_image = morph.ImageMorphingTriangulation(
                        recv_raw_wrap.calibration_frames[calibration_img_idx], recv_raw_wrap.calibration_meshes[calibration_img_idx], pts.data.mesh, 1, pasted_body, True
                )
                recv_fin_lock.acquire()
                recv_fin_wrap.framedata.append(Frame(output_image, pts.fid, False))
                recv_fin_lock.release()