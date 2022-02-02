class client_wrapper(object):
    def __init__(self):
        self.name = "Default"
        self.oppname = "Opposite"
                
        self.waiting = False
        self.accepted = None
        self.calling = False
        self.timestamp = 0
        
        self.callid = ""
        self.oppositename = ""
        
        self.targetip = None
        self.targetport = None
        self.freshrate = 30
        self.resolution = 480


    # When it asks to read a specific size, give it that many bytes, and
    # update our remaining data.
    # def read(self, size):
    #    result = self.data[:size]
    #    self.data = self.data[size:]
    #    self.playhead = self.playhead + (float(size) / CHUNK_SIZE)
    #    return result