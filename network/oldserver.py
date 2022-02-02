import cv2, socket, numpy, pickle, time
s=socket.socket(socket.AF_INET , socket.SOCK_DGRAM)
ip="localhost"
port=3100
s.bind((ip,port))
total=0
start_time=time.time()
while True:
    x=s.recvfrom(100000000)
    end_time=time.time()
    total+=len(x[0])
    if (total % 500000):
        print("Total Transfer (bytes) >=" + str(total))
        print("Bytes / s : " + str(len(x[0])/(1000 * (end_time - start_time))))
    clientip = x[1][0]
    data=x[0]
    data=pickle.loads(data)
    data = cv2.imdecode(data, cv2.IMREAD_COLOR)
    cv2.imshow('my pic', data) #to open image
    if cv2.waitKey(10) == 13:
        break
cv2.destroyAllWindows()