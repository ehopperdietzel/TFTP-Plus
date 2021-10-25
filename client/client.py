import socket
import select
import time
import sys

sys.path.append('../')
from protocol import *

# Configuration
serverAddressPort   = ("127.0.0.1", 3000)
bufferSize          = 512


# Session credentials
userId              = 0
expDatetime         = ""
token               = ""

# Current dir index
currentIndexData = bytearray()

# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.bind(("127.0.0.1", 6000))


print("\nWelcome to TFTP+\n")

def getNextMessage(timeoutSecs):

    if len(select.select([UDPClientSocket],[],[],timeoutSecs)[0]) == 0:
        return False
    else:
        return UDPClientSocket.recvfrom(bufferSize)[0]

def logout():
    global userId,expDatetime,token
    userId              = 0
    expDatetime         = ""
    token               = ""
    print("\nLogged out!")

def handleError(error):
    if error == -1:
        print("\nError: Invalid credentials, try again.")
    elif error == -2:
        print("\nError: Auth failed.")
        logout()
    elif error == -3:
        print("\nError: Expired token.")
        logout()

def login():
    global userId,expDatetime,token,serverAddressPort
    username = raw_input("\nusername: ")
    lenUsername = len(username)
    if lenUsername > 255:
        print("\nerror: username must be less than or equal to 254 chars long.\n")
        login()
        return

    password = raw_input("\npassword: ")
    lenPassword = len(password)
    if lenPassword > 256:
        print("\nerror: password must be less that or equal to 254 chars long.")
        login()
        return
    
    tokenExp = int(raw_input("\ntoken expiration time in hours (0 for no expiration): "))
    if tokenExp < 0 or tokenExp > 65535:
        print("\nerror: expiration time must be a value from 0 to 65535.")
        login()
        return

    print("\nWaiting for server response...")
    request = reqLogin.pack(0,tokenExp,username,password)

    # Retry login 4 times if server doesn't reply
    for i in range(4):
        UDPClientSocket.sendto(request, serverAddressPort)
        event = getNextMessage(2)
        if event == False:
            print("\nSending login request again " + str(i+1))
        else:
            eventId = getMsgId(event)

            # Login success
            if eventId == 0:
                _,userId,expDatetime,token = eveLogin.unpack(event)
                print("\nLogged in!")
                return
            # Invalid credentials
            elif eventId == -1:
                print("\nInvalid credentials, try again.")
                login()
                return
            elif eventId < 0:
                handleError(eventId)

def help():
    print("\nList of Commands:\n")
    if token == "":
        print("     - login: Opens login prompt.")   
    else:
        print("     - logout       : Ends user session.")
        print("     - index        : Gets current server index directory.")
        print("     - back         : Gets previus server index directory.")
        print("     - goto i       : Goes to the directory at index i and gets the index directory.")
        print("     - get i path   : Get file at index i and stores it in 'path'.")
        print("     - send path    : Sends local file located in 'path' to the current path in server.")      




def index():
    global userId,expDatetime,token,currentIndexData
    request = reqIndex.pack(1,userId,expDatetime,token)
    print("\nWaiting for current directory index size response...")

    # Retry login 4 times if server doesn't reply
    for i in range(4):
        UDPClientSocket.sendto(request, serverAddressPort)
        event = getNextMessage(2)
        if event == False:
            print("\nSending index request again " + str(i+1))
        else:
            eventId = getMsgId(event)

            # Index size received
            if eventId == 2:
                _,indexSize = eveIndex.unpack(event)
                print("\nGot index size: "+str(indexSize)+" bytes")
                if indexSize == 0:
                    print("\nCurrent directory is empty, use 'back' command to go back.")
                    return
                else:
                    # Send init index transfer request
                    request = reqIndexInitTransfer.pack(2,True,userId,expDatetime,token)

                    # Retry login 4 times if server doesn't reply
                    for j in range(4):
                        UDPClientSocket.sendto(request, serverAddressPort)
                        event = getNextMessage(2)
                        if event == False:
                            print("\nSending index transfer request again " + str(j+1))
                        else:
                            print("\nTransfer started !")
                            transferFinished = False
                            indexData = bytearray()
                            while transferFinished == False:
                                if event == False:
                                    print("\nTransfer failed due to server response timeout.")
                                    return
                                else:
                                    eventId = getMsgId(event)
                                    if eventId == 2:
                                        _,packetNumber,bytesSize,data = eveIndexTransfer.unpack(event)
                                        request = reqIndexACKTransfer.pack(3,packetNumber,userId,expDatetime,token)
                                        UDPClientSocket.sendto(request, serverAddressPort)
                                        indexData += data[:bytesSize]
                                        lenIndexData = len(indexData)
                                        print("\n"+str(100*lenIndexData/indexSize)+"% of directory index received.")
                                        if lenIndexData == indexSize:
                                            print("\nDirectory index received successfully.")
                                            currentIndexData = indexData
                                            return
                                        event = getNextMessage(60)
                                    elif eventId < 0:
                                        handleError(eventId)
                                        return
                    print("\nIndex transfer failed due to server response timeout.")
                    return

while True:

    help()

    command = raw_input("\n>> ").split()

    if command[0] == 'login':
        login()
    elif command[0] == 'logout':
        logout()
    elif command[0] == 'index':
        index()
