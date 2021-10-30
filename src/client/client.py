from datetime import date, datetime, timedelta
import socket
import select
import time
import sys
import os

sys.path.append('../')
from protocol import *

# Configuration
serverAddressPort   = ("127.0.0.1", 69)
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

def printIndex():
    length = len(currentIndexData)
    offset = 0
    print("\nCurrent server directory index:\n")
    index = 0
    if length == 0:
        print("Directory is empty.")
        return
    while offset != length:
        isDir,nameLen = struct.unpack('=?I',currentIndexData[offset:offset+5])
        offset+=5
        name = struct.unpack('='+str(nameLen)+'s',currentIndexData[offset:offset+nameLen])[0]
        offset+=nameLen
        if isDir:
            print("- ["+str(index)+"][DIR]\t"+ name)
        else:
            print("- ["+str(index)+"][FILE]\t"+ name)
        index+=1


# Wait timeoutSecs seconds for a message, returns False if no messages arrived
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
    if error == eveLoginErrId:
        print("\nError: Invalid credentials, try again.")
    elif error == eveAuthErrId:
        print("\nError: Auth failed.")
        logout()
    elif error == eveExpErrId:
        print("\nError: Expired token.")
        logout()
    elif error == evePohibitedDirAccessErrId:
        print("\nError: Prohibited directory access.")
    elif error == eveNotDirErrId:
        print("\nError: Item selected is not a directory or doesn't exist.")

def handleLostACK(event):
    global userId,expDatetime,token,serverAddressPort
    eventId = getMsgId(event)

    # If server missed index packet ACK
    if eventId == eveIndexTransferId:
        _,packetNumber,bytesSize,data = eveIndexTransfer.unpack(event)
        request = reqIndexACKTransfer.pack(reqIndexACKTransferId,packetNumber,userId,expDatetime,token)
        UDPClientSocket.sendto(request, serverAddressPort)

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
    request = reqLogin.pack(reqLoginId,tokenExp,username,password)

    # Retry login 4 times if server doesn't reply
    for i in range(4):
        UDPClientSocket.sendto(request, serverAddressPort)
        event = getNextMessage(2)
        if event == False:
            print("\nSending login request again " + str(i+1))
        else:
            eventId = getMsgId(event)

            # Login success
            if eventId == eveLoginId:
                _,userId,expDatetime,token = eveLogin.unpack(event)
                print("\nLogged in!")
                return
            # Invalid credentials
            elif eventId == eveLoginErrId:
                print("\nInvalid credentials, try again.")
                login()
                return
            elif eventId < 0:
                handleError(eventId)
            else:
                handleLostACK(event)

def help():
    print("\nList of Commands:\n")
    if token == "":
        print("     - login        : Opens login prompt.")   
    else:
        print("     - logout       : Ends user session.")
        print("     - index        : Gets current server index directory.")
        print("     - back         : Gets previus server index directory.")
        print("     - goto i       : Goes to the directory at index i.")
        print("     - get i        : Gets file at index i and stores it in './downloads'.")
        print("     - send path    : Sends local file located in 'path' to the current directory in the server.")      



# Get the current server index directory
def getIndex():
    global userId,expDatetime,token,currentIndexData

    # Create request message
    request = reqIndex.pack(reqIndexId,userId,expDatetime,token)
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
            if eventId == eveIndexTransferId:
                _,indexSize = eveIndex.unpack(event)

                # If directory is empty
                if indexSize == 0:
                    currentIndexData = bytearray()
                    printIndex()
                    return

                print("\nGot index size: "+str(indexSize)+" bytes")
                if indexSize == 0:
                    print("\nCurrent directory is empty, use 'back' command to go back.")
                    return
                else:
                    # Send init index transfer request
                    request = reqIndexInitTransfer.pack(reqIndexInitTransferId,True,userId,expDatetime,token)

                    # Retry login 4 times if server doesn't reply
                    for j in range(4):
                        UDPClientSocket.sendto(request, serverAddressPort)
                        event = getNextMessage(2)
                        if event == False:
                            print("\nSending index transfer request again " + str(j+1))
                        else:
                            print("\nTransfer started !")
                            transferFinished = False
                            indexData = bytearray(indexSize)
                            totalPackets = int(indexSize/507)
                            if indexSize % 507 != 0:
                                totalPackets += 1
                            packetsReceived = [False]*totalPackets
                            totalBytesReceived = 0

                            while transferFinished == False:
                                if event == False:
                                    print("\nTransfer failed due to server response timeout.")
                                    return
                                else:
                                    eventId = getMsgId(event)
                                    if eventId == eveIndexTransferId:
                                        bytesSize = len(event) - 5
                                        _,packetNumber,data = struct.unpack("=b I "+str(bytesSize)+"s",event)
                            
                                        # Sends ACK
                                        request = reqIndexACKTransfer.pack(reqIndexACKTransferId,packetNumber,userId,expDatetime,token)
                                        UDPClientSocket.sendto(request, serverAddressPort)

                                        # Check if packet has already been received
                                        if not packetsReceived[packetNumber]:
                                            # Stores packet
                                            offset = 507*packetNumber
                                            indexData[offset:offset+bytesSize] = data[:bytesSize]
                                            totalBytesReceived += bytesSize
                                            packetsReceived[packetNumber] = True

                                            print("\n"+str(100*totalBytesReceived/indexSize)+"% of directory index received.")
                                            if totalBytesReceived == indexSize:
                                                print("\nDirectory index received successfully.")
                                                currentIndexData = indexData
                                                printIndex()
                                                return

                                        event = getNextMessage(60)
                                    elif eventId < 0:
                                        handleError(eventId)
                                        return
                                    else:
                                        handleLostACK(event)
                    print("\nIndex transfer failed due to server response timeout.")
                    return
            elif eventId < 0:
                handleError(eventId)
                return
            else:
                handleLostACK(event)

def goBack():
    global userId,expDatetime,token,currentIndexData
    request = reqBack.pack(reqBackId,userId,expDatetime,token)
    print("\nWaiting for go back response...")

    # Retry login 4 times if server doesn't reply
    for i in range(4):
        UDPClientSocket.sendto(request, serverAddressPort)
        event = getNextMessage(10)
        if event == False:
            print("\nSending go back request again " + str(i+1))
        else:
            eventId = getMsgId(event)
            if eventId == eveBackId:
                print("\nGo back successfull.")
                getIndex()
                return
            elif eventId < 0:
                handleError(eventId)
                return
            else:
                handleLostACK(event)
    print("\nSending go back request failed due to server response timout.")

def goTo(index):
    global userId,expDatetime,token,currentIndexData
    request = reqGoto.pack(reqGotoId,index,userId,expDatetime,token)
    print("\nWaiting for goto response...")

    # Retry login 4 times if server doesn't reply
    for i in range(4):
        UDPClientSocket.sendto(request, serverAddressPort)
        event = getNextMessage(10)
        if event == False:
            print("\nSending goto request again " + str(i+1))
        else:
            eventId = getMsgId(event)
            if eventId == eveGotoId:
                print("\nGoto successfull.")
                getIndex()
                return
            elif eventId < 0:
                handleError(eventId)
                return
            else:
                handleLostACK(event)
    print("\nSending goto request failed due to server response timout.")

def getFile(index):
    global userId,expDatetime,token,currentIndexData
    request = reqFileInfo.pack(reqFileInfoId,index,userId,expDatetime,token)
    print("\nWaiting for file size response...")

    # Retry login 4 times if server doesn't reply
    for i in range(4):
        UDPClientSocket.sendto(request, serverAddressPort)
        event = getNextMessage(5)
        if event == False:
            print("\nSending file size request again " + str(i+1))
        else:
            eventId = getMsgId(event)

            # File size received
            if eventId == eveFileInfoId:
                _,transferId,fileSize,filename = eveFileInfo.unpack(event)
                
                if fileSize == 0:
                    print("\nFile contains no data.")
                    request = reqFileInitTransfer.pack(reqFileInitTransferId,transferId,False,userId,expDatetime,token)
                    UDPClientSocket.sendto(request, serverAddressPort)
                    print("\nFile transfer aborted.")
                    return

                # Ask if init transfer
                print("\nFile name: "+filename.rstrip('\x00'))
                print("\nFile size: "+str(fileSize)+" bytes")
                ques = raw_input("\nDo you wish to init transfer? (y/n) ")
                if ques != "y":
                    request = reqFileInitTransfer.pack(reqFileInitTransferId,transferId,False,userId,expDatetime,token)
                    UDPClientSocket.sendto(request, serverAddressPort)
                    print("\nFile transfer aborted.")
                    return

                
                # Send init index transfer request
                request = reqFileInitTransfer.pack(reqFileInitTransferId,transferId,True,userId,expDatetime,token)

                # Retry login 4 times if server doesn't reply
                for j in range(4):
                    UDPClientSocket.sendto(request, serverAddressPort)
                    event = getNextMessage(60)
                    if event == False:
                        print("\nSending file transfer request again " + str(j+1))
                    else:
                        print("\nFile transfer started !")
                        transferFinished = False
                        totalPackets = int(fileSize/506)
                        if fileSize % 506 != 0:
                            totalPackets += 1
                        packetsReceived = [False]*totalPackets
                        totalBytesReceived = 0
                        fd = open('./downloads/'+filename.rstrip('\x00'), 'w')

                        while transferFinished == False:
                            if event == False:
                                print("\nTransfer failed due to server response timeout.")
                                return
                            else:
                                eventId = getMsgId(event)
                                if eventId == eveFileTransferId:
                                    
                                    bytesSize = len(event) - 6
                                    
                                    _,transferId,packetNumber,data = struct.unpack("=b B I "+str(bytesSize)+"s",event)

                                    # Sends ACK
                                    request = reqFileACKTransfer.pack(reqFileACKTransferId,transferId,packetNumber)
                                    UDPClientSocket.sendto(request, serverAddressPort)

                                    # Check if packet has already been received
                                    if not packetsReceived[packetNumber]:
                                        # Stores packet
                                        offset = packetNumber*506
                                        fd.seek(offset)
                                        fd.write(data[:bytesSize])
                                        totalBytesReceived += bytesSize
                                        packetsReceived[packetNumber] = True

                                        print("\n"+str(100*totalBytesReceived/fileSize)+"% of file received.")
                                        if totalBytesReceived == fileSize:
                                            print("\nFile received successfully.")
                                            fd.close()
                                            return

                                    event = getNextMessage(60)
                                elif eventId < 0:
                                    handleError(eventId)
                                    return
                                else:
                                    handleLostACK(event)
                print("\nIndex transfer failed due to server response timeout.")
                return
            elif eventId < 0:
                handleError(eventId)
                return
            else:
                handleLostACK(event)

def sendFile(path):
    global userId,expDatetime,token,currentIndexData

    if not os.path.exists(path):
        print("\nError: File doesn't exists.")
        return
    if os.path.isdir(path):
        print("\nError: Item is not a file.")
        return
    filesize = os.path.getsize(path)
    filename = path.split('/')[-1]

    print(filename)

    request = struct.pack('=b Q H 14s 32s '+str(len(filename))+'s',reqPostTransferId,filesize,userId,expDatetime,token,filename)
    UDPClientSocket.sendto(request, serverAddressPort)
    event = getNextMessage(3)

    if event != False:
        eventId = getMsgId(event)
        if eventId == eveFilePostId:
            _,transferId = eveFilePost.unpack(event)
            fd = open(path,"r")
            totalPackets = int(filesize/506)
            if filesize % 506 != 0:
                totalPackets+=1
            packets = []
            for i in range(totalPackets-1):
                packets.append({"lastSend":None,"receivedACK":False,"size":506})
            packets.append({"lastSend":None,"receivedACK":False,"size":filesize % 506})

            lastACK = datetime.now()
            lastPer = 0
            while True:
                activePackets = 0
                ackPackets = 0
                if lastACK + timedelta(seconds=60) < datetime.now():
                    print("Error: File posting failed due server response timout.")
                    return
                for packet in packets:
                    if packet["lastSend"] != None and packet["receivedACK"] == False and packet["lastSend"] + timedelta(seconds=10) > datetime.now():
                        activePackets += 1
                    if packet["receivedACK"]:
                        ackPackets += 1

                per = int(100*ackPackets/totalPackets)
                if lastPer != per:
                    print(str(per) + "% of file data transfered.")
                    lastPer = per
                if ackPackets == totalPackets:
                    print("Successful file post.")
                    return
                else:
                    ind = 0
                    while activePackets <= 10 and ind < totalPackets:
                        if packets[ind]["lastSend"] == None or (packets[ind]["receivedACK"] == False and packets[ind]["lastSend"] != None and packets[ind]["lastSend"] + timedelta(seconds=10) < datetime.now()):
                            fd.seek(506*ind)
                            request = struct.pack('=b B I '+str(packets[ind]["size"])+'s',reqPostPacketId,transferId,ind,fd.read(packets[ind]["size"]))
                            packets[ind]["lastSend"] = datetime.now()
                            UDPClientSocket.sendto(request, serverAddressPort)
                            activePackets+=1
                        ind+=1
                event = getNextMessage(0)
                while event != False:
                    eventId = getMsgId(event)
                    if eventId == eveFilePostACKId:
                        _,transferId,packetNumber = eveFilePostACK.unpack(event)
                        lastACK = datetime.now()
                        packets[packetNumber]["receivedACK"] = True
                    event = getNextMessage(0)




        elif eventId < 0:
            handleError(eventId)
            return
    else:
        print("Error: Server response timeout.")


while True:

    # Handle problematic messages
    event = getNextMessage(0)
    if event:
        handleLostACK(event)

    # Print help info
    help()

    # Read input command
    command = raw_input("\n>> ").split(' ')

    # Process command
    if command[0] == 'login':
        login()
    elif command[0] == 'logout':
        logout()
    elif command[0] == 'index':
        getIndex()
    elif command[0] == 'back':
        goBack()
    elif command[0] == 'goto':
        goTo(int(command[1]))
    elif command[0] == 'get':
        getFile(int(command[1]))
    elif command[0] == 'send':
        sendFile(''.join(command[1:]))

