#!/usr/bin/python
from socket import *
import sys
import os

serverPort = 80

def createSocket(serverName, serverPort):
    return socket(AF_INET, SOCK_STREAM)

def splitLink(link):
    return link.split("/", 1)

# Create GET request message
def createGETrequestMessage(directory, serverName, rangeStart=-1, rangeEnd=-1):
    if rangeStart > -1 and rangeEnd > -1:
        return "GET /%s HTTP/1.1\r\nHost:%s\r\nRange: bytes=%d-%d\r\n\r\n" % (directory, serverName, rangeStart, rangeEnd)
    return "GET /%s HTTP/1.1\r\nHost:%s\r\n\r\n" % (directory, serverName)

# Create HEAD request message
def createHEADrequestMessage(directory, serverName, rangeStart=-1, rangeEnd=-1):
    if rangeStart > -1 and rangeEnd > -1:
        return "HEAD /%s HTTP/1.1\r\nHost:%s\r\nRange: bytes=%d-%d\r\n\r\n" % (directory, serverName, rangeStart, rangeEnd)

    return "HEAD /%s HTTP/1.1\r\nHost: %s\r\n\r\n" % (directory, serverName)

def getBody(head, get):
    message = get[len(head):]
    lines = []
    for line in message.splitlines():
        lines.append(line)
    return lines

def save_file(file_name, body):
    file_name = file_name.replace("/", "")
    f = open(os.path.join(os.getcwd(), file_name), 'w')
    for i in body:
        f.write(i + "\r\n")
    f.close()

def prepareSocket(server_name, request_mes):
    clientSocket = createSocket(server_name, serverPort)
    clientSocket.connect((server_name, serverPort))
    clientSocket.send(request_mes.encode())
    return clientSocket

def download_files(links, upper_endpoint, lower_endpoint):
    responseList = []
    
    count = 1
    for link in links:
        link_data = splitLink(link)
        requestMessageHead = createHEADrequestMessage(link_data[1], link_data[0])
        requestMessageGet = createGETrequestMessage(link_data[1], link_data[0])

        clientSocket = prepareSocket(link_data[0], requestMessageHead)

        responseHead = ""
        while True:
            resp_part = clientSocket.recv(4096)
            if resp_part == b'':
                break
            responseHead += resp_part.decode()
        clientSocket.close()

        clientSocket = prepareSocket(link_data[0], requestMessageGet)

        responseGet = ""
        while True:
            resp_part = clientSocket.recv(4096)
            if resp_part == b'':
                break
            responseGet += resp_part.decode()

        clientSocket.close()
        if "200 OK" in responseHead.splitlines()[0]:
            responseList.append([link, responseHead])
            body = getBody(responseHead, responseGet)
            if upper_endpoint > -1 or lower_endpoint > -1:
                if len(body) <= lower_endpoint:
                    print("%d. %s (size = %d) is downloaded." %(count, link, lower_endpoint))
                    print("ERROR: The requested file is not requested since the size of the file is smaller than lower endpoint!")
                else:
                    requestMessagePartialGET = createGETrequestMessage(link_data[1], link_data[0], lower_endpoint, upper_endpoint)
                    requestMessagePartialHEAD = createHEADrequestMessage(link_data[1], link_data[0], lower_endpoint, upper_endpoint)
                    
                    clientSocket = prepareSocket(link_data[0], requestMessagePartialGET)

                    responsePartialGET = ""
                    while True:
                        resp_part = clientSocket.recv(4096)
                        if resp_part == b'':
                            break
                        responsePartialGET += resp_part.decode()
                    
                    clientSocket.close()

                    clientSocket = prepareSocket(link_data[0], requestMessagePartialHEAD)

                    responsePartialHEAD = ""
                    while True:
                        resp_part = clientSocket.recv(4096)
                        if resp_part == b'':
                            break
                        responsePartialHEAD += resp_part.decode()
                    
                    clientSocket.close()

                    partialBody = getBody(responsePartialHEAD, responsePartialGET)
                    save_file(link_data[1], partialBody)  
                    print("%d. %s (range = %d - %d) is downloaded." %(count, link, lower_endpoint, upper_endpoint))

            else:
                save_file(link_data[1], body)  
                print("%d. %s (range = Complete file) is downloaded." %(count, link))
        else:
            print("%d. %s is not found." %(count, link))

        count += 1

    return responseList

index_file = ""
endpoints = ""
upper_endpoint = -1
lower_endpoint = -1

for i, arg in enumerate(sys.argv):
    # Index 0 is FileDownloader.py So we start at 1
    if i == 1:
        index_file = arg
    elif i == 2:
        endpoints = arg
        endpoints = endpoints.split("-")

        lower = endpoints[0].split("[")
        upper = endpoints[1].split("]")

        lower_endpoint = int(endpoints[0])
        upper_endpoint = int(endpoints[1])

index_file = splitLink(index_file)

# Specify server name and server port
serverName = index_file[0]
directory = index_file[1]

print("URL of the index file: %s" %sys.argv[1])

if lower_endpoint > -1:
    print("Lower endpoint = %d" %lower_endpoint)
else:
    print("Lower endpoint = Not specified")

if upper_endpoint > -1:
    print("Lower endpoint = %d" %upper_endpoint)
else:
    print("Lower endpoint = Not specified")


# Create client socket
requestMessageIndexGET = createGETrequestMessage(directory, serverName)
clientSocket = prepareSocket(serverName, requestMessageIndexGET)

responseIndexGET = ""
while True:
    resp_part = clientSocket.recv(4096)
    if resp_part == b'':
        break
    responseIndexGET += resp_part.decode()

clientSocket.close()

# Create client socket
requestMessageIndexHEAD = createHEADrequestMessage(directory, serverName)
clientSocket = prepareSocket(serverName, requestMessageIndexHEAD)

responseIndexHEAD = ""
while True:
    resp_part = clientSocket.recv(4096)
    if resp_part == b'':
        break
    responseIndexHEAD += resp_part.decode()

clientSocket.close()

file_count = -1

body = ""
if "200 OK" in responseIndexHEAD.splitlines()[0]:
    body = getBody(responseIndexHEAD, responseIndexGET)
    file_count = len(body)
    print("There are %d file URLs in the index file." % file_count)
    print("Index file is downloaded.")
else:
    print("ERROR: The index file is not found!\r\n" + responseIndexHEAD.splitlines()[0])
    sys.exit(1)

responseList = download_files(body, upper_endpoint, lower_endpoint)
