import pickle
import morph
import cv2


def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation = inter)

    # return the resized image
    return resized

def main():

    srcFile = "example.mov"

    src_pts = pickle.load(open("facepts/" + srcFile.split(".")[0] + ".pkl", "rb"))

    cap = cv2.VideoCapture('videos/' + srcFile)

    frameIdx = 0
    samplingRate = 60 # sample every x frames
    lastGoodFrame = None
    lastGoodFramePoints = None

    cv2.namedWindow('1', cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('2', cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow('1', -200, 0)
    cv2.moveWindow('2', 600, 0)

    while (cap.isOpened()):

        # Capture frame-by-frame
        ret, frame = cap.read()
        #frame = image_resize(frame, width=300)
        if ret == True:

            if frameIdx % samplingRate == 0:
                lastGoodFrame = frame
                lastGoodFramePoints = src_pts[frameIdx]
            # Display the resulting frame

            for point in src_pts[frameIdx]:
                cv2.circle(frame, tuple(point), 2, color=(0, 0, 255), thickness=-1)
            morph.ImageMorphingTriangulation(lastGoodFrame, frame, lastGoodFramePoints, src_pts[frameIdx], 1, 0)

            frameIdx += 1
            # Press Q on keyboard to  exit
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break

        # Break the loop
        else:
            break
if (__name__ == "__main__"):
    main()