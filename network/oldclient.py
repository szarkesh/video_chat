import cv2, socket, pickle, os
s=socket.socket(socket.AF_INET , socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10000000)
serverip="localhost"
serverport=3100
cap = cv2.VideoCapture(0)
while True:
    ret,photo = cap.read()
    cv2.imshow('my pic', photo)
    ret, buffer = cv2.imencode(".jpg", photo, [int(cv2.IMWRITE_JPEG_QUALITY),30])
    x_as_bytes = pickle.dumps(buffer)
    s.sendto(x_as_bytes,(serverip , serverport))
    if cv2.waitKey(10) == 13:
        break
  
cv2.destroyAllWindows()
cap.release()