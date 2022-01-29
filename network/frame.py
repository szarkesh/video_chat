from threading import Lock, Thread
import numpy as np

class Frame:
    def __init__(self, data: bytes, fid: int, isRaw: bool):
        self.lock = Lock()
        self.isRaw = isRaw
        self.fid = fid
        self.data = data
        