class raw_wrapper(object):
    def __init__(self):
        self.tailframeid = 0
        self.framedata = []
        self.featuredata = []
        self.lastGoodFrames = {}
        self.lastGoodFramePoints = {}
        self.headframeid = 0