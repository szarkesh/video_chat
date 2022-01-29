from socket import socket

def send(socket: socket, data: str):
    totalSent = 0
    while totalSent < len(data):
        sent = socket.send(data[totalSent:].encode('utf-8'))
        if sent == 0:
            print("Lost connection, retrying...")
        totalSent += sent
        #print(str(totalSent) + "/" + str(len(data)))