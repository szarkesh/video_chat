class raw_wrapper(object):
    def __init__(self):
        self.tailframeid = 0
        self.framedata = []
        self.featuredata = []
        self.lastGoodFrames = {}
        self.lastGoodFramePoints = {}
        self.headframeid = 0
        self.calibration_frames = []
        self.calibration_meshes = []
        self.calibration_poses = []
        self.calibration_masks = []
        self.background_frame = None